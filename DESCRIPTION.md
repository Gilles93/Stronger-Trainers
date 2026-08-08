# Stronger Trainers

Gen 1's trainers were built around a two-Pokémon gym leader and a party you
outgrow by Cerulean. This fills them out.

Every gym leader, both Elite Four rooms' worth of opponents, the Champion,
Giovanni and the rivals field six Pokémon with hand-picked movesets and coverage
moves for the types that used to wall them. Every other trainer gets a level bump
and a fuller party. The AI estimates damage, weighs accuracy, and switches when
the matchup goes against it.

Red, Blue and Yellow each get their own rosters.

## Short version

Harder trainers, real teams, still Gen 1. Nothing here does anything a player
couldn't: no illegal moves, no invented stats, no reading your party.

## Boss teams

39 rosters, 234 slots. Brock opens with six Rock Pokémon at 14 to 19 and closes
on an Onix with Rock Slide, Earthquake, Body Slam and Toxic. Sabrina's Alakazam
lands at 56. Lance brings two Dragonite at 62 and 65, and the Champion's ace hits
71.

Each team keeps its type identity absolutely, and answers its own weaknesses with
moves rather than off-theme Pokémon. Brock's Rhyhorn carries Thunderbolt for the
Squirtle that used to walk through him; his Kabuto carries Ice Beam for the
Bulbasaur. Misty's Poliwhirl has Earthquake and her Psyduck has Dig, so an
Electric lead isn't a free win. Koga's Golbat can't be touched by Ground at all.

Coverage is spread across the team, not piled onto the ace, so switching in a
hard counter meets a different answer each time.

Movesets are all legal. Every slot is checked against the ROM's own learnsets and
TM/HM tables, counting moves inherited from a pre-evolution, and nothing carries a
move it couldn't know at that level.

## Levels

The levels are calculated. The mod's own trainer scaling means you bank a lot more
experience than vanilla ever gave out, and experience compounds, so boss levels
set by hand drift out of true within a few badges. Instead the game's route order
is walked, every trainer paid out at this mod's settings using the engine's
experience formula, and the growth curve inverted to find the level you'll
actually be. Bosses sit above that by a margin that ramps from +2 at Brock to +14
at the Champion.

Yellow is calculated separately. Its trainer placements and its experience economy
aren't Red's, and vanilla Yellow's late gyms are steeper. No fight ever comes out
below what that version already fielded, which turned out to matter: Yellow's
Koga, Sabrina, Blaine and Giovanni were all higher in the unmodded game than the
levels this mod used to give them.

Yellow's Brock is gentler on purpose, the same way the real game makes him
gentler, because a Pikachu start has nothing for a Rock gym.

## Yellow's rival

His party layout isn't Red's. Yellow gives him three `OPP_RIVAL1` parties where
Red gives nine, and they're three different battles rather than three starter
variants. He fights with the Eevee line, evolving into Jolteon, Flareon or
Vaporeon along whichever branch the game settled at Oak's lab, with Sandslash,
Alakazam, Exeggutor and the rest behind it.

## Gym battle formats

Before you've earned a gym's badge, talking to the leader offers a choice of 2
through 6. That's how many the leader brings; your own party is narrowed to match
and restored afterwards. The ace is always present, the rest are drawn at random,
and the range is always the full 2 to 6 whatever the size of your own team.

## An AI that thinks

Vanilla Gen 1 scores moves from a base of 10 and its three layers only manage:
discourage a status move that would fail, nudge a couple of effects, and ±1 for
type effectiveness. Nothing estimates damage, reads HP or considers accuracy.

This adds all three. Expected damage as a share of the target's bar, a real bonus
for a move that finishes the job weighted by how likely it is to land, Hyper
Beam's recharge counted as the cost it is, healing capped at twice per Pokémon and
only when actually hurt, and no setting up while dying.

It reads HP at the resolution of the 48-pixel bar you can see, and never looks at
your move list, stats or DVs.

Some things are left out on purpose, because they're what makes Gen 1 miserable
rather than hard: re-sleeping a sleeping target, chasing Blizzard freezes, Wrap
and Fire Spin lock-outs, the Hyper Beam no-recharge-on-KO trick, and Explosion
spam.

## Switching

Bosses switch to whichever of their team the matchup favours. No Gen 1 trainer
does this: the engine's own routine takes the first unfainted Pokémon regardless.

It decides on species types, both sides, which is what you can see across the
field. Switching spends the boss's turn, so you get a free move each time. There's
a cap per fight, one turn of grace after every send-out so it can't ping-pong, and
it won't rotate away from a Pokémon that can already finish you, or out of a
matchup it's winning.

`BOSS SWITCHING` off restores vanilla behaviour exactly.

## Ordinary trainers

Levels rise by a configurable percentage, 15% by default. Short parties are filled
out with a different Pokémon sharing one of the trainer's own types, drawn only
from species that appear in wild encounter tables. A lone-Onix Hiker brings a
Rhyhorn and a Geodude; a Sailor's Shellder brings a Psyduck and a Seel.

Picks favour the closest type match and skip anything whose earliest wild
appearance sits well above that trainer's level, so an early Youngster can't open
with a Tauros. The same trainer always brings the same Pokémon.

## No more overdue pre-evolutions

212 of the 999 vanilla party slots hold a Pokémon past the level it would have
evolved at, and the level bump pushes that to 326. Ordinary trainers now field the
stage their level has earned. Stone evolutions have no level of their own, so
`STONE EVO FROM LV` invents one, 30 by default, and 0 leaves stone users alone.

The authored boss rosters are exempt, since their stages are chosen deliberately.

## Slower levelling

`XP GAIN %` sits at 75. Larger, evolved trainer parties pay out more experience in
Gen 1, so without trimming it you'd level faster than vanilla while fighting
harder trainers. Stat experience is untouched: a Pokémon levels more slowly but is
exactly as strong at any given level. This lengthens the game rather than quietly
weakening your team.

It composes with other experience mods instead of overriding them. QoL Toggles'
`EXP x2` with `XP GAIN %` at 50 is just the normal rate.

## Options

Fourteen rows under MODS > Stronger Trainers, all live: a change applies to the
next battle, no restart.

| Row | Default | What it does |
| --- | --- | --- |
| `BOSS TEAMS` | ON | Off reverts bosses to vanilla rosters with the ordinary level bump |
| `BOSS MOVESETS` | ON | Off keeps six-mon teams but uses normal level-up moves |
| `GYM FORMAT CHOICE` | ON | Off skips the picker; gym battles go straight to six |
| `SMART AI` | ON | The damage and accuracy layer |
| `SMART AI FOR` | BOSSES | EVERYONE extends it to all 47 trainer classes |
| `BOSS SWITCHING` | ON | Bosses rotate to answer a bad matchup |
| `SWITCHES PER FIGHT` | 2 | How often one boss may rotate. 0 is the same as off |
| `BOSS LEVEL BONUS` | 0 | Flat levels on top of the calculated ones, up to +20 |
| `TRAINER LEVEL %` | 15 | Level bump for non-boss trainers |
| `MIN PARTY SIZE` | 3 | Pads short ordinary parties up to this |
| `PAD WITH VARIETY` | ON | Off pads with copies instead of new species |
| `EVOLVE PRE-EVOS` | ON | Walks ordinary trainers up to their earned stage |
| `STONE EVO FROM LV` | 30 | Level a stone evolution counts from |
| `XP GAIN %` | 75 | Percentage of the normal payout |

## Installation

Drop the `stronger_trainers` folder into your `mods/` directory, or import the zip
from the launcher. New mods are enabled by default, so restart and it's live.

Where `mods/` lives depends on how you launch the game, which catches people out:

| How you launch | Mods folder |
| --- | --- |
| The packaged `gen1recomp.exe` | `%APPDATA%\pokemon-love2d\mods` |
| `love.exe` pointed at a source folder | `%APPDATA%\LOVE\pokemon-love2d\mods` |

A fused LÖVE executable drops the `LOVE\` path segment, so those are two separate
directories with separate mod sets. If you use both, install to both. On macOS and
Linux the roots are `~/Library/Application Support/` and `~/.local/share/`.

## Compatibility

Trainer Rematch works alongside this. Rematches use the vanilla rosters, since
this mod builds its teams as each battle begins.

Modern Kanto works too, and its own `SMART AI` can be left on; both scoring layers
run, additively. Other trainer mods compose as well: their rosters still get the
level treatment rather than being overwritten.

Any experience mod multiplies with `XP GAIN %` rather than fighting it.

## Known behaviour

- Prize money rises. Gen 1 pays base money times the last Pokémon's level, so
  higher-level trainers are richer. Vanilla formula, not something this changes.
- Rosters are built as each battle starts, so `data.trainers` reads vanilla
  outside battle. A mod that inspects trainer data ahead of time quotes the
  original levels; the battle itself is correct.
- The level curve assumes the default options. Raising `TRAINER LEVEL %` well
  above 15 puts you ahead of it again, and `BOSS LEVEL BONUS` is the answer.
- Explosion, Selfdestruct and the trapping moves are absent from every authored
  team. The AI scores them down deliberately, so authoring one wastes a slot.

## Credits

pret/pokered and pret/pokeyellow, for the trainer, learnset and TM tables this is
authored against.

MIT licensed.
