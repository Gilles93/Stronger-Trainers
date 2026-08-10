"""The static overworld encounters, authored.

Fifteen battles the player walks into rather than earns from a trainer: the
ghost on Pokemon Tower 6F, the two Snorlax asleep in the road, the eight
disguised item balls in the Power Plant, the three legendary birds, and
Mewtwo.

Why they need a table of their own rather than rows in rosters.py:

  * They are not trainer parties. Nothing reaches them through
    `trainer.party` -- BattleState.newWild builds one Pokemon straight from
    the species' level-up set and offers no hook anywhere along the way, so
    the runtime side shadows newWild instead (static_battles.lua).
  * They are identical in every version. Party indices are what forced
    boss_teams.lua to be keyed { red, blue, yellow }; the static scripts are
    shared by all three, so one table serves everywhere and the builder
    validates it against each version's own species and move tables.
  * The AI is different, and that changes what a good moveset is.

That last point is the rule this whole file is written around.

A WILD BATTLE HAS NO AI. TrainerAI.chooseMove short-circuits to
`usable[rng(1, #usable)]` when the battle carries no enemyAIMods, and this
mod attaches its scoring layer to trainer records -- so a static picks
UNIFORMLY AT RANDOM, every turn, forever. A slot that is not a threat is a
free turn for the player one time in four. That inverts the boss rule:
smart_ai can carry a situational move because it only reaches for it when it
is right, and these cannot. Hence: at most one non-damaging move per set, no
recovery paired with a defensive boost (an Amnesia/Rest Snorlax picking at
random is an unkillable stall nobody can wait out), and no charge or
two-turn moves, which hand the player the turn outright.

LEVELS. Three different rules, because these are three different kinds of
encounter, and all of them start from tools/curve.py's own player model --
the "you" column of `python tools/curve.py`, plus the boss ace at each
checkpoint:

    checkpoint          you    local boss ace
    Pokemon Tower       40-41  45  (tower rival)
    Route 12            42     50  (Koga)
    Route 16            46     53  (Silph rival)
    Power Plant         46-48  56  (Sabrina)
    Seafoam             53     60  (Blaine)
    Victory Road        56     62  (Route 22 rematch)
    Cerulean Cave       post-champion, whose ace is 71

  * Power Plant fodder rides the ordinary-trainer bump, the same +15% every
    filler party gets: 40 -> 46 and 43 -> 50. They are traps, not bosses.
  * The landmarks -- the ghost and both Snorlax -- get mini-boss treatment at
    roughly the player's level plus six, which lands them beside the boss ace
    of their own checkpoint. A static is ONE Pokemon against a full party, so
    sitting at the player's level makes it a speed bump.
  * The legendaries sit at a flat 70. This is a deliberate author's choice
    rather than a curve reading: vanilla put all three birds at a flat 50 so
    they read as one tier of thing wherever you met them, and a flat 70 is
    that same idea moved to a tier that means something. It makes Zapdos in
    particular a wall rather than a fight -- reachable around level 48, and
    22 levels above the player -- which is the point of a legendary. Mewtwo
    is 85: it is the postgame superboss with nothing after it, and 81 is the
    level Amnesia comes online, which is the whole of what Mewtwo is.

Levels do not make these harder to CATCH, only harder to survive: Gen 1's
catch roll is driven by the max-HP/current-HP ratio and never reads level.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Explosion is on build_boss_teams.BANNED_EFFECTS, and it is allowed here, on
# these two species only.
#
# The ban is not a statement about the move -- the listed reason is "scored
# down by smart_ai on purpose", which is a fact about an AI these battles
# never consult. A wild Voltorb rolls uniformly, so Explosion is simply the
# 1-in-4 the trap is built around, and it is what the vanilla level-up set
# already hands them at 40 and 43. It also cannot grief the player's catches
# across the whole room: a ball that explodes takes that Voltorb with it.
#
# Keyed by (map, species) rather than by move so the exemption cannot leak
# onto anything else that happens to learn Selfdestruct.
# ---------------------------------------------------------------------------
EXPLODE_ALLOWED = {
    ("POWER_PLANT", "VOLTORB"),
    ("POWER_PLANT", "ELECTRODE"),
}

# ---------------------------------------------------------------------------
# The table. A row is
#
#     (species, vanilla_level, level, moves, why)
#
# `vanilla_level` is not decoration -- it is the match key. The runtime
# recognises a static by the triple (map, species, level the script asked
# for), because keying on species and level alone collides the moment a level
# moves: Electrode at 50 would otherwise catch the wild Electrode in Cerulean
# Cave, and Marowak already appears wild at 40, 43, 52 and 55.
# ---------------------------------------------------------------------------

STATICS = {
    # -- the ghost (scripts/PokemonTower6F.asm) -------------------------------
    # The only one that cannot be caught: story3.lua sets battle.noCatch, so
    # there is no reward to inflate and it can be tuned purely as a fight.
    # 110 base Defence plus Toxic makes it a wall on a timer, which suits a
    # restless soul better than raw power would.
    #
    # Bone Club is its signature and is not here on purpose: 65 power at 85%
    # beside Earthquake's 100 at 100%, same type and same category, is exactly
    # the strictly-dominated slot the builder rejects. Ice Beam off 50 Special
    # is weak in the abstract and the right answer anyway -- Ground touches
    # neither the Flying types that are immune to it nor the Grass types that
    # resist, and Ice is doubly effective into both.
    "POKEMON_TOWER_6F": [
        ("MAROWAK", 30, 46,
         ["EARTHQUAKE", "BODY_SLAM", "ICE_BEAM", "TOXIC"],
         "uncatchable story wall; grinds you down rather than bursting you"),
    ],

    # -- the two sleepers (scripts/Route12.asm, Route16.asm) ------------------
    # Same species twice, and the escalation is that the second one has grown
    # up: Double-Edge is a level 48 move, so the Route 16 Snorlax swings it
    # and the Route 12 one cannot. Amnesia moves special offence and defence
    # together under modern_kanto's split, which is the classic Gen 1 wall.
    #
    # No Rest, deliberately, on either -- see the header.
    "ROUTE_12": [
        ("SNORLAX", 30, 48,
         ["BODY_SLAM", "EARTHQUAKE", "ROCK_SLIDE", "AMNESIA"],
         "the brawler: paralysis, and Rock Slide for what shrugs off Ground"),
    ],
    "ROUTE_16": [
        ("SNORLAX", 30, 52,
         ["DOUBLE_EDGE", "EARTHQUAKE", "ROCK_SLIDE", "AMNESIA"],
         "the same Pokemon four levels past Double-Edge, hitting accordingly"),
    ],

    # -- the Power Plant (scripts/PowerPlant.asm) -----------------------------
    # Vanilla's level 40 Voltorb has NO Electric attack at all: the learnset
    # hands it Sonicboom, Selfdestruct, Light Screen and Swift. Thunderbolt
    # alone is most of what makes the trap sting. Swift is the answer to the
    # Ground types that are immune to Electric, and Thunder Wave from a
    # 140-speed Electrode moving first is the room's real teeth.
    "POWER_PLANT": [
        ("VOLTORB", 40, 46,
         ["THUNDERBOLT", "SWIFT", "THUNDER_WAVE", "SELFDESTRUCT"],
         "six of these; Selfdestruct stings rather than deletes off 30 Attack"),
        ("ELECTRODE", 43, 50,
         ["THUNDERBOLT", "SWIFT", "THUNDER_WAVE", "EXPLOSION"],
         "two of these; 170 power off the fastest thing in the game"),
        ("ZAPDOS", 50, 70,
         ["THUNDERBOLT", "DRILL_PECK", "HYPER_BEAM", "AGILITY"],
         "Hyper Beam is its answer to Ground; Agility takes 100 speed to 200"),
    ],

    # -- the birds ------------------------------------------------------------
    # Articuno's movepool is genuinely bare: Peck is 35, Sky Attack charges,
    # Fly takes two turns, so Ice and Hyper Beam is the whole of it. Blizzard
    # does not dominate Ice Beam -- 120 at 90% against 95 at 100%, with twice
    # the PP -- which is why both are here. Reflect turns 100 base Defence
    # into an actual wall of ice.
    "SEAFOAM_ISLANDS_B4F": [
        ("ARTICUNO", 50, 70,
         ["BLIZZARD", "ICE_BEAM", "HYPER_BEAM", "REFLECT"],
         "10% freeze is permanent in Gen 1 without a Fire move or an Ice Heal"),
    ],
    # Fire Blast burns 30% of the time and a burn halves Attack for the rest
    # of the fight. Double-Edge is the physical answer to everything Fire
    # cannot touch, which under the modern chart is Water, Rock, Fire and
    # Dragon. Fire Spin and Sky Attack are both in its pool and both banned.
    "VICTORY_ROAD_2F": [
        ("MOLTRES", 50, 70,
         ["FIRE_BLAST", "HYPER_BEAM", "DOUBLE_EDGE", "AGILITY"],
         "the last thing between the player and the Elite Four"),
    ],

    # -- Mewtwo ---------------------------------------------------------------
    # Psychic alone is a clean two-hit kill on a level 68 team member. After
    # one Amnesia it is a one-hit kill, and that escalation is the entire
    # fight. Recover makes it a war rather than a race.
    #
    # This is the one set that spends two of four slots on non-damaging moves,
    # against the rule in the header. It is allowed to: with the ghost fix on,
    # Ghost is doubly effective into Psychic, so there is real counterplay,
    # and sleep locks out Recover for anyone who wants to catch it.
    "CERULEAN_CAVE_B1F": [
        ("MEWTWO", 70, 85,
         ["PSYCHIC_M", "AMNESIA", "RECOVER", "BLIZZARD"],
         "Blizzard is for the other Psychics, which are all Psychic resists"),
    ],
}


def rows():
    """(map, species, vanilla_level, level, moves, why), in map order."""
    for map_id in sorted(STATICS):
        for species, vanilla, level, moves, why in STATICS[map_id]:
            yield map_id, species, vanilla, level, list(moves), why


# How many of each row the map actually places. Purely informational -- the
# runtime matches on the triple and so covers every copy -- but a count that
# does not add up to fifteen means a row was lost.
COPIES = {
    ("POWER_PLANT", "VOLTORB"): 6,
    ("POWER_PLANT", "ELECTRODE"): 2,
}


def total_encounters() -> int:
    return sum(COPIES.get((m, sp), 1) for m, sp, _v, _l, _mv, _w in rows())
