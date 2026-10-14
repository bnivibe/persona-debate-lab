# persona-debate-lab

A method for running multi-persona AI debates and scoring the personas against what actually
happened afterwards.

Most persona debates stop at the transcript. This repo keeps the parts that make the next debate
better: one roster of personas with their known biases, a scorecard per persona (did their ideas
survive rebuttal, did they misread facts, did the user end up using their ideas, did it work),
the protocol, and the lessons learned.

- `METHOD.md`: how a round runs, step by step
- `personas/roster.md`: the cast
- `scorecards/rounds.csv`: one row per persona per round, counts only
- `scorecards/outcomes.csv`: one row per round, with the user's 1 to 5 rating of how useful it was
- `lessons/LESSONS.md`: what changed the method and why
- `skill/`: the Claude Code skill that runs rounds, plus `score.py` and a chat mirror
- `guard/`: the privacy guard that keeps personal details out of this repo

## Track record

<!-- scoreboard:start -->
| persona | rounds | proposals | survival | fact errors | adopted | hit rate |
|---|---|---|---|---|---|---|
| `backend-junior` | 1 | 2 | 100% | 1 | 0 | n/a |
| `tech-lead-mid` | 1 | 2 | 100% | 0 | 0 | n/a |
| `hiring-manager` | 1 | 2 | 50% | 0 | 0 | n/a |
| `wh-settler` | 1 | 2 | 50% | 0 | 0 | n/a |

Method: 0 rated round(s), 1 awaiting an outcome; average rating n/a of 5; ideas used n/a.
<!-- scoreboard:end -->

## Privacy

Debates are about real decisions, so transcripts stay private. This repo holds only the method and
counts. `guard/check_public.py` blocks non-English text, contact details, money amounts, links
outside an allowlist, a private list of names, files it cannot read as text, and any path outside
the expected layout. It runs in the pre-commit, commit-msg and pre-push hooks (install them once
per clone with `sh guard/install-hooks.sh`) and in CI, which checks every commit of a push or pull
request, not only the final snapshot. Pull requests from forks fail the guard, because the private
list is a repository secret that forks cannot read.

## License

MIT
