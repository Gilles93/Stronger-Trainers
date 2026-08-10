-- Static overworld encounters.
--
-- The fifteen battles the player walks into rather than earns from a trainer:
-- the ghost on Pokemon Tower 6F, the two Snorlax asleep in the road, the
-- eight disguised item balls in the Power Plant, the three legendary birds
-- and Mewtwo. Levels and movesets are authored in tools/statics.py and read
-- from the generated statics.lua.
--
-- Why this file shadows an engine function instead of using a hook.
--
-- There is no wild-party hook. `trainer.party` is offered by
-- BattleState.newTrainer and has no counterpart on the wild path:
-- BattleState.newWild builds one Pokemon with Pokemon.new and hands it
-- straight to makeBattler, and nothing between those two calls asks the mod
-- runtime anything. Runtime.wantsHook is never consulted on that path at
-- all. So the only choke point is newWild itself, which the engine_internals
-- permission lets this mod reach.
--
-- Shadowing rather than replacing is what keeps it composable: the previous
-- newWild is captured and called, so overworld_wild_spawns and any other mod
-- that *calls* newWild still gets served, and a mod that shadows it after us
-- still wraps whatever we return.
--
-- All fifteen route through here. Fourteen come via Commands.static_battle,
-- and the ghost Marowak does not -- data/scripts/story3.lua builds its battle
-- with BattleState.newWild directly so it can set battle.noCatch -- which is
-- the second reason to sit on newWild rather than on the command.
--
-- HOW A STATIC IS RECOGNISED. By the triple (map, species, the level the
-- caller asked for), never by species and level alone. The map's own wild
-- table is full of the same species: Voltorb roams the Power Plant grass at
-- 21 and 23, Marowak appears wild at 40, 43, 52 and 55, and Electrode at 52
-- and 55 in Cerulean Cave. Keying on the vanilla level the script passes in
-- is exact, and tools/build_statics.py refuses to emit a row whose triple
-- collides with the wild table on its own map.

-- Every path bails to the untouched original, so a build that has moved any
-- of this around loses the feature and nothing else.
return function(mod, STATICS)
  local okBattle, BattleState = pcall(require, "src.battle.BattleState")
  if not okBattle or type(BattleState) ~= "table" then
    mod.log:warn("BattleState unavailable; static encounters disabled")
    return
  end

  local original = BattleState.newWild
  if type(original) ~= "function" then
    mod.log:warn("BattleState.newWild is not a function; "
                 .. "static encounters disabled")
    return
  end

  if type(STATICS) ~= "table" then return end

  -- Which map the player is standing on.
  --
  -- src.core.Game is a singleton module table, and OverworldState:enter
  -- assigns the live instance over the class that Game:load put there
  -- (`Game.overworld = self`, OverworldController.lua). So the field answers
  -- the class before the first map is entered and the instance afterwards;
  -- `ow.map` is what tells the two apart, and a battle can only start from
  -- the second. The argument is preferred over a fresh require because it is
  -- the same table, and a caller with its own game object stays honoured.
  local function currentMap(game)
    local ow = game and game.overworld
    if not (type(ow) == "table" and ow.map) then
      local ok, Game = pcall(require, "src.core.Game")
      ow = ok and type(Game) == "table" and Game.overworld or nil
    end
    if type(ow) == "table" and type(ow.map) == "table" then
      return ow.map.id
    end
    return nil
  end

  local function rowFor(game, species, level)
    local mapId = currentMap(game)
    if not mapId then return nil end
    for _, row in ipairs(STATICS[mapId] or {}) do
      if row[1] == species and row[2] == level then return row end
    end
    return nil
  end

  -- The authored set, written onto the Pokemon rather than only onto the
  -- battler view.
  --
  -- makeBattler takes `curMoves = mon.moves` by reference, so mutating one
  -- would reach both -- but a caught legendary is `self.enemy.mon` handed
  -- straight to the party (BattleState.lua's catch path stamps OT on that
  -- exact table), so the Pokemon is the one that has to be right. Both
  -- fields are assigned explicitly rather than relying on the alias holding.
  --
  -- The shape is the one newTrainer builds for an authored party slot:
  -- { id = , pp = }, PP from the merged move record so another mod's PP edit
  -- is honoured.
  local function applyMoves(battle, data, moves)
    local enemy = battle and battle.enemy
    local mon = enemy and enemy.mon
    if not mon then return end
    local built = {}
    for _, moveId in ipairs(moves) do
      local mdef = data and data.moves and data.moves[moveId]
      -- a move this build does not carry is skipped rather than fatal: a
      -- three-move legendary is a worse fight, an assert is a crash
      if mdef then
        built[#built + 1] = { id = moveId, pp = mdef.pp or 0 }
      end
    end
    if #built == 0 then return end
    mon.moves = built
    enemy.curMoves = built
  end

  BattleState.newWild = function(game, species, level, opts)
    if mod.options:get("statics") == false then
      return original(game, species, level, opts)
    end

    local ok, row = pcall(rowFor, game, species, level)
    if not ok or type(row) ~= "table" then
      return original(game, species, level, opts)
    end

    -- The level goes in through the original, not patched on afterwards:
    -- newWild runs Pokemon.new and makeBattler, and stats, HP and the
    -- level-up fallback set all key off the level it was given.
    local battle = original(game, species, row[3], opts)

    -- Moves are the second switch, mirroring BOSS TEAMS / BOSS MOVESETS: with
    -- them off the encounter keeps the raised level and the engine fills in
    -- the species' own level-up set for it.
    if mod.options:get("static_moves") ~= false and type(row[4]) == "table" then
      pcall(applyMoves, battle, game and game.data, row[4])
    end
    return battle
  end
end
