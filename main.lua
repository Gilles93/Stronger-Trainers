-- Stronger Trainers
--
-- Most of it lands in one place: the `trainer.party` hook that
-- BattleState.newTrainer offers just after it picks a roster and before it
-- instantiates any Pokemon (src/battle/BattleState.lua:670).
--
--   * 39 named parties -- the eight gym leaders, the Elite Four, the
--     Champion, every rival battle, Giovanni's three fights and the Celadon
--     Chief -- are replaced outright by authored six-slot teams carrying
--     hand-picked movesets.
--   * every other party in the game keeps its own species and gets a
--     proportional level bump, short parties are padded out, and any slot
--     left standing past its own evolution level is walked up its line.
--
-- One thing does not: the optional XP reduction rides `exp.gain` instead,
-- which is the engine's own per-participant payout hook.
--
-- Why the hook and not `mod.content.trainers:patch`:
--
--   * Movesets. The battle builder honours a `moves` list on a party slot
--     (BattleState.lua:689) but the `trainers` registry schema declares a
--     slot as `{ level, species }` only, and nested records are validated
--     strictly (Schemas.lua:177-185), so a `moves` key in a patch is a hard
--     load error at api 2. The hook is the only door custom sets fit
--     through.
--   * Live options. `mod.options:get` reads the manager's current value, so
--     reading it here means the MODS-menu sliders take effect on the next
--     battle instead of the next restart.
--   * Composition. The hook receives whatever the merged registry plus every
--     other mod produced, so a different trainer mod's roster still gets the
--     level treatment rather than being overwritten by ours.
--
-- The party handed in is the live `data.trainers[class].parties[n]` table, so
-- nothing here mutates it -- every path builds a fresh table.

local MAX_PARTY = 6   -- what the battle UI's ball row can draw
local MAX_LEVEL = 100

local function clampLevel(n)
  n = math.floor(tonumber(n) or 1)
  if n < 1 then return 1 end
  if n > MAX_LEVEL then return MAX_LEVEL end
  return n
end

-- A boss slot is { species, level, moves? }.  `moves` is dropped when the
-- player has turned custom sets off, which leaves the engine to fill in the
-- species' own level-up set for that level.
local function bossParty(team, bonus, withMoves)
  local out = {}
  for i = 1, math.min(#team, MAX_PARTY) do
    local slot = team[i]
    out[i] = { species = slot[1], level = clampLevel(slot[2] + bonus) }
    if withMoves and slot[3] then
      -- copy the move list too: the caller must never be able to reach
      -- into our required module's tables
      local moves = {}
      for j, id in ipairs(slot[3]) do moves[j] = id end
      out[i].moves = moves
    end
  end
  return out
end

-- Gen 1 leaves trainers holding pre-evolutions long past the level they would
-- have evolved at: 212 of the 999 vanilla party slots are already overdue
-- before this mod raises anything, and the level bump takes that to 326.  This
-- walks a slot up its line to the stage its level has actually earned.
--
-- `lookup` reads the MERGED pokemon registry rather than a table of our own,
-- so another mod's evolution edits are honoured without this file naming them
-- -- with all_pokemon_catchable_151 installed the four trade lines carry a
-- LEVEL row (KADABRA/GRAVELER/HAUNTER at 42, MACHOKE at 45) and those fire
-- here too.
--
-- Stone evolutions carry no level at all, so one has to be invented for them:
-- `stoneLevel`, with 0 meaning "leave stone users on their pre-evo".  EEVEE is
-- the only species with more than one stone row, and the first row wins, which
-- is the same first-match rule Evolution.pendingFor dispatches on.
local MAX_EVO_STEPS = 5   -- gen 1's longest line is 3; this is a cycle guard

local function evolvedSpecies(lookup, species, level, stoneLevel)
  local seen = {}
  local current = species
  for _ = 1, MAX_EVO_STEPS do
    if seen[current] then break end
    seen[current] = true
    local def = lookup(current)
    local target
    for _, evo in ipairs(def and def.evolutions or {}) do
      local byLevel = evo.method == "LEVEL" and evo.level
                      and level >= evo.level
      local byStone = evo.method == "ITEM" and stoneLevel > 0
                      and level >= stoneLevel
      if byLevel or byStone then
        target = evo.species
        break
      end
    end
    -- a line naming a species this build does not carry stops where it is,
    -- rather than handing the battle builder a slot Pokemon.new would assert on
    if not target or not lookup(target) then break end
    current = target
  end
  return current
end

-- Ordinary trainers: same species, levels raised by `pct`, then padded up to
-- `minSize` by cycling back through the trainer's own mons -- a Bug Catcher
-- gains another Caterpie rather than something off-theme, and the copies come
-- from the front of the list so the ace stays the ace.
--
-- `evolve` runs after the bump and before the padding, so a padded copy is a
-- copy of the evolved slot and the two never disagree.  It is nil when the
-- player has the option off.
local function scaleParty(party, pct, minSize, evolve)
  local out = {}
  for i, slot in ipairs(party) do
    local level = slot.level or 1
    if pct > 0 then
      level = level + math.max(1, math.floor(level * pct / 100 + 0.5))
    end
    level = clampLevel(level)
    local species = slot.species
    if evolve and species then species = evolve(species, level) end
    out[i] = { species = species, level = level }
    -- carry through anything another mod put on the slot (a `moves` list of
    -- its own, for instance) without knowing what it is
    for k, v in pairs(slot) do
      if k ~= "level" and k ~= "species" then out[i][k] = v end
    end
  end

  local original = #out
  if original > 0 then
    local target = math.min(minSize, MAX_PARTY)
    local pick = 0
    while #out < target do
      pick = pick % original + 1
      local src = out[pick]
      local copy = {}
      for k, v in pairs(src) do copy[k] = v end
      out[#out + 1] = copy
    end
  end
  return out
end

-- XP payout scaling.  `pct` is a percentage of normal, so 100 is a no-op and
-- the option row never has to be consulted twice.  The engine floors every
-- division in its own exp maths and never pays less than 1 point
-- (Experience.gainFor), so the same floor is kept here: a reduced payout can
-- get very small, but a Pokemon that fought always earns something.
local function scaleXp(gained, pct)
  if type(gained) ~= "number" then return gained end
  if not pct or pct >= 100 then return gained end
  return math.max(1, math.floor(gained * pct / 100))
end

-- Sibling files are read and compiled by hand rather than required: mods are
-- sandboxed away from the game's package path (the same shape SHINY_POKEMON
-- uses for its palette table).  A sibling that fails to load costs its own
-- feature and nothing else.
local function loadSibling(mod, name, what)
  local src = mod:read(name)
  if type(src) ~= "string" or src == "" then
    mod.log:warn("%s missing or empty; %s disabled", name, what)
    return nil
  end
  local compile = loadstring or load
  local chunk, err = compile(src, "@" .. name)
  if not chunk then
    mod.log:warn("%s failed to compile (%s); %s disabled", name,
                 tostring(err), what)
    return nil
  end
  local ok, value = pcall(chunk)
  if not ok then
    mod.log:warn("%s errored (%s); %s disabled", name, tostring(value), what)
    return nil
  end
  return value
end

-- Which format the player picked for the gym battle now starting; shared with
-- gym_formats.lua.  `count` nil means an ordinary full-roster battle.
local formatState = { class = nil, count = nil, snapshot = nil }

-- shared with smart_ai.lua: the layer id and test handles it publishes
local aiState = {}

-- Cut an authored roster down to `count`, always keeping the ace.  The ace is
-- the highest-level slot, which the authored tables put last; survivors are
-- re-sorted by level so it stays last and the fight still builds.
local function trimToFormat(team, count)
  if not count or count >= #team then return team end
  local acePos, aceLevel = 1, -1
  for i, slot in ipairs(team) do
    if slot[2] > aceLevel then acePos, aceLevel = i, slot[2] end
  end
  local pool = {}
  for i, slot in ipairs(team) do
    if i ~= acePos then pool[#pool + 1] = slot end
  end
  -- Fisher-Yates over the non-ace slots, then take what we need
  for i = #pool, 2, -1 do
    local j = math.random(i)
    pool[i], pool[j] = pool[j], pool[i]
  end
  local picked = { team[acePos] }
  for i = 1, count - 1 do picked[#picked + 1] = pool[i] end
  table.sort(picked, function(a, b) return a[2] < b[2] end)
  return picked
end

return function(mod)
  local BOSS_TEAMS = loadSibling(mod, "boss_teams.lua", "boss teams") or {}

  mod.options:define({
    { key = "boss_teams", label = "BOSS TEAMS", type = "toggle", default = true },
    { key = "boss_moves", label = "BOSS MOVESETS", type = "toggle", default = true },
    { key = "gym_formats", label = "GYM FORMAT CHOICE", type = "toggle",
      default = true },
    { key = "smart_ai", label = "SMART AI", type = "toggle", default = true },
    { key = "smart_ai_scope", label = "SMART AI FOR", type = "choice",
      default = "bosses", choices = { { "BOSSES", "bosses" },
                                      { "EVERYONE", "all" } } },
    { key = "boss_bonus", label = "BOSS LEVEL BONUS", type = "number",
      default = 0, min = 0, max = 20, step = 1 },
    { key = "trainer_levels", label = "TRAINER LEVEL %", type = "number",
      default = 15, min = 0, max = 50, step = 5 },
    { key = "min_party", label = "MIN PARTY SIZE", type = "number",
      default = 3, min = 1, max = 6, step = 1 },
    { key = "evolve_pre_evos", label = "EVOLVE PRE-EVOS", type = "toggle",
      default = true },
    -- 0 leaves stone users alone; the row only matters with the toggle on
    { key = "stone_level", label = "STONE EVO FROM LV", type = "number",
      default = 30, min = 0, max = 60, step = 5 },
    -- a percentage of the normal payout; 100 is off, and the default trims a
    -- quarter to offset what the bigger, evolved trainer parties pay out
    { key = "xp_gain", label = "XP GAIN %", type = "number",
      default = 75, min = 25, max = 100, step = 5 },
  })

  local function num(key, fallback)
    return math.floor(tonumber(mod.options:get(key)) or fallback)
  end

  -- Read through the merged registry every call rather than caching a table:
  -- registries settle after every mod has loaded, and a cache built here would
  -- miss whatever loads after us.  A build without the registry makes this
  -- answer nil, which turns the evolution pass into a clean no-op.
  local pokedex = mod.content and mod.content.pokemon
  local function speciesDef(id)
    if not (pokedex and pokedex.get) then return nil end
    local ok, def = pcall(pokedex.get, pokedex, id)
    if ok then return def end
    return nil
  end

  -- published so the format state and the roster trimming can be driven
  -- directly by tests, and read by any mod that wants to know a restricted
  -- gym battle is in progress
  mod.exports.formatState = formatState
  mod.exports.trimToFormat = trimToFormat
  mod.exports.aiState = aiState
  mod.exports.evolvedSpecies = evolvedSpecies
  mod.exports.speciesDef = speciesDef
  mod.exports.scaleXp = scaleXp

  mod.hooks:wrap("trainer.party", function(next, oppClass, partyIndex, _party)
    -- let the rest of the chain settle first, then transform what it agreed on
    local party = next()
    if type(party) ~= "table" or #party == 0 then return party end

    local team = mod.options:get("boss_teams") ~= false
      and BOSS_TEAMS[tostring(oppClass) .. "#" .. tostring(partyIndex)]
      or nil

    if team then
      -- a format the player just picked narrows the roster; the ace stays
      if formatState.count and formatState.class == oppClass then
        team = trimToFormat(team, formatState.count)
      end
      return bossParty(team, num("boss_bonus", 0),
                       mod.options:get("boss_moves") ~= false)
    end
    -- Authored rosters above returned already: they are picked stage by stage
    -- on purpose, and evolving them would take Lance from two DRAGONITE to
    -- four and give Blaine a second RAPIDASH.  Only the game's own parties
    -- are walked up.
    local evolve = nil
    if mod.options:get("evolve_pre_evos") ~= false then
      local stone = num("stone_level", 30)
      evolve = function(species, level)
        return evolvedSpecies(speciesDef, species, level, stone)
      end
    end
    return scaleParty(party, num("trainer_levels", 15), num("min_party", 3),
                      evolve)
  end)

  -- XP payout.  `exp.gain` is consulted once per participant and the number it
  -- returns is also the one the "gained N EXP" line prints, so scaling here
  -- keeps the announcement and the total honest with each other.
  --
  -- Wrapping rather than replacing is what makes this compose: qol_toggles'
  -- EXP x2 and trainer_rematch's rematch payout wrap this same hook, and each
  -- transforms whatever the previous link produced.  They multiply out, so
  -- EXP x2 against 50% here really is the normal rate, in any hook order.
  --
  -- Stat exp is deliberately left alone.  Experience.apply credits it before
  -- this hook is consulted (Experience.lua:58-61), so a Pokemon levels more
  -- slowly but is exactly as strong at a given level as it would otherwise be.
  mod.hooks:wrap("exp.gain", function(next, ctx)
    -- the fallback matches the declared default, so an unreadable option row
    -- yields the documented behaviour rather than a quietly different game
    return scaleXp(next(ctx), num("xp_gain", 75))
  end)

  -- The two feature files reach for engine modules, so each is installed
  -- under its own pcall: a failure costs that feature and nothing else.
  local setupFormats = loadSibling(mod, "gym_formats.lua", "gym format choice")
  if type(setupFormats) == "function" then
    local ok, err = pcall(setupFormats, mod, formatState)
    if not ok then
      mod.log:warn("gym format choice failed to install (%s); "
                   .. "boss teams and level scaling are unaffected", tostring(err))
    end
  end

  -- The AI layer needs the roster keys to know which classes count as bosses,
  -- so it is handed BOSS_TEAMS rather than reading them itself.
  local setupAI = loadSibling(mod, "smart_ai.lua", "smart AI")
  if type(setupAI) == "function" then
    local ok, install = pcall(setupAI, mod, aiState)
    if ok and type(install) == "function" then
      local ok2, err2 = pcall(install, BOSS_TEAMS)
      if not ok2 then
        mod.log:warn("smart AI failed to install (%s); everything else is "
                     .. "unaffected", tostring(err2))
      end
    elseif not ok then
      mod.log:warn("smart AI failed to load (%s)", tostring(install))
    end
  end
end
