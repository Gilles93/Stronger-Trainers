# Stronger Trainers

Gym leaders, the Elite Four, the Champion, the rivals and Giovanni field full
six-Pokémon teams with hand-picked movesets. Every other trainer keeps its own
species but gets a level bump and a padded-out party.

Drop this folder into your `mods/` directory, or import the zip from the
launcher. New mods are enabled by default, so restart and it's live. There's a
fuller write-up in `DESCRIPTION.md`, including where `mods/` lives for each way
of launching the game.

## What changed

39 authored rosters covering 204 slots. Every gym leader that had fewer than six
Pokémon now has six, and so do the Elite Four, the Champion, Giovanni's three
fights and the Celadon Chief.

| Leader | Vanilla | Now |
| --- | --- | --- |
| Brock | Geodude 12, Onix 14 | Geodude 14, Sandshrew 14, Rhyhorn 15, Kabuto 16, Graveler 16, Onix 19 |
| Misty | Staryu 18, Starmie 21 | Psyduck 20, Horsea 20, Shellder 21, Staryu 21, Poliwhirl 22, Starmie 24 |
| Lt. Surge | 3 mons, ace 24 | Voltorb 22, Pikachu 22, Magnemite 23, Electrode 25, Magneton 25, Raichu 27 |
| Erika | 3 mons, ace 29 | Weepinbell 28, Gloom 28, Tangela 29, Exeggcute 29, Victreebel 31, Vileplume 32 |
| Koga | 4 mons, ace 43 | Koffing 41, Golbat 42, Venomoth 43, Arbok 44, Muk 44, Weezing 46 |
| Sabrina | 4 mons, ace 43 | Mr. Mime 42, Venomoth 42, Kadabra 43, Hypno 44, Exeggutor 44, Alakazam 46 |
| Blaine | 4 mons, ace 47 | Ponyta 44, Growlithe 45, Magmar 46, Rapidash 47, Ninetales 47, Arcanine 50 |
| Giovanni | 5 mons, ace 50 | Dugtrio 47, Marowak 48, Persian 49, Nidoqueen 50, Nidoking 51, Rhydon 53 |

Lance closes on two Dragonite, at 63 and 65. The Champion's ace reaches 68. Full
Elite Four tables are in `DESCRIPTION.md`.

Rival battles scale with your own roster rather than jumping straight to six.
The Oak's-lab battle deliberately stays one-on-one, since you own a single level
5 starter there and a filled party would be unwinnable rather than hard. Route
22 gets three, Cerulean five, and everything from the S.S. Anne onward six.

Movesets are Gen 1 legal. All 204 slots were checked against the ROM's own
learnset and TM/HM tables, including moves inherited from a pre-evolution, so a
Graveler really can carry the Rock Throw it picked up as a Geodude. Nothing has
a move it couldn't legitimately know at that level, and nothing is a stat-stick
with no attack.

## Gym battle formats

Before you have a gym's badge, talking to the leader runs their dialogue, then a
"How many POKéMON each?" prompt, then the team picker, then the battle.

The number is how many the leader brings. It draws from its six with the ace
always included and the rest at random, so even a 2v2 against Brock means facing
that level 19 Onix.

You then pick your own side from the party screen, one at a time in send-out
order, so your first pick leads. Each round lists only the Pokémon still
unpicked, and B undoes your last pick or backs out of the encounter entirely on
the first one.

- The picker always runs 2 to 6 whatever the size of your party, and Up and Down
  roll around inside that range. Pick 6 with five Pokémon and it's your five
  against their six. Being outnumbered is a legitimate fight, and it means you
  never have to carry a full party just to face a full team. Your side is capped
  at what you can actually field.
- B backs out of the whole encounter from the format picker or your first pick,
  so you can always leave to heal.
- The pick screen only appears when there's a team to choose. If the format takes
  everything you have standing, whether that's 6v6 with five Pokémon or 3v3 with
  three, the set is forced and it goes straight to the battle in party order.
- Only the badge-earning fight offers the choice. Once you hold the badge the
  leader's dialogue is exactly vanilla, TM re-give included.
- Nothing compensates for the format. A 2v2 really is a quicker, swingier fight
  and 6v6 the full slog. It's a preference knob, not a difficulty setting.
- Losing blacks you out as Gen 1 would, even with healthy Pokémon in reserve.

## Smarter boss AI

Gen 1's trainer AI scores each move from a base of 10 and picks the lowest. All
three vanilla passes together only discourage a status move that would fail,
nudge a few effects on one turn, and add or subtract 1 for type effectiveness.
Nothing estimates damage, reads HP, or weighs accuracy.

This adds a fourth scoring pass:

- Damage and KO detection through the game's own formula, so a 120-power neutral
  move stops losing to a 40-power super-effective one, and a move that finishes
  your Pokémon gets taken.
- Accuracy weighting, valuing expected damage rather than raw power, so it stops
  gambling on Horn Drill and Blizzard when a reliable move wins. This sometimes
  makes the AI easier, which is correct.
- Self-preservation. It won't set up while it's dying, and it heals when
  genuinely hurt, at most twice per Pokémon and only below half HP, so it can't
  Recover-stall you. Sabrina has two Recover users and still only gets four
  heals in total.
- Sensible status use. It won't re-paralyse or re-sleep, and it won't waste a
  status move on a target that already has one.

It plays fair. It reads your HP at the resolution of the on-screen HP bar, 48
pixels wide, and never looks at your move list, stats or DVs. It knows what
someone sitting opposite could see.

Some tactics are deliberately excluded because they make Gen 1 miserable rather
than hard: re-sleeping a sleeping target, chasing Blizzard freezes, Wrap and
Fire Spin lock-outs, the Hyper Beam no-recharge-on-KO trick, and Explosion spam.
Each is suppressed explicitly rather than just left unrewarded, so a future
scoring tweak can't quietly reintroduce it.

It defaults to on, bosses only, so route trainers stay as dumb as Gen 1
intended. `SMART AI FOR = EVERYONE` turns it on for all 47 trainer classes.

### It composes with Modern Kanto

If you have Modern Kanto, turn its `SMART AI` on too. It ships off by default,
and the two do different jobs. Modern Kanto patches the vanilla `LAYER_3` so
type effectiveness multiplies dual types out properly, while this registers a
separate layer id and references it from each trainer's `aiMods`, so both run
additively and neither overwrites the other. Patching `LAYER_3` here would have
silently thrown Modern Kanto's work away.

## Overdue pre-evolutions

Gen 1 is careless about this: 212 of its 999 trainer party slots are already
past their own evolution level before this mod raises anything, and the level
bump takes that to 326. Ordinary trainers now field the stage their level has
actually earned. A level 16 Bulbasaur is an Ivysaur, a level 32 one is a
Venusaur, and a Bug Catcher's level 13 Caterpie shows up as a Butterfree that
knows Confusion. Chains run to completion rather than stopping a stage short.

The evolved form brings its own level-up moveset with it, which is a bigger
jump than the base stats alone. Route 3 in particular gets noticeably meaner.

Stone evolutions carry no level in Gen 1, so `STONE EVO FROM LV` supplies one.
It defaults to 30, taking a late Pikachu to Raichu and a Gloom to Vileplume. Set
it to 0 to leave stone users alone.

Evolution lines are read from the merged Pokémon data, not a private table, so
other mods' evolution edits apply for free. With **All Pokémon Catchable 151**
installed ((from DarkLinkDuck), its trade-evolution fixes (Kadabra, Graveler and Haunter at 42,
Machoke at 45) reach trainers too.

The 39 authored rosters are exempt, since their stages are chosen by hand.
Evolving them would take Lance from two Dragonite to four and hand Blaine a
second Rapidash.

## Tuning it while you play

Ten rows under MODS > Stronger Trainers. They read live, so a change applies
to the very next battle with no restart.

| Row | Default | What it does |
| --- | --- | --- |
| `BOSS TEAMS` | ON | Off reverts bosses to their vanilla rosters and gives them the ordinary level bump instead |
| `BOSS MOVESETS` | ON | Off keeps the six-mon teams but lets the engine pick each mon's normal level-up moves |
| `GYM FORMAT CHOICE` | ON | Off skips the format picker; gym battles go straight to the full six |
| `SMART AI` | ON | The extra scoring layer described above |
| `SMART AI FOR` | BOSSES | Set to EVERYONE to extend it to all 47 trainer classes |
| `BOSS LEVEL BONUS` | 0 | Adds flat levels on top of the authored boss levels, up to +20 |
| `TRAINER LEVEL %` | 15 | Level bump for every non-boss trainer. 0 leaves them alone |
| `MIN PARTY SIZE` | 3 | Pads short ordinary parties up to this, reusing the trainer's own species |
| `EVOLVE PRE-EVOS` | ON | Walks ordinary trainers' Pokémon up to the stage their level has earned |
| `STONE EVO FROM LV` | 30 | The level a stone evolution counts from. 0 leaves stone users on their pre-evo |

If the early game bites too hard, drop `TRAINER LEVEL %` to 10 and `MIN PARTY
SIZE` to 2, or turn `EVOLVE PRE-EVOS` off for the Bug Catcher stretch. If you
want a real wall, `BOSS LEVEL BONUS` +5 with `TRAINER LEVEL %` 25.

## Worth knowing

- Prize money goes up. Gen 1 pays out base money times the last Pokémon's level,
  so higher-level trainers are richer. That's the vanilla formula, not something
  this mod touches.
- Experience goes up a little too, for the same reason. Gen 1 pays experience
  off the defeated Pokémon's base experience, and evolved forms are worth more,
  so beating an evolved trainer party levels you slightly faster than vanilla.
- Rosters are rewritten as each battle starts, so `data.trainers` still reads
  vanilla outside battle. A mod that inspects trainer data ahead of time, like
  Trainer Rematch's level-gap warning, will quote the original levels. The
  battle itself is correct.
- It stacks with other trainer mods rather than fighting them. Non-boss parties
  get the level treatment applied to whatever the other mod produced.
- No save changes. Your file works with or without this mod, and disabling it
  mid-playthrough is safe.

## How it works

Most of it happens in the `trainer.party` hook the battle builder offers just
after it picks a roster and before it instantiates any Pokémon
(`src/battle/BattleState.lua:670`).

The registry route (`mod.content.trainers:patch`) can't carry movesets. The
battle builder honours a `moves` list on a party slot
(`BattleState.lua:689`), but the `trainers` schema declares a slot as
`{ level, species }` and validates nested records strictly
(`Schemas.lua:177-185`), so a `moves` key in a patch is a hard load error at api
2. The hook is the only door custom sets fit through, and it's also what makes
the options read live and lets the mod compose with others.

`boss_teams.lua` is generated, not hand-written. The authoring source and its
validator live outside the mod, and the generator refuses to emit a roster
containing an unknown species, an unknown move, a move that species cannot learn
at that level, a party over six, or a slot over four moves.

## Verified against

gen1recomp 0.1.72 (`gen1recomp-0.1.72-windows`)

- Rosters: boss teams resolving to six with the right aces and move lists, the
  lab battle staying 1v1, ordinary parties scaling and padding, six-mon parties
  not growing past six, the level clamp at 100, and the input party table never
  being mutated.
- Evolutions: both sides of the exact boundary (a level 19 Magikarp stays, a
  level 20 becomes Gyarados), two-step chains completing, species with no
  evolutions and species the build doesn't carry falling through untouched,
  stone evolutions firing only at or above the configured level and never at 0,
  trade rows never firing on their own, Eevee resolving to one eeveelution and
  the same one every call, padded copies matching the evolved slot, and all 39
  authored rosters coming back with their exact species lists.
- Formats: a talk override on all 8 gyms, the ace present at every format across
  240 random rolls, exact counts, picks ordered lead to ace, the picker offering
  2 to 6 whatever your party size, never reaching 1 over 30 presses, and wrapping
  at both ends.
- Party safety: the party table keeping its identity, the battle party landing in
  pick order rather than party order, every Pokémon returning to its original
  index afterwards, the same objects coming back rather than copies, fainted
  Pokémon never being selected, restore being idempotent, and a one-Pokémon party
  surviving intact.
- Smart AI: registered under its own id and referenced from all 47 trainer
  classes, since a registered but unreferenced layer would never run. Brock keeps
  his original `aiMods`, `LAYER_3` is left intact, and each scoring rule is
  asserted exactly.

## Licence

MIT. See `LICENSE`.
