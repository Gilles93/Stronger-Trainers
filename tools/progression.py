"""The order a playthrough happens in, and which boss each key belongs to.

Two things live here that no extracted table records:

  * the route order -- which trainers a player has beaten before each boss.
    maps.lua knows where trainers stand, not when you reach them.
  * the party-index mapping per boss battle. Rival party indices are chosen
    by script at runtime, not stamped on the map object, and Yellow remaps
    them entirely (src/script/Commands.lua YELLOW_RIVAL_PARTIES). Getting
    this wrong is the exact bug this release fixes, so the mapping is
    written out per version rather than inferred.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Rival battles, in story order. Each entry names the roster key the engine
# will actually ask for, per version.
#
# Red/Blue: base + starter counterpick (CHARMANDER +0, SQUIRTLE +1,
# BULBASAUR +2), so each battle owns three consecutive keys.
# Yellow: keyed off save.rivalStarter (1 JOLTEON / 2 FLAREON / 3 VAPOREON);
# the early battles are fixed single parties because Eevee has not branched
# yet. Both mappings are verified against Commands.rival_battle.
# ---------------------------------------------------------------------------

RIVAL_BATTLES = [
    # (label,             red keys,                     yellow keys)
    ("lab",              [("OPP_RIVAL1", i) for i in (1, 2, 3)],
                         [("OPP_RIVAL1", 1)]),
    ("route22_first",    [("OPP_RIVAL1", i) for i in (4, 5, 6)],
                         [("OPP_RIVAL1", 2)]),
    ("cerulean",         [("OPP_RIVAL1", i) for i in (7, 8, 9)],
                         [("OPP_RIVAL1", 3)]),
    ("ss_anne",          [("OPP_RIVAL2", i) for i in (1, 2, 3)],
                         [("OPP_RIVAL2", 1)]),
    ("tower",            [("OPP_RIVAL2", i) for i in (4, 5, 6)],
                         [("OPP_RIVAL2", i) for i in (2, 3, 4)]),
    ("silph",            [("OPP_RIVAL2", i) for i in (7, 8, 9)],
                         [("OPP_RIVAL2", i) for i in (5, 6, 7)]),
    ("route22_second",   [("OPP_RIVAL2", i) for i in (10, 11, 12)],
                         [("OPP_RIVAL2", i) for i in (8, 9, 10)]),
    ("champion",         [("OPP_RIVAL3", i) for i in (1, 2, 3)],
                         [("OPP_RIVAL3", i) for i in (1, 2, 3)]),
]


def rival_keys(version: str, label: str):
    for name, red, yellow in RIVAL_BATTLES:
        if name == label:
            return yellow if version == "yellow" else red
    raise KeyError(label)


# ---------------------------------------------------------------------------
# The timeline. ("maps", [...]) contributes every trainer standing on those
# maps; ("boss", label) is a milestone -- the player's level is sampled just
# before it, and the boss's own payout lands just after.
#
# Gym maps appear in the segment before their leader: their trainers are
# beatable on the way in. The leader object itself is filtered out of map
# payouts by BOSS_CLASSES below, so it is only ever counted once, as a boss.
# ---------------------------------------------------------------------------

TIMELINE = [
    ("boss", "lab"),
    ("boss", "route22_first"),
    ("maps", ["VIRIDIAN_FOREST", "PEWTER_GYM"]),
    ("boss", "OPP_BROCK"),
    ("maps", ["ROUTE_3", "MT_MOON_1F", "MT_MOON_B1F", "MT_MOON_B2F",
              "ROUTE_4", "CERULEAN_CITY"]),
    ("boss", "cerulean"),
    ("maps", ["CERULEAN_GYM"]),
    ("boss", "OPP_MISTY"),
    ("maps", ["ROUTE_24", "ROUTE_25", "ROUTE_5", "ROUTE_6",
              "SS_ANNE_1F_ROOMS", "SS_ANNE_2F_ROOMS", "SS_ANNE_B1F_ROOMS",
              "SS_ANNE_BOW"]),
    ("boss", "ss_anne"),
    ("maps", ["VERMILION_GYM"]),
    ("boss", "OPP_LT_SURGE"),
    ("maps", ["ROUTE_11", "ROUTE_9", "ROUTE_10", "ROCK_TUNNEL_1F",
              "ROCK_TUNNEL_B1F", "ROUTE_8", "GAME_CORNER", "CELADON_GYM"]),
    ("boss", "OPP_ERIKA"),
    ("maps", ["ROCKET_HIDEOUT_B1F", "ROCKET_HIDEOUT_B2F",
              "ROCKET_HIDEOUT_B3F", "ROCKET_HIDEOUT_B4F"]),
    ("boss", "OPP_GIOVANNI#1"),
    ("maps", ["POKEMON_TOWER_3F", "POKEMON_TOWER_4F", "POKEMON_TOWER_5F",
              "POKEMON_TOWER_6F", "POKEMON_TOWER_7F"]),
    ("boss", "tower"),
    ("maps", ["ROUTE_12", "ROUTE_13", "ROUTE_14", "ROUTE_15", "FUCHSIA_GYM"]),
    ("boss", "OPP_KOGA"),
    ("maps", ["ROUTE_16", "ROUTE_17", "ROUTE_18", "FIGHTING_DOJO",
              "SILPH_CO_2F", "SILPH_CO_3F", "SILPH_CO_4F", "SILPH_CO_5F",
              "SILPH_CO_6F"]),
    ("boss", "silph"),
    ("maps", ["SILPH_CO_7F", "SILPH_CO_8F", "SILPH_CO_9F", "SILPH_CO_10F",
              "SILPH_CO_11F"]),
    ("boss", "OPP_GIOVANNI#2"),
    ("maps", ["SAFFRON_GYM"]),
    ("boss", "OPP_SABRINA"),
    ("maps", ["ROUTE_19", "ROUTE_20", "ROUTE_21", "POKEMON_MANSION_1F",
              "POKEMON_MANSION_2F", "POKEMON_MANSION_3F",
              "POKEMON_MANSION_B1F", "CINNABAR_GYM"]),
    ("boss", "OPP_BLAINE"),
    ("maps", ["VIRIDIAN_GYM"]),
    ("boss", "OPP_GIOVANNI#3"),
    ("boss", "route22_second"),
    ("maps", ["VICTORY_ROAD_1F", "VICTORY_ROAD_2F", "VICTORY_ROAD_3F"]),
    ("boss", "OPP_LORELEI"),
    ("boss", "OPP_BRUNO"),
    ("boss", "OPP_AGATHA"),
    ("boss", "OPP_LANCE"),
    ("boss", "champion"),
]

# Classes whose map objects are milestones rather than route filler, so a
# map payout never double-counts a boss.
BOSS_CLASSES = {
    "OPP_BROCK", "OPP_MISTY", "OPP_LT_SURGE", "OPP_ERIKA", "OPP_KOGA",
    "OPP_SABRINA", "OPP_BLAINE", "OPP_GIOVANNI", "OPP_LORELEI", "OPP_BRUNO",
    "OPP_AGATHA", "OPP_LANCE", "OPP_RIVAL1", "OPP_RIVAL2", "OPP_RIVAL3",
    "OPP_CHIEF",
}

# How far above the player each milestone's ace should sit. The complaint
# this release answers is that the late game stayed soft, so the margin
# ramps instead of sitting flat: an early leader is a check, the Elite Four
# is a wall.
MARGIN = {
    "lab": 0, "route22_first": 1,
    "OPP_BROCK": 2,
    "cerulean": 2,
    "OPP_MISTY": 3,
    "ss_anne": 3,
    "OPP_LT_SURGE": 3,
    "OPP_ERIKA": 4,
    "OPP_GIOVANNI#1": 4,
    "tower": 4,
    "OPP_KOGA": 5,
    "silph": 5,
    "OPP_GIOVANNI#2": 5,
    "OPP_SABRINA": 6,
    "OPP_BLAINE": 6,
    "OPP_GIOVANNI#3": 7,
    "route22_second": 7,
    # The gauntlet gets its own step up. The computed player level is flat
    # across all four rooms -- there is nothing to fight between them -- so a
    # flat margin gave three identical aces; these stagger so the gauntlet
    # still climbs, and the Champion keeps his gap above Lance.
    "OPP_LORELEI": 11, "OPP_BRUNO": 11, "OPP_AGATHA": 12, "OPP_LANCE": 13,
    "champion": 14,
}

# Per-version margin corrections.
#
# Yellow starts the player on a Pikachu, which a Rock gym walls outright, and
# the ROM itself compensates: vanilla Yellow's Brock is level 10/12 against
# Red's 12/14. That easing is deliberate game design, not an oversight, so it
# survives here -- everywhere else Yellow's vanilla curve is the *steeper*
# one and needs no help.
MARGIN_ADJUST = {
    "yellow": {"OPP_BROCK": -2},
}


def margin_for(version: str, key: str) -> int:
    return (MARGIN.get(key, 4)
            + MARGIN_ADJUST.get(version, {}).get(key, 0))


# Ordered boss milestones, for reporting.
MILESTONES = [key for kind, key in TIMELINE if kind == "boss"]
