-- Headless check that this mod loads and behaves, run through the engine's
-- OWN mod loader against real extracted data, once per game version.
--
-- There is no standalone Lua on a normal Windows checkout, so the runner is
-- LOVE in console mode. LOVE mounts exactly one project directory, which is
-- this folder, so the engine's `src/` has to be reachable some other way:
-- hence the package searcher below, which reads absolute paths through plain
-- io. That one detail is what makes the rest possible.
--
--   lovec.exe tests --game <extracted release payload>
--                   --mod-dir <this repo> --mod stronger_trainers
--                   --version yellow --data <dir with pokemon.lua, ...>
--
-- `--game` is the RELEASE payload unzipped out of gen1recomp.exe (or out of
-- the newer .love in the save directory's updates/), not a dev checkout: the
-- dev tree reports itself as 0.0.0-dev and is not what players run. run.sh
-- extracts it and runs every engine/version pair.
--
-- The release payload ships no tests/, so the loader's filesystem seam is
-- served here by a flat path->content table built from the mod's own files.
-- That also means no directory listing and no io.popen, which is what the
-- engine's own FsIo needs and cannot get inside a LOVE process on Windows.

local T = { checks = 0, failures = 0 }

function T.check(cond, label)
  T.checks = T.checks + 1
  if not cond then
    T.failures = T.failures + 1
    print("  FAIL  " .. tostring(label))
  else
    print("  ok    " .. tostring(label))
  end
  return cond
end

function T.eq(got, want, label)
  return T.check(got == want,
    string.format("%s (got %s, want %s)", label, tostring(got), tostring(want)))
end

-- ---------------------------------------------------------------------------
-- Reach the engine tree. LOVE's own loaders only see the mounted project, so
-- engine modules are resolved by absolute path through io instead.
-- ---------------------------------------------------------------------------

local function addEngineSearcher(root)
  local function searcher(name)
    local rel = name:gsub("%.", "/")
    for _, candidate in ipairs({ root .. "/" .. rel .. ".lua",
                                 root .. "/" .. rel .. "/init.lua" }) do
      local handle = io.open(candidate, "rb")
      if handle then
        local src = handle:read("*a")
        handle:close()
        local chunk, err = loadstring(src, "@" .. candidate)
        if not chunk then error(err, 0) end
        return chunk
      end
    end
    return nil, "\n\tno engine module " .. name .. " under " .. root
  end
  table.insert(package.loaders, 2, searcher)
end

local function parseArgs(argv)
  local opts = {}
  local i = 1
  while i <= #argv do
    local key = tostring(argv[i]):match("^%-%-(.+)$")
    if key then
      opts[key] = argv[i + 1]
      i = i + 2
    else
      i = i + 1
    end
  end
  return opts
end

-- ---------------------------------------------------------------------------
-- A dataset per version, built the way tests/mod_examples_tests.lua does it:
-- loadfile past the require cache, then Data.seedDefaults, so three versions
-- can be loaded in three processes without either leaking into the other.
-- ---------------------------------------------------------------------------

local DATASETS = {
  "constants", "pokemon", "moves", "trainers", "type_chart", "maps",
}

local function buildData(Data, dir)
  local methods = {}
  for key, value in pairs(Data) do
    if type(value) == "function" then methods[key] = value end
  end
  local set = setmetatable({}, { __index = methods })
  local loaded = 0
  for _, name in ipairs(DATASETS) do
    local path = dir .. "/" .. name .. ".lua"
    local handle = io.open(path, "rb")
    if handle then
      local src = handle:read("*a")
      handle:close()
      local chunk = loadstring(src, "@" .. path)
      if chunk then
        set[name] = chunk()
        loaded = loaded + 1
      end
    end
  end
  if Data.seedDefaults then Data.seedDefaults(set) end
  return set, loaded
end

-- ---------------------------------------------------------------------------
-- The loader's filesystem seam, backed by the mod's real files read through
-- io. Same surface Loader.new expects; no listing, no popen.
-- ---------------------------------------------------------------------------

local MOD_FILES = {
  "manifest.json", "main.lua", "boss_teams.lua", "gym_formats.lua",
  "smart_ai.lua", "mod.card", "DESCRIPTION.md", "README.md", "LICENSE",
}

local function stageMod(dir, id)
  local files, count = {}, 0
  for _, name in ipairs(MOD_FILES) do
    local handle = io.open(dir .. "/" .. name, "rb")
    if handle then
      files["mods/" .. id .. "/" .. name] = handle:read("*a")
      handle:close()
      count = count + 1
    end
  end
  return files, count
end

local function memfs(files)
  return {
    read = function(path) return files[path] end,
    getInfo = function(path)
      if files[path] then return { type = "file" } end
      local prefix = path .. "/"
      for key in pairs(files) do
        if key:sub(1, #prefix) == prefix then return { type = "directory" } end
      end
      return nil
    end,
    load = function(path)
      if not files[path] then return nil, "no file: " .. path end
      return loadstring(files[path], "@" .. path)
    end,
    getDirectoryItems = function(path)
      local seen, items = {}, {}
      local prefix = path .. "/"
      for key in pairs(files) do
        if key:sub(1, #prefix) == prefix then
          local child = key:sub(#prefix + 1):match("^[^/]+")
          if child and not seen[child] then
            seen[child] = true
            items[#items + 1] = child
          end
        end
      end
      table.sort(items)
      return items
    end,
  }
end

-- ---------------------------------------------------------------------------

local function run(opts)
  addEngineSearcher(opts.game)

  local GameVersion = require("src.core.GameVersion")
  GameVersion.set(opts.version)
  T.eq(GameVersion.get(), opts.version, "engine reports the version under test")

  local Data = require("src.core.Data")
  local TypeChart = require("src.battle.TypeChart")
  local Loader = require("src.mods.Loader")
  local Runtime = require("src.mods.Runtime")

  local data, loaded = buildData(Data, opts.data)
  T.check(loaded >= 5, "extracted data loaded (" .. loaded .. " modules)")
  T.check(data.pokemon and data.pokemon.PIKACHU ~= nil, "pokemon table present")
  TypeChart.load(data)

  local files, staged = stageMod(opts["mod-dir"], opts.mod)
  T.check(staged >= 5, "mod files staged (" .. staged .. ")")

  local loader = Loader.new({ fs = memfs(files) })
  local ok, err = pcall(loader.load, loader, data)
  T.check(ok, "loader:load did not raise (" .. tostring(err) .. ")")
  for _, message in ipairs(loader.errors or {}) do
    T.check(false, "loader error: " .. tostring(message))
  end
  T.eq(#(loader.errors or {}), 0, "zero loader errors")

  local mod = loader.mods and loader.mods[opts.mod]
  T.check(mod ~= nil, "mod discovered")
  T.eq(mod and mod.state, "loaded", "mod reached the loaded state")

  -- ----------------------------------------------------------- rosters
  -- The engine asks for a party by class and index; that is the only thing
  -- the mod keys on, so it is the only thing worth asserting.
  local function partyFor(class, index)
    local vanilla = data.trainers[class] and data.trainers[class].parties
    local base = vanilla and vanilla[index] or {}
    return Runtime.call("trainer.party", function() return base end,
                        class, index, base)
  end

  local function aceOf(party)
    local top = 0
    for _, slot in ipairs(party or {}) do
      if (slot.level or 0) > top then top = slot.level end
    end
    return top
  end

  -- The regression. In Yellow, OPP_RIVAL1 has three parties and they are
  -- three DIFFERENT battles: the lab, Route 22, and Cerulean. 1.6.0 keyed
  -- all three to the lab fight's starter variants, so a player met a lone
  -- level 6 starter every time. Red's #2 really IS a lab variant, and has
  -- to stay one.
  local lab = partyFor("OPP_RIVAL1", 1)
  T.eq(#lab, 1, "rival's lab battle is a single Pokemon")

  local second = partyFor("OPP_RIVAL1", 2)
  if opts.version == "yellow" then
    T.check(#second > 1,
      "yellow OPP_RIVAL1#2 is the Route 22 team, not a lone starter (" ..
      #second .. " slots)")
    T.check(aceOf(second) > 6,
      "yellow OPP_RIVAL1#2 ace outlevels the lab fight (L" ..
      aceOf(second) .. ")")
    local third = partyFor("OPP_RIVAL1", 3)
    T.check(#third > 1, "yellow OPP_RIVAL1#3 is the Cerulean team")
    T.check(aceOf(third) > aceOf(second),
      "yellow rival's Cerulean team outlevels his Route 22 team")
    -- his identity is the Eevee line, never a starter
    local names = {}
    for _, slot in ipairs(lab) do names[slot.species] = true end
    T.check(names.EEVEE == true, "yellow rival leads with Eevee, not a starter")
  else
    T.eq(#second, 1, opts.version .. " OPP_RIVAL1#2 is still a lab variant")
  end

  -- every authored key must be a key this version's data actually has
  local overrun = 0
  for _, class in ipairs({ "OPP_RIVAL1", "OPP_RIVAL2", "OPP_RIVAL3" }) do
    local parties = data.trainers[class] and data.trainers[class].parties or {}
    for index = 1, 12 do
      local got = partyFor(class, index)
      if index > #parties and #got > 0 and #(parties[index] or {}) == 0 then
        overrun = overrun + 1
      end
    end
  end
  T.eq(overrun, 0, "no roster is keyed past the version's real party count")

  -- gym leaders field six, with movesets
  for _, class in ipairs({ "OPP_BROCK", "OPP_MISTY", "OPP_LT_SURGE",
                           "OPP_ERIKA", "OPP_KOGA", "OPP_SABRINA",
                           "OPP_BLAINE", "OPP_LANCE" }) do
    local party = partyFor(class, 1)
    T.eq(#party, 6, class .. " fields six Pokemon")
    local withMoves, legal = 0, 0
    for _, slot in ipairs(party) do
      if slot.moves and #slot.moves > 0 then
        withMoves = withMoves + 1
        local allKnown = true
        for _, id in ipairs(slot.moves) do
          if not data.moves[id] then allKnown = false end
        end
        if allKnown then legal = legal + 1 end
      end
    end
    T.eq(withMoves, 6, class .. " carries a moveset on every slot")
    T.eq(legal, 6, class .. " uses only move ids this version has")
  end

  -- ------------------------------------------------------- boss switching
  -- The riskiest new code, so it is exercised directly rather than trusted:
  -- a boss that is outclassed should rotate to a backup that is not.
  local st = mod and mod.exports and mod.exports.aiState
  local consider = st and st.considerSwitch
  T.check(type(consider) == "function", "switch decision is exported for test")
  if type(consider) == "function" then
    local function battler(types, hp)
      return { curTypes = types, curMoves = {},
               mon = { hp = hp or 100, stats = { hp = 100 }, level = 50 } }
    end
    -- a Fire boss facing a Water lead, with a Water backup of its own
    local battle = {
      kind = "trainer", oppClass = "OPP_BLAINE", turnCount = 5,
      enemyIndex = 1, data = data,
      player = battler({ "WATER" }),
      enemy = battler({ "FIRE" }),
      enemyParty = {
        { species = "ARCANINE", hp = 100, stats = { hp = 100 }, level = 50 },
        { species = "LAPRAS",   hp = 100, stats = { hp = 100 }, level = 50 },
      },
    }
    local action = consider(battle)
    T.check(action ~= nil and action.index == 2,
      "an outclassed boss rotates to the backup that answers the matchup")

    -- and it stays put when it already has the advantage
    local winning = {
      kind = "trainer", oppClass = "OPP_BLAINE", turnCount = 5,
      enemyIndex = 1, data = data,
      player = battler({ "GRASS" }),
      enemy = battler({ "FIRE" }),
      enemyParty = {
        { species = "ARCANINE", hp = 100, stats = { hp = 100 }, level = 50 },
        { species = "LAPRAS",   hp = 100, stats = { hp = 100 }, level = 50 },
      },
    }
    T.check(consider(winning) == nil,
      "a boss with the advantage does not throw away a turn switching")

    -- a grace turn after every send-out, so it can never ping-pong
    local fresh = {
      kind = "trainer", oppClass = "OPP_BLAINE", turnCount = 0,
      enemyIndex = 1, data = data,
      player = battler({ "WATER" }),
      enemy = battler({ "FIRE" }),
      enemyParty = {
        { species = "ARCANINE", hp = 100, stats = { hp = 100 }, level = 50 },
        { species = "LAPRAS",   hp = 100, stats = { hp = 100 }, level = 50 },
      },
    }
    consider(fresh)
    T.check(consider(fresh) == nil,
      "no second switch on the same turn a Pokemon came out")

    -- and never for an ordinary trainer
    local grunt = {
      kind = "trainer", oppClass = "OPP_YOUNGSTER", turnCount = 5,
      enemyIndex = 1, data = data,
      player = battler({ "WATER" }),
      enemy = battler({ "FIRE" }),
      enemyParty = {
        { species = "ARCANINE", hp = 100, stats = { hp = 100 }, level = 50 },
        { species = "LAPRAS",   hp = 100, stats = { hp = 100 }, level = 50 },
      },
    }
    T.check(consider(grunt) == nil, "ordinary trainers never switch")
  end
end

function love.load(argv)
  local opts = parseArgs(argv or {})
  for _, key in ipairs({ "game", "mod-dir", "mod", "version", "data" }) do
    if not opts[key] then
      print("missing --" .. key)
      love.event.quit(2)
      return
    end
  end
  print(("== stronger_trainers :: %s :: engine %s =="):format(
    opts.version, tostring(opts.game):match("([^/\\]+)$") or "?"))
  local ok, err = pcall(run, opts)
  if not ok then
    T.failures = T.failures + 1
    print("  FAIL  harness raised: " .. tostring(err))
  end
  print(("%d checks, %d FAILURES"):format(T.checks, T.failures))
  love.event.quit(T.failures == 0 and 0 or 1)
end
