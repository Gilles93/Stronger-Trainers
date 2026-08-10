"""Where the boss levels come from.

The old numbers were vanilla plus a few levels, chosen by feel. That is why
the late game went soft: the mod raises every ordinary trainer by 15%, pads
short parties out to three and evolves overdue pre-evolutions, so the player
banks far more experience than vanilla ever handed out -- and experience
compounds, because a bigger payout raises your level, which raises the
payout of the next fight. Trimming gains to 75% does not undo that.

So the levels are computed instead. Walk the real progression, pay out the
real trainers at the mod's own settings using the engine's own experience
formula, invert the growth curve, and put each boss a set margin above the
level the player will actually be. Boss payouts feed the same pool, which
makes this a fixed point: raising Koga raises what the player brings to
Sabrina. It is iterated to convergence rather than solved once.

    python tools/curve.py                # the shipped curve, both versions
    python tools/curve.py --vanilla      # sanity: what vanilla predicts
    python tools/curve.py --sensitivity  # how much the model assumptions move it
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

import gamedata
import luadata
import progression

MAX_PARTY = 6
MAX_LEVEL = 100

# Level offsets from the ace for an authored six-slot team. Matches the
# shape the hand-authored rosters already used (Brock 14/14/15/16/16/19).
SPREAD = [-5, -5, -4, -3, -3, 0]

# How many Pokemon the player is actually sharing experience between by the
# time they reach each milestone. Calibrated against what a full-clear
# vanilla playthrough is reported to reach (see `--vanilla`): a flat share
# fits the midgame but badly under-predicts Brock, because at Brock the
# starter has done nearly all the fighting.
TEAM_SIZE = [
    ("lab", 1), ("route22_first", 1), ("OPP_BROCK", 2), ("cerulean", 3),
    ("OPP_MISTY", 3), ("ss_anne", 4), ("OPP_LT_SURGE", 4), ("OPP_ERIKA", 5),
    ("OPP_GIOVANNI#1", 5), ("tower", 6),
]
DEFAULT_TEAM_SIZE = 6


def team_size_at(key: str) -> int:
    for name, size in TEAM_SIZE:
        if name == key:
            return size
    return DEFAULT_TEAM_SIZE


def ace_share_for(size: int, ace_weight: float) -> float:
    """The ace's cut when it draws `ace_weight` times an even split."""
    return ace_weight / (size - 1 + ace_weight)


@dataclass
class Settings:
    """The mod's own option defaults, plus the player model."""

    trainer_levels_pct: int = 15     # TRAINER LEVEL %
    min_party: int = 3               # MIN PARTY SIZE
    evolve: bool = True              # EVOLVE PRE-EVOS
    stone_level: int = 30            # STONE EVO FROM LV
    xp_pct: int = 75                 # XP GAIN %

    # Player model. A Gen 1 payout goes only to Pokemon that were sent out,
    # so the share the ace ends up with depends on how many others it is
    # sharing with -- which is why a flat share mis-predicts both ends of the
    # game. The team fills up instead: one Pokemon at the lab, six by the
    # midgame (TEAM_SIZE), and the ace draws `ace_weight` times an even split.
    # `wild_bonus` is the allowance for wild battles and incidental grinding
    # on top of trainer payouts.
    # Fitted against the reported vanilla full-clear curve: 11 checkpoints,
    # total error 16 levels, worst case 3, no directional bias (`--vanilla`).
    # wild_bonus stays 0 because trainer payouts alone reproduce those
    # levels -- a player who also grinds wilds will run above this curve, and
    # the MODS menu's BOSS LEVEL BONUS row is the dial for them.
    ace_weight: float = 1.2
    wild_bonus: float = 0.0
    ace_curve_species: str = "CHARMANDER"   # MEDIUM_SLOW, the common ace shape

    # Assume the player fights essentially every trainer on the way. Lower
    # this to model a skipper.
    clear_rate: float = 1.0

    boss_teams: bool = True          # authored rosters in play


def scaled_party(g, party, s: Settings):
    """Apply the mod's ordinary-trainer treatment: bump, evolve, then pad."""
    out = []
    for species, level in party:
        if s.trainer_levels_pct > 0:
            level = level + max(1, int(level * s.trainer_levels_pct / 100 + 0.5))
        level = max(1, min(MAX_LEVEL, level))
        if s.evolve:
            species = g.evolved_at(species, level, s.stone_level)
        out.append((species, level))
    if out:
        target = min(s.min_party, MAX_PARTY)
        i = 0
        while len(out) < target:
            out.append(out[i % len(out)])
            i += 1
    return out


def party_payout(g, party, s: Settings) -> int:
    """Experience the player banks for beating this party."""
    total = 0
    for species, level in party:
        total += g.exp_yield(species, level, participants=1, is_trainer=True)
    total = total * s.xp_pct // 100
    return int(total * (1.0 + s.wild_bonus) * s.clear_rate)


def map_payout(g, map_ids, s: Settings) -> int:
    """Every ordinary trainer standing on these maps."""
    total = 0
    wanted = set(map_ids)
    for map_id, cls, idx in g.placements():
        if map_id not in wanted or cls in progression.BOSS_CLASSES:
            continue
        parties = g.trainers.get(cls) or []
        if not parties:
            continue
        party = parties[min(idx, len(parties)) - 1]
        total += party_payout(g, scaled_party(g, party, s), s)
    return total


def vanilla_boss_party(g, version: str, key: str):
    """The version's own roster for a milestone key.

    A rival milestone owns several keys (one per branch); the player only
    fights one, so the first is representative.
    """
    if key.startswith("OPP_"):
        cls, _, idx = key.partition("#")
        idx = int(idx) if idx else 1
    else:
        keys = progression.rival_keys(version, key)
        cls, idx = keys[0]
    parties = g.trainers.get(cls) or []
    if not parties:
        return []
    return parties[min(idx, len(parties)) - 1]


def team_from_ace(ace: int, size: int = MAX_PARTY):
    """Spread a six-slot team below its ace, ace last."""
    levels = [max(1, min(MAX_LEVEL, ace + d)) for d in SPREAD[:size]]
    return sorted(levels)


def simulate(g, version: str, s: Settings, boss_ace: dict):
    """Walk the timeline; report the player's level entering each boss fight.

    `boss_ace` maps a milestone key to the ace level that boss will field, so
    boss payouts reflect the rosters being designed rather than vanilla's.
    """
    ace_xp = 0.0
    rows = []
    # the share moves with the team, so it is read from the milestone the
    # player is heading towards rather than fixed for the run
    share = ace_share_for(team_size_at(progression.MILESTONES[0]), s.ace_weight)
    for kind, key in progression.TIMELINE:
        if kind == "maps":
            ace_xp += map_payout(g, key, s) * share
            continue

        share = ace_share_for(team_size_at(key), s.ace_weight)
        level = g.level_at_exp(s.ace_curve_species, int(ace_xp))
        rows.append((key, level))

        vanilla = vanilla_boss_party(g, version, key)
        if not vanilla:
            continue
        if s.boss_teams and key in boss_ace:
            size = min(MAX_PARTY, max(len(vanilla), MAX_PARTY))
            party = [(sp, lv) for (sp, _), lv in zip(
                (vanilla * MAX_PARTY)[:size], team_from_ace(boss_ace[key], size))]
        else:
            party = scaled_party(g, vanilla, s) if not s.boss_teams else vanilla
        ace_xp += party_payout(g, party, s) * share
    return rows


def vanilla_ace(g, version: str, key: str) -> int:
    party = vanilla_boss_party(g, version, key)
    return max((lv for _, lv in party), default=1)


_PREVIOUS = None


def previous_ace(version: str, key: str) -> int:
    """The ace level release 1.6.0 already fielded for this milestone.

    A difficulty mod must not hand players an *easier* fight than the release
    before it, and the computed curve does dip in two places -- Brock, where
    the new ramp is gentler than the old flat bonus, and the Champion, who was
    previously set well above what the player actually arrives at. Flooring
    here keeps the ramp everywhere it raises and changes nothing where it
    would lower. 1.6.0's table is version-agnostic, so the same floor applies
    to all three.
    """
    global _PREVIOUS
    if _PREVIOUS is None:
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "boss_teams_1.6.0.lua")
        _PREVIOUS = luadata.load(path) if os.path.exists(path) else {}
    if key.startswith("OPP_"):
        keys = [key if "#" in key else key + "#1"]
    else:
        keys = [f"{cls}#{idx}" for cls, idx in progression.rival_keys("red", key)]
    best = 0
    for k in keys:
        for slot in (_PREVIOUS.get(k) or []):
            best = max(best, slot[1])
    return best


def compute(version: str, s: Settings, iterations: int = 8):
    """Fixed-point solve for the boss ace levels."""
    g = gamedata.load(version)
    boss_ace = {k: vanilla_ace(g, version, k) for k in progression.MILESTONES}
    rows = []
    for _ in range(iterations):
        rows = simulate(g, version, s, boss_ace)
        nxt = {}
        for key, player_level in rows:
            target = player_level + progression.margin_for(version, key)
            # Two floors. Never below what the version itself fielded -- that
            # is what stopped Yellow's Koga/Sabrina/Blaine/Giovanni being
            # nerfed by the mod -- and never below the previous release.
            #
            # A deliberate per-version easing is exempt from the second floor:
            # it is a considered decision rather than the accidental slide the
            # floor exists to catch, and without the exemption the 1.6.0 number
            # would simply overwrite it.
            floor = vanilla_ace(g, version, key) + 1
            if key not in progression.MARGIN_ADJUST.get(version, {}):
                floor = max(floor, previous_ace(version, key))
            nxt[key] = max(1, min(MAX_LEVEL, max(target, floor)))
        # Third floor: every milestone outranks the one before it.
        #
        # The model predicts a level, and between two fights the player only
        # banks what the first one paid -- so late in the run consecutive
        # milestones round to the same number. Lorelei and Bruno both landed
        # on a 67 ace with an identical 62-67 spread, which is defensible as a
        # prediction and wrong as a fight: the Elite Four is an escalating
        # gauntlet, and reading the same six levels twice running makes the
        # second member feel like a repeat of the first. One level is enough
        # to keep the shape without arguing with the model.
        running = 0
        for key in progression.MILESTONES:
            if key in nxt:
                nxt[key] = min(MAX_LEVEL, max(nxt[key], running + 1))
                running = nxt[key]
        if nxt == boss_ace:
            break
        boss_ace = nxt
    return rows, boss_ace


def report(version: str, s: Settings):
    g = gamedata.load(version)
    rows, boss_ace = compute(version, s)
    print(f"===== {version}   (ace_weight={s.ace_weight} wild_bonus={s.wild_bonus} "
          f"xp={s.xp_pct}% trainers=+{s.trainer_levels_pct}%)")
    print(f"{'milestone':20} {'you':>4} {'+m':>3} {'ace':>4} {'vanilla':>8} "
          f"{'team':>22}")
    for key, player_level in rows:
        ace = boss_ace[key]
        van = vanilla_ace(g, version, key)
        team = team_from_ace(ace)
        print(f"{key:20} {player_level:>4} {progression.MARGIN.get(key,4):>+3} "
              f"{ace:>4} {van:>8} {str(team):>22}")
    return rows, boss_ace


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vanilla", action="store_true",
                    help="model an unmodded game, to sanity-check the model")
    ap.add_argument("--sensitivity", action="store_true",
                    help="vary the player-model assumptions")
    ap.add_argument("--versions", default="red,yellow")
    args = ap.parse_args()

    if args.vanilla:
        s = Settings(trainer_levels_pct=0, min_party=1, evolve=False,
                     xp_pct=100, boss_teams=False, wild_bonus=0.20)
        for v in args.versions.split(","):
            report(v, s)
            print()
        return 0

    if args.sensitivity:
        for share in (1.2, 1.5, 2.0):
            for wild in (0.15, 0.30, 0.45):
                s = Settings(ace_weight=share, wild_bonus=wild)
                rows, ace = compute("red", s)
                sample = {k: v for k, v in rows}
                print(f"share={share:.2f} wild={wild:.2f}  "
                      f"Brock you={sample['OPP_BROCK']:>2} "
                      f"Koga you={sample['OPP_KOGA']:>2} "
                      f"Lance you={sample['OPP_LANCE']:>2} "
                      f"Champion you={sample['champion']:>2} "
                      f"-> champion ace {ace['champion']}")
        return 0

    for v in args.versions.split(","):
        report(v, Settings())
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
