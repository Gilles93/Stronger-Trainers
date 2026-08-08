"""What a slot could legitimately know, grouped so coverage is pickable.

Authoring aid. Rosters are written by hand, but "can a level 19 Onix carry
this?" is a data question, and guessing it from memory is how a roster ends
up with a move the species never learns. Prints the legal pool for a
species/level, damaging moves grouped by type, so a coverage gap is visible
at a glance.

    python tools/movepool.py ONIX:19 KABUTO:16 --version red
    python tools/movepool.py --team OPP_BROCK   # the authored team's pools
"""

from __future__ import annotations

import argparse
from collections import defaultdict

import gamedata

STATUS = 0


def pools(g, species: str, level: int):
    legal = g.legal_moves(species, level)
    by_type = defaultdict(list)
    status = []
    for mid in sorted(legal):
        mv = g.moves[mid]
        power = mv.get("power") or 0
        if power > 0:
            by_type[mv.get("type") or "?"].append((mid, power, mv.get("accuracy") or 100))
        else:
            status.append(mid)
    return by_type, status


def show(g, species: str, level: int, damaging_only=False):
    types = "/".join(g.types(species))
    print(f"-- {species} L{level}  [{types}]")
    by_type, status = pools(g, species, level)
    for t in sorted(by_type):
        entries = sorted(by_type[t], key=lambda e: -e[1])
        text = ", ".join(f"{m}({p})" for m, p, _ in entries)
        print(f"   {t:9} {text}")
    if status and not damaging_only:
        print(f"   {'STATUS':9} {', '.join(status)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slots", nargs="*", help="SPECIES:LEVEL")
    ap.add_argument("--version", default="red")
    ap.add_argument("--damaging", action="store_true")
    args = ap.parse_args()
    g = gamedata.load(args.version)
    for slot in args.slots:
        species, _, level = slot.partition(":")
        show(g, species.upper(), int(level or 50), args.damaging)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
