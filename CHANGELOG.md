# Changelog

## 1.7.1

Early-game pass. The first gyms were unfair rather than hard.

Brock had Thunderbolt, Ice Beam and Fire Blast at one badge, so every starter
had a hard counter waiting and you have no TMs to answer with. Misty ran Ice
Beam on four of six, which locks out the Grass starter her gym is supposed to
be weak to. Neither has an off-type move now, Surge keeps one and Erika two.
Koga onward is untouched: by then you've been through Celadon and can build the
same kind of team yourself.

Also on Brock and Misty, nothing goes above Body Slam any more — Earthquake and
Surf were both in there — and Starmie loses Psychic. That was the worst of it,
hitting a Grass starter for double while Water only managed half, so bringing
the right counter was the wrong move.

Less repetition all round. Rock Slide was on five of Brock's six, Bubblebeam on
five of Misty's, Thunderbolt on all six of Surge's and Sleep Powder on four of
Erika's. Nothing runs on more than three of a team now.

Dig and Horn Drill are off every roster. Dig spends a turn underground for
damage the AI overrates, and Horn Drill is a coin flip.

Levels are unchanged.

## 1.7.0

### Yellow is fixed

Rival battles were broken in Yellow. You'd meet a lone level 6 starter at Oak's
lab, then again on Route 22, then again in Cerulean, a different species each
time. Yellow arranges its rival fights differently from Red and Blue, and the mod
wasn't accounting for it.

Yellow's rival now fights with his Eevee, evolved into Jolteon, Flareon or
Vaporeon depending on how your early meetings went, backed by Sandslash, Alakazam
and Exeggutor. Not a borrowed starter.

Yellow's leaders were also coming out *weaker* than the unmodded game. Koga,
Sabrina, Blaine and Giovanni are all higher in vanilla Yellow than the levels this
mod was giving them. Fixed, and Yellow now gets its own levels throughout.

### The later gyms actually bite now

They were too soft. The mod hands out more experience than vanilla ever did, so
you were arriving well above the level each leader was set to, and the gap only
widened as the game went on.

| | was | now |
| --- | --- | --- |
| Misty | 24 | 28 |
| Lt. Surge | 27 | 35 |
| Erika | 32 | 43 |
| Koga | 46 | 50 |
| Sabrina | 46 | 56 |
| Blaine | 50 | 60 |
| Giovanni | 53 | 61 |
| Lorelei / Bruno / Agatha | 59 / 61 / 62 | 67 / 67 / 68 |
| Lance | 65 | 69 |
| Champion | 68 | 71 |

Mid-game rival fights moved with them: the S.S. Anne battle from 22 to 35, the
Pokémon Tower one from 28 to 45, Silph from 43 to 53.

### Gym leaders can hurt you now

Teams still keep their type, but they've got answers for what used to wall them.
Koga's Muk carries Thunderbolt, his Weezing adds Fire Blast, and his Arbok
answers Ground with an Earthquake of its own. (The early gyms got this too at
first — see 1.7.1, which took it back off them.)

Answers are spread around the team rather than saved for the ace, so switching in
a counter runs into something different each time. Every moveset is still
legitimate.

### Bosses switch

Send in a hard counter and a leader may rotate to something that handles it. It
costs them the turn, so you get a free move out of it, and there's a cap per fight
so nobody dances around you. It won't rotate away from a Pokémon that's about to
knock you out, or out of a matchup it's already winning.

New options: `BOSS SWITCHING` (on) and `SWITCHES PER FIGHT` (2). Off gives you the
old behaviour exactly.

### More varied trainers

Short parties used to get filled out with copies of what the trainer already had.
They now get something new that suits them: a lone-Onix Hiker brings a Rhyhorn and
a Geodude, a Sailor's Shellder brings a Psyduck and a Seel. Always something you
could have caught yourself by that point, and the same trainer always brings the
same Pokémon.

New option: `PAD WITH VARIETY` (on).

### Also

- Dropped two moves that did nothing: Whirlwind, which can't work against a
  trainer, and Sky Attack, which wastes a turn charging.
- The Celadon Chief's team only ever applied in Red.
