"""Validate the authored static encounters and emit statics.lua.

Same contract as build_boss_teams.py: nothing is written unless every check
passes for every version the mod claims to support. The checks differ from
the boss ones in three places, and each difference is a fact about wild
battles rather than a loosened standard.

  * There is no TM gate and no coverage budget. Those exist because a gym
    leader is met at a point in the game where the player's own options are
    known; a legendary is optional, reachable in any order, and the vanilla
    game already hands its wild Pokemon whatever their learnset says.
  * Explosion is allowed, on the two Power Plant species only. The boss ban
    reads "scored down by smart_ai on purpose", which is a fact about an AI
    a wild battle never consults. statics.EXPLODE_ALLOWED is the exemption
    list and it is keyed by (map, species), not by move.
  * Two checks exist that the boss builder has no need for, both of them
    consequences of the uniform-random wild AI: half of every set must deal
    damage, and no move may be strictly dominated by another on the same
    Pokemon. smart_ai can be trusted not to pick the worse of two Ground
    moves. A d4 cannot.

The collision check is the one that would have shipped a bug. The runtime
recognises a static by (map, species, the level the script asked for), so a
species that also appears in that map's own wild table at that exact level
would turn every grass encounter into a legendary.

    python tools/build_statics.py            # validate and write
    python tools/build_statics.py --check    # validate only
"""

from __future__ import annotations

import argparse
import os
import sys

import gamedata
import statics
from build_boss_teams import BANNED_EFFECTS

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "statics.lua")

# Blue ships Red's maps and Red's species tables; only its trainer data
# differs, and no static reads trainer data.
VERSIONS = ("red", "blue", "yellow")
MAP_DATA_TWIN = {"blue": "red"}

# A wild battle rolls a d4 every turn. Half the set has to be able to hurt
# the player or the encounter spends its fight doing nothing.
MIN_DAMAGING = 0.5


def _dominates(a: dict, b: dict) -> bool:
    """True when a move is strictly worse than another on the same Pokemon.

    Same type and both damaging, at least as much power and at least as much
    accuracy, better in one of them. A Pokemon carrying both will only ever
    want the winner, and a random pick will reach for the loser a quarter of
    the time.

    A move that faints its own user never counts as the dominator. Explosion
    beats Swift on paper and is not a replacement for it.
    """
    if (a.get("effect") or "") == "EXPLODE_EFFECT":
        return False
    if a.get("type") != b.get("type"):
        return False
    pa, pb = a.get("power") or 0, b.get("power") or 0
    if pa <= 0 or pb <= 0:
        return False
    aa, ab = a.get("accuracy") or 100, b.get("accuracy") or 100
    return pa >= pb and aa >= ab and (pa > pb or aa > ab)


def validate(version: str) -> list:
    """Every failure, not just the first."""
    g = gamedata.load(version)
    maps = gamedata.load(MAP_DATA_TWIN.get(version, version))
    problems = []

    for map_id, species, vanilla, level, moves, _why in statics.rows():
        where = f"{version} {map_id}/{species}"

        if maps.maps and map_id not in maps.maps:
            problems.append(f"{where}: no map {map_id} in this version")

        if species not in g.species:
            problems.append(f"{where}: no species {species}")
            continue

        if not 1 <= level <= 100:
            problems.append(f"{where}: level {level}")
        if level < vanilla:
            problems.append(
                f"{where}: level {level} is below the vanilla {vanilla} -- "
                f"a static is never meant to get easier")

        # The match key must be unique on its own map. See the module header.
        enc = maps.encounters.get(map_id) or {}
        for field in ("grass", "water"):
            group = enc.get(field) or {}
            for slot in (group.get("slots") or []):
                if slot.get("species") == species and slot.get("level") == vanilla:
                    problems.append(
                        f"{where}: the {field} table on this map already has "
                        f"{species} at {vanilla} -- the runtime cannot tell "
                        f"the static from a grass encounter")

        for mv in moves:
            if mv not in g.moves:
                problems.append(f"{where}: no move {mv}")
                continue
            effect = g.moves[mv].get("effect") or ""
            if effect in BANNED_EFFECTS:
                if not (effect == "EXPLODE_EFFECT"
                        and (map_id, species) in statics.EXPLODE_ALLOWED):
                    problems.append(
                        f"{where}: {mv} {BANNED_EFFECTS[effect]}")
            if mv not in g.legal_moves(species, level):
                problems.append(f"{where}: L{level} cannot learn {mv}")

        known = [g.moves[mv] for mv in moves if mv in g.moves]

        damaging = [m for m in known if (m.get("power") or 0) > 0]
        if len(damaging) < len(moves) * MIN_DAMAGING:
            problems.append(
                f"{where}: only {len(damaging)} of {len(moves)} slots deal "
                f"damage, and a wild Pokemon picks at random")

        for i, a in enumerate(known):
            for j, b in enumerate(known):
                if i != j and _dominates(a, b):
                    problems.append(
                        f"{where}: {b['id']} is strictly beaten by "
                        f"{a['id']} on the same Pokemon")

        # The boss rule, unchanged: a best attack that dwarfs the next one
        # gets repeated however the moves are chosen.
        powers = sorted((m.get("power") or 0 for m in damaging), reverse=True)
        if len(powers) >= 2 and powers[0] >= 2 * powers[1]:
            problems.append(
                f"{where}: best attack is {powers[0]} power against "
                f"{powers[1]} for the next -- it will repeat")

    return problems


def lua_literal() -> str:
    lines = [
        "-- Generated by tools/build_statics.py -- do not hand-edit.",
        "--",
        "-- The static overworld encounters, keyed by map. A row is",
        "-- { species, vanillaLevel, level, moves }.",
        "--",
        "-- vanillaLevel is the match key, not decoration: static_battles.lua",
        "-- recognises one of these by the triple (map, species, the level the",
        "-- script asked for). Matching on species and level alone would break",
        "-- the moment a level moves -- Electrode at 50 collides with the wild",
        "-- Electrode in Cerulean Cave, and Marowak appears wild at 40, 43, 52",
        "-- and 55.",
        "--",
        "-- Not keyed by game version, unlike boss_teams.lua. Party indices are",
        "-- what forced that; the static scripts are shared by Red, Blue and",
        "-- Yellow alike, and the builder validates this one table against all",
        "-- three.",
        "return {",
    ]
    for map_id in sorted(statics.STATICS):
        lines.append(f'  ["{map_id}"] = {{')
        for species, vanilla, level, moves, why in statics.STATICS[map_id]:
            move_list = ", ".join(f'"{m}"' for m in moves)
            lines.append(f"    -- {why}")
            lines.append(f'    {{ "{species}", {vanilla}, {level}, '
                         f"{{ {move_list} }} }},")
        lines.append("  },")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="validate only")
    args = ap.parse_args()

    problems = []
    for version in VERSIONS:
        problems.extend(validate(version))

    if problems:
        print(f"FAILED: {len(problems)} problem(s)\n")
        for p in problems:
            print(" ", p)
        return 1

    rows = list(statics.rows())
    print(f"all statics legal for every version "
          f"({len(rows)} rows, {statics.total_encounters()} encounters)")

    if not args.check:
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(lua_literal())
        print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
