# Lessons

Each lesson is about the method, never about a situation. Newest first.

## 2026-10-30 · Ideas not adopted wait in a pool, and reports start in plain words
The user defined what an idea meeting is for: the debate produces many ideas into a candidate pool,
the good ones are adopted, and the rest stay in the pool to compete in the next debate as one idea
among others. The same day the user could not tell what the adopted idea was from a report written
in the room's terms (a "line", a "state file", a "first slice"). Outcomes now feed the pool, and
every report to the user opens with each idea in plain words before any of the room's labels.

## 2026-10-30 · Finding candidates is the meeting's work, and a builder sits in it
Asked for new candidates to join two kept ones, the moderator had a research agent draft them before
the meeting. The user stopped it: the candidates were to come out of the debate. The same day the
user asked for a developer persona next to the creative, trend and judging seats, since nobody in
the room would build the ideas. The context for a candidate search now carries only raw material,
and idea meetings seat a persona who builds what the ideas need.

## 2026-10-30 · "Equal terms" meant new, not equal to each other
Two ideas had lost a selection to a third, and the user asked to debate them again on equal terms.
The moderator read that as the two being equal to each other, and put each one's earlier meeting
into the context. The user meant that both should rejoin the other candidates as if the room had
never seen them. A requeued idea now enters with the same description as every other candidate and
none of its history. And when the user's words allow two readings, the moderator states its
reading before preparing anything.

## 2026-10-30 · A cast of specialists, with one insider per idea, looked one-sided
Asked to weigh two earlier ideas on equal terms, the moderator offered one insider per idea and two
judges. The user found the cast all specialists, missing a creative mind and someone who knows the
current trends, and then found the insiders partisan. Idea meetings now seat a concept maker and a
trend scout, the scout fed with trend facts checked that week, and equal-terms comparisons cast no
one tied to either side. The same day the user asked that every remark on how meetings run be
recorded and turned into a rule before the next meeting; that is now step 11.

## 2026-10-26 · The first rated round scored 2 of 5
The user used two of eight ideas and said the cast never grasped the setting: what kind of room it
was and who would be answering. That round ran before the context checklist existed. The checklist
(goal, decision date, audience and venue, facts with sources, constraints) is now step 2 of a round;
the next ratings will show whether it closes this gap.

## 2026-10-23 · A round became a meeting with the user in the room
Two scripted passes (proposals, one cross-rebuttal) left gaps the user noticed. Each persona
rebutted one idea, so most ideas were never challenged and still counted as survivors. The design
the user was shown came from the moderator combining survivors after the round; the room never
argued it. A round's summary primed the next round. And personas could not ask the user, so they
filled private facts and preferences themselves. Now personas keep their memory through the
meeting, talk in turns, ask the user, and the minutes split ideas that held up from ideas nobody
challenged. Rounds recorded before this lesson (up to T002 round 4) ran the old way; compare
their ratings with the meetings' before keeping this.

## 2026-10-13 · Personas misread facts, and other personas do not catch it
In one round a persona widened a single fact into two ("both companies said X" when only one
did). No rebuttal noticed. A dedicated fact-check step before synthesis now records misreads per
persona, and the scorecard keeps a `fact_errors` count.

## 2026-10-13 · A consensus kill is a strong signal
Three of four rebuttals independently attacked the same idea for the same reason (the audience
in the room could not answer it). When rebuttals converge like that, kill the idea without
waiting for another round.

## 2026-10-13 · Describe the venue, not just the topic
Personas weighed who would hear the question as heavily as the question itself. Put the
audience and the time available into the thread context, or the proposals assume an ideal room.

## 2026-07-31 · Subagents can return only a status string
Eight runs in a row returned "done" or "idle" instead of content. Pre-run one persona before
launching the rest; when one returns a status string, ask the same agent once to re-output.

## 2026-07-22 · Cast by job, not by stance
With stance-based personas, four of five rebuttals in one round hit the single defender and the
round became a pile-on. Job-based personas take positions from their situation, so the sides
change with the topic.

## 2026-07-22 · Keep the thread context short
The whole thread file is pasted into every persona prompt. A long file slows rounds, costs more,
and drags new rounds toward old conclusions. Keep transcripts elsewhere and pass only the
current candidates, dead branches and steering.
