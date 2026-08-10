# Stronger Trainers

Gen 1 gym leaders are too easy. This fixes that.

Every leader, the Elite Four, the Champion, Giovanni and all fourteen rival
fights field six Pokémon with hand-picked movesets. Everyone else gets a level
bump and a fuller party. The AI actually works out which move hurts you.

Red, Blue and Yellow.

## The gyms

| Leader | Team |
| --- | --- |
| Brock | Geodude 14, Sandshrew 14, Rhyhorn 15, Kabuto 16, Graveler 16, Onix 19 |
| Misty | Psyduck 23, Shellder 23, Seadra 24, Poliwhirl 25, Staryu 25, Starmie 28 |
| Lt. Surge | Voltorb 31, Pikachu 31, Magnemite 32, Electrode 33, Magneton 33, Raichu 36 |
| Erika | Tangela 38, Gloom 38, Weepinbell 39, Exeggutor 40, Victreebel 40, Vileplume 43 |
| Koga | Koffing 45, Golbat 45, Venomoth 46, Arbok 47, Muk 47, Weezing 50 |
| Sabrina | Mr. Mime 51, Venomoth 51, Kadabra 52, Hypno 53, Exeggutor 53, Alakazam 56 |
| Blaine | Ponyta 55, Growlithe 55, Magmar 56, Rapidash 57, Ninetales 57, Arcanine 60 |
| Giovanni | Dugtrio 56, Marowak 56, Persian 57, Nidoqueen 58, Nidoking 58, Rhydon 61 |

Then Lorelei 67, Bruno 68, Agatha 69, Lance 70 on two Dragonite, and your rival
at 71.

Those levels are worked out from where you'll actually be by the time you get
there, so the late gyms hit as hard as the early ones did. Yellow has its own
set. Its Brock is gentler, the same way the real game's is, because a Pikachu
start has nothing for a Rock gym.

Each gym keeps its type. The later ones answer their own weaknesses with moves
instead of off-theme Pokémon, and those answers sit on different members, so
switching in a counter meets something new each time. Koga's Muk carries
Thunderbolt, his Golbat can't be touched by Ground at all. Brock and Misty stay
pure, because at one badge you have a starter and no TMs.

One Pokémon carries a move it couldn't normally learn, on purpose. Ground is
immune to Electric, which left Surge's gym with no answer at all to a Diglett
caught in the cave next door. His Pikachu and his Raichu know Surf now, like
the Pokémon Stadium one. Fair warning: Raichu's one-shots any Ground type you
can field at three badges, so the obvious counter is the wrong plan.

## Pick your gym battle

Before you've earned a badge, the leader asks how many Pokémon each. Two to six.
You choose your own side from the party screen in send-out order, and it's
restored afterwards. Their ace is always in there, the rest are drawn at random,
so the same gym plays differently twice. Prize money scales with the size, so a
short fight isn't a shortcut.

## The AI

Vanilla trainers pick close to at random. They don't look at your HP, and
they'll happily use Bide while you set up. This one works out which move
actually does the most to you, heals when it's hurt rather than at full health,
won't set up while it's dying, and won't gamble on Horn Drill.

Bosses switch. Send in a hard counter and a leader may rotate to something that
handles it. That costs them the turn, so you get a free move, and the switch
lands first, so your attack hits whatever came in. There's a cap per fight, and
a Pokémon has to stand its ground for a turn before it can leave again.

It plays fair. It goes on type matchups and your HP bar, which is what anyone
sitting opposite could see, and nothing else. The tactics that make Gen 1
miserable rather than hard are left out: no re-sleeping, no Wrap lock-outs, no
Explosion spam.

## The things that aren't trainers

Fifteen battles in Kanto have no trainer behind them, and vanilla left all of
them where they were.

| Encounter | Was | Now |
| --- | --- | --- |
| Ghost Marowak, Pokémon Tower 6F | 30 | 46 — Earthquake, Body Slam, Ice Beam, Toxic |
| Snorlax, Route 12 | 30 | 48 — Body Slam, Earthquake, Rock Slide, Amnesia |
| Snorlax, Route 16 | 30 | 52 — Double-Edge, Earthquake, Rock Slide, Amnesia |
| Voltorb ×6, Power Plant | 40 | 46 — Thunderbolt, Swift, Thunder Wave, Selfdestruct |
| Electrode ×2, Power Plant | 43 | 50 — Thunderbolt, Swift, Thunder Wave, Explosion |
| Zapdos | 50 | 70 — Thunderbolt, Drill Peck, Hyper Beam, Agility |
| Articuno | 50 | 70 — Blizzard, Ice Beam, Hyper Beam, Reflect |
| Moltres | 50 | 70 — Fire Blast, Hyper Beam, Double-Edge, Agility |
| Mewtwo | 70 | 85 — Psychic, Amnesia, Recover, Blizzard |

The birds are a flat 70, the way vanilla made them a flat 50: one tier of
thing, wherever you meet it. Mewtwo is 85 because Amnesia arrives at 81, and a
Mewtwo that can't use Amnesia isn't really Mewtwo.

A wild Pokémon has no AI at all — it picks from its four moves at random, every
turn. So these sets are built the opposite way round from the boss ones: almost
every slot is something that hurts you, because a move that only matters
sometimes is a wasted turn one time in four. It's also why no Snorlax here
knows Rest, and why Voltorb finally knows an Electric attack, which in the real
game it never does.

Catching them is exactly as hard as it always was. Gen 1 rolls on how much
health is left as a fraction of the total, and never reads the level.

## Everyone else

Levels up 15%, short parties filled out with something new rather than a second
Caterpie, and no more level 30 Bulbasaurs. Padding always suits the trainer and
is always something you could have caught yourself by then.

Experience is cut to 75%. Bigger, evolved parties pay out more, so without it
you'd end up over-levelled while fighting harder opponents. Your Pokémon are
exactly as strong at any given level as they'd normally be. The game just runs
longer.

## Options

Sixteen rows under MODS > Stronger Trainers. They apply to the next battle, no
restart.

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
| `STATIC ENCOUNTERS` | ON | Off puts the legendaries and the rest back to vanilla |
| `STATIC MOVESETS` | ON | Off keeps the levels but uses their normal moves |
| `XP GAIN %` | 75 | Percentage of the normal experience. 100 turns it off |

Too much early on? Drop `TRAINER LEVEL %` to 10 and `MIN PARTY SIZE` to 2. Want
a wall? `BOSS LEVEL BONUS` +5 with `TRAINER LEVEL %` 25. If you grind a lot
you'll get ahead of the fights, and `BOSS LEVEL BONUS` is the fix for that too.
Bosses are levelled expecting you to be on 75% experience, so raising
`XP GAIN %` makes them easier relative to you.

## Install

Drop the `stronger_trainers` folder into `mods/`, or import the zip from the
launcher. New mods are on by default, so restart and it's live.

Where `mods/` lives depends on how you launch, which catches people out:

| Launching with | Mods folder |
| --- | --- |
| `gen1recomp.exe` | `%APPDATA%\pokemon-love2d\mods` |
| `love.exe` and a source folder | `%APPDATA%\LOVE\pokemon-love2d\mods` |

Two separate folders with separate mod sets. Install to both if you use both. On
macOS and Linux the roots are `~/Library/Application Support/` and
`~/.local/share/`.

## Compatibility

Trainer Rematch is fine; rematches use the vanilla teams. Modern Kanto is fine
and you can leave its own `SMART AI` on. Other trainer mods work too, and their
teams still get the level treatment. Experience mods stack with `XP GAIN %`
rather than fighting it.

You'll be richer, too. Gen 1 pays prize money on the last Pokémon's level, and
these teams are higher.

## Credits

Built on the pret disassemblies of Red and Yellow. MIT licensed, see `LICENSE`.
