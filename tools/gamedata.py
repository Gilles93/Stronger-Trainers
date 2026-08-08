"""One version's game data, read from ROM-extracted tables.

Everything the authoring tools need to be *correct* rather than plausible:
move legality per species, the type chart, and the engine's own experience
and growth maths. Nothing here is authored -- it is all the ROM's own
numbers, so a roster that passes these checks is a roster the real build
will accept.

Populate the tables first. They are ROM-derived and never committed, so
`.romdata/<version>/` starts empty; the simplest source is the game's own
import cache, which is exactly what the running build reads:

    cp "$APPDATA/pokemon-love2d/<version>/data/generated"/*.lua \\
       .romdata/<version>/

Import the version through the launcher once and that directory appears (Red
on older builds lives in the un-prefixed `data/generated`). The release
payload ships no Python extractor -- extraction is `src/import/RomExtractor.lua`
inside the game -- so the cache is the route, not a build script.
"""

from __future__ import annotations

import os
from functools import lru_cache

import luadata

VERSIONS = ("red", "blue", "yellow")

# src/pokemon/Growth.lua -- total experience to reach level n.
GROWTH_CURVES = {
    "MEDIUM_FAST": lambda n: n ** 3,
    "MEDIUM_SLOW": lambda n: (6 * n ** 3) // 5 - 15 * n * n + 100 * n - 140,
    "FAST": lambda n: (4 * n ** 3) // 5,
    "SLOW": lambda n: (5 * n ** 3) // 4,
}

MAX_LEVEL = 100


def _normalize_parties(raw):
    """`parties` arrives as a list or a 1-based dict; slots likewise."""
    if not raw:
        return []
    keys = sorted(raw) if isinstance(raw, dict) else range(len(raw))
    out = []
    for k in keys:
        party = raw[k] if isinstance(raw, dict) else raw[k]
        if isinstance(party, dict):
            party = [party[i] for i in sorted(party)]
        out.append([(s["species"], s["level"]) for s in party])
    return out


class GameData:
    def __init__(self, version: str, root: str):
        self.version = version
        self.dir = os.path.join(root, version)
        self.species = luadata.load(os.path.join(self.dir, "pokemon.lua"))
        self.moves = luadata.load(os.path.join(self.dir, "moves.lua"))
        self._trainers_raw = luadata.load(os.path.join(self.dir, "trainers.lua"))
        self.trainers = {
            cid: _normalize_parties(rec.get("parties"))
            for cid, rec in self._trainers_raw.items()
        }
        chart = luadata.load(os.path.join(self.dir, "type_chart.lua"))
        self.matchups = {
            (m["attacker"], m["defender"]): m["multiplier"]
            for m in chart["matchups"]
        }
        enc_path = os.path.join(self.dir, "encounters.lua")
        self.encounters = luadata.load(enc_path) if os.path.exists(enc_path) else {}

        maps_path = os.path.join(self.dir, "maps.lua")
        self.maps = luadata.load(maps_path) if os.path.exists(maps_path) else {}

        # reverse evolution links, so a slot may keep a move its earlier
        # stage learned -- an Ivysaur legitimately knows Bulbasaur's moves
        self.pre_evos = {}
        for sid, rec in self.species.items():
            for evo in (rec.get("evolutions") or []):
                self.pre_evos.setdefault(evo["species"], []).append(sid)

    # ------------------------------------------------------------- legality

    def _line(self, species):
        """A species and every stage it evolved from."""
        seen, stack, out = set(), [species], []
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in self.species:
                continue
            seen.add(cur)
            out.append(cur)
            stack.extend(self.pre_evos.get(cur, ()))
        return out

    @lru_cache(maxsize=None)
    def legal_moves(self, species: str, level: int):
        """Every move this slot could legitimately know.

        Level-up moves stay level-gated -- a Pokemon cannot know what it has
        not learned yet -- and a pre-evolution's learnset counts at the level
        that stage would have learned it. TM and HM moves are not gated at
        all: where in the game the TM is found is the player's problem, not a
        legality question (the era gate was dropped deliberately).
        """
        ok = set()
        for stage in self._line(species):
            rec = self.species[stage]
            ok.update(rec.get("level1Moves") or [])
            for row in (rec.get("learnset") or []):
                if row["level"] <= level:
                    ok.add(row["move"])
            ok.update(rec.get("tmhm") or [])
        return frozenset(m for m in ok if m in self.moves)

    def types(self, species: str):
        return tuple(self.species[species]["types"])

    def effectiveness(self, move_type: str, defender_types) -> float:
        """Full dual-type product, x1 per unlisted matchup (multipliers are x10)."""
        mult = 1.0
        for d in defender_types:
            row = self.matchups.get((move_type, d))
            if row is not None:
                mult *= row / 10.0
        return mult

    # ---------------------------------------------------------- experience

    def curve(self, species: str):
        rate = self.species[species].get("growthRate") or "MEDIUM_FAST"
        return GROWTH_CURVES.get(rate, GROWTH_CURVES["MEDIUM_FAST"])

    def exp_at_level(self, species: str, level: int) -> int:
        return max(0, self.curve(species)(max(1, level)))

    def level_at_exp(self, species: str, exp: int) -> int:
        """Inverse of the growth curve, clamped to 1..100."""
        fn = self.curve(species)
        lo, hi = 1, MAX_LEVEL
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if fn(mid) <= exp:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def exp_yield(self, species: str, level: int, participants: int = 1,
                  is_trainer: bool = True) -> int:
        """src/battle/Experience.lua gainFor, floors included."""
        rec = self.species.get(species)
        if not rec:
            return 0
        base = rec["baseExp"] // max(1, participants)
        exp = base * level // 7
        if is_trainer:
            exp = int(exp * 3 // 2)
        return exp

    # -------------------------------------------------------------- helpers

    def evolved_at(self, species: str, level: int, stone_level: int = 30) -> str:
        """The stage `level` has earned, mirroring main.lua's evolvedSpecies."""
        cur, seen = species, set()
        for _ in range(5):
            if cur in seen:
                break
            seen.add(cur)
            target = None
            for evo in (self.species.get(cur, {}).get("evolutions") or []):
                by_level = evo.get("method") == "LEVEL" and level >= (evo.get("level") or 999)
                by_stone = evo.get("method") == "ITEM" and stone_level > 0 and level >= stone_level
                if by_level or by_stone:
                    target = evo["species"]
                    break
            if not target or target not in self.species:
                break
            cur = target
        return cur

    def placements(self):
        """(map_id, trainer_class, party_index) for every trainer object."""
        out = []
        for mid, m in self.maps.items():
            for obj in (m.get("objects") or []):
                cls = obj.get("trainerClass")
                if cls:
                    out.append((m.get("id", mid), cls, obj.get("trainerParty") or 1))
        return out


_CACHE = {}


def load(version: str, root: str = None) -> GameData:
    root = root or os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), ".romdata")
    key = (version, root)
    if key not in _CACHE:
        _CACHE[key] = GameData(version, root)
    return _CACHE[key]
