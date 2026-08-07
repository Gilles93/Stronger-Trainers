# Stronger Trainers

Gym leaders in Gen 1 famously turn up with two Pokémon and lose to a single
well-levelled starter. This mod gives them full six-Pokémon teams with proper
movesets, lets you agree the battle format before the fight, and teaches the AI
to actually look at how much damage its moves do.

For the [Pokémon Gen 1 Recompilation](https://github.com/bryanthaboi/gen1recomp).
Needs engine 0.1.0 or newer (tested on 0.1.72), mod API 2. Works on Red, Blue
and Yellow.

## Short version

Six-Pokémon boss teams with real movesets, a pick-your-format gym battle
system, and a fair-play AI that estimates damage. Everything is switchable from
the MODS menu.

## What it changes

### Bosses field real teams

There are 39 authored rosters covering 204 Pokémon. Every gym leader that had
two to five now has six, and so do the Elite Four, the Champion, Giovanni's
three fights and the Celadon Chief.

| Leader | Vanilla | With this mod |
| --- | --- | --- |
| Brock | Geodude 12, Onix 14 | Geodude 14, Sandshrew 14, Rhyhorn 15, Kabuto 16, Graveler 16, Onix 19 |
| Misty | Staryu 18, Starmie 21 | Psyduck 20, Horsea 20, Shellder 21, Staryu 21, Poliwhirl 22, Starmie 24 |
| Lt. Surge | 3, ace 24 | Voltorb 22, Pikachu 22, Magnemite 23, Electrode 25, Magneton 25, Raichu 27 |
| Erika | 3, ace 29 | Weepinbell 28, Gloom 28, Tangela 29, Exeggcute 29, Victreebel 31, Vileplume 32 |
| Koga | 4, ace 43 | Koffing 41, Golbat 42, Venomoth 43, Arbok 44, Muk 44, Weezing 46 |
| Sabrina | 4, ace 43 | Mr. Mime 42, Venomoth 42, Kadabra 43, Hypno 44, Exeggutor 44, Alakazam 46 |
| Blaine | 4, ace 47 | Ponyta 44, Growlithe 45, Magmar 46, Rapidash 47, Ninetales 47, Arcanine 50 |
| Giovanni | 5, ace 50 | Dugtrio 47, Marowak 48, Persian 49, Nidoqueen 50, Nidoking 51, Rhydon 53 |

The Elite Four:

| Lorelei (ace 59) | Bruno (ace 61) | Agatha (ace 62) | Lance (ace 65) |
| --- | --- | --- | --- |
| Seadra 55 | Onix 56 | Haunter 57 | Dragonair 59 |
| Dewgong 56 | Hitmonlee 57 | Golbat 58 | Dragonair 60 |
| Cloyster 56 | Hitmonchan 57 | Arbok 59 | Gyarados 61 |
| Slowbro 57 | Primeape 58 | Weezing 60 | Aerodactyl 62 |
| Jynx 57 | Golem 59 | Muk 60 | Dragonite 63 |
| Lapras 59 | Machamp 61 | Gengar 62 | Dragonite 65 |

Every one of them carries a hand-picked four-move set. Hitmonchan gets the full
elemental punch spread, Slowbro gets Amnesia, Aerodactyl gets Sky Attack, and
Lance's second Dragonite opens with Hyper Beam.

The Champion fields Pidgeot 63, Alakazam 63 and Rhydon 64 whatever you did. The
last three slots depend on your starter, since he still counter-picks:

| You chose | Slots 4 to 6 |
| --- | --- |
| Charmander | Arcanine 65, Exeggutor 65, Blastoise 68 |
| Squirtle | Gyarados 65, Arcanine 65, Venusaur 68 |
| Bulbasaur | Exeggutor 65, Gyarados 65, Charizard 68 |

All 204 slots were validated against the ROM's own level-up and TM/HM tables,
including moves inherited from a pre-evolution, so a Graveler really can carry
the Rock Throw it learned as a Geodude. Nothing knows a move it couldn't
legitimately have, and nothing is a stat-stick with no way to attack.

Rival battles scale with your own roster rather than jumping straight to six.
The optional Oak's-lab battle stays one-on-one, because you own a single level 5
starter at that point and a filled party would be unwinnable rather than hard.

### Choose your gym battle format

Before you earn a badge, talking to a leader now runs their dialogue, then a
"How many POKéMON each?" prompt, then a screen where you pick your team, and
then the battle.

The number is how many the leader brings, anywhere from 2 to 6, and the full
range is always offered whatever the size of your party. Its ace is always among
them and the rest are drawn at random, so even a 2v2 against Brock means facing
that Onix.

You then pick your own side from the party screen one at a time, in send-out
order, so your first pick leads. Each round lists only the Pokémon still
unpicked. Pressing B undoes your last pick, or backs out of the encounter
altogether from the format prompt, so you can always leave to heal. If the
format takes everything you have standing there is nothing to choose, so it
skips the pick screen rather than making you confirm the inevitable.

Losing blacks you out exactly as Gen 1 would, even with healthy Pokémon sitting
in reserve. A small format is a real commitment.

### An AI that thinks

Gen 1's trainer AI scores each move from a base of 10 and takes the lowest. All
three of its passes together only discourage a status move that would fail,
nudge a few effects on one turn, and add or subtract 1 for type effectiveness.
Nothing in there estimates damage, reads HP, or weighs accuracy.

This adds a fourth scoring pass that does:

- Damage and KO detection, using the game's own formula, so a 120-power neutral
  move stops losing out to a 40-power super-effective one and a move that
  finishes your Pokémon actually gets taken.
- Accuracy weighting, valuing expected damage rather than raw power, so it stops
  gambling on Horn Drill and Blizzard when a reliable move wins.
- Self-preservation. It won't set up while it's dying, and it heals at most
  twice per Pokémon and only below half HP, so it can't stall you out.
- Sensible status use. No re-paralysing, no re-sleeping, and no status wasted on
  a target that already has one.

It plays fair. It reads your HP at the resolution of the on-screen HP bar, which
is 48 pixels wide, and never looks at your move list, stats or DVs. It knows
what an opponent sitting across the table from you could see, and nothing more.

Some things are deliberately left out because they make Gen 1 miserable rather
than hard: re-sleeping a sleeping target, chasing Blizzard freezes, Wrap and
Fire Spin lock-outs, the Hyper Beam no-recharge-on-KO trick, and Explosion spam.
Each of those is suppressed on purpose, not merely left unrewarded.

It defaults to bosses only, so route trainers stay as dumb as Gen 1 intended.

### Ordinary trainers

Everyone else keeps their own species but gets a proportional level bump, and
parties shorter than a configurable minimum get padded out with more of that
trainer's own Pokémon. A Bug Catcher gains another Caterpie rather than
something off-theme.

## Options

Eight rows under MODS > Stronger Trainers. They're read live, so a change
applies to the very next battle with no restart needed.

| Row | Default | Effect |
| --- | --- | --- |
| `BOSS TEAMS` | ON | Off reverts bosses to vanilla rosters with the ordinary level bump |
| `BOSS MOVESETS` | ON | Off keeps the six-mon teams but uses each Pokémon's normal level-up moves |
| `GYM FORMAT CHOICE` | ON | Off skips the format picker; gyms go straight to the full six |
| `SMART AI` | ON | The extra scoring pass |
| `SMART AI FOR` | BOSSES | Set to EVERYONE to extend it to all 47 trainer classes |
| `BOSS LEVEL BONUS` | 0 | Flat levels on top of the authored boss levels, up to +20 |
| `TRAINER LEVEL %` | 15 | Level bump for non-boss trainers. 0 leaves them alone |
| `MIN PARTY SIZE` | 3 | Pads short ordinary parties up to this |

If it bites too hard early on, try `TRAINER LEVEL %` at 10 and `MIN PARTY SIZE`
at 2. If you want a real wall, `BOSS LEVEL BONUS` +5 with `TRAINER LEVEL %` at
25.

## Installation

Drop the `STRONGER_TRAINERS` folder into your `mods/` directory, or import the
zip from the launcher. New mods are enabled by default, so restart and it's
live.

Where `mods/` lives depends on how you launch the game, which catches people
out:

| How you launch | Mods folder |
| --- | --- |
| The packaged `gen1recomp.exe` | `%APPDATA%\pokemon-love2d\mods` |
| `love.exe` pointed at a source folder | `%APPDATA%\LOVE\pokemon-love2d\mods` |

A fused LÖVE executable drops the `LOVE\` path segment, so those are two
genuinely separate directories with separate mod sets. If you use both, install
to both. On macOS and Linux the equivalents are
`~/Library/Application Support/` and `~/.local/share/`.

## Compatibility

Trainer Rematch works alongside this. Rematches use the vanilla rosters, since
this mod builds its teams as each battle begins.

Modern Kanto is fully compatible and better together. Turn its `SMART AI` on,
since it ships off: it fixes dual-type effectiveness in the vanilla scoring
pass, while this mod adds damage and HP reasoning in a separate pass. Both run.

Other trainer mods compose too. Non-boss parties get the level treatment applied
to whatever the other mod produced rather than being overwritten.

There are no save changes. Your file works with or without this mod, and
disabling it mid-playthrough is safe.

## Known behaviour

Prize money goes up. Gen 1 pays base money times the last Pokémon's level, so
higher-level trainers are richer. That's the vanilla formula, untouched.

Rosters are built as each battle starts, so trainer data still reads vanilla
outside battle. A mod that inspects it beforehand, like a rematch level-gap
warning, will quote the original levels. The battle itself is correct.

The mod needs the `engine_internals` permission, because it reaches for the
party screen, the text box and the map script table.

## Credits

Trainer, learnset, TM/HM and move tables come from
[pret/pokered](https://github.com/pret/pokered) by way of the recomp's ROM
import. The boss rosters are authored, generated by a validator that refuses any
unknown species, unknown move, or move a species cannot legally learn at that
level.
