-- Gym battle formats.
--
-- Before you have a gym's badge, talking to the leader now runs:
--
--   leader's pre-battle dialogue  ->  "how many?" picker  ->  battle
--
-- The number is how many the LEADER brings, drawn from its six with its ace
-- always among them and the rest at random.  You then pick your own side from
-- the party screen one at a time, in send-out order -- first pick leads -- and
-- each round lists only the Pokemon still unpicked.
--
-- How it hooks in:
--
--   * `map_scripts` is a compose registry and the chain head wins, so an
--     entry for a gym's leader talk key replaces the engine's handler
--     (data/scripts/gyms.lua).  Once you hold the badge we hand straight back
--     to `MapScripts.baseTalk`, the engine's own delegation API, so the
--     post-badge dialogue and the bag-was-full TM retry stay vanilla -- none
--     of that is reimplemented here.
--   * `engageTrainer`'s fourth argument suppresses its own pre-battle text
--     (src/world/OverworldController.lua:3076), which is what lets the picker
--     sit *between* the dialogue and the battle rather than before both.
--   * `PartyMenu` does the picking: `onSwitch` without `battle` or `pickOnly`
--     makes A select (PartyMenu.lua:569) and keeps the engine's own
--     "Choose a POKeMON." prompt, and `opts.party` takes the shrinking
--     candidate list.
--   * Your side is installed by snapshotting `game.save.party` and rebuilding
--     that SAME table from your picks, then putting the snapshot back at
--     `battle.ended`.  The same table because engine state holds it; a
--     rebuild rather than a filter because pick order has to be able to
--     differ from party order.  The same Pokemon objects go back, never
--     copies, so HP and EXP earned in the fight are the real thing, and while
--     a snapshot is held `save.write` is vetoed so a narrowed, reordered
--     party can never reach the disk.
--
-- Losing with healthy Pokemon still in reserve blacks you out exactly as
-- gen 1 would.  That needs no code here: `battle.ended` fires before the
-- Pokemon Center heal on the loss path (BattleState.lua:1449), so the party
-- is whole again by the time anything looks at it.

return function(mod, state)
  local MapScripts = require("src.script.MapScripts")
  local TextBox = require("src.render.TextBox")
  local QuantityBox = require("src.ui.QuantityBox")
  local PartyMenu = require("src.ui.PartyMenu")
  local Strings = require("src.core.Strings")

  -- The format is how many the LEADER brings, so it is offered in full
  -- regardless of your own roster: your side is whatever you can field, up to
  -- that many.  Tying the ceiling to your party size instead would mean a
  -- five-Pokemon player could never face a leader's full six, which is the
  -- whole point of the mod.
  local MIN_FORMAT = 2  -- a 1v1 is not a gym battle
  local MAX_FORMAT = 6

  -- The engine's quantity selector counts 1..max and takes no floor, so it
  -- would offer a 1v1.  Inherit from it -- its draw reads only self.qty, so
  -- the box is pixel-identical to the game's own -- and replace just the
  -- stepping so Up/Down roll around within min..max.
  local FormatBox = setmetatable({}, { __index = QuantityBox })
  FormatBox.__index = FormatBox
  FormatBox.isOpaque = QuantityBox.isOpaque

  local function rollRange(v, min, max)
    if v < min then return max end
    if v > max then return min end
    return v
  end

  function FormatBox.new(game, opts)
    local box = setmetatable({}, FormatBox)
    box.game = game
    box.min = math.max(1, opts.min or 1)
    box.max = math.max(box.min, opts.max or 6)
    box.qty = math.min(math.max(opts.start or box.max, box.min), box.max)
    box.onDone = opts.onDone
    return box
  end

  function FormatBox:update(_dt)
    local input = self.game.input
    if input:wasPressed("up") then
      self.qty = rollRange(self.qty + 1, self.min, self.max)
    elseif input:wasPressed("down") then
      self.qty = rollRange(self.qty - 1, self.min, self.max)
    elseif input:wasPressed("a") then
      self.game.stack:pop()
      if self.onDone then self.onDone(self.qty) end
    elseif input:wasPressed("b") then
      self.game.stack:pop()
      if self.onDone then self.onDone(nil) end
    end
  end

  -- map id, leader talk key and beaten-flag for each gym, matching
  -- data/scripts/gyms.lua
  local GYMS = {
    { map = "PEWTER_GYM",    key = "TEXT_PEWTERGYM_BROCK",
      flag = "EVENT_BEAT_BROCK",    class = "OPP_BROCK" },
    { map = "CERULEAN_GYM",  key = "TEXT_CERULEANGYM_MISTY",
      flag = "EVENT_BEAT_MISTY",    class = "OPP_MISTY" },
    { map = "VERMILION_GYM", key = "TEXT_VERMILIONGYM_LT_SURGE",
      flag = "EVENT_BEAT_LT_SURGE", class = "OPP_LT_SURGE" },
    { map = "CELADON_GYM",   key = "TEXT_CELADONGYM_ERIKA",
      flag = "EVENT_BEAT_ERIKA",    class = "OPP_ERIKA" },
    { map = "FUCHSIA_GYM",   key = "TEXT_FUCHSIAGYM_KOGA",
      flag = "EVENT_BEAT_KOGA",     class = "OPP_KOGA" },
    { map = "SAFFRON_GYM",   key = "TEXT_SAFFRONGYM_SABRINA",
      flag = "EVENT_BEAT_SABRINA",  class = "OPP_SABRINA" },
    { map = "CINNABAR_GYM",  key = "TEXT_CINNABARGYM_BLAINE",
      flag = "EVENT_BEAT_BLAINE",   class = "OPP_BLAINE" },
    { map = "VIRIDIAN_GYM",  key = "TEXT_VIRIDIANGYM_GIOVANNI",
      flag = "EVENT_BEAT_GIOVANNI", class = "OPP_GIOVANNI" },
  }

  local function healthyCount(game)
    local n = 0
    for _, mon in ipairs(game.save.party or {}) do
      if mon and (mon.hp or 0) > 0 then n = n + 1 end
    end
    return n
  end

  local function healthyList(game)
    local out = {}
    for _, mon in ipairs(game.save.party or {}) do
      if mon and (mon.hp or 0) > 0 then out[#out + 1] = mon end
    end
    return out
  end

  -- Is there a team to choose, or only an order?  When the format takes
  -- everything standing the set is forced, and the pick screen would be
  -- button presses rather than a decision, so it is skipped.
  local function needsPicker(healthyN, format)
    return math.min(format, healthyN) < healthyN
  end

  -- Make `chosen` the battle party, in that exact order.
  --
  -- Snapshot the whole list, then rebuild the SAME table in place: identity
  -- matters because engine state holds this exact table, and rebuilding is
  -- what lets pick order differ from party order -- a filter with index
  -- bookkeeping could not reorder.  Restoring is then provably exact rather
  -- than a reconstruction: the snapshot is put back element for element.
  local function setBattleParty(game, chosen)
    local party = game.save.party
    local snapshot = {}
    for i, mon in ipairs(party) do snapshot[i] = mon end
    for i = #party, 1, -1 do party[i] = nil end
    for i, mon in ipairs(chosen) do party[i] = mon end
    return snapshot
  end

  local function restoreParty(game)
    local snapshot = state.snapshot
    if not snapshot then return end
    state.snapshot = nil
    local party = game.save.party
    for i = #party, 1, -1 do party[i] = nil end
    for i, mon in ipairs(snapshot) do party[i] = mon end
  end

  -- the very text engageTrainer would have printed: the trainer header's
  -- battle line, else the object's own text, else the engine's stock taunt
  -- (src/world/OverworldController.lua:3015-3020)
  local function preBattleText(game, ow, npc)
    local label = ow.map and ow.map.def and ow.map.def.label
    local d = npc.def
    local header = label and game.data:trainerHeader(label, d.index)
    local text = header and header.battle and game.data.text[header.battle]
    if not text and label then
      text = select(1, game.data:resolveText(label, d.text))
    end
    return text or Strings("I like shorts!\nThey're comfy and\neasy to wear!")
  end

  local function enabled()
    return mod.options:get("gym_formats") ~= false
  end

  local function handlerFor(gym)
    return function(game, ow, npc, done)
      local base = MapScripts.baseTalk(gym.map, gym.key)

      -- already beaten, feature switched off, or nothing standing to battle
      -- with at all: the engine's own handler, untouched
      if game.save.flags[gym.flag] or not enabled()
         or healthyCount(game) < 1 then
        if base then return base(game, ow, npc, done) end
        return ow:engageTrainer(npc, done)
      end

      -- Pick your side one at a time, in send-out order.  Each round shows
      -- only the Pokemon still unpicked, so nothing can be chosen twice and
      -- the list shrinks as you go.
      --
      -- Passing `onSwitch` with neither `battle` nor `pickOnly` set is what
      -- makes A select and hand the mon back (PartyMenu.lua:569) while the
      -- prompt stays the engine's own "Choose a POKeMON." box -- `pickOnly`
      -- would have printed "Use on which one?", which is for medicine.
      local function pickTeam(want, onReady)
        local picks = {}

        local function remaining()
          local out, taken = {}, {}
          for _, mon in ipairs(picks) do taken[mon] = true end
          for _, mon in ipairs(healthyList(game)) do
            if not taken[mon] then out[#out + 1] = mon end
          end
          return out
        end

        local function step()
          local candidates = remaining()
          -- enough picked, or nothing left to pick with
          if #picks >= want or #candidates == 0 then
            onReady(picks)
            return
          end
          game.stack:push(PartyMenu.new(game, {
            party = candidates,
            onSwitch = function(mon)
              picks[#picks + 1] = mon
              step()
            end,
            -- B undoes the last pick, and on the first pick backs out of the
            -- encounter entirely -- same escape the format picker offers
            onCancel = function()
              if #picks == 0 then
                if done then done() end
              else
                picks[#picks] = nil
                step()
              end
            end,
          }))
        end

        step()
      end

      local function ask()
        game.stack:push(FormatBox.new(game, {
          min = MIN_FORMAT,
          max = MAX_FORMAT,
          start = MAX_FORMAT,
          onDone = function(n)
            -- B backs out of the whole encounter, so you can leave to heal
            -- or reorder; the leader can be challenged again any time
            if not n then
              if done then done() end
              return
            end

            local healthy = healthyList(game)
            local want = math.min(n, #healthy)
            local function begin(chosen)
              if #chosen == 0 then
                if done then done() end
                return
              end
              state.class = gym.class
              state.count = n
              state.snapshot = setBattleParty(game, chosen)
              ow:engageTrainer(npc, done, nil, true)
            end

            -- forced set: party order stands in for a choice.  This is also
            -- where a lone Pokemon lands.
            if not needsPicker(#healthy, n) then
              begin(healthy)
              return
            end

            game.stack:push(TextBox.new(game,
              Strings("Choose %d POKéMON,\nin order!", want), function()
                pickTeam(want, begin)
              end))
          end,
        }))
      end

      game.stack:push(TextBox.new(game, preBattleText(game, ow, npc), function()
        game.stack:push(TextBox.new(game,
          Strings("How many POKéMON\neach?"), ask))
      end))
    end
  end

  for _, gym in ipairs(GYMS) do
    mod.content.map_scripts:register(gym.map, {
      talk = { [gym.key] = handlerFor(gym) },
    })
  end

  -- published so the party narrowing can be tested directly: it is the one
  -- part of this mod that touches save state
  mod.exports.FormatBox = FormatBox
  mod.exports.MIN_FORMAT = MIN_FORMAT
  mod.exports.MAX_FORMAT = MAX_FORMAT
  mod.exports.setBattleParty = setBattleParty
  mod.exports.restoreParty = restoreParty
  mod.exports.healthyCount = healthyCount
  mod.exports.healthyList = healthyList
  mod.exports.needsPicker = needsPicker

  -- A shorter fight pays a shorter purse.
  --
  -- Gen 1 prize money is `baseMoney x the level of the LAST enemy Pokemon`
  -- (BattleState.lua:3977), and the roster trim re-sorts survivors by level
  -- so the ace is always last -- so a "2 each" gym battle paid exactly what a
  -- "6 each" did. In a difficulty mod the shortest option should not also be
  -- the most profitable one.
  --
  -- Scaled by overlaying baseMoney for this battle only, which is the same
  -- shape the engine itself uses to give the rival his name
  -- (BattleState.newTrainer: setmetatable({ name = ... }, { __index = ... })).
  -- The overlay is what keeps it honest: the "got Y for winning!" line reads
  -- the same field, so the number announced is the number paid.
  mod.events:on("battle.started", function(ev)
    local battle = ev and ev.battle
    if not (battle and battle.trainer and battle.oppClass == state.class) then
      return
    end
    local full, fielded = state.full, state.fielded
    if not (full and fielded and fielded < full and full > 0) then return end
    local base = battle.trainer.baseMoney
    if type(base) ~= "number" or base <= 0 then return end
    local scaled = math.max(1, math.floor(base * fielded / full))
    battle.trainer = setmetatable({ baseMoney = scaled },
                                  { __index = battle.trainer })
  end)

  -- put the party back the moment the battle is over, win, lose or run
  mod.events:on("battle.ended", function(ev)
    local game = ev and ev.battle and ev.battle.game
    if game then restoreParty(game) end
    state.class, state.count = nil, nil
    state.full, state.fielded = nil, nil
  end)

  -- belt and braces: no progress write may capture a narrowed party
  mod.hooks:wrap("save.write", function(next, _game)
    if state.snapshot then
      mod.log:warn("save skipped: a gym format battle is still in progress")
      return false
    end
    return next()
  end)
end
