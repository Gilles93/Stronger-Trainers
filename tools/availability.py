"""When the player can first have a move, measured in badges.

Full move legality was the right call for the late game and the wrong one for
the early gyms. Brock shipped 1.7.0 carrying Thunderbolt, Ice Beam, Fire
Blast, Rock Slide and Earthquake: every one of those is a Celadon purchase or
later, and at badge one the player has two Pokemon and no TMs at all. Every
starter had a hard counter waiting and no way to answer it.

So the early gyms get a second gate on top of legality: a leader may not carry
a TM move the player could not also have by the time they reach that gym.
Field pickups below are read off the ROM's own item placements (the map each
TM sits on, mapped to the gym you have beaten by then). Shop and prize TMs
have no map object, so they are listed by where they are sold.

From Koga onward there is no gate. By Celadon the player has the department
store, the Game Corner, six Pokemon and evolved forms, which is exactly the
point at which a fully optimised gym team is a fair fight rather than a wall.
"""

from __future__ import annotations

# What each gym specialises in. A leader's own type -- and plain Normal -- is
# never "coverage": a Rock gym leading with Rock Slide is the fight working as
# intended, and the player answers it with a type advantage the same way they
# always did. Only a move that reaches OUTSIDE the gym's type counts against
# the budget, because that is the one the player has no answer to.
GYM_TYPE = {
    "OPP_BROCK": "ROCK", "OPP_MISTY": "WATER", "OPP_LT_SURGE": "ELECTRIC",
    "OPP_ERIKA": "GRASS", "OPP_KOGA": "POISON", "OPP_SABRINA": "PSYCHIC_TYPE",
    "OPP_BLAINE": "FIRE", "OPP_GIOVANNI": "GROUND",
}

# Gym order, 1-indexed. The number is "badges you hold when you challenge".
GYMS = ["OPP_BROCK", "OPP_MISTY", "OPP_LT_SURGE", "OPP_ERIKA",
        "OPP_KOGA", "OPP_SABRINA", "OPP_BLAINE", "OPP_GIOVANNI"]

# The first gym by which a TM move is obtainable. Anything absent is either a
# level-up move (gated by level instead) or a TM from beyond the gated range,
# which the gate treats as unavailable.
#
# Field pickups, from the ROM's item placements:
#   Mt Moon, Routes 3/4 ......... before Misty
#   Routes 24/25, S.S. Anne ..... before Surge
#   Rocket Hideout .............. before Erika
#   Routes 12/15 ................ before Koga
#   Silph Co .................... before Sabrina
#   Pokemon Mansion ............. before Blaine
#   Victory Road ................ after the eighth badge
#
# Shops and prizes:
#   Celadon dept store + Game Corner ... reachable after Surge, so before Erika
#   Fire Blast ......................... Blaine's own gift, after his gym
TM_FROM_GYM = {
    # Mt Moon and the early routes
    "MEGA_PUNCH": 2, "WATER_GUN": 2, "WHIRLWIND": 2,
    # Nugget Bridge, Route 25, the S.S. Anne
    "THUNDER_WAVE": 3, "SEISMIC_TOSS": 3, "BODY_SLAM": 3, "REST": 3,
    "TELEPORT": 3, "DIG": 3,
    # Celadon: the department store and the Game Corner
    "ICE_BEAM": 4, "THUNDERBOLT": 4, "BUBBLEBEAM": 4, "PSYCHIC_M": 4,
    "ROCK_SLIDE": 4, "TOXIC": 4, "DOUBLE_TEAM": 4, "REFLECT": 4,
    "HYPER_BEAM": 4, "SUBSTITUTE": 4, "DRAGON_RAGE": 4, "COUNTER": 4,
    "DOUBLE_EDGE": 4, "HORN_DRILL": 4, "RAZOR_WIND": 4, "MIMIC": 4,
    # later, and therefore never available to a gated gym
    "PAY_DAY": 5, "RAGE": 5,
    "EARTHQUAKE": 6, "SWORDS_DANCE": 6, "TAKE_DOWN": 6,
    "BLIZZARD": 7, "SOLARBEAM": 7,
    "FIRE_BLAST": 8,
    "SUBMISSION": 9, "MEGA_KICK": 9, "SKY_ATTACK": 9, "EXPLOSION": 9,
}

# How many off-type damaging moves a gym team may carry in total. None means
# no limit. The ramp tracks the player's own toolkit: nothing before Celadon,
# because there is nothing to buy.
COVERAGE_BUDGET = {
    "OPP_BROCK": 0,
    "OPP_MISTY": 0,
    "OPP_LT_SURGE": 1,
    "OPP_ERIKA": 2,
}

# Gyms past this point are not gated at all.
GATED_THROUGH = 4

# The first two gyms get three further limits, because at one and two badges
# the player has a starter, maybe two catches, no TMs and no items worth the
# name. Any of these three alone is enough to turn the fight into a wall.
#
#   STRICT_STAB  no damaging move outside the gym's type (or Normal) at all,
#                the Pokemon's OWN type included. This is the one that was
#                missing: Starmie is Water/Psychic, so its Psychic counted as
#                its own STAB and slipped the coverage budget -- while being
#                2x into the Grass/Poison starter a player brings to counter
#                a Water gym, whose Water moves that starter resists. Kabuto's
#                Water Gun at Brock is the same shape.
#   MAX_POWER    nothing above Body Slam. Earthquake and Surf are ace moves
#                and they were sitting on the first two gyms in the game.
#   MAX_REPEATS  a move may appear on at most this many of the six. Rock Slide
#                was on five of Brock's, Bubblebeam on five of Misty's and
#                Thunderbolt on all six of Surge's, which reads as one Pokemon
#                fought six times. This one also applies to Surge and Erika,
#                who are otherwise ungated.
STRICT_STAB = {"OPP_BROCK", "OPP_MISTY"}
MAX_POWER = {"OPP_BROCK": 85, "OPP_MISTY": 85}
# Counts status moves too: Sleep Powder on four of Erika's six is worse in
# play than any attack she has.
MAX_REPEATS = {"OPP_BROCK": 3, "OPP_MISTY": 3, "OPP_LT_SURGE": 3,
               "OPP_ERIKA": 3}


def strict_stab(cls: str) -> bool:
    return cls.partition("#")[0] in STRICT_STAB


def max_power(cls: str):
    return MAX_POWER.get(cls.partition("#")[0])


def max_repeats(cls: str):
    return MAX_REPEATS.get(cls.partition("#")[0])


def gym_index(cls: str) -> int | None:
    """1-indexed position in the badge order, or None for a non-gym boss."""
    base = cls.partition("#")[0]
    return GYMS.index(base) + 1 if base in GYMS else None


def is_gated(cls: str) -> bool:
    idx = gym_index(cls)
    return idx is not None and idx <= GATED_THROUGH


def is_coverage(move_type: str, gym_cls: str, own_types) -> bool:
    """Does this move reach outside the gym's type?

    Normally a Pokemon's own type is not coverage -- Koga's Golbat using a
    Flying move is just Golbat. At the first two gyms that exemption is
    dropped, because "its own STAB" is no comfort to a player being hit for
    double damage by the very Pokemon they brought the right counter to.
    """
    if move_type in (None, "NORMAL"):
        return False
    if move_type == GYM_TYPE.get(gym_cls.partition("#")[0]):
        return False
    if strict_stab(gym_cls):
        return True
    return move_type not in own_types


def available(move: str, cls: str) -> bool:
    """Could the player hold this move by the time they fight `cls`?

    Only ever asked about coverage moves. Vanilla itself hands leaders TM
    moves the player cannot buy yet -- Misty's Starmie has Bubblebeam at the
    second badge -- and that has never been the unfair part. Being hit by a
    super-effective move you have no answer to is.
    """
    idx = gym_index(cls)
    if idx is None or idx > GATED_THROUGH:
        return True
    needed = TM_FROM_GYM.get(move)
    return needed is None or needed <= idx


def budget(cls: str):
    return COVERAGE_BUDGET.get(cls.partition("#")[0])
