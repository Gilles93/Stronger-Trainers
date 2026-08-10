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
-- Two things do not. The optional XP reduction rides `exp.gain` instead,
-- which is the engine's own per-participant payout hook. The static
-- overworld encounters -- the legendaries, the Snorlax, the ghost, the Power
-- Plant's item balls -- have no hook to ride at all: nothing on
-- BattleState.newWild's path consults the mod runtime, so static_battles.lua
-- shadows that function directly.
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
-- `minSize`.
--
-- Padding used to cycle back through the trainer's own mons, so a Bug Catcher
-- gained a second Caterpie.  On theme, but it read as a duplication bug rather
-- than a roster.  `pad` now supplies a DIFFERENT species sharing one of the
-- trainer's types; the copy is still the fallback for any build where no such
-- species can be found, or where the player has turned variety off.
--
-- `evolve` runs after the bump and before the padding, so a padded copy is a
-- copy of the evolved slot and the two never disagree.  It is nil when the
-- player has the option off.
local function scaleParty(party, pct, minSize, evolve, pad)
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
    -- Two separate sets, and the distinction matters.  `taken` grows as slots
    -- are added, so padding never repeats a species.  `theme` is frozen from
    -- the trainer's OWN Pokemon and never grows -- otherwise each pick widens
    -- the pool for the next one, and a Hiker whose Onix was joined by an
    -- Omanyte (Rock/Water, on theme) would find Water on theme too and end up
    -- fielding a Wartortle.
    local taken, theme = {}, {}
    for i = 1, original do
      if out[i].species then
        taken[out[i].species] = true
        theme[#theme + 1] = out[i].species
      end
    end
    local pick = 0
    while #out < target do
      pick = pick % original + 1
      local src = out[pick]
      local copy = {}
      for k, v in pairs(src) do copy[k] = v end
      local species = pad and pad(#out + 1, copy.level, taken, theme)
      if species then
        copy.species = species
        taken[species] = true
        -- a different species does not inherit the original's move list;
        -- the engine fills in its own level-up set
        copy.moves = nil
      end
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

-- Which game this process is running, and therefore which roster table to
-- read.  This is the fix for the bug 1.6.0 shipped with.
--
-- Party indices are NOT the same across versions.  Red and Blue give
-- OPP_RIVAL1 nine parties -- three battles times three starter counter-picks
-- -- while Yellow gives it three, one per battle, because his Eevee has no
-- counter-pick to make.  So Yellow's OPP_RIVAL1#2 and #3 are the Route 22 and
-- Cerulean fights, exactly where a shared table holds "the lab battle, but
-- the player chose a different starter": one level 6 starter, three times
-- over, which is precisely what players reported.  The full mapping is
-- documented on Commands.rival_battle.
--
-- Guarded: a build old enough to lack GameVersion is a Red build by
-- definition, and a missing optional module should not stop the mod loading.
local function gameVersion()
  local ok, GameVersion = pcall(require, "src.core.GameVersion")
  if ok and type(GameVersion) == "table" and type(GameVersion.get) == "function" then
    local got, id = pcall(GameVersion.get)
    if got and type(id) == "string" and id ~= "" then return id end
  end
  return "red"
end

-- Which format the player picked for the gym battle now starting; shared with
-- gym_formats.lua.  `count` nil means an ordinary full-roster battle.
-- `full` and `fielded` are filled in by the party hook once the roster is
-- actually cut, so the prize can be scaled to the fight that was fought.
local formatState = { class = nil, count = nil, snapshot = nil,
                      full = nil, fielded = nil }

-- shared with smart_ai.lua: the layer id and test handles it publishes
local aiState = {}

-- Cut an authored roster down to `count`, always keeping the ace.  The ace is
-- the highest-level slot, which the authored tables put last; survivors are
-- re-sorted by level so it stays last and the fight still builds.
--
-- `>=` rather than `>` is what makes "last" true when levels tie, and the
-- tie is the normal case on the game's own rosters rather than a corner:
-- vanilla Erika fields Victreebel and Vileplume both at 29, and taking the
-- first of the two dropped the Vileplume the gym is built around.
local function trimToFormat(team, count)
  if not count or count >= #team then return team end
  local acePos, aceLevel = 1, -1
  for i, slot in ipairs(team) do
    if slot[2] >= aceLevel then acePos, aceLevel = i, slot[2] end
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

-- The same cut over the engine's own slot shape ({ species = , level = })
-- rather than an authored row.
--
-- It exists because the two features are independently switchable and the
-- picker is not: with BOSS TEAMS off and GYM FORMAT CHOICE on, the leader
-- fell through to the ordinary scaling path, which never saw the format at
-- all.  Your side was still narrowed to what you picked, so answering "3
-- each" fielded three against the leader's full six.
local function trimRecords(party, count)
  if not count or count >= #party then return party end
  local acePos, aceLevel = 1, -1
  for i, slot in ipairs(party) do
    -- last of a tie wins, same rule and same reason as trimToFormat
    if (slot.level or 0) >= aceLevel then acePos, aceLevel = i, slot.level or 0 end
  end
  local pool = {}
  for i, slot in ipairs(party) do
    if i ~= acePos then pool[#pool + 1] = slot end
  end
  for i = #pool, 2, -1 do
    local j = math.random(i)
    pool[i], pool[j] = pool[j], pool[i]
  end
  local picked = { party[acePos] }
  for i = 1, count - 1 do picked[#picked + 1] = pool[i] end
  table.sort(picked, function(a, b) return (a.level or 0) < (b.level or 0) end)
  return picked
end

return function(mod)
  -- boss_teams.lua is { red = {...}, blue = {...}, yellow = {...} }.  An
  -- unrecognised version falls back to Red rather than to nothing: a build
  -- reporting something new should still get a hard game, and Red's table is
  -- the one whose party layout the other two are closest to.
  local ALL_TEAMS = loadSibling(mod, "boss_teams.lua", "boss teams") or {}
  local VERSION = gameVersion()
  local BOSS_TEAMS = ALL_TEAMS[VERSION] or ALL_TEAMS.red or {}
  if not ALL_TEAMS[VERSION] then
    mod.log:warn("no boss rosters for game version %q; using the Red table",
                 tostring(VERSION))
  else
    mod.log:info("boss rosters loaded for %s (%d parties)", VERSION,
                 (function() local n = 0 for _ in pairs(BOSS_TEAMS) do n = n + 1 end return n end)())
  end

  mod.options:define({
    { key = "boss_teams", label = "BOSS TEAMS", type = "toggle", default = true },
    { key = "boss_moves", label = "BOSS MOVESETS", type = "toggle", default = true },
    { key = "gym_formats", label = "GYM FORMAT CHOICE", type = "toggle",
      default = true },
    { key = "smart_ai", label = "SMART AI", type = "toggle", default = true },
    { key = "smart_ai_scope", label = "SMART AI FOR", type = "choice",
      default = "bosses", choices = { { "BOSSES", "bosses" },
                                      { "EVERYONE", "all" } } },
    -- The most opinionated row in the mod: no Gen 1 trainer rotates on
    -- purpose, so it gets its own toggle rather than riding SMART AI.
    { key = "boss_switching", label = "BOSS SWITCHING", type = "toggle",
      default = true },
    { key = "boss_switch_cap", label = "SWITCHES PER FIGHT", type = "number",
      default = 2, min = 0, max = 5, step = 1 },
    { key = "boss_bonus", label = "BOSS LEVEL BONUS", type = "number",
      default = 0, min = 0, max = 20, step = 1 },
    { key = "trainer_levels", label = "TRAINER LEVEL %", type = "number",
      default = 15, min = 0, max = 50, step = 5 },
    { key = "min_party", label = "MIN PARTY SIZE", type = "number",
      default = 3, min = 1, max = 6, step = 1 },
    -- off restores the old behaviour: padding with copies of what the
    -- trainer already fields
    { key = "pad_variety", label = "PAD WITH VARIETY", type = "toggle",
      default = true },
    { key = "evolve_pre_evos", label = "EVOLVE PRE-EVOS", type = "toggle",
      default = true },
    -- 0 leaves stone users alone; the row only matters with the toggle on
    { key = "stone_level", label = "STONE EVO FROM LV", type = "number",
      default = 30, min = 0, max = 60, step = 5 },
    -- Two rows for the same reason BOSS TEAMS and BOSS MOVESETS are two: the
    -- level and the moveset are separately objectionable.  With STATIC
    -- MOVESETS off, a legendary keeps its raised level and reverts to the
    -- level-up set the engine would have given it there.
    { key = "statics", label = "STATIC ENCOUNTERS", type = "toggle",
      default = true },
    { key = "static_moves", label = "STATIC MOVESETS", type = "toggle",
      default = true },
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

  -- ------------------------------------------------------ padding with variety
  --
  -- A short party is filled out with a different species that shares one of
  -- the trainer's own types, rather than a second copy of what he already
  -- has.  Three data-driven rules keep the picks feeling native, with no
  -- hand-maintained tables:
  --
  --   * only species that appear in a WILD ENCOUNTER table are eligible,
  --     which is a data-side way of saying "something he could have caught".
  --     That excludes the fossils, the game-corner prizes, the gift Pokemon
  --     and every legendary without this file naming one of them.
  --   * only base stages go in the pool; the pick is then walked up its own
  --     line to the slot's level by the same `evolve` the trainer's own
  --     Pokemon get, so a Bug Catcher at 14 gets a Metapod and one at 40 gets
  --     a Butterfree, with no level table to maintain.
  --   * a species whose earliest wild appearance is well above this slot's
  --     level is skipped, so a level 12 Youngster cannot open with a Tauros
  --     just because Tauros is a catchable Normal type.
  --
  -- Registry iteration order is not stable, and a trainer who fields a
  -- different Pokemon each time you meet him reads as broken rather than
  -- varied.  So the candidate lists are sorted and the pick is a hash of the
  -- trainer's own identity: the same trainer always brings the same Pokemon.
  local padPool   -- built on first use, by which point registries have settled

  local function collectWild(record, species, minLevel)
    for _, field in ipairs({ "grass", "water" }) do
      local group = record and record[field]
      for _, slot in ipairs(group and group.slots or {}) do
        local id, level = slot.species, slot.level or 1
        if id then
          species[id] = true
          if not minLevel[id] or level < minLevel[id] then
            minLevel[id] = level
          end
        end
      end
    end
  end

  local function buildPadPool()
    local pool = { byType = {}, minLevel = {}, size = 0 }
    local dex = mod.content and mod.content.pokemon
    if not (dex and dex.each) then return pool end

    -- where each species can be caught, and from what level
    local wild, sawWild = {}, false
    local enc = mod.content and mod.content.encounters
    if enc and enc.each then
      local ok = pcall(function()
        for _, record in enc:each() do
          sawWild = true
          collectWild(record, wild, pool.minLevel)
        end
      end)
      if not ok then sawWild = false end
    end

    -- anything that is some other species' evolution is not a base stage
    local defs, evolved = {}, {}
    local ok = pcall(function()
      for id, def in dex:each() do
        defs[id] = def
        for _, evo in ipairs(def and def.evolutions or {}) do
          if evo.species then evolved[evo.species] = true end
        end
      end
    end)
    if not ok then return pool end

    -- The wild filter is required, not best-effort.  It is the only thing
    -- keeping the fossils, the game-corner prizes, the gift Pokemon and the
    -- legendaries out -- not one of them appears in a single wild table -- so
    -- without encounter data the honest move is to leave `size` at 0 and let
    -- the old copy-padding stand, rather than open the pool to Mewtwo.
    if not sawWild then return pool end

    for id, def in pairs(defs) do
      if not evolved[id] and wild[id] then
        for _, kind in ipairs(def.types or {}) do
          pool.byType[kind] = pool.byType[kind] or {}
          local list = pool.byType[kind]
          list[#list + 1] = id
        end
        pool.size = pool.size + 1
      end
    end
    for _, list in pairs(pool.byType) do table.sort(list) end
    return pool
  end

  -- djb2 over the trainer's identity: stable across sessions and builds, and
  -- unlike math.random it cannot be disturbed by whatever else drew from the
  -- shared stream this turn.
  local function padSeed(...)
    local h = 5381
    for _, value in ipairs({ ... }) do
      local text = tostring(value)
      for i = 1, #text do
        h = (h * 33 + text:byte(i)) % 2147483647
      end
    end
    return h
  end

  -- How far above a slot's level a species' earliest wild appearance may sit
  -- before it stops being plausible for that trainer.
  local PAD_LEVEL_SLACK = 5

  local function padderFor(oppClass, partyIndex, evolve)
    if mod.options:get("pad_variety") == false then return nil end
    padPool = padPool or buildPadPool()
    if padPool.size == 0 then return nil end

    return function(slotIndex, level, taken, theme)
      -- the types this trainer is themed on, read off his OWN Pokemon only
      local kinds, seen = {}, {}
      for _, species in ipairs(theme or {}) do
        local def = speciesDef(species)
        for _, kind in ipairs(def and def.types or {}) do
          if not seen[kind] then
            seen[kind] = true
            kinds[#kinds + 1] = kind
          end
        end
      end
      table.sort(kinds)

      -- Bucket by how many of the trainer's types a candidate shares, and
      -- only ever pick from the closest non-empty bucket.  Sharing *any* type
      -- is too loose: a Bug Catcher's Weedle makes Poison on theme, which
      -- would let a Tentacool in on a technicality.  Preferring the deepest
      -- overlap keeps a Bug/Poison catcher reaching for Bug/Poison first.
      local buckets, listed = {}, {}
      local deepest = 0
      for _, kind in ipairs(kinds) do
        for _, id in ipairs(padPool.byType[kind] or {}) do
          local earliest = padPool.minLevel[id]
          local plausible = not earliest
            or earliest <= (level or 1) + PAD_LEVEL_SLACK
          if plausible and not listed[id] then
            listed[id] = true
            local overlap = 0
            for _, mine in ipairs(speciesDef(id) and speciesDef(id).types or {}) do
              if seen[mine] then overlap = overlap + 1 end
            end
            buckets[overlap] = buckets[overlap] or {}
            local list = buckets[overlap]
            list[#list + 1] = id
            if overlap > deepest then deepest = overlap end
          end
        end
      end

      -- Try the closest bucket first, then fall through to looser ones. The
      -- fall-through is not optional: the deepest bucket is often a single
      -- species and often the one the trainer already fields -- a Weedle is
      -- the only Bug/Poison base stage -- so stopping at the best bucket
      -- would hand back nothing and drop us onto a duplicate copy.
      local seed = padSeed(oppClass, partyIndex, slotIndex)
      for depth = deepest, 1, -1 do
        local candidates = buckets[depth]
        if candidates and #candidates > 0 then
          table.sort(candidates)
          -- walk from the hashed start so a taken species moves the pick
          -- along rather than ending the search
          local start = seed % #candidates
          for step = 0, #candidates - 1 do
            local id = candidates[(start + step) % #candidates + 1]
            local grown = evolve and evolve(id, level or 1) or id
            if not taken[grown] then return grown end
          end
        end
      end
      return nil
    end
  end

  -- published so the format state and the roster trimming can be driven
  -- directly by tests, and read by any mod that wants to know a restricted
  -- gym battle is in progress
  mod.exports.padderFor = padderFor
  mod.exports.formatState = formatState
  mod.exports.trimToFormat = trimToFormat
  mod.exports.aiState = aiState
  mod.exports.evolvedSpecies = evolvedSpecies
  mod.exports.speciesDef = speciesDef
  mod.exports.scaleXp = scaleXp

  mod.hooks:wrap("trainer.party", function(next, oppClass, partyIndex, _party)
    -- let the rest of the chain settle first, then transform what it agreed on
    local party = next()

    local team = mod.options:get("boss_teams") ~= false
      and BOSS_TEAMS[tostring(oppClass) .. "#" .. tostring(partyIndex)]
      or nil

    -- An authored roster is consulted BEFORE the empty-party bail-out, which
    -- is what lets one stand in for a class this version ships no data for.
    -- OPP_CHIEF is the case: unused in Red and an empty table in Blue and
    -- Yellow, so the old ordering meant his roster could never apply outside
    -- Red even when another mod placed him.
    if not team and (type(party) ~= "table" or #party == 0) then
      return party
    end

    if team then
      -- a format the player just picked narrows the roster; the ace stays
      if formatState.count and formatState.class == oppClass then
        formatState.full = #team
        team = trimToFormat(team, formatState.count)
        formatState.fielded = #team
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
    local scaled = scaleParty(party, num("trainer_levels", 15),
                              num("min_party", 3), evolve,
                              padderFor(oppClass, partyIndex, evolve))
    -- the leader honours the format the player just picked whether or not
    -- its authored roster is switched on (see trimRecords)
    if formatState.count and formatState.class == oppClass then
      formatState.full = #scaled
      scaled = trimRecords(scaled, formatState.count)
      formatState.fielded = #scaled
    end
    return scaled
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

  -- Static overworld encounters: the legendaries, the two Snorlax, the ghost
  -- and the Power Plant's disguised item balls.  Its table is handed in the
  -- same way boss_teams.lua is, and for the same reason -- the feature file
  -- reaches for engine internals and the data file must not.
  local setupStatics = loadSibling(mod, "static_battles.lua",
                                   "static encounters")
  if type(setupStatics) == "function" then
    local STATICS = loadSibling(mod, "statics.lua", "static encounters") or {}
    local ok, err = pcall(setupStatics, mod, STATICS)
    if not ok then
      mod.log:warn("static encounters failed to install (%s); everything "
                   .. "else is unaffected", tostring(err))
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
