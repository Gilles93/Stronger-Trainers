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
import availability
import gamedata

# Effects the AI cannot play well, so authoring them wastes a slot.
#
# CHARGE_EFFECT is the one that bit twice. smart_ai.lua scores a move on the
# damage Damage.compute reports, and for a charge move that is the full hit
# with no account of the turn spent winding up -- so the AI rates Dig above
# Rock Slide and then spends every other turn underground. Sky Attack was
# pulled for this in 1.7.0 and Dig was missed; it is a rule now, not a
# judgement call.
#
# EXPLODE and the trapping moves are suppressed by smart_ai on purpose: they
# are the cheese the AI is built not to play.
BANNED_EFFECTS = {
    "CHARGE_EFFECT": "spends a turn charging, which the AI does not model",
    "EXPLODE_EFFECT": "scored down by smart_ai on purpose",
    "TRAPPING_EFFECT": "scored down by smart_ai on purpose",
    "OHKO_EFFECT": "a coin flip, not a fight",
}
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


def moves_for(spec, version: str):
    """A slot's move list, which may vary by version.

    Yellow's rosters sit at their own computed levels, so a level-up move can
    be legal in Red and out of reach in Yellow with the same species -- Brock's
    Onix is 19 in Red and 17 in Yellow, and Rock Throw arrives at 19. A slot
    may therefore give a dict keyed by version, with "*" as the default.
    """
    if isinstance(spec, dict):
        return list(spec.get(version) or spec["*"])
    return list(spec)


def build_version(version: str, boss_ace: dict, rival_label: dict = None):
    """Every roster this version should carry, keyed "CLASS#party".

    `rival_label`, when given, is filled in with key -> battle label so the
    validator can hold each rival slot to the TM gate for its own stage.
    """
    out = {}
    if rival_label is None:
        rival_label = {}

    # --- gyms, Giovanni, Elite Four: same team everywhere, levels per version
    for table in (rosters.GYM_LEADERS, rosters.GIOVANNI, rosters.ELITE_FOUR):
        for key, team in table.items():
            # a single-fight boss is a milestone by class (OPP_BROCK); one
            # who is fought repeatedly is a milestone per fight
            # (OPP_GIOVANNI#1..#3)
            cls = key.split("#")[0]
            ace = boss_ace[cls] if cls in boss_ace else boss_ace[key]
            levels = _levels(ace, len(team))
            out[key] = [(sp, lv, moves_for(mv, version))
                        for (sp, mv), lv in zip(team, levels)]

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
                # the champion table wins where it has an entry; every other
                # fight falls through to the per-battle rival sets
                team = [(sp, moves.get(sp) or rosters.rival_moves(sp, label))
                        for sp in species]
            elif label == "champion":
                team = list(rosters.CHAMPION_RB[branch])
            else:
                team = [(sp, rosters.rival_moves(sp, label))
                        for sp in rosters.RB_RIVAL_TEAMS[label][branch]]
            levels = _levels(ace, len(team))
            out[f"{cls}#{idx}"] = [
                (sp, lv, mv) for (sp, mv), lv in zip(team, levels)]
            rival_label[f"{cls}#{idx}"] = label

    # --- the Celadon Chief: an unused class in Red and absent from the other
    # two, kept only so a mod that places him gets a real team.
    if version == "red":
        out["OPP_CHIEF#1"] = [
            (sp, lv, mv) for (sp, mv), lv in zip(rosters.CHIEF, _levels(48, 6))]
    return out


def validate(version: str, table, rival_label: dict = None):
    """Every failure, not just the first -- a fix pass wants the whole list."""
    rival_label = rival_label or {}
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
                elif (g.moves[mv].get("effect") or "") in BANNED_EFFECTS:
                    problems.append(
                        f"{version} {key} slot {pos}: {species} {mv} "
                        f"{BANNED_EFFECTS[g.moves[mv]['effect']]}")
                elif availability.event_legal(species, mv):
                    # a documented exception (availability.EVENT_LEGAL): it
                    # skips the legality check and the TM gate together,
                    # because a move the species cannot learn at all was
                    # never going to be one the player could buy either
                    pass
                elif (availability.is_gated(key)
                      and availability.is_coverage(
                          (g.moves[mv].get("type")), key, g.types(species))
                      and (g.moves[mv].get("power") or 0) > 0
                      and mv not in g.levelup_moves(species, level)
                      and not availability.available(mv, key)):
                    problems.append(
                        f"{version} {key} slot {pos}: {species} {mv} needs a "
                        f"TM the player cannot own by that gym")
                elif mv not in g.legal_moves(species, level):
                    problems.append(
                        f"{version} {key} slot {pos}: {species} L{level} "
                        f"cannot learn {mv}")
                elif (key in rival_label
                      and mv not in g.levelup_moves(species, level)
                      and not availability.rival_allows(mv, rival_label[key])):
                    problems.append(
                        f"{version} {key} slot {pos}: {species} {mv} needs a "
                        f"TM the player cannot own by the {rival_label[key]} "
                        f"fight")

        # A slot whose best attack dwarfs its next one repeats that move
        # however the AI is scored, because using it really is correct. The
        # variety has to be built into the moveset, not asked of the AI.
        # Seismic Toss, Night Shade and Sonicboom are listed at 1 power but
        # deal the user's level or a flat amount, which lands somewhere around
        # a mid-power move for most of the game. Rate them there so they do not
        # read as dead weight next to a real attack.
        FIXED_AS = 60
        FIXED = {"SPECIAL_DAMAGE_EFFECT", "SUPER_FANG_EFFECT"}

        def rated(mv):
            rec = g.moves.get(mv) or {}
            if (rec.get("effect") or "") in FIXED:
                return FIXED_AS
            return rec.get("power") or 0

        # The rival is exempt before Celadon. A gym leader is met once, at a
        # point the author chose; the rival is met at level 6 and again at 62,
        # and before the department store a Pokemon genuinely has one good
        # move and three filler ones. Rattata's Hyper Fang really is twice
        # anything else it can know at 22, and the only way to satisfy the
        # rule would be to hand him TMs the player cannot buy yet. Gym teams
        # keep the strict version -- they are all authored past this point.
        VARIETY_FROM_LEVEL = 40

        for species, level, moves in slots:
            if key in rival_label and level < VARIETY_FROM_LEVEL:
                continue
            powers = sorted((rated(mv) for mv in (moves or [])), reverse=True)
            powers = [p for p in powers if p > 0]
            if len(powers) >= 2 and powers[0] >= 2 * powers[1]:
                problems.append(
                    f"{version} {key}: {species}'s best attack is {powers[0]} "
                    f"power against {powers[1]} for the next -- it will repeat")

        cap = availability.max_power(key)
        if cap is not None:
            for species, level, moves in slots:
                for mv in (moves or []):
                    power = (g.moves.get(mv) or {}).get("power") or 0
                    if power > cap:
                        problems.append(
                            f"{version} {key}: {species} {mv} is {power} power, "
                            f"over the {cap} limit for this gym")

        repeats = availability.max_repeats(key)
        if repeats is not None:
            seen = {}
            for _species, _level, moves in slots:
                for mv in (moves or []):
                    seen[mv] = seen.get(mv, 0) + 1
            for mv, n in sorted(seen.items()):
                if n > repeats:
                    problems.append(
                        f"{version} {key}: {mv} appears on {n} of the team, "
                        f"max {repeats}")

        # The early gyms also get a coverage budget. Legality alone let Brock
        # field five different super-effective answers at badge one.
        cap = availability.budget(key)
        if cap is not None:
            spent = []
            for species, _level, moves in slots:
                own = set(g.types(species))
                for mv in (moves or []):
                    rec = g.moves.get(mv) or {}
                    if (rec.get("power") or 0) <= 0:
                        continue
                    # Normal is not coverage, it is the filler every Pokemon
                    # has. Only a super-effective-capable off-type move counts.
                    if not availability.is_coverage(rec.get("type"), key, own):
                        continue
                    spent.append(f"{species}:{mv}")
            if len(spent) > cap:
                problems.append(
                    f"{version} {key}: {len(spent)} off-type coverage moves, "
                    f"budget {cap} ({', '.join(spent)})")

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
        labels = {}
        tables[version] = build_version(version, boss_ace, labels)
        problems.extend(validate(version, tables[version], labels))

    if problems:
        print(f"FAILED: {len(problems)} problem(s)\n")
        for p in problems:
            print(" ", p)
        return 1

    counts = ", ".join(f"{v} {len(tables[v])}" for v in VERSIONS)
    print(f"all rosters legal for every version ({counts} rosters)")

    if args.diff:
        import luadata
        old = luadata.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "boss_teams_1.6.0.lua"))
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
