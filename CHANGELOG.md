# Changelog

## 1.7.2

Bosses were spamming one move. Three things caused it.

The AI scores every move and picks the lowest, breaking ties at random, and
that tie-break is the only variety Gen 1's AI has. Scoring damage on a fine
scale made ties impossible, so the biggest move won every turn forever —
five of Giovanni's six had exactly one best move. Damage is now graded in
bands, so moves of similar strength tie again and a genuinely dominant move
still wins.

Status moves could never be chosen at all. They scored nothing, which left
them at the base value while any attack scored below it, and the lowest wins.
That was 117 authored moves across the rosters — Toxic, Screech, Hypnosis,
Sand Attack — that had never once been used. They're worth a turn each now,
once, and they're skipped when the target is nearly down.

Repeating last turn's move costs a point. Enough to lose a tie to an equally
good move, never enough to talk a boss out of a knockout.

Some movesets were the problem rather than the AI. Twenty-two Pokémon had a
best attack that dwarfed everything else beside it, so they were always going
to repeat it. Those slots got a real second option or lost the dead weight —
Brock's Geodude no longer carries Tackle alongside Body Slam, Agatha's Haunter
gets Night Shade, the Champion's Pidgeot gets Swift.

Also: an attack that happens to carry a status side effect is judged as an
attack again. Body Slam was being discouraged against an already-paralysed
target, which made no sense.

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
