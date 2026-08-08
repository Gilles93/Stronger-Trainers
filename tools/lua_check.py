"""Run the mod's actual Lua, headless, under the interpreter LOVE uses.

tests/run.sh is the fuller check -- it goes through the engine's real mod
loader -- but it needs a LOVE runtime on the machine. This needs nothing but
the repo: lupa embeds LuaJIT 2.1, which is the same Lua 5.1 dialect LOVE
runs, so main.lua and smart_ai.lua are compiled and executed for real rather
than eyeballed.

What it proves:

  * every Lua file compiles under Lua 5.1 (not 5.4 -- `loadstring` and the
    absence of integer division are real differences);
  * boss_teams.lua is version-keyed and every version has a full table;
  * the trainer.party hook hands back the right party for the fights that
    were broken -- Yellow's OPP_RIVAL1#2 and #3 in particular;
  * the new switch decision rotates when outclassed, holds when ahead, and
    refuses on ordinary trainers.

    python tools/lua_check.py
"""

from __future__ import annotations

import os
import sys

from lupa.luajit21 import LuaRuntime

import gamedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUA_FILES = ("main.lua", "boss_teams.lua", "gym_formats.lua", "smart_ai.lua")

checks = 0
failures = 0


def check(cond, label):
    global checks, failures
    checks += 1
    if cond:
        print(f"  ok    {label}")
    else:
        failures += 1
        print(f"  FAIL  {label}")
    return bool(cond)


def eq(got, want, label):
    return check(got == want, f"{label} (got {got!r}, want {want!r})")


def read(name):
    with open(os.path.join(REPO, name), "r", encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. compiles

def compile_all():
    print("== compiles under Lua 5.1 (LuaJIT 2.1, as LOVE runs it)")
    for name in LUA_FILES:
        lua = LuaRuntime(unpack_returned_tuples=True)
        chunk = lua.eval("function(src, name) return loadstring(src, name) end")
        fn, err = None, None
        result = chunk(read(name), "@" + name)
        if isinstance(result, tuple):
            fn, err = (result + (None, None))[:2]
        else:
            fn = result
        check(fn is not None, f"{name} compiles" + (f" ({err})" if err else ""))


# ------------------------------------------------------- 2. the roster table

def roster_table():
    print("\n== boss_teams.lua shape")
    lua = LuaRuntime(unpack_returned_tuples=True)
    teams = lua.execute(read("boss_teams.lua"))
    versions = sorted(k for k in teams.keys())
    eq(versions, ["blue", "red", "yellow"], "keyed by all three versions")
    for version in versions:
        table = teams[version]
        count = sum(1 for _ in table.keys())
        check(count > 25, f"{version} carries {count} rosters")
    return teams


# --------------------------------------------- 3. the mod, running for real

STUB = """
local VERSION, FILES, DATA = ...

-- require: engine modules the mod reaches for, stubbed to the minimum the
-- code under test actually touches.
local stubs = {}
stubs["src.core.GameVersion"] = {
  get = function() return VERSION end,
  isYellow = function() return VERSION == "yellow" end,
}
stubs["src.battle.Damage"] = {
  -- never enough to finish anything, so canFinish() cannot mask a switch
  compute = function() return 0 end,
}
stubs["src.battle.TypeChart"] = {
  effectiveness = function(moveType, defenderTypes)
    local mult = 10
    for _, dt in ipairs(defenderTypes) do
      local row = DATA.matchups[moveType .. ">" .. dt]
      if row then mult = math.floor(mult * row / 10) end
    end
    return mult
  end,
  rows = function() return {} end,
}
local realRequire = require
require = function(name)
  if stubs[name] then return stubs[name] end
  error("unstubbed require: " .. tostring(name), 0)
end

-- the slice of the mod API these files use
local recorded = { hooks = {}, options = {}, warnings = {} }
local optionValues = {}

local function registry(backing)
  return {
    register = function() end,
    patch = function() end,
    each = function()
      if not backing then return function() return nil end end
      return coroutine.wrap(function()
        for id, record in pairs(backing) do coroutine.yield(id, record) end
      end)
    end,
    get = function(_, id) return DATA.pokemon[id] end,
  }
end

local mod = {
  read = function(_, name) return FILES[name] end,
  log = {
    warn = function(_, fmt, ...)
      recorded.warnings[#recorded.warnings + 1] = tostring(fmt)
    end,
    info = function() end,
  },
  options = {
    define = function(_, rows)
      for _, row in ipairs(rows) do
        recorded.options[#recorded.options + 1] = row.key
        optionValues[row.key] = row.default
      end
    end,
    get = function(_, key) return optionValues[key] end,
  },
  hooks = {
    wrap = function(_, name, fn) recorded.hooks[name] = fn end,
  },
  events = { on = function() end },
  content = {
    pokemon = registry(DATA.pokemon),
    encounters = registry(DATA.encounters),
    trainers = registry(), ai_classes = registry(),
  },
  exports = {},
}

local chunk = assert(loadstring(FILES["main.lua"], "@main.lua"))
chunk()(mod)

return { mod = mod, recorded = recorded, options = optionValues }
"""


def lua_data(lua, g):
    """The engine data surface the mod actually touches, as Lua tables.

    Pokemon records carry types AND evolutions, because the padding pool needs
    both: evolutions to work out which species are base stages, types to work
    out what is on theme. Encounters come through whole so the wild-species
    filter is exercised against real encounter tables rather than a fixture.
    """
    pokemon = {}
    for sid, rec in g.species.items():
        evos = [lua.table_from({
            "species": e["species"], "method": e.get("method"),
            "level": e.get("level"),
        }) for e in (rec.get("evolutions") or [])]
        pokemon[sid] = lua.table_from({
            "types": lua.table_from(list(rec["types"])),
            "evolutions": lua.table_from(evos),
        })

    encounters = {}
    for mid, rec in g.encounters.items():
        groups = {}
        for field in ("grass", "water"):
            group = rec.get(field)
            if not group:
                continue
            slots = [lua.table_from({"species": s["species"], "level": s["level"]})
                     for s in (group.get("slots") or [])]
            groups[field] = lua.table_from({"slots": lua.table_from(slots)})
        if groups:
            encounters[mid] = lua.table_from(groups)

    return lua.table_from({
        "pokemon": lua.table_from(pokemon),
        "encounters": lua.table_from(encounters),
        "matchups": lua.table_from(
            {f"{a}>{d}": m for (a, d), m in g.matchups.items()}),
    })


def run_mod(version, g):
    lua = LuaRuntime(unpack_returned_tuples=True)
    files = lua.table_from({name: read(name) for name in LUA_FILES})
    data = lua_data(lua, g)
    loader = lua.execute(
        "return function(src) return assert(loadstring(src, '@stub')) end")
    return lua, loader(STUB)(version, files, data)


def behaviour():
    print("\n== the trainer.party hook, per version")
    for version in ("red", "blue", "yellow"):
        g = gamedata.load("red" if version == "blue" else version)
        lua, env = run_mod(version, g)
        print(f"  -- {version}")

        opts = env["recorded"]["options"]
        names = [opts[i] for i in range(1, len(list(opts.values())) + 1)]
        check("boss_switching" in names, "BOSS SWITCHING option defined")
        check("boss_switch_cap" in names, "switch cap option defined")

        hook = env["recorded"]["hooks"]["trainer.party"]
        check(hook is not None, "trainer.party hook registered")

        def party(cls, index):
            vanilla = g.trainers.get(cls) or []
            base = vanilla[index - 1] if index <= len(vanilla) else []
            luabase = lua.table_from([
                lua.table_from({"species": s, "level": l}) for s, l in base])
            got = hook(lambda: luabase, cls, index, luabase)
            return [(got[i]["species"], got[i]["level"])
                    for i in range(1, len(list(got.values())) + 1)]

        lab = party("OPP_RIVAL1", 1)
        eq(len(lab), 1, "rival's lab battle is one Pokemon")

        second = party("OPP_RIVAL1", 2)
        if version == "yellow":
            check(len(second) > 1,
                  f"yellow OPP_RIVAL1#2 is the Route 22 team ({len(second)} slots)")
            check(max(l for _, l in second) > 6,
                  "yellow OPP_RIVAL1#2 outlevels the lab fight")
            third = party("OPP_RIVAL1", 3)
            check(len(third) > 1, "yellow OPP_RIVAL1#3 is the Cerulean team")
            check(max(l for _, l in third) > max(l for _, l in second),
                  "Cerulean outlevels Route 22")
            check(lab[0][0] == "EEVEE", "yellow rival leads with Eevee")
        else:
            eq(len(second), 1, f"{version} OPP_RIVAL1#2 is still a lab variant")
            check(lab[0][0] in ("SQUIRTLE", "BULBASAUR", "CHARMANDER"),
                  f"{version} rival leads with a starter")

        brock = party("OPP_BROCK", 1)
        eq(len(brock), 6, "Brock fields six")
        expect = 17 if version == "yellow" else 19
        eq(max(l for _, l in brock), expect,
           f"Brock's ace is the computed {version} level")

        sabrina = party("OPP_SABRINA", 1)
        eq(max(l for _, l in sabrina), 56, "Sabrina's ace is the computed level")

        # an ordinary trainer still just gets scaled, not replaced
        grunt = party("OPP_YOUNGSTER", 1)
        check(len(grunt) >= 3, "an ordinary trainer is padded to the minimum")

        # Padding brings variety, not copies.
        #
        # Two things this must NOT assert. Vanilla parties repeat species on
        # their own (a Lass really does field two Pidgey), so only the slots
        # padding added are checked for novelty. And the theme is read off the
        # kept slots as the mod sees them -- post level bump and evolution --
        # not off the vanilla base forms, because an evolution can add a type.
        padded, dupes, off_theme, examples = 0, 0, 0, []
        for cls in ("OPP_YOUNGSTER", "OPP_BUG_CATCHER", "OPP_LASS",
                    "OPP_SAILOR", "OPP_HIKER", "OPP_FISHER", "OPP_ROCKET"):
            for index in range(1, min(4, len(g.trainers.get(cls) or [])) + 1):
                original = g.trainers[cls][index - 1]
                got = party(cls, index)
                if len(got) <= len(original):
                    continue
                padded += 1
                kept, added = got[:len(original)], got[len(original):]
                theme = set()
                for sp, _ in kept:
                    theme.update(g.types(sp))
                seen = {sp for sp, _ in kept}
                for sp, _ in added:
                    if sp in seen:
                        dupes += 1
                    seen.add(sp)
                    if not (set(g.types(sp)) & theme):
                        off_theme += 1
                        examples.append(f"{cls}#{index} {sp}{g.types(sp)}"
                                        f" vs {sorted(theme)}")
        check(padded > 0, f"{padded} ordinary parties actually got padded")
        if g.encounters:
            eq(dupes, 0, "padding never repeats a species already on the team")
        else:
            # No encounter data means no way to tell a catchable Pokemon from a
            # legendary, so the feature stands down and the old copy-padding
            # applies. Assert that fallback rather than skipping it: a real
            # game always has encounter data loaded, so this path only shows up
            # here, and it must stay harmless.
            check(dupes > 0,
                  "without encounter data, padding falls back to copies")
            check(off_theme == 0, "the fallback is still on theme")
        eq(off_theme, 0, "every padded Pokemon shares a type with the trainer"
                         + (" -- " + "; ".join(examples[:3]) if examples else ""))

        # and the same trainer brings the same Pokemon every time
        stable = all(party("OPP_BUG_CATCHER", 1) == party("OPP_BUG_CATCHER", 1)
                     for _ in range(3))
        check(stable, "a trainer's padded team is stable across encounters")


SWITCH_TEST = """
local aiState, DATA = ...
local consider = aiState.considerSwitch
if type(consider) ~= "function" then return { missing = true } end

local function battler(types)
  return { curTypes = types, curMoves = {},
           mon = { hp = 100, stats = { hp = 100 }, level = 50 } }
end
local function mon(species)
  return { species = species, hp = 100, stats = { hp = 100 }, level = 50 }
end
local function battle(oppClass, playerTypes, enemyTypes, bench, turn)
  return {
    kind = "trainer", oppClass = oppClass, turnCount = turn or 5,
    enemyIndex = 1, data = DATA,
    player = battler(playerTypes), enemy = battler(enemyTypes),
    enemyParty = { mon(bench[1]), mon(bench[2]) },
  }
end

local out = {}
-- a Fire boss facing Water, holding a Water backup: rotate to it
local losing = battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                      { "ARCANINE", "LAPRAS" })
local act = consider(losing)
out.rotates = act ~= nil and act.index == 2

-- already winning: do not throw away a turn
out.holds = consider(battle("OPP_BLAINE", { "GRASS" }, { "FIRE" },
                            { "ARCANINE", "LAPRAS" })) == nil

-- a grace turn after every send-out, so it cannot ping-pong
local fresh = battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                     { "ARCANINE", "LAPRAS" }, 0)
consider(fresh)
out.graceTurn = consider(fresh) == nil

-- ordinary trainers never rotate
out.bossesOnly = consider(battle("OPP_YOUNGSTER", { "WATER" }, { "FIRE" },
                                 { "ARCANINE", "LAPRAS" })) == nil

-- no backup worth the turn: stay put
out.noPointless = consider(battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                                  { "ARCANINE", "NINETALES" })) == nil

-- the cap is respected
local capped = battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                      { "ARCANINE", "LAPRAS" })
local n = 0
for i = 1, 8 do
  capped.turnCount = capped.turnCount + 2
  capped.enemyIndex = 1
  if consider(capped) then n = n + 1 end
end
out.capped = n <= 2
return out
"""


def switching():
    print("\n== boss switching decision")
    g = gamedata.load("red")
    lua, env = run_mod("red", g)
    ai = env["mod"]["exports"]["aiState"]
    if ai is None or ai["considerSwitch"] is None:
        check(False, "switch decision reachable (smart_ai installed)")
        return
    check(True, "switch decision reachable (smart_ai installed)")
    data = lua.table_from({
        "pokemon": lua.table_from({k: lua.table_from(
            {"types": lua.table_from(list(v["types"]))})
            for k, v in g.species.items()}),
        "moves": lua.table_from({}),
    })
    runner = lua.execute(
        "return function(src) return assert(loadstring(src, '@switch')) end")
    out = runner(SWITCH_TEST)(ai, data)
    check(not out["missing"], "considerSwitch is exported")
    check(out["rotates"], "an outclassed boss rotates to the backup that answers")
    check(out["holds"], "a boss with the advantage keeps its turn")
    check(out["graceTurn"], "no second rotation the turn a Pokemon came out")
    check(out["bossesOnly"], "ordinary trainers never rotate")
    check(out["noPointless"], "no rotation when no backup is actually better")
    check(out["capped"], "the per-fight switch cap holds")


def main():
    compile_all()
    roster_table()
    behaviour()
    switching()
    print(f"\n{checks} checks, {failures} FAILURES")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
