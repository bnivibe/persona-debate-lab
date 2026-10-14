# Method

A round is a short, structured argument among three to five personas from
`personas/roster.md`, run as parallel AI subagents, followed by a synthesis by the moderator.
Rounds are stored privately; what is public is the method, the roster and the counts.

## A round

1. **Collect steering.** If the thread mirrors to a chat channel, read the user's notes posted
   since the last round and add them to the thread's steering section.
2. **Check context, then cast.** The thread context must state five things before any persona
   runs: the goal (what decision or event this prepares), the decision date, the audience and
   venue (who hears the result, and how much time they have), the facts with their sources, and
   the constraints. Ask the user for whatever is missing; personas fill gaps with an ideal world.
   Then run `python3 skill/bin/score.py --brief` and pick three to five personas whose jobs touch
   the topic. Show the user the cast with one line of reasoning each and wait for a yes. Every
   round includes at least one persona who was not in the previous round.
3. **Pre-run one persona.** Launch one persona alone. If it returns a status string
   ("done", "idle") instead of content, ask the same agent once to re-output its answer. If that
   also fails, stop and tell the user.
4. **Proposals.** Launch the rest in parallel. Each gets its roster row and the thread context,
   and returns one or two ideas of at most 250 characters each. Dead branches may not return.
5. **Cross-rebuttal.** Launch everyone again with all proposals. Each picks the strongest idea
   that is not its own and names exactly which link is weak. No self-defense, no polite comments.
   Known bias may be used as an argument.
6. **Fact check.** Before synthesis, the moderator checks every factual claim in proposals and
   rebuttals against the thread context and records each misread against its persona.
7. **Synthesis.** Survivors, dead ideas with the reason, what nobody broke, the most interesting
   clash, misreads found in step 6, a missing perspective (a cast suggestion for next round), and
   three directions for the next round. Discount each rebuttal by its author's known bias.
8. **Record.** Save the round privately, then append one row per persona to
   `scorecards/rounds.csv` with `outcome` set to `pending`.
9. **Outcome.** When the real event the thread prepared for has happened, ask the user three
   questions: which ideas were used, whether each helped, and how useful the round was overall on
   a scale of 1 to 5. Fill `adopted` and `outcome` in `scorecards/rounds.csv`, fill `ideas_used`
   and `rating` in `scorecards/outcomes.csv`, run `score.py --write`, and add a lesson if the
   result generalizes.

## Scorecard fields

| field | meaning |
|---|---|
| `proposals` | ideas the persona proposed this round |
| `survived` | of those, ideas no rebuttal broke (an idea that was attacked and weakened does not count) |
| `attacked` | rebuttals aimed at this persona's ideas |
| `fact_errors` | misreads found in the fact check |
| `adopted` | ideas the user actually used; blank until the outcome is known |
| `outcome` | `hit`, `miss`, `mixed`, or `pending` |

`scorecards/outcomes.csv` holds one row per round, so the method itself is scored, not only the
personas:

| field | meaning |
|---|---|
| `ideas_total` | ideas proposed in the round, all personas together |
| `ideas_used` | of those, ideas the user actually used; blank until the outcome is known |
| `rating` | the user's 1 to 5 rating of the round's usefulness; blank while pending |

If the average rating or the adoption rate drops after a method change, the change goes back.

## Privacy

Nothing personal enters this repo. Threads are `T001`, `T002`, ... with a category
(`career`, `tech`, `learning`, `life`, `tooling`). Run `sh guard/install-hooks.sh` once per clone;
the hooks and CI run `guard/check_public.py`.
