# Method

A round is a meeting. Three to five personas from `personas/roster.md` sit in one room with the
user, who owns the meeting and the topic. They talk to each other: propose, object, agree, ask.
When a persona needs something only the user knows or decides, it asks the user, and the meeting
waits for the answer. The moderator runs the room and has no opinion. Rounds are stored privately;
what is public is the method, the roster and the counts.

Before 2026-10-23 a round was two scripted passes (proposals, then one cross-rebuttal) and the user
was not in the room. `lessons/LESSONS.md` says why it changed; compare ratings across the two.

## Who is in the room

| who | role |
|---|---|
| the user | Owns the meeting. States the topic in their own words, approves the cast, answers questions, may speak or end the meeting at any pause. What the user says is the ground truth for their preferences and private facts. |
| personas | Speak from their job, in short turns. Each persona is one persistent agent for the whole meeting, so it remembers everything said, including the user's answers. |
| moderator | Gives the floor, relays everything said to everyone, checks facts as they come up, turns questions for the user into plain questions in the user's language, keeps time, writes the minutes. Never proposes, ranks, or merges ideas. |

## A meeting

1. **Collect steering.** If the thread mirrors to a chat channel, read the user's notes posted
   since the last round and add them to the thread's steering section.
2. **Check context, then cast.** The thread context must state five things before any persona
   runs: the goal (what decision or event this prepares), the decision date, the audience and
   venue (who hears the result, and how much time they have), the facts with their sources, and
   the constraints. Ask the user for whatever is missing. In a meeting that looks for or weighs
   ideas, the constraints leave out build time and schedule unless the user sets them: ideas are
   judged on their quality, and a persona's guess at the user's time is not a constraint. The
   context of an idea meeting quotes the user's own words for what makes an idea good, and says
   what is not an idea: turning something the user already does into an automation or a skill is
   skill work, which the user does often anyway, and it goes to the user's skill upkeep instead. In
   a meeting that looks for ideas, the moderator does not gather the material: the context gives
   the goal, the decision date, the audience and venue, the constraints, the user's bar for a good
   idea, the candidate pool, what not to put back, and where the user's own material lives with what
   is off limits, and nothing else; the user's earlier answers and adopted ideas go in only as what
   not to put back, never as a starting point. Each persona finds its own facts (step 3). The
   topic goes in as the user said it,
   quoted. Earlier rounds go in as a short neutral list (what stood, what died and why, what was
   left open), and anything from them may be reopened. An idea the user puts back among other
   candidates after it lost a selection goes in as new: the same short description as every other
   candidate, and none of its earlier rounds, so the cast meets it for the first time. When the
   user's words for the topic or its scope can be read two ways, say in one line how they were
   read before preparing the context. Then run `python3 skill/bin/score.py
   --brief` and pick three to five personas whose jobs touch the topic. A meeting that looks for
   new ideas, or weighs ideas against each other, seats one persona whose job is making new
   concepts, one who tracks current trends, and one who builds what the ideas would need and asks
   whether it can be made; the trend persona finds its own dated trend facts, each with its source.
   When the topic is finding new candidates, the context never carries a list of candidates the
   moderator or a helper drew up beforehand: the candidates come from the room. When ideas
   are weighed on equal terms, no persona whose job ties it to one of them is cast; pooled ideas carry
   no author, so a persona that proposed one may sit again. An idea meeting fills five seats by role
   (concept, trend, builder, critic, open), each from its seat list in `personas/roster.md`, and
   rotates them: a persona sits at most two idea meetings in a row and then rests one; at least two
   seats change from the last idea meeting; a persona whose idea was adopted sits out the next idea
   meeting (a meeting stopped before its close does not count), so the room does not circle the
   last adoption; one with no adopted idea, or with a misread, is changed first. Every seat
   list keeps at least two personas, so a resting persona always has a stand-in. Show the user the cast with one line of
   reasoning each and wait for a yes. Every round includes at least one persona who was not in the
   previous round.
3. **Seat the room.** Start one persona alone with the opening brief from
   `skill/templates/persona-brief.md`. If it returns a status string ("done", "idle") instead of
   content, ask the same agent once to re-output its answer; if that also fails, stop and tell the
   user. Then start the rest in parallel. Each opening statement says where the persona stands, in
   at most 60 words, and puts at most two ideas on the table, each at most 250 characters. In a
   meeting that looks for ideas, each persona prepares before it speaks: it reads and analyzes the
   user's own material where the context points (never what is off limits), browses the web for
   what people need and do now, in and beyond software, benchmarks what already exists in the space (products, projects, write-ups,
   each with a source, looked up where it can), drafts at least five ideas on its own, and brings
   the two least obvious that survive its own benchmark, each with one benchmark line of at most
   150 characters: the closest thing that exists, and how this idea differs. The drafts stay
   private; only the opening is shown. The moderator labels every
   idea when it is first stated (`DE-1`, `DE-2`, ... by persona) and keeps each agent's id so the
   same agent hears every later turn.
4. **Turns.** In a turn the moderator sends every persona, in parallel, everything said since its
   last turn: statements, fact flags, the user's answers and remarks. Each persona answers with
   exactly one move of at most 80 words:
   - `object` to a named idea, naming the weak link;
   - `support` or `refine` a named idea, saying what it adds;
   - `deepen` the ideas the moderator dealt the persona, in the deepening turn (below);
   - `answer` an objection or a question put to it, with something new (a fact, a narrower
     version); restating a position is a `pass`;
   - `propose` a new idea (at most three per persona per meeting, counting the opening);
   - `ask` a named persona;
   - `ask-user` a question only the user can answer: a preference, a private fact, a decision;
   - `withdraw` one of its own ideas, saying why;
   - `pass`.
   A `refine` changes the named idea in place: it stays its author's idea and does not count toward
   the refiner's proposals. A turn ends when every persona has answered.
   A persona's known bias, from the roster, may be used as an argument.
   In a meeting that looks for ideas, the first turn is a deepening turn, before anything is
   weeded out. The moderator deals every idea on the table, the pooled ones included, to the
   personas so that each idea is deepened exactly once and no persona gets its own: ideas in label
   order go round the personas in seating order, a persona's own idea passing to the next. Each
   persona answers with one `deepen` per idea dealt to it, at most 80 words each: a concrete picture
   of the user using it, how it differs from its benchmark, and the part that is not obvious and
   makes it worth building. No objections or withdrawals in that turn. Ideas are judged from the
   second turn on.
5. **Check facts in the room.** Before relaying a turn, the moderator checks its factual claims
   against the context and the user's answers. A misread is flagged to everyone in the next relay,
   in one line that cites the fact, and is counted against its persona. Facts a persona found in
   its own benchmarking count only with their source. In a meeting that looks for ideas the
   moderator also flags an idea that only automates what the user already does; its author makes
   it new or withdraws it.
6. **Ask the user.** The meeting pauses when a turn contains an `ask-user` move. If the context
   already answers it, the moderator says so to the room and does not ask. Otherwise it puts the
   remaining questions to the user, at most three at once, in the user's language and in plain
   words, with no internal labels (no idea labels, fact numbers or persona ids): who is asking, the
   question, and why it matters to the decision. The user's answer goes to every persona verbatim
   and into the context as a fact from the user. "I don't know" and "you decide" are answers too.
   A question whose answer may decide an idea asks about the idea itself as well as the fact (would
   the user use it, does it interest the user): a factual answer alone is not the user's verdict on
   an idea, and a persona's own "if not, I withdraw" is its guess, not the user's.
   The user may also speak at any pause, and that remark is relayed the same way. Between pauses
   the moderator shows the user each turn as a short transcript (one line per speaker, passes
   left out) and keeps going.
7. **Close.** The meeting ends at whichever comes first: the user says so; two turns in a row
   bring no new idea, objection or question; or, after six turns, the user chooses not to continue
   (the moderator asks). Then every persona gives a closing statement in parallel, two lines: what it
   now supports, and what it still doubts.
8. **Minutes.** Every meeting ends with a report the user can keep, made without being asked: a
   document saved where the user's records live, with a page for reading it, and the chat carries
   a short summary and the link. The report opens with each standing idea in two or three plain
   sentences, in the user's language and without the room's labels: what it does, an example from
   something the user has already done, and what changes for the user. Then the moderator writes
   only what was said in the room:
   - Decided: what the room agreed on with no objection left unanswered, naming anyone who still
     disagrees.
   - Standing ideas, split into those that held up under objection and those nobody challenged.
     An unchallenged idea has not been tested.
   - Withdrawn and dropped ideas: by whom, and why. An idea is dropped when an objection to it was
     still unanswered at the close. Ideas withdrawn because of the user's answers are listed apart,
     so the user can revive them; a revived idea is a standing idea again.
   - The user's answers, and the questions still open for the user.
   - Misreads flagged in step 5.
   - A missing perspective (a cast suggestion for next round), and up to three next topics.

   The moderator does not combine ideas into a design the room never discussed. If a combination
   looks useful, it puts it to the room as a question before step 7, and it enters the minutes only
   if the room took it up.
9. **Record.** Save the meeting privately, then append one row per persona to
   `scorecards/rounds.csv` with `outcome` set to `pending`.
10. **Outcome.** When the real event the thread prepared for has happened, ask the user three
    questions: which ideas were used, whether each helped, and how useful the meeting was overall
    on a scale of 1 to 5. Fill `adopted` and `outcome` in `scorecards/rounds.csv`, fill
    `ideas_used` and `rating` in `scorecards/outcomes.csv`, run `score.py --write`, and add a
    lesson if the result generalizes. In a meeting that looks for ideas, the user adopts the ideas
    worth building from the standing ones. Every standing idea not adopted goes into the user's
    candidate pool, and the next meeting that looks for ideas takes the whole pool in as candidates,
    on equal terms with the room's new ideas and with none of their history (step 2).
11. **Feedback on the method.** Whenever the user remarks on how a meeting is run (the cast, the
    questions, the pace, the format, the report), record the remark in the same turn, apply it to
    the running meeting where it can be, and before the next meeting turn it into a change to this
    file, the roster or the skill, with a lesson saying why. Tell the user what changed.

## Scorecard fields

| field | meaning |
|---|---|
| `proposals` | ideas the persona put on the table this meeting, opening included |
| `survived` | of those, ideas still standing at the close: not withdrawn, not dropped, and no objection left unanswered |
| `attacked` | `object` moves aimed at this persona's ideas |
| `fact_errors` | misreads flagged in step 5 |
| `adopted` | ideas the user actually used; blank until the outcome is known |
| `outcome` | `hit`, `miss`, `mixed`, or `pending` |

`scorecards/outcomes.csv` holds one row per meeting, so the method itself is scored, not only the
personas:

| field | meaning |
|---|---|
| `ideas_total` | ideas put on the table in the meeting, all personas together |
| `ideas_used` | of those, ideas the user actually used; blank until the outcome is known |
| `rating` | the user's 1 to 5 rating of the meeting's usefulness; blank while pending |

If the average rating or the adoption rate drops after a method change, the change goes back.

## Privacy

Nothing personal enters this repo. Threads are `T001`, `T002`, ... with a category
(`career`, `tech`, `learning`, `life`, `tooling`). Run `sh guard/install-hooks.sh` once per clone;
the hooks and CI run `guard/check_public.py`.
