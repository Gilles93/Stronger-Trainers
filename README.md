# Stronger Trainers

A difficulty mod for the Gen 1 recomp. Gym leaders, the Elite Four, the Champion,
Giovanni and the rivals field six Pokémon with proper movesets and answers for the
types that used to walk through them. Everyone else gets a level bump and a fuller
party.

Works with Red, Blue and Yellow.

## Install

Drop the folder into your `mods/` directory, or import the zip from the launcher.
Mods are on by default, so restart and it's live.

`mods/` isn't in the same place for both ways of launching:

| Launching with | Mods folder |
| --- | --- |
| `gen1recomp.exe` | `%APPDATA%\pokemon-love2d\mods` |
| `love.exe` and a source folder | `%APPDATA%\LOVE\pokemon-love2d\mods` |

Those are two separate folders with separate mod sets. Install to both if you use
both. On macOS and Linux the roots are `~/Library/Application Support/` and
`~/.local/share/`.

## What you're up against

| Leader | Team |
| --- | --- |
| Brock | Geodude 14, Sandshrew 14, Rhyhorn 15, Kabuto 16, Graveler 16, Onix 19 |
| Misty | Psyduck 23, Shellder 23, Seadra 24, Poliwhirl 25, Staryu 25, Starmie 28 |
| Lt. Surge | Voltorb 30, Pikachu 30, Magnemite 31, Electrode 32, Magneton 32, Raichu 35 |
| Erika | Tangela 38, Gloom 38, Weepinbell 39, Exeggutor 40, Victreebel 40, Vileplume 43 |
| Koga | Koffing 45, Golbat 45, Venomoth 46, Arbok 47, Muk 47, Weezing 50 |
| Sabrina | Mr. Mime 51, Venomoth 51, Kadabra 52, Hypno 53, Exeggutor 53, Alakazam 56 |
| Blaine | Ponyta 55, Growlithe 55, Magmar 56, Rapidash 57, Ninetales 57, Arcanine 60 |
| Giovanni | Dugtrio 56, Marowak 56, Persian 57, Nidoqueen 58, Nidoking 58, Rhydon 61 |

Then Lorelei 67, Bruno 67, Agatha 68, Lance 69 on two Dragonite, and the Champion
at 71.

Yellow runs a few levels apart in places. Its Brock is easier, because a Pikachu
start has nothing for a Rock gym, and its Koga hits a little harder.

Every gym team is still its own type, but the later ones can hurt what used to
wall them. Koga's Muk carries Thunderbolt, his Weezing adds Fire Blast, and his
Golbat can't be touched by Ground at all. The answers are spread around the team
rather than saved for the ace, so switching in a counter runs into something
different each time.

The early gyms don't do that. Brock and Misty stick to their own type, Lt. Surge
gets one move outside his and Erika two. Coverage arrives from Koga onward, which
is when you've been through Celadon and can build the same kind of team yourself.
Brock is still a wall, you just answer him with a type advantage the way the gym
intends.

Movesets are all legitimate. Nothing carries a move it couldn't have learned.

## Rivals

Every rival fight is filled out. The Oak's lab battle stays one-on-one, since you
own a single level 5 starter there. Route 22 brings three, Cerulean five, and
everything from the S.S. Anne onward six.

Yellow's rival fights with his Eevee, evolved into Jolteon, Flareon or Vaporeon
depending on how your early meetings went, with Sandslash, Alakazam and Exeggutor
behind it.

## Pick your gym battle

Before you've earned a gym's badge, talking to the leader lets you choose how many
Pokémon they bring, anywhere from 2 to 6. Your own party is narrowed to match for
the fight and put back afterwards. Their ace is always in there.

The choice is always 2 through 6, because it's how many the *leader* brings, not
how many you own.

## Trainers that play properly

The AI estimates what each move will actually do, so it picks the one that hurts
you most instead of rolling a dice. It weighs accuracy, so it won't fish for a
low-percentage gamble. It heals when it's hurt rather than at full HP, and it won't set up while
it's dying.

Bosses also switch now. Send in a hard counter and a leader may rotate to
something that handles it. It costs them the turn, so you get a free move out of
it, and there's a limit per fight so nobody dances around you.

It doesn't cheat. It reads what you could see across the field and nothing else,
and the genuinely miserable Gen 1 tactics are left out: no re-sleeping a sleeping
Pokémon, no Wrap lock-outs, no Explosion spam.

## Everyone else

Ordinary trainers get a level bump, and short parties get filled out with
something new rather than a second copy of what they already had. A lone-Onix
Hiker brings a Rhyhorn and a Geodude. A Sailor's Shellder brings a Psyduck and a
Seel. It's always something that fits the trainer, and always something you could
have caught yourself by that point.

They also stop fielding Pokémon that should have evolved ages ago. A level 16
Bulbasaur is an Ivysaur.

Experience is trimmed to 75% out of the box, because bigger trainer parties pay
out more and you'd otherwise level faster than vanilla while fighting harder
opponents. Stat experience is untouched, so your Pokémon are exactly as strong at
any given level — the game just runs longer.

## Options

Fourteen rows under MODS > Stronger Trainers. They apply to the next battle, no
restart needed.

| Row | Default | What it does |
| --- | --- | --- |
| `BOSS TEAMS` | ON | Off gives bosses their vanilla teams back |
| `BOSS MOVESETS` | ON | Off keeps the six-mon teams but uses their normal moves |
| `GYM FORMAT CHOICE` | ON | Off skips the picker; gym battles go straight to six |
| `SMART AI` | ON | The smarter move choice |
| `SMART AI FOR` | BOSSES | EVERYONE gives it to every trainer in the game |
| `BOSS SWITCHING` | ON | Bosses rotate to answer a bad matchup |
| `SWITCHES PER FIGHT` | 2 | How often one boss may rotate. 0 is the same as off |
| `BOSS LEVEL BONUS` | 0 | Extra levels for every boss, up to +20 |
| `TRAINER LEVEL %` | 15 | Level bump for everyone else. 0 leaves them alone |
| `MIN PARTY SIZE` | 3 | Fills short parties up to this |
| `PAD WITH VARIETY` | ON | Off fills them with copies instead of new Pokémon |
| `EVOLVE PRE-EVOS` | ON | Trainers field the stage their level has earned |
| `STONE EVO FROM LV` | 30 | When stone evolutions count. 0 leaves them alone |
| `XP GAIN %` | 75 | Percentage of the normal experience. 100 turns it off |

Too much early on? Drop `TRAINER LEVEL %` to 10 and `MIN PARTY SIZE` to 2, or turn
`EVOLVE PRE-EVOS` off for the Bug Catcher stretch. Want a wall? `BOSS LEVEL BONUS`
+5 with `TRAINER LEVEL %` 25.

If you grind a lot you'll get ahead of the curve. `BOSS LEVEL BONUS` is the fix.

## Notes

- Trainers are richer. Gen 1 pays prize money off the last Pokémon's level, so
  higher levels mean bigger payouts. That's the original formula, untouched.
- Trainer Rematch works alongside this. Rematches use the vanilla teams.
- Modern Kanto works too, and you can leave its own `SMART AI` on.
- Other experience mods stack with `XP GAIN %` rather than fighting it. QoL
  Toggles' `EXP x2` against 50% here is just the normal rate.

## Licence

MIT. See `LICENSE`.
