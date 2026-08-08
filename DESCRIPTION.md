# Stronger Trainers

Gen 1's gym leaders bring two or three Pokémon and forget to attack. This fixes
that.

Every gym leader, the Elite Four, the Champion, Giovanni and the rivals field six
Pokémon with proper movesets and real answers to the types that used to walk
through them. Everyone else gets a level bump and a fuller party. The AI actually
plays: it works out which move hurts you most, heals when it's hurt, and switches
when the matchup turns against it.

Red, Blue and Yellow are all supported.

## Short version

Harder trainers, real teams, still Gen 1. Nothing here does anything a player
couldn't do: no illegal moves, no invented stats, no peeking at your party.

## Boss fights

Brock opens with six Rock Pokémon and closes on an Onix with Rock Slide and
Toxic. Sabrina's Alakazam lands at 56. Lance brings two
Dragonite, and the Champion's ace hits 71.

Each team still keeps its type, and the later ones answer their own weaknesses
with moves rather than off-theme Pokémon. Koga's Muk carries Thunderbolt, his
Weezing adds Fire Blast, and his Golbat can't be touched by Ground at all.
Answers are spread around the team instead of saved for the ace, so switching in a
hard counter meets something different each time.

The early gyms are left alone deliberately. Brock and Misty stick to their own
type, Surge gets one move outside his, Erika two, and full coverage starts at
Koga — the first leader you meet after Celadon, which is where you can build that
kind of team yourself. Brock is still a wall; you just beat him with a type
advantage the way the gym intends.

Levels are tuned to where you'll actually be by the time you get there, which
means the later gyms hit as hard as the early ones did. Yellow is tuned separately.
Its Brock is gentler, the same way the real game makes him gentler, because a
Pikachu start has nothing for a Rock gym.

## Yellow's rival

He fights with his Eevee, evolved into Jolteon, Flareon or Vaporeon depending on
how your early meetings with him went, backed by Sandslash, Alakazam, Exeggutor
and the rest. Not a borrowed starter.

## Pick your gym battle

Before you've earned a gym's badge, talking to the leader offers a choice of 2
through 6. That's how many they bring; your own party is narrowed to match and
restored afterwards. Their ace is always present and the rest are drawn at random,
so the same gym plays differently twice.

## An AI worth beating

Vanilla Gen 1 trainers barely think. They don't estimate damage, don't look at your
HP, and don't care whether a move is likely to land.

This one does all three. It picks the move that actually does the most, values a
finishing blow properly, won't fish for a low-accuracy gamble, heals when it's hurt instead
of at full health, and won't set up while it's dying.

Bosses also switch. Send in a hard counter and a leader may rotate to something
that handles it. That costs them their turn, so you get a free move out of it, and
there's a cap per fight so nobody dances around you. It won't rotate away from a
Pokémon that's about to knock you out, or out of a matchup it's already winning.

It plays fair. It reads what you could see across the field and nothing more. The
tactics that make Gen 1 miserable rather than hard are left out on purpose: no
re-sleeping a sleeping Pokémon, no chasing Blizzard freezes, no Wrap lock-outs, no
Explosion spam.

## Everyone else

Ordinary trainers get a configurable level bump, 15% by default, and short parties
get filled out with something new instead of a second copy of what they already
had. A lone-Onix Hiker brings a Rhyhorn and a Geodude. A Sailor's Shellder brings a
Psyduck and a Seel. It always suits the trainer, and it's always something you
could have caught yourself by that point in the game.

They also stop holding Pokémon that should have evolved ages ago, which Gen 1 does
constantly. A level 16 Bulbasaur is an Ivysaur now.

## Slower levelling

Experience is trimmed to 75%. Bigger, evolved trainer parties pay out more, so
without this you'd end up levelling faster than vanilla while fighting harder
opponents. Stat experience is untouched: your Pokémon are exactly as strong at any
given level, the game just runs longer. It lengthens the game rather than quietly
weakening your team.

## Options

Fourteen rows under MODS > Stronger Trainers, all live — a change applies to the
next battle, no restart.

| Row | Default | What it does |
| --- | --- | --- |
| `BOSS TEAMS` | ON | Off gives bosses their vanilla teams back |
| `BOSS MOVESETS` | ON | Off keeps six-mon teams but uses their normal moves |
| `GYM FORMAT CHOICE` | ON | Off skips the picker; gym battles go straight to six |
| `SMART AI` | ON | The smarter move choice |
| `SMART AI FOR` | BOSSES | EVERYONE gives it to every trainer in the game |
| `BOSS SWITCHING` | ON | Bosses rotate to answer a bad matchup |
| `SWITCHES PER FIGHT` | 2 | How often one boss may rotate. 0 is the same as off |
| `BOSS LEVEL BONUS` | 0 | Extra levels for every boss, up to +20 |
| `TRAINER LEVEL %` | 15 | Level bump for everyone else |
| `MIN PARTY SIZE` | 3 | Fills short parties up to this |
| `PAD WITH VARIETY` | ON | Off fills them with copies instead of new Pokémon |
| `EVOLVE PRE-EVOS` | ON | Trainers field the stage their level has earned |
| `STONE EVO FROM LV` | 30 | When stone evolutions count |
| `XP GAIN %` | 75 | Percentage of the normal experience |

## Installation

Drop the `stronger_trainers` folder into your `mods/` directory, or import the zip
from the launcher. New mods are enabled by default, so restart and it's live.

Where `mods/` lives depends on how you launch the game, which catches people out:

| How you launch | Mods folder |
| --- | --- |
| The packaged `gen1recomp.exe` | `%APPDATA%\pokemon-love2d\mods` |
| `love.exe` pointed at a source folder | `%APPDATA%\LOVE\pokemon-love2d\mods` |

Those are two separate directories with separate mod sets. If you use both, install
to both. On macOS and Linux the roots are `~/Library/Application Support/` and
`~/.local/share/`.

## Compatibility

Trainer Rematch works alongside this; rematches use the vanilla teams. Modern
Kanto works too, and you can leave its own `SMART AI` on. Other trainer mods are
fine as well — their teams still get the level treatment. Any experience mod stacks
with `XP GAIN %` rather than fighting it.

## Worth knowing

- Trainers are richer. Gen 1 pays prize money off the last Pokémon's level, so
  higher levels mean bigger payouts. Original formula, untouched.
- If you grind a lot you'll get ahead of the curve. `BOSS LEVEL BONUS` is the fix.

## Credits

pret/pokered and pret/pokeyellow.

MIT licensed.
