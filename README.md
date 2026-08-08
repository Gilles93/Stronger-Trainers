# Stronger Trainers

A difficulty mod for the Gen 1 recomp. Gym leaders, the Elite Four, the Champion,
Giovanni and the rivals field six Pokémon with hand-picked movesets and real type
coverage. Everyone else gets a level bump and a fuller party.

Red, Blue and Yellow are all supported, each with its own rosters.

## Install

Drop the folder into your `mods/` directory, or import the zip from the launcher.
Mods are on by default, so restart and it's live.

`mods/` isn't in the same place for both ways of launching:

| Launching with | Mods folder |
| --- | --- |
| `gen1recomp.exe` | `%APPDATA%\pokemon-love2d\mods` |
| `love.exe` and a source folder | `%APPDATA%\LOVE\pokemon-love2d\mods` |

A fused LÖVE binary drops the `LOVE\` segment, so those are two separate folders
with separate mod sets. Install to both if you use both. On macOS and Linux the
roots are `~/Library/Application Support/` and `~/.local/share/`.

## Boss teams

39 rosters covering the eight leaders, the Elite Four, the Champion, Giovanni's
three fights and every rival battle.

| Leader | Red / Blue | Yellow |
| --- | --- | --- |
| Brock | Geodude 14, Sandshrew 14, Rhyhorn 15, Kabuto 16, Graveler 16, Onix 19 | ace 17 |
| Misty | Psyduck 23, Shellder 23, Seadra 24, Poliwhirl 25, Staryu 25, Starmie 28 | same |
| Lt. Surge | Voltorb 30, Pikachu 30, Magnemite 31, Electrode 32, Magneton 32, Raichu 35 | same |
| Erika | Tangela 38, Gloom 38, Weepinbell 39, Exeggutor 40, Victreebel 40, Vileplume 43 | same |
| Koga | Koffing 45, Golbat 45, Venomoth 46, Arbok 47, Muk 47, Weezing 50 | ace 51 |
| Sabrina | Mr. Mime 51, Venomoth 51, Kadabra 52, Hypno 53, Exeggutor 53, Alakazam 56 | same |
| Blaine | Ponyta 55, Growlithe 55, Magmar 56, Rapidash 57, Ninetales 57, Arcanine 60 | ace 59 |
| Giovanni | Dugtrio 56, Marowak 56, Persian 57, Nidoqueen 58, Nidoking 58, Rhydon 61 | same |

Then Lorelei 67, Bruno 67, Agatha 68, Lance 69 on two Dragonite, and the Champion
at 71.

Yellow's Brock is easier on purpose. Yellow starts you on a Pikachu that a Rock
gym walls outright, and the game itself compensates: vanilla Yellow's Brock is
10/12 where Red's is 12/14.

Movesets are Gen 1 legal. All of them are checked against the ROM's own learnsets
and TM lists, pre-evolution moves included, so a Graveler can carry the Rock
Throw it picked up as a Geodude.

## Type coverage

Every gym team is still its own type. What changed is that they can hurt the
things that used to wall them. Brock's Rhyhorn carries Thunderbolt and his Kabuto
carries Ice Beam, both legal TMs, and it's still six Rock Pokémon. Misty answers
Electric with Earthquake on Poliwhirl and Dig on Psyduck. Koga's Golbat ignores
Ground outright and his Arbok answers it with an Earthquake of its own.

Coverage is spread across the team instead of stacked on the ace, so switching in
a counter runs into a different answer each time.

## Levels

Boss levels are calculated rather than chosen. This mod raises every ordinary
trainer by 15%, pads short parties and evolves overdue pre-evolutions, so you
bank far more experience than vanilla hands out, and that compounds: a bigger
payout raises your level, which raises the payout of the next fight. Setting
bosses to vanilla plus a few levels, which is what earlier versions did, is why
the later gyms kept going soft.

So the route order gets walked instead. Every trainer is paid out at this mod's
own settings using the game's experience formula, and the growth curve is
inverted to find the level you'll actually be standing there. Each boss sits
above that by a margin that ramps from +2 at Brock to +14 at the Champion.
Yellow is calculated separately, because its trainers and its experience economy
aren't Red's.

No fight is ever below what that version already fielded. That mattered more than
expected: vanilla Yellow's Koga, Sabrina, Blaine and Giovanni were all *higher*
than the levels this mod used to give them, so Yellow players were getting weaker
leaders than the unmodded game.

The curve assumes the default option values and that you fight most of what you
walk past. Push `TRAINER LEVEL %` well past 15 and you'll outpace it again;
`BOSS LEVEL BONUS` is the dial for that.

## Gym battle formats

Before you have a gym's badge, talking to the leader lets you pick how many
Pokémon they bring, 2 through 6. Your own party is narrowed to match for the
fight and put back afterwards. The leader's ace is always in there.

The range is always the full 2 to 6, because the number is how many the *leader*
brings, not how many you own.

## Bosses switch

No Gen 1 trainer switches on purpose. The game's own routine grabs the first
unfainted Pokémon whatever the matchup, and only a few classes even roll for it.
Bosses now switch to whichever of their team the matchup favours.

It plays off what you can see, species types on both sides, never your move list
or your stats. The turn it costs is the trade: you get a free move every time a
boss rotates. There's a cap per fight, a turn of grace after every send-out so it
can't ping-pong, and it won't switch away from a Pokémon that can already finish
you. It won't rotate out of a matchup it's winning either.

This is the most opinionated thing in the mod, so it has its own row.
`BOSS SWITCHING` off gives you exact vanilla behaviour.

## Ordinary trainers

Levels go up by a configurable percentage. Parties shorter than `MIN PARTY SIZE`
get filled out with a *different* Pokémon sharing one of the trainer's types, so
a lone-Onix Hiker brings a Rhyhorn and a Geodude rather than a second Onix.

Only Pokémon that turn up in wild encounter tables are eligible, which is a
data-side way of saying "something he could have caught". No fossil, game corner
prize, gift Pokémon or legendary appears in a single wild table in Gen 1, so that
one rule keeps all of them out. Picks favour the closest type match and skip
anything whose earliest wild appearance is well above that trainer's level, so a
level 12 Youngster can't open with a Tauros.

The same trainer always brings the same Pokémon. A trainer who fielded something
different on every encounter would look broken rather than varied.

## Overdue pre-evolutions

Gen 1 leaves trainers holding pre-evolutions long past the level they'd have
evolved at. 212 of the 999 vanilla party slots are already overdue before this
mod touches anything, and the level bump takes that to 326. Ordinary trainers now
get the stage their level has earned, so a level 16 Bulbasaur is an Ivysaur.

The 39 authored boss rosters are exempt. Their stages are picked by hand, and
evolving them would take Lance from two Dragonite to four and give Blaine a
second Rapidash.

## Experience

`XP GAIN %` trims the payout, 75% out of the box. Bigger, evolved parties are
worth more experience in Gen 1, and without this you'd level faster than vanilla
while fighting harder trainers. Stat experience is left alone, so a Pokémon
levels more slowly but is exactly as strong at a given level.

It multiplies with other experience mods rather than overriding them. QoL
Toggles' `EXP x2` against 50% here is simply the normal rate.

## Options

Fourteen rows under MODS > Stronger Trainers. They read live, so a change applies
to the next battle without a restart.

| Row | Default | What it does |
| --- | --- | --- |
| `BOSS TEAMS` | ON | Off reverts bosses to vanilla rosters with the ordinary level bump |
| `BOSS MOVESETS` | ON | Off keeps the six-mon teams but uses each Pokémon's normal level-up moves |
| `GYM FORMAT CHOICE` | ON | Off skips the picker; gym battles go straight to six |
| `SMART AI` | ON | Damage and accuracy weighting on top of the vanilla AI |
| `SMART AI FOR` | BOSSES | EVERYONE extends it to all 47 trainer classes |
| `BOSS SWITCHING` | ON | Bosses rotate to answer a bad matchup. Off is vanilla |
| `SWITCHES PER FIGHT` | 2 | How often one boss may rotate. 0 is the same as off |
| `BOSS LEVEL BONUS` | 0 | Flat levels on top of the calculated ones, up to +20 |
| `TRAINER LEVEL %` | 15 | Level bump for non-boss trainers. 0 leaves them alone |
| `MIN PARTY SIZE` | 3 | Pads short ordinary parties up to this |
| `PAD WITH VARIETY` | ON | Off pads with copies of the trainer's own Pokémon instead |
| `EVOLVE PRE-EVOS` | ON | Walks ordinary trainers up to the stage their level earned |
| `STONE EVO FROM LV` | 30 | Level a stone evolution counts from. 0 leaves them alone |
| `XP GAIN %` | 75 | Percentage of the normal payout. 100 turns it off |

Too much early on? Drop `TRAINER LEVEL %` to 10 and `MIN PARTY SIZE` to 2, or
turn `EVOLVE PRE-EVOS` off for the Bug Catcher stretch. Want a wall?
`BOSS LEVEL BONUS` +5 with `TRAINER LEVEL %` 25.

## Notes

- Prize money goes up. Gen 1 pays base money times the last Pokémon's level, so
  higher-level trainers are richer. That's the vanilla formula.
- Rosters are built as each battle starts, so `data.trainers` still reads vanilla
  outside battle. A mod that checks trainer data ahead of time, like Trainer
  Rematch's level-gap warning, will quote the original levels. The battle itself
  is correct.
- Explosion, Selfdestruct and the trapping moves aren't authored anywhere. The AI
  scores them down on purpose, so a slot spent on one is a slot wasted.
- Modern Kanto works alongside this. Turn its `SMART AI` on too; both layers run.

Built against gen1recomp 0.1.72 and the 0.1.75 update, with data from Red, Blue
and Yellow ROMs.

## Licence

MIT. See `LICENSE`.
