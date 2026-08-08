"""Validate the authored rosters and emit boss_teams.lua.

The validation is the point. A roster is only shippable if, for every version
the mod claims to support:

  * every species and move id exists in that version's tables;
  * every move is one that slot could legitimately know at its level;
  * every party key the table defines is a key that version's trainer data
    actually has -- the check that would have caught the Yellow bug, where
    OPP_RIVAL1#2 and #3 mean "Route 22" and "Cerulean" in Yellow but "the lab
    battle, other starter" in Red.

Nothing is written unless all three pass for all three versions.

    python tools/build_boss_teams.py            # validate and write
    python tools/build_boss_teams.py --check    # validate only
    python tools/build_boss_teams.py --diff     # what changed vs 1.6.0
"""

from __future__ import annotations

import argparse
import os
import sys

import curve
import gamedata
import progression
import rosters

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "boss_teams.lua")

# Red and Blue ship byte-identical trainer tables apart from OPP_CHIEF, which
# Blue leaves empty, so Blue reuses Red's rosters wholesale.
VERSIONS = ("red", "blue", "yellow")
TRAINER_DATA_TWIN = {"blue": "red"}


def _levels(ace: int, size: int):
    return curve.team_from_ace(ace, size) if size == curve.MAX_PARTY else \
        sorted(max(1, min(curve.MAX_LEVEL, ace + d))
               for d in curve.SPREAD[curve.MAX_PARTY - size:])


def build_version(version: str, boss_ace: dict):
    """Every roster this version should carry, keyed "CLASS#party"."""
    out = {}

    # --- gyms, Giovanni, Elite Four: same team everywhere, levels per version
    for table in (rosters.GYM_LEADERS, rosters.GIOVANNI, rosters.ELITE_FOUR):
        for key, team in table.items():
            # a single-fight boss is a milestone by class (OPP_BROCK); one
            # who is fought repeatedly is a milestone per fight
            # (OPP_GIOVANNI#1..#3)
            cls = key.split("#")[0]
            ace = boss_ace[cls] if cls in boss_ace else boss_ace[key]
            levels = _levels(ace, len(team))
            out[key] = [(sp, lv, mv) for (sp, mv), lv in zip(team, levels)]

    # --- rivals
    for label, _red, _yellow in progression.RIVAL_BATTLES:
        keys = progression.rival_keys(version, label)
        ace = boss_ace[label]
        for branch, (cls, idx) in enumerate(keys, start=1):
            if version == "yellow":
                if label in rosters.YELLOW_RIVAL_NEUTRAL:
                    species = rosters.YELLOW_RIVAL_NEUTRAL[label]
                else:
                    species = rosters.YELLOW_RIVAL_BRANCHED[label][branch]
                moves = rosters.CHAMPION_YELLOW_MOVES if label == "champion" else {}
                team = [(sp, moves.get(sp)) for sp in species]
            elif label == "champion":
                team = list(rosters.CHAMPION_RB[branch])
            else:
                team = [(sp, None) for sp in rosters.RB_RIVAL_TEAMS[label][branch]]
            levels = _levels(ace, len(team))
            out[f"{cls}#{idx}"] = [
                (sp, lv, mv) for (sp, mv), lv in zip(team, levels)]

    # --- the Celadon Chief: an unused class in Red and absent from the other
    # two, kept only so a mod that places him gets a real team.
    if version == "red":
        out["OPP_CHIEF#1"] = [
            (sp, lv, mv) for (sp, mv), lv in zip(rosters.CHIEF, _levels(48, 6))]
    return out


def validate(version: str, table):
    """Every failure, not just the first -- a fix pass wants the whole list."""
    g = gamedata.load(version)
    data_version = TRAINER_DATA_TWIN.get(version, version)
    gd = gamedata.load(data_version)
    problems = []

    for key, slots in sorted(table.items()):
        cls, _, idx = key.partition("#")
        idx = int(idx)

        parties = gd.trainers.get(cls)
        if parties is None:
            problems.append(f"{version} {key}: no trainer class {cls}")
        elif cls == "OPP_CHIEF" and not parties:
            pass                      # unused class, deliberately kept
        elif idx > len(parties):
            problems.append(
                f"{version} {key}: this version has only {len(parties)} "
                f"{cls} parties -- key would land on the wrong battle")

        if len(slots) > 6:
            problems.append(f"{version} {key}: {len(slots)} slots, max 6")

        for pos, (species, level, moves) in enumerate(slots, start=1):
            if species not in g.species:
                problems.append(f"{version} {key} slot {pos}: no species {species}")
                continue
            if not 1 <= level <= 100:
                problems.append(f"{version} {key} slot {pos}: level {level}")
            for mv in (moves or []):
                if mv not in g.moves:
                    problems.append(
                        f"{version} {key} slot {pos} {species}: no move {mv}")
                elif mv not in g.legal_moves(species, level):
                    problems.append(
                        f"{version} {key} slot {pos}: {species} L{level} "
                        f"cannot learn {mv}")
    return problems


def lua_literal(tables):
    lines = [
        "-- Generated by tools/build_boss_teams.py -- do not hand-edit.",
        "--",
        "-- Boss rosters per game version, keyed \"CLASS#party\". A slot is",
        "-- { species, level, moves } and moves may be nil, meaning the",
        "-- engine's own level-up set for that species at that level.",
        "--",
        "-- Keyed by version because party indices are NOT the same across",
        "-- versions: Yellow gives OPP_RIVAL1 three parties (the lab, Route 22",
        "-- and Cerulean) where Red gives nine (three battles x three starter",
        "-- counter-picks). A single shared table therefore put a level 6",
        "-- starter into three different Yellow fights.",
        "return {",
    ]
    for version in VERSIONS:
        table = tables[version]
        lines.append(f"  {version} = {{")
        for key in sorted(table):
            lines.append(f'    ["{key}"] = {{')
            for species, level, moves in table[key]:
                if moves:
                    move_list = ", ".join(f'"{m}"' for m in moves)
                    lines.append(f'      {{ "{species}", {level}, '
                                 f'{{ {move_list} }} }},')
                else:
                    lines.append(f'      {{ "{species}", {level} }},')
            lines.append("    },")
        lines.append("  },")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--diff", action="store_true", help="compare against 1.6.0")
    args = ap.parse_args()

    tables, problems = {}, []
    for version in VERSIONS:
        data_version = TRAINER_DATA_TWIN.get(version, version)
        _rows, boss_ace = curve.compute(data_version, curve.Settings())
        tables[version] = build_version(version, boss_ace)
        problems.extend(validate(version, tables[version]))

    if problems:
        print(f"FAILED: {len(problems)} problem(s)\n")
        for p in problems:
            print(" ", p)
        return 1

    counts = ", ".join(f"{v} {len(tables[v])}" for v in VERSIONS)
    print(f"all rosters legal for every version ({counts} rosters)")

    if args.diff:
        import luadata
        old = luadata.load(os.path.join(REPO, "boss_teams_1.6.0.lua"))
        for key in sorted(set(old) | set(tables["red"])):
            o = old.get(key)
            n = tables["red"].get(key)
            if o is None:
                print(f"  + red {key}")
            elif n is None:
                print(f"  - red {key}")
            else:
                oa, na = max(s[1] for s in o), max(s[1] for s in n)
                if oa != na:
                    print(f"  ~ {key}: ace {oa} -> {na}")

    if not args.check:
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(lua_literal(tables))
        print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
