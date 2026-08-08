"""The authored boss teams: species and movesets. Levels come from curve.py.

Design rules, applied to every gym team:

  * Type identity is absolute. Every slot is the gym's type or a dual-type
    carrying it, with at most one thematic ally (Brock's Sandshrew is Ground,
    Sabrina's Venomoth is the Psychic-adjacent Bug). A Water gym never
    fields a Raichu to cover its Electric weakness -- it covers that
    weakness with a Ground *move* on a Water Pokemon.
  * Coverage answers the gym type's own weaknesses -- but only from the
    point the player could answer back. The early gyms are gated by
    availability.py: nothing off-type at Brock or Misty, one move at Surge,
    two at Erika, unrestricted from Koga on. 1.7.0 shipped Brock carrying
    Thunderbolt, Ice Beam, Fire Blast, Rock Slide and Earthquake at one
    badge, which is not a hard fight, it is a locked door.
  * Four slots each: one or two STAB, one or two coverage, at most one
    status. Coverage is spread across the team rather than stacked on the
    ace, so switching in a hard counter meets a different answer each time.

Two deliberate omissions:

  * Charge moves -- Dig, Sky Attack, Solarbeam, Razor Wind -- appear
    nowhere. smart_ai scores a move on the damage Damage.compute reports,
    and for a charge move that is the full hit with no account of the turn
    spent winding up, so the AI rates Dig above Rock Slide and then spends
    every other turn underground. Brock had it on three of six at 100 base
    power, at one badge.
  * OHKO moves likewise. smart_ai weights by accuracy, so a 30% Horn Drill
    scores near the bottom and the slot is dead -- until the one time it
    lands and decides the fight on a coin flip.
  * EXPLOSION and SELFDESTRUCT appear nowhere. smart_ai.lua scores them +6
    on purpose -- they are the cheese the AI is built not to play -- so
    authoring them just wastes a slot the AI will refuse to use.
  * Trapping moves (Wrap, Clamp, Fire Spin, Bind) likewise: suppressed by
    the same rule, for the same reason.

Levels are NOT here. They are computed per version by curve.py, because
Yellow's experience economy differs from Red's and the whole point of this
release is that hand-picked levels drift out of true.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Gym leaders. Ace last; the level spread is applied in that order.
# ---------------------------------------------------------------------------

GYM_LEADERS = {
    # Rock. Rock and Normal only, nothing over Body Slam, and no move on more
    # than three of the six -- see availability.py. Earthquake and Dig are
    # gone: Gen 1 has no mild Ground attack, so the Ground half of this gym is
    # a defensive trait here rather than an offensive one, which is what
    # vanilla does too. Rock Throw carries the middle of the team and Rock
    # Slide is kept for Rhyhorn and the Onix.
    "OPP_BROCK#1": [
        ("GEODUDE",   ["TACKLE", "BODY_SLAM", "DEFENSE_CURL"]),
        ("SANDSHREW", ["SCRATCH", "SWIFT", "SAND_ATTACK"]),
        ("RHYHORN",   ["ROCK_SLIDE", "HORN_ATTACK", "BODY_SLAM"]),
        ("KABUTO",    ["SCRATCH", "HARDEN", "BODY_SLAM"]),
        # Yellow's Brock sits two levels lower, and Rock Throw arrives at 16
        # for the Geodude line and 19 for Onix, so Yellow falls back to the TM
        ("GRAVELER",  {"*": ["ROCK_THROW", "TACKLE", "DEFENSE_CURL"],
                       "yellow": ["ROCK_SLIDE", "TACKLE", "DEFENSE_CURL"]}),
        ("ONIX",      {"*": ["ROCK_SLIDE", "ROCK_THROW", "SCREECH", "TOXIC"],
                       "yellow": ["ROCK_SLIDE", "TACKLE", "SCREECH", "TOXIC"]}),
    ],
    # Water. Water and Normal only. Starmie's Psychic is gone despite being
    # its own STAB: it is 2x into the Grass/Poison starter a player brings to
    # answer a Water gym, whose Water moves that starter already resists, so
    # the "correct" counter was the worst possible pick. Surf went with it at
    # 95 power. Water Gun carries the front, Bubblebeam the back, and Starmie
    # gets Recover instead of a fourth attack -- the AI heals at most twice
    # and only below half, so it is a longer fight rather than an unwinnable
    # one.
    "OPP_MISTY#1": [
        ("PSYDUCK",   ["WATER_GUN", "SCRATCH", "BODY_SLAM", "DOUBLE_TEAM"]),
        ("SHELLDER",  ["WATER_GUN", "TRI_ATTACK", "SUPERSONIC", "WITHDRAW"]),
        ("SEADRA",    ["BUBBLEBEAM", "SWIFT", "TOXIC", "SMOKESCREEN"]),
        ("POLIWHIRL", ["WATER_GUN", "BODY_SLAM", "HYPNOSIS", "DOUBLESLAP"]),
        ("STARYU",    ["BUBBLEBEAM", "SWIFT", "THUNDER_WAVE", "HARDEN"]),
        ("STARMIE",   ["BUBBLEBEAM", "TRI_ATTACK", "THUNDER_WAVE", "RECOVER"]),
    ],
    # Electric. Weak to Ground, which Electric moves cannot touch at all, so
    # the answers are Raichu's Submission (2x into Rock) and Electrode's
    # Toxic for anything bulky enough to sit there.
    "OPP_LT_SURGE#1": [
        # Voltorb and Electrode have no level-up Electric attack at all, so
        # they take the Thunderbolt; everything in the Pikachu and Magnemite
        # lines learns Thundershock and uses that instead.
        ("VOLTORB",   ["THUNDERBOLT", "SONICBOOM", "SCREECH", "DOUBLE_TEAM"]),
        ("PIKACHU",   ["THUNDERSHOCK", "QUICK_ATTACK", "THUNDER_WAVE", "SWIFT"]),
        ("MAGNEMITE", ["THUNDERSHOCK", "SONICBOOM", "SUPERSONIC", "THUNDER_WAVE"]),
        ("ELECTRODE", ["THUNDERBOLT", "SCREECH", "TOXIC", "SWIFT"]),
        ("MAGNETON",  ["THUNDERSHOCK", "SWIFT", "DOUBLE_TEAM", "THUNDER_WAVE"]),
        ("RAICHU",    ["THUNDERBOLT", "SEISMIC_TOSS", "BODY_SLAM", "AGILITY"]),
    ],
    # Grass. Weak to Fire/Ice/Poison/Flying/Bug -- the worst-covered type in
    # Gen 1, so the threat here is status: powder into Toxic, with
    # Exeggutor's Psychic as the one real coverage move on the team.
    "OPP_ERIKA#1": [
        # Sleep Powder was on four of six, which is the whole fight decided
        # before it starts. Two carry it now; the rest lean on Stun Spore and
        # Toxic, which cost you the fight more slowly and more fairly.
        ("TANGELA",    ["MEGA_DRAIN", "BODY_SLAM", "STUN_SPORE", "TOXIC"]),
        ("GLOOM",      ["ACID", "SLEEP_POWDER", "MEGA_DRAIN", "TOXIC"]),
        ("WEEPINBELL", ["RAZOR_LEAF", "ACID", "STUN_SPORE", "GROWTH"]),
        ("EXEGGUTOR",  ["PSYCHIC_M", "HYPNOSIS", "REFLECT", "LEECH_SEED"]),
        ("VICTREEBEL", ["RAZOR_LEAF", "ACID", "BODY_SLAM", "SLEEP_POWDER"]),
        ("VILEPLUME",  ["MEGA_DRAIN", "BODY_SLAM", "TOXIC", "STUN_SPORE"]),
    ],
    # Poison. Weak to Ground/Psychic/Bug. Golbat is outright immune to
    # Ground, Arbok answers it with Earthquake of its own, and Muk/Weezing
    # carry Thunderbolt for the Water and Flying types that wall Sludge.
    "OPP_KOGA#1": [
        ("KOFFING",  ["SLUDGE", "TOXIC", "FIRE_BLAST", "SMOKESCREEN"]),
        ("GOLBAT",   ["WING_ATTACK", "CONFUSE_RAY", "TOXIC", "MEGA_DRAIN"]),
        ("VENOMOTH", ["PSYCHIC_M", "SLEEP_POWDER", "MEGA_DRAIN", "DOUBLE_TEAM"]),
        ("ARBOK",    ["EARTHQUAKE", "GLARE", "BODY_SLAM", "ACID"]),
        ("MUK",      ["SLUDGE", "TOXIC", "THUNDERBOLT", "BODY_SLAM"]),
        ("WEEZING",  ["SLUDGE", "TOXIC", "THUNDERBOLT", "FIRE_BLAST"]),
    ],
    # Psychic. Barely weak to anything in Gen 1, so this team is about
    # answering what resists it: Mr. Mime's Thunderbolt, Exeggutor's Mega
    # Drain, Alakazam's Seismic Toss for anything that shrugs off special
    # attacks entirely.
    "OPP_SABRINA#1": [
        ("MR_MIME",   ["PSYCHIC_M", "THUNDERBOLT", "BARRIER", "SEISMIC_TOSS"]),
        ("VENOMOTH",  ["PSYCHIC_M", "SLEEP_POWDER", "MEGA_DRAIN", "DOUBLE_TEAM"]),
        ("KADABRA",   ["PSYCHIC_M", "RECOVER", "REFLECT", "THUNDER_WAVE"]),
        ("HYPNO",     ["PSYCHIC_M", "HYPNOSIS", "BODY_SLAM", "REST"]),
        ("EXEGGUTOR", ["PSYCHIC_M", "MEGA_DRAIN", "SLEEP_POWDER", "REFLECT"]),
        ("ALAKAZAM",  ["PSYCHIC_M", "RECOVER", "SEISMIC_TOSS", "THUNDER_WAVE"]),
    ],
    # Fire. Weak to Water/Ground/Rock. Fire cannot answer Water, so the
    # answers are Ground and Fighting moves: Growlithe and Arcanine dig,
    # Magmar takes Rock apart with Submission.
    "OPP_BLAINE#1": [
        ("PONYTA",    ["FIRE_BLAST", "STOMP", "BODY_SLAM", "TAKE_DOWN"]),
        ("GROWLITHE", ["FIRE_BLAST", "TAKE_DOWN", "BODY_SLAM", "AGILITY"]),
        ("MAGMAR",    ["FIRE_BLAST", "SUBMISSION", "CONFUSE_RAY", "BODY_SLAM"]),
        ("RAPIDASH",  ["FIRE_BLAST", "STOMP", "SWIFT", "TAKE_DOWN"]),
        ("NINETALES", ["FLAMETHROWER", "CONFUSE_RAY", "TOXIC", "BODY_SLAM"]),
        ("ARCANINE",  ["FIRE_BLAST", "DOUBLE_EDGE", "BODY_SLAM", "TAKE_DOWN"]),
    ],
}

# ---------------------------------------------------------------------------
# Giovanni's three fights. Ground, weak to Water/Grass/Ice -- and the Nidos
# answer all three, which is why they are his signature.
# ---------------------------------------------------------------------------

GIOVANNI = {
    "OPP_GIOVANNI#1": [
        ("SANDSHREW",  ["EARTHQUAKE", "ROCK_SLIDE", "SWIFT", "SAND_ATTACK"]),
        ("ONIX",       ["ROCK_SLIDE", "EARTHQUAKE", "BODY_SLAM", "TOXIC"]),
        ("RHYHORN",    ["ROCK_SLIDE", "EARTHQUAKE", "THUNDERBOLT", "HORN_ATTACK"]),
        ("DUGTRIO",    ["EARTHQUAKE", "ROCK_SLIDE", "SLASH", "SAND_ATTACK"]),
        ("PERSIAN",    ["BITE", "BODY_SLAM", "THUNDERBOLT", "SCREECH"]),
        ("KANGASKHAN", ["BODY_SLAM", "EARTHQUAKE", "MEGA_PUNCH", "TAIL_WHIP"]),
    ],
    "OPP_GIOVANNI#2": [
        ("RHYHORN",    ["ROCK_SLIDE", "EARTHQUAKE", "THUNDERBOLT", "STOMP"]),
        ("PERSIAN",    ["SLASH", "BODY_SLAM", "BUBBLEBEAM", "SCREECH"]),
        ("NIDORINO",   ["HORN_ATTACK", "ICE_BEAM", "THUNDERBOLT", "DOUBLE_KICK"]),
        ("DUGTRIO",    ["EARTHQUAKE", "ROCK_SLIDE", "SLASH", "SAND_ATTACK"]),
        ("KANGASKHAN", ["BODY_SLAM", "EARTHQUAKE", "MEGA_PUNCH", "ICE_BEAM"]),
        ("NIDOQUEEN",  ["EARTHQUAKE", "ICE_BEAM", "THUNDERBOLT", "BODY_SLAM"]),
    ],
    "OPP_GIOVANNI#3": [
        ("DUGTRIO",   ["EARTHQUAKE", "ROCK_SLIDE", "SLASH", "SAND_ATTACK"]),
        ("MAROWAK",   ["EARTHQUAKE", "BONEMERANG", "ICE_BEAM", "BODY_SLAM"]),
        ("PERSIAN",   ["SLASH", "BODY_SLAM", "BUBBLEBEAM", "SCREECH"]),
        ("NIDOQUEEN", ["EARTHQUAKE", "ICE_BEAM", "THUNDERBOLT", "BODY_SLAM"]),
        ("NIDOKING",  ["EARTHQUAKE", "ICE_BEAM", "THUNDERBOLT", "BODY_SLAM"]),
        ("RHYDON",    ["EARTHQUAKE", "ROCK_SLIDE", "BODY_SLAM", "TAKE_DOWN"]),
    ],
}

# ---------------------------------------------------------------------------
# Elite Four and the Champion.
# ---------------------------------------------------------------------------

ELITE_FOUR = {
    # Ice/Water, weak to Fire/Fighting/Rock. Slowbro's Psychic covers
    # Fighting; Lapras's Thunderbolt covers the Water types Ice cannot dent.
    "OPP_LORELEI#1": [
        ("SEADRA",   ["SURF", "ICE_BEAM", "TOXIC", "SMOKESCREEN"]),
        ("DEWGONG",  ["BLIZZARD", "SURF", "BODY_SLAM", "REST"]),
        ("CLOYSTER", ["BLIZZARD", "SURF", "SPIKE_CANNON", "TOXIC"]),
        ("SLOWBRO",  ["SURF", "PSYCHIC_M", "ICE_BEAM", "AMNESIA"]),
        ("JYNX",     ["BLIZZARD", "PSYCHIC_M", "LOVELY_KISS", "BODY_SLAM"]),
        ("LAPRAS",   ["BLIZZARD", "SURF", "THUNDERBOLT", "BODY_SLAM"]),
    ],
    # Fighting, weak to Psychic/Flying. Rock Slide answers Flying, and
    # Hitmonchan's elemental punches are Gen 1's only spread of them.
    "OPP_BRUNO#1": [
        ("ONIX",        ["ROCK_SLIDE", "EARTHQUAKE", "BODY_SLAM", "TOXIC"]),
        ("HITMONLEE",   ["HI_JUMP_KICK", "MEGA_KICK", "SEISMIC_TOSS", "TOXIC"]),
        ("HITMONCHAN",  ["SUBMISSION", "FIRE_PUNCH", "ICE_PUNCH", "THUNDERPUNCH"]),
        ("PRIMEAPE",    ["SUBMISSION", "BODY_SLAM", "ROCK_SLIDE", "THRASH"]),
        ("GOLEM",       ["EARTHQUAKE", "ROCK_SLIDE", "BODY_SLAM", "FIRE_BLAST"]),
        ("MACHAMP",     ["SUBMISSION", "EARTHQUAKE", "ROCK_SLIDE", "BODY_SLAM"]),
    ],
    # Ghost/Poison. Gen 1's Ghost moves cannot touch Psychic, so her damage
    # is Psychic and Thunderbolt with Hypnosis and Toxic underneath.
    "OPP_AGATHA#1": [
        ("HAUNTER", ["PSYCHIC_M", "HYPNOSIS", "CONFUSE_RAY", "MEGA_DRAIN"]),
        ("GOLBAT",  ["WING_ATTACK", "CONFUSE_RAY", "TOXIC", "MEGA_DRAIN"]),
        ("ARBOK",   ["EARTHQUAKE", "GLARE", "BODY_SLAM", "ACID"]),
        ("WEEZING", ["SLUDGE", "TOXIC", "THUNDERBOLT", "FIRE_BLAST"]),
        ("MUK",     ["SLUDGE", "TOXIC", "THUNDERBOLT", "BODY_SLAM"]),
        ("GENGAR",  ["PSYCHIC_M", "HYPNOSIS", "THUNDERBOLT", "MEGA_DRAIN"]),
    ],
    # Dragon/Flying. Gen 1 has exactly one Dragon move and it deals a flat
    # 40, so every Dragon here fights with borrowed coverage instead --
    # Blizzard, Thunderbolt, Surf.
    "OPP_LANCE#1": [
        ("DRAGONAIR",  ["SURF", "THUNDER_WAVE", "BODY_SLAM", "AGILITY"]),
        ("DRAGONAIR",  ["BLIZZARD", "THUNDER_WAVE", "BODY_SLAM", "HYPER_BEAM"]),
        ("GYARADOS",   ["HYDRO_PUMP", "BLIZZARD", "BODY_SLAM", "HYPER_BEAM"]),
        ("AERODACTYL", ["FIRE_BLAST", "DOUBLE_EDGE", "BITE", "HYPER_BEAM"]),
        ("DRAGONITE",  ["BLIZZARD", "THUNDERBOLT", "BODY_SLAM", "AGILITY"]),
        ("DRAGONITE",  ["BLIZZARD", "SURF", "THUNDER_WAVE", "HYPER_BEAM"]),
    ],
}

# Champion, Red/Blue: one roster per starter branch. The ace is the fully
# evolved counter-pick to the player's own starter, as the game intends.
CHAMPION_RB = {
    1: [  # player chose Charmander -> rival carries Blastoise
        ("PIDGEOT",   ["DOUBLE_EDGE", "WING_ATTACK", "TOXIC", "SAND_ATTACK"]),
        ("ALAKAZAM",  ["PSYCHIC_M", "RECOVER", "SEISMIC_TOSS", "THUNDER_WAVE"]),
        ("RHYDON",    ["EARTHQUAKE", "ROCK_SLIDE", "BODY_SLAM", "TAKE_DOWN"]),
        ("ARCANINE",  ["FIRE_BLAST", "DOUBLE_EDGE", "BODY_SLAM", "TAKE_DOWN"]),
        ("EXEGGUTOR", ["PSYCHIC_M", "MEGA_DRAIN", "SLEEP_POWDER", "STUN_SPORE"]),
        ("BLASTOISE", ["SURF", "BLIZZARD", "BODY_SLAM", "EARTHQUAKE"]),
    ],
    2: [  # Squirtle -> Venusaur
        ("PIDGEOT",  ["DOUBLE_EDGE", "WING_ATTACK", "TOXIC", "SAND_ATTACK"]),
        ("ALAKAZAM", ["PSYCHIC_M", "RECOVER", "SEISMIC_TOSS", "THUNDER_WAVE"]),
        ("RHYDON",   ["EARTHQUAKE", "ROCK_SLIDE", "BODY_SLAM", "TAKE_DOWN"]),
        ("GYARADOS", ["HYDRO_PUMP", "BLIZZARD", "BODY_SLAM", "HYPER_BEAM"]),
        ("ARCANINE", ["FIRE_BLAST", "DOUBLE_EDGE", "BODY_SLAM", "TAKE_DOWN"]),
        ("VENUSAUR", ["RAZOR_LEAF", "SLEEP_POWDER", "BODY_SLAM", "MEGA_DRAIN"]),
    ],
    3: [  # Bulbasaur -> Charizard
        ("PIDGEOT",   ["DOUBLE_EDGE", "WING_ATTACK", "TOXIC", "SAND_ATTACK"]),
        ("ALAKAZAM",  ["PSYCHIC_M", "RECOVER", "SEISMIC_TOSS", "THUNDER_WAVE"]),
        ("RHYDON",    ["EARTHQUAKE", "ROCK_SLIDE", "BODY_SLAM", "TAKE_DOWN"]),
        ("EXEGGUTOR", ["PSYCHIC_M", "MEGA_DRAIN", "SLEEP_POWDER", "STUN_SPORE"]),
        ("GYARADOS",  ["HYDRO_PUMP", "BLIZZARD", "BODY_SLAM", "HYPER_BEAM"]),
        ("CHARIZARD", ["FIRE_BLAST", "EARTHQUAKE", "SLASH", "SWORDS_DANCE"]),
    ],
}

# The Celadon Chief. An unused trainer class: Red carries party data for him
# that nothing in the game ever triggers, and Blue and Yellow leave the table
# empty. Kept so that a mod which does place him finds a real team rather
# than whatever the empty roster would produce.
CHIEF = [
    ("MACHOKE",  ["SUBMISSION", "KARATE_CHOP", "SEISMIC_TOSS", "LOW_KICK"]),
    ("GOLBAT",   ["WING_ATTACK", "CONFUSE_RAY", "TOXIC", "MEGA_DRAIN"]),
    ("MAROWAK",  ["EARTHQUAKE", "BONEMERANG", "ICE_BEAM", "BODY_SLAM"]),
    ("WEEZING",  ["SLUDGE", "TOXIC", "THUNDERBOLT", "FIRE_BLAST"]),
    ("HYPNO",    ["PSYCHIC_M", "HYPNOSIS", "BODY_SLAM", "REST"]),
    ("PERSIAN",  ["SLASH", "BODY_SLAM", "BUBBLEBEAM", "SCREECH"]),
]

# ---------------------------------------------------------------------------
# Rivals. Species per battle; the mid-game fights carry no movesets, exactly
# as before -- the engine fills in each species' own level-up set, which is
# the right texture for a rival who is meant to feel like a player.
#
# Red/Blue keeps its existing shape: three branches per battle, keyed by the
# player's starter counter-pick.
#
# Yellow is new, and it is the whole reason for this release. His party
# indices are laid out completely differently (three RIVAL1 parties, not
# nine), which is why the old table put a level 6 starter into every one of
# his early fights. His identity is the Eevee line, not a starter.
# ---------------------------------------------------------------------------

# Yellow: Eevee stays unevolved through the S.S. Anne, then arrives as its
# branch from the Tower on. Vanilla holds the evolution back to Silph, but
# vanilla's Tower Eevee is level 25 where this curve puts the fight at 45 --
# an unevolved Eevee at that level is not a fight, it is a formality. The
# branch is already decided by then (save.rivalStarter is set at the lab), so
# nothing has to be guessed.
YELLOW_EEVEELUTION = {1: "JOLTEON", 2: "FLAREON", 3: "VAPOREON"}

# Support cast per branch, mirroring which Pokemon vanilla Yellow gives him
# alongside each evolution.
YELLOW_SUPPORT = {
    1: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "CLOYSTER", "NINETALES"],
    2: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "MAGNETON", "CLOYSTER"],
    3: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "NINETALES", "MAGNETON"],
}

# Earlier stages of that support cast, for the fights before it has evolved.
YELLOW_DEVOLVE = {
    "SANDSLASH": "SANDSHREW", "ALAKAZAM": "KADABRA", "EXEGGUTOR": "EXEGGCUTE",
    "CLOYSTER": "SHELLDER", "NINETALES": "VULPIX", "MAGNETON": "MAGNEMITE",
}

CHAMPION_YELLOW_MOVES = {
    "JOLTEON":  ["THUNDERBOLT", "PIN_MISSILE", "DOUBLE_KICK", "AGILITY"],
    "FLAREON":  ["FIRE_BLAST", "BODY_SLAM", "QUICK_ATTACK", "TAKE_DOWN"],
    "VAPOREON": ["SURF", "BLIZZARD", "BODY_SLAM", "ACID_ARMOR"],
    "SANDSLASH": ["EARTHQUAKE", "ROCK_SLIDE", "SLASH", "SWIFT"],
    "ALAKAZAM": ["PSYCHIC_M", "RECOVER", "SEISMIC_TOSS", "THUNDER_WAVE"],
    "EXEGGUTOR": ["PSYCHIC_M", "MEGA_DRAIN", "SLEEP_POWDER", "STUN_SPORE"],
    "CLOYSTER": ["BLIZZARD", "SURF", "SPIKE_CANNON", "TOXIC"],
    "NINETALES": ["FLAMETHROWER", "CONFUSE_RAY", "TOXIC", "BODY_SLAM"],
    "MAGNETON": ["THUNDERBOLT", "THUNDER_WAVE", "SWIFT", "DOUBLE_TEAM"],
}


# His first four fights are a single party each -- Eevee has not branched in
# the data yet -- so their support cast has to be branch-neutral. Vanilla's
# own picks (Spearow, Rattata, Sandshrew) carry that fine.
YELLOW_RIVAL_NEUTRAL = {
    "lab":           ["EEVEE"],
    "route22_first": ["SPEAROW", "RATTATA", "EEVEE"],
    "cerulean":      ["SPEAROW", "SANDSHREW", "RATTATA", "KADABRA", "EEVEE"],
    "ss_anne":       ["FEAROW", "RATICATE", "SANDSHREW", "KADABRA", "EEVEE"],
}

# From the Tower on, one roster per branch. Kadabra holds until Silph so the
# rival's own team still visibly progresses across the four fights.
YELLOW_RIVAL_BRANCHED = {
    "tower": {
        1: ["SANDSLASH", "KADABRA", "EXEGGCUTE", "SHELLDER", "NINETALES", "JOLTEON"],
        2: ["SANDSLASH", "KADABRA", "EXEGGCUTE", "MAGNEMITE", "SHELLDER", "FLAREON"],
        3: ["SANDSLASH", "KADABRA", "EXEGGCUTE", "NINETALES", "MAGNEMITE", "VAPOREON"],
    },
    "silph": {
        1: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "CLOYSTER", "NINETALES", "JOLTEON"],
        2: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "MAGNETON", "CLOYSTER", "FLAREON"],
        3: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "NINETALES", "MAGNETON", "VAPOREON"],
    },
    "route22_second": {
        1: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "CLOYSTER", "NINETALES", "JOLTEON"],
        2: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "MAGNETON", "CLOYSTER", "FLAREON"],
        3: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "NINETALES", "MAGNETON", "VAPOREON"],
    },
    "champion": {
        1: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "CLOYSTER", "NINETALES", "JOLTEON"],
        2: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "MAGNETON", "CLOYSTER", "FLAREON"],
        3: ["SANDSLASH", "ALAKAZAM", "EXEGGUTOR", "NINETALES", "MAGNETON", "VAPOREON"],
    },
}

# Red/Blue rival species per battle and branch, unchanged from 1.6.0 apart
# from levels. Branch order matches the counter-pick offset: +0 Charmander
# chosen (rival has Squirtle), +1 Squirtle (Bulbasaur), +2 Bulbasaur
# (Charmander).
RB_RIVAL_TEAMS = {
    "lab": {
        1: ["SQUIRTLE"], 2: ["BULBASAUR"], 3: ["CHARMANDER"],
    },
    "route22_first": {
        1: ["PIDGEY", "RATTATA", "SQUIRTLE"],
        2: ["PIDGEY", "RATTATA", "BULBASAUR"],
        3: ["PIDGEY", "RATTATA", "CHARMANDER"],
    },
    "cerulean": {
        1: ["SPEAROW", "RATTATA", "ABRA", "PIDGEOTTO", "WARTORTLE"],
        2: ["SPEAROW", "RATTATA", "ABRA", "PIDGEOTTO", "IVYSAUR"],
        3: ["SPEAROW", "RATTATA", "ABRA", "PIDGEOTTO", "CHARMELEON"],
    },
    "ss_anne": {
        1: ["RATICATE", "KADABRA", "EXEGGCUTE", "PIDGEOTTO", "WARTORTLE"],
        2: ["RATICATE", "KADABRA", "GROWLITHE", "PIDGEOTTO", "IVYSAUR"],
        3: ["RATICATE", "KADABRA", "EXEGGCUTE", "PIDGEOTTO", "CHARMELEON"],
    },
    "tower": {
        1: ["RATICATE", "KADABRA", "EXEGGCUTE", "GROWLITHE", "PIDGEOTTO", "WARTORTLE"],
        2: ["RATICATE", "KADABRA", "GYARADOS", "GROWLITHE", "PIDGEOTTO", "IVYSAUR"],
        3: ["RATICATE", "KADABRA", "EXEGGCUTE", "GYARADOS", "PIDGEOTTO", "CHARMELEON"],
    },
    "silph": {
        1: ["ALAKAZAM", "EXEGGCUTE", "GROWLITHE", "RHYHORN", "PIDGEOT", "BLASTOISE"],
        2: ["ALAKAZAM", "GROWLITHE", "GYARADOS", "RHYHORN", "PIDGEOT", "VENUSAUR"],
        3: ["ALAKAZAM", "EXEGGCUTE", "GYARADOS", "RHYHORN", "PIDGEOT", "CHARIZARD"],
    },
    "route22_second": {
        1: ["RHYDON", "ARCANINE", "EXEGGUTOR", "PIDGEOT", "ALAKAZAM", "BLASTOISE"],
        2: ["RHYDON", "GYARADOS", "ARCANINE", "PIDGEOT", "ALAKAZAM", "VENUSAUR"],
        3: ["RHYDON", "EXEGGUTOR", "GYARADOS", "PIDGEOT", "ALAKAZAM", "CHARIZARD"],
    },
}
