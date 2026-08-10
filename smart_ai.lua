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
  local FINISH_BELOW = 0.4   -- below this, stop setting up and finish it
  local SETUP_ABOVE = 0.5    -- and never set up below this much of your own

  -- Damage in bands, not a gradient.
  --
  -- TrainerAI.chooseMove takes the LOWEST-scoring move and breaks ties at
  -- random among the minima, and that tie-break is the only variety Gen 1's
  -- AI has ever had: the three vanilla layers only ever nudge by one, so ties
  -- are the normal case.  Scoring damage per-point made ties impossible and
  -- collapsed this layer into "use the single biggest move, every turn" --
  -- five of Giovanni's six had exactly one best move and never deviated from
  -- it.  Bands let comparable moves tie again, while a genuinely dominant
  -- move still wins outright.
  local function damageBand(share)
    if share >= 0.9 then return 4 end      -- takes the bar off
    if share >= 0.4 then return 2 end      -- a solid hit
    return 1                               -- chip
  end
  -- How much better a backup has to be before a boss will spend a turn
  -- rotating to it, on the chart's x10 scale.
  --
  -- Not "one effectiveness step", whatever the old comment here said: the
  -- number this is compared against is a DIFFERENCE of two x10 multipliers,
  -- and a step on that scale is worth +5 going 0.5x -> 1x, +10 going 1x ->
  -- 2x and +20 going 2x -> 4x.  10 is the neutral-to-super-effective step,
  -- which is the one that matters: it buys a rotation that turns an even
  -- trade into a threat, and refuses one that only stops a resist.
  local SWITCH_MIN_GAIN = 10

  -- effect ids as they appear in the ROM data
  local HEAL = { HEAL_EFFECT = true }
  local LEECH = { LEECH_SEED_EFFECT = true }
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
  --
  -- Confusion is in here for the same reason the stat moves below are: it
  -- reached no branch at all, which left CONFUSE_RAY and SUPERSONIC sitting
  -- at the base 10 while any attack scored under it, so neither could ever
  -- be picked -- 24 authored roster slots carry one of them.  It is checked
  -- against a different field than the rest (see `already` in score): gen 1
  -- keeps confusion as a volatile on the battler, not as mon.status.
  local INFLICTS = {
    SLEEP_EFFECT = "sleep",
    POISON_EFFECT = "poison", POISON_SIDE_EFFECT1 = "poison",
    POISON_SIDE_EFFECT2 = "poison",
    PARALYZE_EFFECT = "paralysis", PARALYZE_SIDE_EFFECT1 = "paralysis",
    PARALYZE_SIDE_EFFECT2 = "paralysis",
    CONFUSION_EFFECT = "confusion", CONFUSION_SIDE_EFFECT = "confusion",
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

  -- Every "lower the target's something" effect is named the same way --
  -- DEFENSE_DOWN2_EFFECT, ACCURACY_DOWN1_EFFECT -- so match the shape rather
  -- than list twenty ids that would drift out of date.
  local function isDebuff(effect)
    return type(effect) == "string" and effect:find("_DOWN%d") ~= nil
  end

  -- Per-battle memory, all keyed by the live enemy mon and all cleared
  -- together: heals spent, stat moves already used, and last turn's move.
  local heals, statUses, lastMove

  local function forget()
    heals = setmetatable({}, { __mode = "k" })
    statUses = setmetatable({}, { __mode = "k" })
    lastMove = setmetatable({}, { __mode = "k" })
  end
  forget()

  local function usedFor(mon, effect)
    local per = mon and statUses[mon]
    return (per and per[effect]) or 0
  end

  mod.events:on("battle.started", forget)
  mod.events:on("battle.ended", forget)
  mod.events:on("battle.move_used", function(ev)
    local battle, user, move = ev and ev.battle, ev and ev.user, ev and ev.move
    if not (battle and user and move) or user.isPlayer then return end
    if not user.mon then return end
    if HEAL[move.effect] then
      -- This event is emitted before the effect runs (BattleState.lua:3481),
      -- and HEAL_EFFECT refuses outright at full HP -- Rest included
      -- (MoveEffects.lua:204, 211).  It reads the very HP this event carries,
      -- so a heal that is about to fail is knowable here, and one that never
      -- restored anything must not spend one of the two the boss gets.
      local mon = user.mon
      local full = mon.stats and mon.stats.hp and mon.hp == mon.stats.hp
      if not full then
        heals[mon] = (heals[mon] or 0) + 1
      end
    end
    lastMove[user.mon] = move.id
    if (move.power or 0) == 0 then
      local per = statUses[user.mon]
      if not per then per = {}; statUses[user.mon] = per end
      per[move.effect] = (per[move.effect] or 0) + 1
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
    -- how much of the target is left, and whether finishing it now beats
    -- spending the turn on anything else
    local left = maxHp > 0 and hp / maxHp or 1
    local finishing = left <= FINISH_BELOW
    local isStatusMove = (def.power or 0) == 0

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
      adj = adj - damageBand(share)

      -- a move that finishes the job, weighted by how likely it is to land
      if dmg >= hp and hp > 0 then
        adj = adj - (acc >= 0.9 and 4 or acc >= 0.7 and 3 or 2)
      end
      -- Hyper Beam's recharge is a real cost when it does not finish things.
      -- The exploit is the reverse -- valuing it BECAUSE a KO skips the
      -- recharge -- and that is simply not modelled anywhere here.
      if RECHARGE[def.effect] and dmg < hp then adj = adj + 3 end
    end

    -- --------------------------------------------------- status, used sanely
    --
    -- Only for moves that do nothing else.  The old rule fired on damaging
    -- moves carrying a status side effect too, so Body Slam was discouraged
    -- against an already-paralysed target -- it is a fine attack either way.
    local want = isStatusMove and INFLICTS[def.effect]
    if want then
      -- "it already has that" reads a different field per family: confusion
      -- is a volatile counter on the battler (MoveEffects.lua:154 refuses a
      -- second application), everything else is the persistent mon.status
      local already
      if want == "confusion" then
        already = target.confusedTurns ~= nil
      else
        already = target.mon ~= nil and target.mon.status ~= nil
      end
      if already then
        adj = adj + 4                      -- already statused: pointless
      elseif finishing then
        adj = adj + 2                      -- too late to be worth a turn
      elseif want == "sleep" then
        adj = adj - 1                      -- worth a turn, but never a lock
      else
        adj = adj - 2
      end
    end

    -- ------------------------------------------------ stat moves and seeding
    --
    -- These scored nothing at all before, which pinned them at the base of 10
    -- while any attack scored below it.  Since the lowest score wins, that
    -- made every one of them unpickable -- 117 authored status moves across
    -- the rosters that could never once be used.  Each is worth a turn, once.
    if isStatusMove and (SETUP[def.effect] or LEECH[def.effect]
                         or isDebuff(def.effect)) then
      if usedFor(user.mon, def.effect) > 0 then
        adj = adj + 3                      -- said once already
      elseif finishing then
        adj = adj + 2                      -- finish it instead
      elseif SETUP[def.effect] and mine < SETUP_ABOVE then
        adj = adj + 4                      -- no setting up while dying
      else
        adj = adj - 1
      end
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

    -- ----------------------------------------------------------- say it once
    -- One point of "pick something else".  Enough to lose a tie to an equally
    -- good move, never enough to talk it out of a knockout.
    if def.id and lastMove[user.mon] == def.id then
      adj = adj + 1
    end

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

  -- The two halves of the "resolve it first" fix below, both weak-keyed on
  -- the outgoing battler so they go with the battle.  They are separate
  -- because they have opposite lifetimes: `rotating` answers exactly one
  -- turn-order question and is consumed doing it, while `withdrawn` has to
  -- outlive the switch so the player's row -- which runs after it -- can
  -- still recognise the Pokemon it was aimed at.  Leaving `withdrawn` set is
  -- safe: every send-out builds a fresh battler, so an entry can never
  -- describe whoever is on the field later.
  local rotating = setmetatable({}, { __mode = "k" })
  local withdrawn = setmetatable({}, { __mode = "k" })

  local function recordFor(battle)
    local rec = switching[battle]
    if not rec then
      -- `seen` counts this Pokemon's own action decisions since it came out.
      -- The lead starts at 1 so its opening decision may still rotate, the
      -- way it always has; every later send-out starts at 0 and owes a turn
      -- on the field before it may leave again.
      rec = { count = 0, index = battle.enemyIndex, seen = 1 }
      switching[battle] = rec
    end
    -- Settle the last rotation against what actually happened.  The decision
    -- is made a turn ahead of the action that carries it out, and executeAction
    -- drops the whole row if the Pokemon is knocked out before it comes up
    -- (BattleState.lua:3173), so a rotation can be chosen and never run.
    -- Charging the fight's switch allowance for one that never happened cost
    -- the boss a rotation it never got to make.  Counted optimistically and
    -- refunded here rather than counted on confirmation, because the failure
    -- that matters is the other one: a cap that never fills would let a boss
    -- rotate every turn for the rest of the fight.
    if rec.pending then
      if battle.enemyIndex ~= rec.pending then
        rec.count = math.max(0, rec.count - 1)
      end
      rec.pending = nil
    end
    -- a send-out (ours or a faint replacement) starts the count again
    if rec.index ~= battle.enemyIndex then
      rec.index = battle.enemyIndex
      rec.seen = 0
    end
    rec.seen = rec.seen + 1
    return rec
  end

  -- Rotating first, the way every generation from 2 on does it.
  --
  -- Gen 1 gives the trainer's item/switch the enemy's own slot in the turn
  -- order -- pokered runs TrainerAI where ExecuteEnemyMove would have gone --
  -- and BattleState.resolveTurn is faithful to that: an aiSwitch action
  -- carries no move id, so orderMove hands TurnOrder a nil move, priority is
  -- 0 on both sides and the faster mon goes first.  A player faster than the
  -- boss therefore spends the turn hitting the Pokemon that is already on its
  -- way out, which is what gets reported as "it switched after I attacked".
  --
  -- Two things have to move together, and the second is why this is not a
  -- one-line answer to battle.turn_order:
  --
  --   * order.  battle.turn_order is the engine's own choke point for who
  --     goes first, so the rotation turn answers "the enemy" there and every
  --     other turn falls through to the vanilla speed compare untouched.
  --   * target.  resolveTurn builds BOTH rows of the turn -- each a
  --     {user, target, action} triple -- before either one runs, so the
  --     player's row holds the battler that was out when the turn began.  The
  --     rotation replaces battle.enemy with a fresh battler, which leaves
  --     that row aimed at a Pokemon that has left the field: the send-out
  --     message would play and the attack would still land on the one that
  --     withdrew.  Vanilla only reaches this when a Juggler or Agatha rolls
  --     a switch while faster; rotating on purpose makes it every time.
  --
  -- The retarget is installed on the battle INSTANCE -- Lua finds it before
  -- BattleState.__index does -- and only on a fight this mod has actually
  -- rotated in, so wild battles, ordinary trainers and the link-battle
  -- lockstep never see it.  The class method is read at call time so a
  -- class-level wrap by another mod still composes.  Returns false when the
  -- engine module is out of reach, and the caller then leaves the turn order
  -- alone too: vanilla ordering is the wrong feel, a send-out that hits the
  -- wrong Pokemon is a broken battle.
  local function installRetarget(battle)
    if rawget(battle, "executeAction") then return true end
    local ok, BattleState = pcall(require, "src.battle.BattleState")
    if not (ok and type(BattleState) == "table"
            and type(BattleState.executeAction) == "function") then
      return false
    end
    battle.executeAction = function(self, user, target, action)
      -- `target ~= self.enemy` is what makes this fire only once the switch
      -- has really happened, and the HP test keeps it off the other way a
      -- battler leaves the field: a Pokemon that fainted mid-turn must go on
      -- reaching the vanilla no-op rather than handing its row to whatever
      -- replaced it.
      if target and withdrawn[target] and target ~= self.enemy
         and target.mon and (target.mon.hp or 0) > 0 then
        target = self.enemy
      end
      return BattleState.executeAction(self, user, target, action)
    end
    return true
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

  -- What a Pokemon of ours actually threatens: the best multiplier any of its
  -- damaging MOVES lands on what the player has out.
  --
  -- Reading our own movesets is not a fairness question -- it is our own team,
  -- and the rule this file holds to is about never reading the PLAYER's. It is
  -- also the difference between the rotation meaning something and not: judged
  -- on species types, a mono-type roster has nothing better to rotate to, ever.
  -- Blaine is six Fire and Surge is six Electric, so between them they could
  -- not rotate in a single one of the 456 lead-vs-player matchups the type
  -- chart allows -- while Blaine's Magmar sits on the bench carrying Psychic
  -- and Submission, which is exactly the answer the rotation exists to find.
  --
  -- Species types stay the proxy for what the PLAYER threatens, because that
  -- is the half we are not allowed to look up.
  local function threatOf(battle, moves, ownTypes, theirs)
    local dex = battle.data and battle.data.moves
    local top
    for _, mv in ipairs(moves or {}) do
      local def = dex and mv and dex[mv.id]
      if def and (def.power or 0) > 0 and def.type then
        local m = TypeChart.effectiveness(def.type, theirs)
        if not top or m > top then top = m end
      end
    end
    -- no readable moveset (a slot the engine filled in, or a status-only
    -- set): fall back to species types, which is what this always did
    if not top then return bestAgainst(ownTypes, theirs) end
    return top
  end

  -- How well a Pokemon of `mine` fares against what the player has out:
  -- what it threatens, less what it is threatened by.  0 is an even trade.
  local function matchup(battle, mine, moves)
    local theirs = battle.player and battle.player.curTypes
    if not (mine and theirs and #mine > 0 and #theirs > 0) then return nil end
    return threatOf(battle, moves, mine, theirs) - bestAgainst(theirs, mine)
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

    -- Never in place of a forced action.  BattleState.lockedAction is what
    -- the vanilla chain would have answered with here, and it covers a Hyper
    -- Beam recharge, a Thrash/Petal Dance/Rage lock, a charging two-turn
    -- move, the boss's own Wrap, Bide -- and being held in place by the
    -- PLAYER's Wrap or Fire Spin, which is the one that matters.  Returning
    -- a switch ahead of it let a boss walk out of a trap the player spent a
    -- turn setting, and skip the Hyper Beam recharge this file's own scoring
    -- layer charges it three points for.  Sixteen roster slots carry Hyper
    -- Beam and six carry Thrash or Petal Dance, so it was not theoretical.
    local known, locked = pcall(battle.lockedAction, battle, battle.enemy)
    if known and locked then return nil end

    local rec = recordFor(battle)
    if rec.count >= cap then return nil end
    -- One action on the field before it may rotate again.  Counting the
    -- enemy's own decisions rather than battle.turnCount is deliberate: only
    -- resolveTurn advances turnCount, so a turn the player spent on an item,
    -- a ball, a failed run or a switch of their own never moved it -- and
    -- resolveTurn reads the enemy's action BEFORE it increments, which is
    -- what let the old `turnCount <= since` compare pass on the very next
    -- turn and rotate a Pokemon straight back out of its own send-out.
    if rec.seen < 2 then return nil end

    local current = matchup(battle, battle.enemy and battle.enemy.curTypes,
                            battle.enemy and battle.enemy.curMoves)
    -- unknown types mean no informed call is available; leave the turn alone
    if current == nil or current >= 0 then return nil end
    if canFinish(battle) then return nil end

    local pick, pickScore
    for i, mon in ipairs(battle.enemyParty or {}) do
      if i ~= battle.enemyIndex and (mon.hp or 0) > 0 then
        local score = matchup(battle, typesFor(battle, mon), mon.moves)
        if score and (not pickScore or score > pickScore) then
          pick, pickScore = i, score
        end
      end
    end
    if not pick or pickScore < current + SWITCH_MIN_GAIN then return nil end

    rec.count = rec.count + 1
    rec.index = pick
    rec.pending = pick      -- ... unless the engine never runs it; see recordFor
    rec.seen = 0            -- the one coming in owes its turn on the field
    -- mark the outgoing battler only once the retarget is really in place;
    -- both the turn-order answer and the retarget key off this, so they can
    -- never be half-applied
    if battle.enemy and installRetarget(battle) then
      rotating[battle.enemy] = true
      withdrawn[battle.enemy] = true
    end
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

    -- The rotation goes first (see `installRetarget`).  resolveTurn asks this
    -- straight after the action above is chosen, so the outgoing battler is
    -- still the one on the field and `withdrawn` is the only thing that has
    -- to be true.  Every other turn -- and every wild, link or ordinary
    -- trainer battle, which never mark it -- falls through to the vanilla
    -- speed compare with the arguments untouched.
    mod.hooks:wrap("battle.turn_order", function(next, _player, _pMove, enemy)
      if enemy and rotating[enemy] then
        rotating[enemy] = nil    -- one turn's question, answered
        return false             -- "the player moves first" -- not this turn
      end
      return next()
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
