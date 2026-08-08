-- Smarter trainer AI, as an ai_classes scoring layer.
--
-- Vanilla gen 1 scores every usable move from a base of 10, each layer nudges
-- additively, and the LOWEST score wins with ties broken at random
-- (TrainerAI.chooseMove).  All three vanilla layers together only handle:
-- discourage a status move that would fail (+5), encourage some effects on the
-- encouragement turn (-1), and +-1 for type effectiveness.  Nothing estimates
-- damage, reads HP, or weighs accuracy.  This layer adds that.
--
-- Why a new record id and not a patch of LAYER_3:
--
--   TrainerAI resolves layers from each trainer's own `aiMods` list, and an
--   entry may name ANY registered ai_classes record by string
--   (TrainerAI.lua:255-266).  So registering a new id and appending it to
--   aiMods composes with the vanilla three AND with modern_kanto's LAYER_3
--   type pass -- every layer runs, additively, in aiMods order.  Patching
--   LAYER_3 instead would have silently replaced modern_kanto's work.
--   The flip side, which modern_kanto's own comment warns about: a registered
--   id nobody references never runs, so the aiMods patch below is not
--   optional bookkeeping, it is what makes this layer exist at all.
--
-- Fair information only.  The AI reads the target's HP at the resolution of
-- the on-screen HP bar (48 pixels, the width gen 1 draws) and never looks at
-- the player's move list, stats or DVs.  It plays off what a person sitting
-- opposite could see.
--
-- Deliberately NOT modelled, because they are the tactics that make gen 1
-- miserable rather than hard: re-sleeping a sleeping target, chasing Blizzard
-- freezes, Wrap/Fire Spin lock-outs, the Hyper Beam no-recharge-on-KO rule,
-- and Explosion spam.  The suppressions are explicit below rather than
-- emergent, so they cannot be undone by a scoring tweak.

return function(mod, state)
  local Damage = require("src.battle.Damage")
  local TypeChart = require("src.battle.TypeChart")

  local LAYER_ID = "ST_SMART"
  local HP_BAR_PIXELS = 48   -- gen 1 draws the HP bar 48px wide
  local MAX_HEALS = 2        -- healing moves per Pokemon per battle
  local HEAL_BELOW = 0.5     -- and only when this hurt
  -- one full effectiveness step on the chart's x10 scale: the improvement a
  -- backup has to offer before a boss will spend a turn rotating to it
  local SWITCH_MIN_GAIN = 10

  -- effect ids as they appear in the ROM data
  local HEAL = { HEAL_EFFECT = true }
  local SETUP = {
    ATTACK_UP1_EFFECT = true, ATTACK_UP2_EFFECT = true,
    DEFENSE_UP1_EFFECT = true, DEFENSE_UP2_EFFECT = true,
    SPECIAL_UP1_EFFECT = true, SPECIAL_UP2_EFFECT = true,
    SPEED_UP2_EFFECT = true, EVASION_UP1_EFFECT = true,
    FOCUS_ENERGY_EFFECT = true, LIGHT_SCREEN_EFFECT = true,
    REFLECT_EFFECT = true, MIST_EFFECT = true,
  }
  -- the status a move inflicts, so a move can be checked against what the
  -- target already has instead of vanilla's blanket "has any status"
  local INFLICTS = {
    SLEEP_EFFECT = "sleep",
    POISON_EFFECT = "poison", POISON_SIDE_EFFECT1 = "poison",
    POISON_SIDE_EFFECT2 = "poison",
    PARALYZE_EFFECT = "paralysis", PARALYZE_SIDE_EFFECT1 = "paralysis",
    PARALYZE_SIDE_EFFECT2 = "paralysis",
  }
  -- cheese, suppressed on purpose
  local TRAPPING = { TRAPPING_EFFECT = true }
  local EXPLODE = { EXPLODE_EFFECT = true }
  local RECHARGE = { HYPER_BEAM_EFFECT = true }
  -- fixed-damage moves: real damage that Damage.compute reports as 0 because
  -- their listed power is 0
  local FIXED = {
    SPECIAL_DAMAGE_EFFECT = true, SUPER_FANG_EFFECT = true,
    OHKO_EFFECT = true,
  }

  -- Deterministic damage estimate.  forceCrit skips the crit roll entirely;
  -- the accuracy roll is the only remaining rng(0,255) call, and answering 0
  -- makes it never miss so the estimate is the move's damage, not a coin
  -- flip.  The damage roll asks for (randMin, randMax) and gets the midpoint.
  local function estimateRng(lo, hi)
    if lo == 0 and hi == 255 then return 0 end
    return math.floor(((lo or 0) + (hi or 0)) / 2)
  end

  -- What the HP bar shows, not what the save holds.
  local function visibleHp(mon)
    if not (mon and mon.stats and mon.stats.hp) then return 0, 1 end
    local max = math.max(1, mon.stats.hp)
    local px = math.ceil(math.max(0, mon.hp or 0) / max * HP_BAR_PIXELS)
    return px / HP_BAR_PIXELS * max, max
  end

  local function selfFraction(battler)
    local mon = battler and battler.mon
    if not (mon and mon.stats and mon.stats.hp) then return 1 end
    return math.max(0, mon.hp or 0) / math.max(1, mon.stats.hp)
  end

  -- heals used, keyed by the live enemy mon; cleared per battle
  local heals = setmetatable({}, { __mode = "k" })

  mod.events:on("battle.started", function() heals = setmetatable({}, { __mode = "k" }) end)
  mod.events:on("battle.ended", function() heals = setmetatable({}, { __mode = "k" }) end)
  mod.events:on("battle.move_used", function(ev)
    local battle, user, move = ev and ev.battle, ev and ev.user, ev and ev.move
    if not (battle and user and move) or user.isPlayer then return end
    if HEAL[move.effect] and user.mon then
      heals[user.mon] = (heals[user.mon] or 0) + 1
    end
  end)

  local function bossClasses(teams)
    local set = {}
    for key in pairs(teams or {}) do
      local class = tostring(key):match("^(.*)#")
      if class then set[class] = true end
    end
    return set
  end

  local function score(view, def, current, bosses)
    if not def then return current end
    local battle, user, target = view.battle, view.user, view.target
    if not (battle and user and target) then return current end

    -- live gating, so the MODS rows apply to the next turn rather than the
    -- next restart
    if mod.options:get("smart_ai") == false then return current end
    if mod.options:get("smart_ai_scope") ~= "all"
       and not bosses[tostring(battle.oppClass)] then
      return current
    end

    local adj = 0
    local hp, maxHp = visibleHp(target.mon)
    local mine = selfFraction(user)

    -- ---------------------------------------------------------- damage & KO
    local dmg = 0
    local ok, result = pcall(Damage.compute, battle.ruleset, user, target, def,
                             { forceCrit = false, rng = estimateRng })
    if ok and type(result) == "number" then dmg = result end
    if dmg == 0 and FIXED[def.effect] then
      -- Seismic Toss and friends: level damage is the honest approximation,
      -- Super Fang takes half of what the bar shows
      dmg = def.effect == "SUPER_FANG_EFFECT" and hp / 2
            or (user.mon and user.mon.level or 20)
      if def.effect == "OHKO_EFFECT" then dmg = hp end
    end

    if dmg > 0 then
      -- accuracy weighting: expected damage, so a reliable move beats a
      -- stronger gamble.  This is what stops Horn Drill and Blizzard looking
      -- like free wins, and it can make the AI *easier* -- that is correct.
      local acc = math.min(100, def.accuracy or 100) / 100
      local expected = dmg * acc
      local share = math.min(1, expected / math.max(1, maxHp))
      adj = adj - math.floor(share * 6 + 0.5)   -- up to -6 for a full bar

      -- a move that finishes the job, weighted by how likely it is to land
      if dmg >= hp and hp > 0 then
        adj = adj - (acc >= 0.9 and 6 or acc >= 0.7 and 4 or 2)
      end
      -- Hyper Beam's recharge is a real cost when it does not finish things.
      -- The exploit is the reverse -- valuing it BECAUSE a KO skips the
      -- recharge -- and that is simply not modelled anywhere here.
      if RECHARGE[def.effect] and dmg < hp then adj = adj + 3 end
    end

    -- --------------------------------------------------- status, used sanely
    local want = INFLICTS[def.effect]
    if want then
      local has = target.mon and target.mon.status
      if has then
        adj = adj + 4                      -- already statused: pointless
      elseif want == "sleep" then
        adj = adj + 1                      -- fair play, never a lock: no bonus
      end
    end

    -- ------------------------------------------------------ self-preservation
    if SETUP[def.effect] and mine < 0.5 then
      adj = adj + 4                        -- no setting up while dying
    end

    if HEAL[def.effect] then
      local used = (user.mon and heals[user.mon]) or 0
      if used >= MAX_HEALS or mine > HEAL_BELOW then
        adj = adj + 8                       -- capped, or not hurt enough
      else
        adj = adj - 3
      end
    end

    -- ------------------------------------------------------------- no cheese
    if TRAPPING[def.effect] then adj = adj + 3 end
    if EXPLODE[def.effect] then adj = adj + 6 end

    return current + adj
  end

  -- ------------------------------------------------------------- switching
  --
  -- Vanilla Gen 1 trainers effectively never switch on purpose:
  -- TrainerAI.switchAction takes the FIRST unfainted backup whatever the
  -- matchup, and only a handful of classes roll for it at all.  This makes a
  -- boss rotate deliberately, into something the matchup actually favours.
  --
  -- Why `battle.enemy_action` and not an ai_classes brain: a brain supersedes
  -- the class action AND move scoring outright (BattleState:vanillaEnemyAction
  -- returns brain(self) before either runs), which would throw away this
  -- file's own scoring layer, the vanilla three, and modern_kanto's type
  -- pass.  Wrapping the choke point instead lets the switch be an exception
  -- and leaves every other turn to fall through untouched.
  --
  -- Fair information, the same rule the scoring layer holds to: this reads
  -- SPECIES TYPES on both sides, which is what a player can see across the
  -- field, and never the player's move list, stats or DVs.  Type stands in
  -- for what each side is threatening rather than a peek at what it actually
  -- carries.
  --
  -- The turn it costs is what keeps it honest -- the player gets a free move
  -- every time a boss rotates -- and three things stop it becoming a stall:
  -- a per-battle cap, a grace turn after every send-out so it can never
  -- ping-pong, and a refusal to switch away from a Pokemon that can already
  -- finish the job this turn.

  -- per-battle bookkeeping; weak keys so a finished battle is collectable
  local switching = setmetatable({}, { __mode = "k" })

  local function recordFor(battle)
    local rec = switching[battle]
    if not rec then
      rec = { count = 0, index = battle.enemyIndex, since = -1 }
      switching[battle] = rec
    end
    -- a send-out (ours or a faint replacement) restarts the grace turn
    if rec.index ~= battle.enemyIndex then
      rec.index = battle.enemyIndex
      rec.since = battle.turnCount or 0
    end
    return rec
  end

  local function typesFor(battle, mon)
    local dex = battle.data and battle.data.pokemon
    local def = dex and mon and mon.species and dex[mon.species]
    return def and def.types or nil
  end

  -- best multiplier any of `attacking` gets against `defending`, x10
  local function bestAgainst(attacking, defending)
    local top = 0
    for _, t in ipairs(attacking) do
      local m = TypeChart.effectiveness(t, defending)
      if m > top then top = m end
    end
    return top
  end

  -- How well a Pokemon of `mine` fares against what the player has out:
  -- what it threatens, less what it is threatened by.  0 is an even trade.
  local function matchup(battle, mine)
    local theirs = battle.player and battle.player.curTypes
    if not (mine and theirs and #mine > 0 and #theirs > 0) then return nil end
    return bestAgainst(mine, theirs) - bestAgainst(theirs, mine)
  end

  -- Would the Pokemon already out finish the player this turn?  Switching
  -- away from a kill is never right, and this is the same visible-HP,
  -- deterministic estimate the scoring layer uses.
  local function canFinish(battle)
    local user, target = battle.enemy, battle.player
    if not (user and target and battle.data and battle.data.moves) then
      return false
    end
    local hp = visibleHp(target.mon)
    if hp <= 0 then return true end
    for _, mv in ipairs(user.curMoves or {}) do
      local def = battle.data.moves[mv.id]
      if def then
        local ok, dmg = pcall(Damage.compute, battle.ruleset, user, target, def,
                             { forceCrit = false, rng = estimateRng })
        if ok and type(dmg) == "number" and dmg >= hp then return true end
      end
    end
    return false
  end

  local function considerSwitch(battle, bosses)
    if not battle or battle.kind ~= "trainer" then return nil end
    if mod.options:get("boss_switching") == false then return nil end
    if not bosses[tostring(battle.oppClass)] then return nil end

    local cap = math.floor(tonumber(mod.options:get("boss_switch_cap")) or 2)
    if cap <= 0 then return nil end

    local rec = recordFor(battle)
    if rec.count >= cap then return nil end
    -- one full turn on the field before it may rotate again
    if (battle.turnCount or 0) <= rec.since then return nil end

    local current = matchup(battle, battle.enemy and battle.enemy.curTypes)
    -- unknown types mean no informed call is available; leave the turn alone
    if current == nil or current >= 0 then return nil end
    if canFinish(battle) then return nil end

    local pick, pickScore
    for i, mon in ipairs(battle.enemyParty or {}) do
      if i ~= battle.enemyIndex and (mon.hp or 0) > 0 then
        local score = matchup(battle, typesFor(battle, mon))
        if score and (not pickScore or score > pickScore) then
          pick, pickScore = i, score
        end
      end
    end
    if not pick or pickScore < current + SWITCH_MIN_GAIN then return nil end

    rec.count = rec.count + 1
    rec.index = pick
    rec.since = battle.turnCount or 0
    return { special = "aiSwitch", index = pick }
  end

  return function(teams)
    local bosses = bossClasses(teams)

    -- A throw in here would cost the enemy its whole turn, so any surprise
    -- falls through to whatever the chain would have chosen anyway.
    mod.hooks:wrap("battle.enemy_action", function(next, battle)
      local ok, action = pcall(considerSwitch, battle, bosses)
      if ok and type(action) == "table" then return action end
      return next(battle)
    end)

    mod.content.ai_classes:register(LAYER_ID, {
      kind = "layer",
      score = function(view, def, current)
        local ok, result = pcall(score, view, def, current, bosses)
        -- a throw in here would take the enemy's whole turn with it, so an
        -- unexpected shape leaves the vanilla score alone
        if ok and type(result) == "number" then return result end
        return current
      end,
    })

    -- Make every trainer reference the layer.  Registering without this is
    -- the inert-record trap; the live option check inside `score` is what
    -- actually decides whether it does anything, which keeps the MODS rows
    -- working without a restart.
    local attached = 0
    for id, record in mod.content.trainers:each() do
      local mods = {}
      local seen = false
      for _, entry in ipairs(record.aiMods or {}) do
        mods[#mods + 1] = entry
        if entry == LAYER_ID then seen = true end
      end
      if not seen then
        mods[#mods + 1] = LAYER_ID
        mod.content.trainers:patch(id, { aiMods = mods })
        attached = attached + 1
      end
    end
    mod.log:info("smart AI layer attached to %d trainer classes", attached)

    state.LAYER_ID = LAYER_ID
    state.scoreFor = score
    state.bosses = bosses
    state.heals = function() return heals end
    state.considerSwitch = function(battle) return considerSwitch(battle, bosses) end
    state.matchup = matchup
  end
end
