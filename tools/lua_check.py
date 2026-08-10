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

        # Every slot carries a moveset. A slot with none is not a lighter
        # roster, it is a different fight: the engine fills it with the last
        # four moves the species learns by growing up, which is how the Silph
        # Co. rival ended up leading with a Rhydon whose best attack was Fury
        # Attack at 15 power. Every rival fight shipped that way.
        bare = []
        for key in table.keys():
            for i, slot in enumerate(table[key].values(), start=1):
                if slot[3] is None:
                    bare.append(f"{key} slot {i} {slot[1]}")
        eq(len(bare), 0, f"{version}: every boss slot has an authored moveset"
                         + (" -- " + "; ".join(bare[:3]) if bare else ""))
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
-- Only executeAction matters here: the switching fix shadows it per battle
-- instance so the player's row cannot land on a Pokemon that already left.
-- Recording the triple it was finally handed is the whole assertion.
stubs["src.battle.BattleState"] = {
  executeAction = function(self, user, target, action)
    self.executed = { user = user, target = target, action = action }
  end,
}
-- gym_formats.lua reaches for five UI/script modules at install time. Stubbed
-- to nothing useful on purpose: the picker itself is not under test here, but
-- without them the whole file fails to install and its battle.started and
-- battle.ended handlers -- the prize scaling and the party restore -- never
-- register at all, which is how the prize bug hid.
stubs["src.script.MapScripts"] = { baseTalk = function() return nil end }
stubs["src.render.TextBox"] = { new = function() return {} end }
stubs["src.ui.QuantityBox"] = { isOpaque = function() return true end }
stubs["src.ui.PartyMenu"] = { new = function() return {} end }
stubs["src.core.Strings"] = setmetatable({}, {
  __call = function(_, fmt) return tostring(fmt) end })
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
local recorded = { hooks = {}, options = {}, warnings = {}, events = {} }
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
  -- a list per name, not one handler: main.lua, gym_formats.lua and
  -- smart_ai.lua all listen to battle.started, and the engine fires all three
  events = { on = function(_, name, fn)
    local list = recorded.events[name]
    if not list then list = {}; recorded.events[name] = list end
    list[#list + 1] = fn
  end },
  content = {
    pokemon = registry(DATA.pokemon),
    encounters = registry(DATA.encounters),
    trainers = registry(), ai_classes = registry(),
    map_scripts = registry(),
  },
  exports = {},
}

local chunk = assert(loadstring(FILES["main.lua"], "@main.lua"))
chunk()(mod)

return { mod = mod, recorded = recorded, options = optionValues,
         fire = function(name, ev)
           for _, fn in ipairs(recorded.events[name] or {}) do fn(ev) end
         end }
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


def formats():
    print("\n== gym battle formats")
    g = gamedata.load("red")
    lua, env = run_mod("red", g)
    hook = env["recorded"]["hooks"]["trainer.party"]
    state = env["mod"]["exports"]["formatState"]

    def leader(cls="OPP_BROCK"):
        vanilla = g.trainers[cls][0]
        base = lua.table_from([
            lua.table_from({"species": s, "level": l}) for s, l in vanilla])
        got = hook(lambda: base, cls, 1, base)
        return [got[i]["species"] for i in range(1, len(list(got.values())) + 1)]

    state["class"], state["count"] = None, None
    eq(len(leader()), 6, "no format picked leaves the full authored roster")

    # The one documented break from move legality, asserted so it cannot
    # quietly spread: Surge's Pikachu line carries Surf (the Stadium Surfing
    # Pikachu, which this engine already recognises), and nothing else does.
    import availability
    eq(sorted(availability.EVENT_LEGAL),
       [("PIKACHU", "SURF"), ("RAICHU", "SURF")],
       "exactly two moves are exempt from legality")

    state["class"], state["count"] = "OPP_BROCK", 3
    eq(len(leader()), 3, "a 3-each format cuts the authored roster to three")

    # The picker narrows YOUR side whatever the other toggles say, so the
    # leader has to honour the same number on the ordinary scaling path --
    # with BOSS TEAMS off it never used to, and "2 each" fielded 2 against 3.
    env["options"]["boss_teams"] = False
    state["count"] = 2
    eq(len(leader()), 2, "and cuts the leader's own party with BOSS TEAMS off")

    # Whichever roster it cuts, the ace survives -- and a tie at the top is
    # the normal case on the game's own rosters, not a corner: vanilla Erika
    # fields Victreebel and Vileplume both at 29, and taking the first of the
    # two dropped the Vileplume the gym is built around.
    state["class"] = "OPP_ERIKA"
    kept = leader("OPP_ERIKA")
    check("VILEPLUME" in kept,
          f"a tied ace keeps the roster's last slot (kept {kept})")

    # A shorter fight pays a shorter purse. Gen 1 reads prize money off the
    # LAST enemy Pokemon's level and the trim keeps the ace last, so "2 each"
    # used to pay exactly what "6 each" did.
    env["options"]["boss_teams"] = True
    state["class"], state["count"] = "OPP_BROCK", 2
    leader()                                   # the hook records full/fielded
    battle = lua.table_from({
        "oppClass": "OPP_BROCK",
        "trainer": lua.table_from({"baseMoney": 99}),
    })
    env["fire"]("battle.started", lua.table_from({"battle": battle}))
    eq(battle["trainer"]["baseMoney"], 33,
       "a 2-of-6 gym battle pays a third of the purse")

    # and a full-size fight is left alone
    state["class"], state["count"] = "OPP_BROCK", 6
    leader()
    full = lua.table_from({
        "oppClass": "OPP_BROCK",
        "trainer": lua.table_from({"baseMoney": 99}),
    })
    env["fire"]("battle.started", lua.table_from({"battle": full}))
    eq(full["trainer"]["baseMoney"], 99, "a full roster pays the full purse")


SWITCH_TEST = """
local aiState, DATA, hooks = ...
local consider = aiState.considerSwitch
if type(consider) ~= "function" then return { missing = true } end

local function battler(types)
  return { curTypes = types, curMoves = {},
           mon = { hp = 100, stats = { hp = 100 }, level = 50 } }
end
local function mon(species, moves)
  return { species = species, hp = 100, stats = { hp = 100 }, level = 50,
           moves = moves }
end
local function battle(oppClass, playerTypes, enemyTypes, bench, turn)
  local party = {}
  for i, species in ipairs(bench) do party[i] = mon(species) end
  return {
    kind = "trainer", oppClass = oppClass, turnCount = turn or 5,
    enemyIndex = 1, data = DATA,
    player = battler(playerTypes), enemy = battler(enemyTypes),
    enemyParty = party,
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

-- A Pokemon that just came in owes a turn on the field before it may leave
-- again.  turnCount is advanced by one between decisions here on purpose:
-- that is the real shape of the next turn, and the old `turnCount <= since`
-- compare waved it straight through because resolveTurn reads the enemy's
-- action BEFORE it increments.
local pong = battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                    { "ARCANINE", "LAPRAS", "VAPOREON" })
local first = consider(pong)
pong.enemyIndex = first and first.index or 2   -- the send-out happened
pong.turnCount = pong.turnCount + 1
out.graceTurn = consider(pong) == nil
pong.turnCount = pong.turnCount + 1
out.graceEnds = consider(pong) ~= nil

-- a forced action is not something to rotate out of: the vanilla chain would
-- have answered with a Hyper Beam recharge, a thrash, or being held by the
-- player's Wrap, and walking out of one is the boss cheating
local held = battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                    { "ARCANINE", "LAPRAS" })
held.lockedAction = function() return { special = "bound" } end
out.locked = consider(held) == nil

-- ordinary trainers never rotate
out.bossesOnly = consider(battle("OPP_YOUNGSTER", { "WATER" }, { "FIRE" },
                                 { "ARCANINE", "LAPRAS" })) == nil

-- no backup worth the turn: stay put
out.noPointless = consider(battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                                  { "ARCANINE", "NINETALES" })) == nil

-- The cap is respected, counting rotations that really land: each accepted
-- one moves enemyIndex to the Pokemon it picked, the way the send-out does.
-- (Holding enemyIndex still instead would be the phantom case below, which
-- is refunded on purpose and would never reach the cap at all.)
local capped = battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                      { "ARCANINE", "LAPRAS", "VAPOREON" })
local n = 0
for i = 1, 8 do
  capped.turnCount = capped.turnCount + 1
  local act = consider(capped)
  if act then
    n = n + 1
    capped.enemyIndex = act.index
  end
end
out.capped = n == 2

-- A mono-type roster can still rotate, because what a Pokemon threatens is
-- read off its own MOVES rather than its species.  Six Fire Pokemon have no
-- better species to rotate to, ever -- Blaine and Surge between them could
-- not fire once across every matchup the type chart allows -- but one of
-- those six is carrying Psychic and Submission, which is the answer the
-- rotation exists to find.
local mono = battle("OPP_BLAINE", { "ROCK" }, { "FIRE" }, { "PONYTA", "MAGMAR" })
mono.enemy.curMoves = { { id = "FIRE_BLAST" } }
mono.enemyParty[1].moves = { { id = "FIRE_BLAST" } }
mono.enemyParty[2].moves = { { id = "SUBMISSION" } }
local monoAct = consider(mono)
out.monoRotates = monoAct ~= nil and monoAct.index == 2

-- and a bench that really has no answer still holds its turn
local noAnswer = battle("OPP_BLAINE", { "ROCK" }, { "FIRE" },
                        { "PONYTA", "RAPIDASH" })
noAnswer.enemy.curMoves = { { id = "FIRE_BLAST" } }
noAnswer.enemyParty[1].moves = { { id = "FIRE_BLAST" } }
noAnswer.enemyParty[2].moves = { { id = "FIRE_BLAST" } }
out.monoHolds = consider(noAnswer) == nil

-- A rotation the engine never carried out does not spend one of them.  The
-- decision is made a turn ahead of the action, and executeAction drops the
-- whole row if the Pokemon is knocked out first, so enemyIndex staying put
-- is the tell.  Left uncorrected, a boss lost rotations it never made.
local dropped = battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                       { "ARCANINE", "LAPRAS", "VAPOREON" })
local phantom = 0
for i = 1, 6 do
  -- enemyIndex is deliberately never moved: the switch did not happen
  if consider(dropped) then phantom = phantom + 1 end
end
out.refunded = phantom > 2

-- ---------------------------------------------------------- when it resolves
-- The rotation goes first and the player's move follows it onto whatever
-- came IN.  Both halves are checked, because forcing the order without the
-- retarget is worse than the bug: the send-out plays and the attack still
-- lands on the Pokemon that withdrew.
local order = hooks["battle.turn_order"]
out.orderHooked = type(order) == "function"
if out.orderHooked then
  local turn = battle("OPP_BLAINE", { "WATER" }, { "FIRE" },
                      { "ARCANINE", "LAPRAS" })
  local leaving = turn.enemy
  local rotation = consider(turn)
  out.rotationDecided = rotation ~= nil

  local function ask(b)
    return order(function() return true end, b.player, nil, b.enemy, nil, {})
  end
  out.enemyFirst = ask(turn) == false
  -- and only for the turn it rotates on
  out.laterTurnsUntouched = ask(turn) == true

  -- the engine now swaps battle.enemy for a fresh battler, while the row it
  -- built for the player still names the one that left
  turn.enemyIndex = rotation and rotation.index or 2
  turn.enemy = battler({ "WATER" })
  turn:executeAction(turn.player, leaving, { id = "SURF" })
  out.retargeted = turn.executed ~= nil and turn.executed.target == turn.enemy

  -- but a battler that left by FAINTING keeps its row, so the engine's own
  -- "the target is down, do nothing" guard still gets to run
  leaving.mon.hp = 0
  turn:executeAction(turn.player, leaving, { id = "SURF" })
  out.faintedKeepsRow = turn.executed.target == leaving
end
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
        # real move records: what a Pokemon threatens is read off its own
        # moves now, so the fixture needs their types and powers
        "moves": lua.table_from({
            mid: lua.table_from({
                "id": mid, "power": rec.get("power") or 0,
                "accuracy": rec.get("accuracy") or 100,
                "type": rec.get("type"), "effect": rec.get("effect"),
            }) for mid, rec in g.moves.items()}),
    })
    runner = lua.execute(
        "return function(src) return assert(loadstring(src, '@switch')) end")
    out = runner(SWITCH_TEST)(ai, data, env["recorded"]["hooks"])
    check(not out["missing"], "considerSwitch is exported")
    check(out["rotates"], "an outclassed boss rotates to the backup that answers")
    check(out["holds"], "a boss with the advantage keeps its turn")
    check(out["graceTurn"], "no second rotation the turn a Pokemon came out")
    check(out["graceEnds"], "and it may rotate again once that turn is spent")
    check(out["locked"], "no rotating out of a recharge, a thrash or a Wrap")
    check(out["bossesOnly"], "ordinary trainers never rotate")
    check(out["noPointless"], "no rotation when no backup is actually better")
    check(out["capped"], "the per-fight switch cap holds")
    check(out["refunded"], "a rotation the engine dropped costs nothing")
    check(out["monoRotates"], "a mono-type roster rotates on its movesets")
    check(out["monoHolds"], "but not when the bench carries the same answer")

    print("\n== when a rotation resolves")
    check(out["orderHooked"], "battle.turn_order is wrapped")
    if not out["orderHooked"]:
        return
    check(out["rotationDecided"], "the rotation under test was decided")
    check(out["enemyFirst"], "the rotation resolves before the player's move")
    check(out["laterTurnsUntouched"], "every other turn keeps vanilla order")
    check(out["retargeted"], "the player's move follows onto what came in")
    check(out["faintedKeepsRow"], "a fainted target is left for the engine's guard")



SCORING_TEST = """
local aiState, DATA, fire = ...
local scoreFor = aiState.scoreFor
if type(scoreFor) ~= "function" then return { missing = true } end

local function mon(hp, max)
  return { hp = hp, stats = { hp = max }, level = 40, status = nil }
end
local function view(targetHp)
  local battle = { oppClass = "OPP_BROCK", ruleset = {}, data = DATA }
  local user = { mon = mon(100, 100), curTypes = { "ROCK" }, curMoves = {} }
  local target = { mon = mon(targetHp, 100), curTypes = { "NORMAL" },
                   curMoves = {} }
  battle.player, battle.enemy = target, user
  return { battle = battle, user = user, target = target }, user
end

local bosses = { OPP_BROCK = true }
local out = {}

-- a stat-lowering move used to score a flat 10 and could never be picked
local v = view(100)
out.debuffBeatsBase = scoreFor(v, DATA.moves.SCREECH, 10, bosses) < 10
out.toxicBeatsBase = scoreFor(v, DATA.moves.TOXIC, 10, bosses) < 10

-- but not when the target is nearly finished
local dying = view(20)
out.finishInstead = scoreFor(dying, DATA.moves.TOXIC, 10, bosses)
                    > scoreFor(v, DATA.moves.TOXIC, 10, bosses)

-- a damaging move with a status side effect is not treated as a status move
out.bodySlamUnpenalised =
  scoreFor(v, DATA.moves.BODY_SLAM, 10, bosses) <= 10

-- repeating last turn's move costs a point
local before = scoreFor(v, DATA.moves.SCREECH, 10, bosses)
fire("battle.move_used", { battle = v.battle, user = v.user,
                           move = DATA.moves.SCREECH })
local after = scoreFor(v, DATA.moves.SCREECH, 10, bosses)
out.repeatCosts = after > before

-- and a stat move said twice is discouraged beyond the repeat damper alone
out.saidOnce = after - before >= 1

-- Confuse Ray and Supersonic reached no branch at all, so they kept the base
-- 10 -- unpickable next to any attack, on 24 authored roster slots
local clean = view(100)
out.confuseBeatsBase = scoreFor(clean, DATA.moves.CONFUSE_RAY, 10, bosses) < 10
-- but not at a target that is already confused: gen 1 keeps that as a
-- volatile on the battler, not as mon.status
local confused = view(100)
confused.target.confusedTurns = 3
out.confuseRedundant =
  scoreFor(confused, DATA.moves.CONFUSE_RAY, 10, bosses) > 10

-- A heal is capped per Pokemon per battle, and HEAL_EFFECT refuses outright
-- at full HP, so a heal that restored nothing must not spend one of them.
-- battle.move_used carries the HP the effect is about to read, which is what
-- makes the difference knowable at all.
local hv, healer = view(100)
healer.mon.hp = healer.mon.stats.hp
fire("battle.move_used", { battle = hv.battle, user = healer,
                           move = DATA.moves.RECOVER })
out.failedHealFree = (aiState.heals()[healer.mon] or 0) == 0
healer.mon.hp = 40
fire("battle.move_used", { battle = hv.battle, user = healer,
                           move = DATA.moves.RECOVER })
out.realHealCounts = (aiState.heals()[healer.mon] or 0) == 1
return out
"""


def scoring():
    print("\n== move scoring")
    g = gamedata.load("red")
    lua, env = run_mod("red", g)
    ai = env["mod"]["exports"]["aiState"]
    data = lua.table_from({
        "moves": lua.table_from({
            mid: lua.table_from({
                "id": mid, "power": rec.get("power") or 0,
                "accuracy": rec.get("accuracy") or 100,
                "type": rec.get("type"), "effect": rec.get("effect"),
            }) for mid, rec in g.moves.items()}),
    })
    runner = lua.execute(
        "return function(src) return assert(loadstring(src, '@score')) end")
    out = runner(SCORING_TEST)(ai, data, env["fire"])
    if out["missing"]:
        check(False, "scoreFor is exported")
        return
    check(out["debuffBeatsBase"], "a stat-lowering move can now be chosen")
    check(out["toxicBeatsBase"], "a status move can now be chosen")
    check(out["finishInstead"], "status is discouraged against a dying target")
    check(out["bodySlamUnpenalised"],
          "an attack with a status side effect is judged as an attack")
    check(out["repeatCosts"], "last turn's move costs a point this turn")
    check(out["saidOnce"], "a stat move already used is discouraged again")
    check(out["confuseBeatsBase"], "a confusion move can now be chosen")
    check(out["confuseRedundant"],
          "but not at a target that is already confused")
    check(out["failedHealFree"], "a heal that would fail spends no heal")
    check(out["realHealCounts"], "and one that lands still counts")


def main():
    compile_all()
    roster_table()
    behaviour()
    formats()
    switching()
    scoring()
    print(f"\n{checks} checks, {failures} FAILURES")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
