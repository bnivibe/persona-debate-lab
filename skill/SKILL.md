---
name: idea-debate
description: Run a meeting among cast personas and the user to develop an idea, scored against real outcomes. Personas talk to each other and ask the user what only the user knows. Use when the user asks for a debate on an idea or a decision, wants another round, or wants to record how a past debate turned out.
---

# idea-debate

Follow `METHOD.md` in this repo for the meeting itself. This file covers how to keep the room
running, where things live, and the rules that keep the public repo clean.

## Settings

A private local file supplies these values; never write them into this repo:

| setting | meaning |
|---|---|
| `lab_repo` | local clone of this repo |
| `transcripts` | private location for `thread.md` and `rounds/round-NN.md` per thread |
| `webhook_env`, `bot_token_env` | names of the secret variables for the chat mirror |
| `denylist` | path of the private deny-list read by the guard |
| `language` | language the personas speak in, and the user's language: the room is shown to the user, and questions are put to the user, in the user's language |

## Running the room

- Each persona is one subagent started fresh for the meeting, never a copy of the moderator's own
  conversation, which would carry the moderator's view into the room. Keep its agent id and send
  every later turn to that same agent, so it remembers what was said.
- Write the running transcript into the private `rounds/round-NN.md` after every turn, agent ids
  included, so a restart loses nothing. If an agent is lost, start a fresh one with its opening
  brief plus the transcript so far, and say so in the minutes.
- Turns run in parallel: every persona hears the same relay and answers once.
- Show the user each turn as it ends and keep going. Stop only for questions to the user, for the
  check after six turns, and at the close. The user may interrupt at any time; whatever the user
  says is relayed to every persona before the next turn.
- Ask the user in the user's own terms. A question that uses the moderator's labels (idea labels,
  fact numbers, persona ids, round numbers) is rewritten before it is asked.

## Threads

- One thread per topic, stored under `transcripts`, using `skill/templates/thread.md`.
- Each thread gets a public id (`T001`, ...) and a category when its first round is recorded.
  The id-to-topic map lives only in the private `thread.md` front matter.
- Keep `thread.md` short: current candidates, dead branches with the reason, steering, round index.
- Before the first round, fill the five context items in the template (goal, decision date,
  audience and venue, facts with sources, constraints). Ask the user for anything missing.

## Recording a round

1. Save the meeting with `skill/templates/round.md` under `transcripts`: minutes first, then the
   transcript.
2. Append one row per cast persona to `scorecards/rounds.csv` (counts only, `outcome` = `pending`),
   and one row for the round to `scorecards/outcomes.csv` with `ideas_total` filled and
   `ideas_used` and `rating` left blank.
3. If a new employer, person or place appeared in the thread, add it to the deny-list first.
4. In this repo: `python3 skill/bin/score.py --write`, `python3 guard/check_public.py`, then commit
   on a branch and open a pull request.

## Mirroring

`python3 skill/bin/discord_debate.py post < messages.json` posts `{"persona", "content"}` items;
`fetch --channel ID [--after ID] [--user ID]` collects the user's notes. Both exit quietly when the
secret is unset. Use roster labels as display names and split any minutes longer than 2,000
characters into several messages. Mirror failures never undo a commit.

## Outcomes

When the event a thread prepared for is over, ask the user which ideas were used, whether each
helped, and how useful each round was on a scale of 1 to 5. Update `adopted` and `outcome` in
`scorecards/rounds.csv` and `ideas_used` and `rating` in `scorecards/outcomes.csv`, run
`score.py --write`, and add a lesson to `lessons/LESSONS.md` only if it changes how meetings should
run. Check the method line of the scoreboard after any change to `METHOD.md`: a falling average
rating or adoption rate is the signal to revert.

## Never

Unattended rounds, automatic scoring of idea quality, a standing chat listener, or any personal
detail in this repo.
