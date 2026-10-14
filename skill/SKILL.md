---
name: idea-debate
description: Run a multi-round debate among cast personas to develop an idea, scored against real outcomes. Use when the user asks for a debate on an idea or a decision, wants another round, or wants to record how a past debate turned out.
---

# idea-debate

Follow `METHOD.md` in this repo for the round itself. This file covers where things live and the
rules that keep the public repo clean.

## Settings

A private local file supplies these values; never write them into this repo:

| setting | meaning |
|---|---|
| `lab_repo` | local clone of this repo |
| `transcripts` | private location for `thread.md` and `rounds/round-NN.md` per thread |
| `webhook_env`, `bot_token_env` | names of the secret variables for the chat mirror |
| `denylist` | path of the private deny-list read by the guard |
| `language` | language the debate runs in, and the language of the short report to the user |

## Threads

- One thread per topic, stored under `transcripts`, using `skill/templates/thread.md`.
- Each thread gets a public id (`T001`, ...) and a category when its first round is recorded.
  The id-to-topic map lives only in the private `thread.md` front matter.
- Keep `thread.md` short: current candidates, dead branches with the reason, steering, round index.
- Before the first round, fill the five context items in the template (goal, decision date,
  audience and venue, facts with sources, constraints). Ask the user for anything missing.

## Recording a round

1. Save the full round with `skill/templates/round.md` under `transcripts`.
2. Append one row per cast persona to `scorecards/rounds.csv` (counts only, `outcome` = `pending`),
   and one row for the round to `scorecards/outcomes.csv` with `ideas_total` filled and
   `ideas_used` and `rating` left blank.
3. If a new employer, person or place appeared in the thread, add it to the deny-list first.
4. In this repo: `python3 skill/bin/score.py --write`, `python3 guard/check_public.py`, then commit
   on a branch and open a pull request.

## Mirroring

`python3 skill/bin/discord_debate.py post < messages.json` posts `{"persona", "content"}` items;
`fetch --channel ID [--after ID] [--user ID]` collects the user's notes. Both exit quietly when the
secret is unset. Use roster labels as display names and split any synthesis longer than 2,000
characters into several messages. Mirror failures never undo a commit.

## Outcomes

When the event a thread prepared for is over, ask the user which ideas were used, whether each
helped, and how useful each round was on a scale of 1 to 5. Update `adopted` and `outcome` in
`scorecards/rounds.csv` and `ideas_used` and `rating` in `scorecards/outcomes.csv`, run
`score.py --write`, and add a lesson to `lessons/LESSONS.md` only if it changes how rounds should
run. Check the method line of the scoreboard after any change to `METHOD.md`: a falling average
rating or adoption rate is the signal to revert.

## Never

Unattended rounds, automatic scoring of idea quality, a standing chat listener, or any personal
detail in this repo.
