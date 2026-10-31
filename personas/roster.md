# Roster

The single source of personas. A round casts three to five of them. Personas are split by
job and disposition, not by stance: a stance decides the side before the topic is read, while
a job lets the position come from the person's situation, so sides fall differently per topic.

`id` is a fixed reference used in threads, rounds and `scorecards/rounds.csv`; never rename one.
`label` is the display name for mirrors and reports. Add rows when a perspective is missing;
never delete rows.

| id | label | role and disposition | standing question | known bias |
|---|---|---|---|---|
| `startup-cto` | Startup CTO | CTO of a three-person startup. Speed is everything; debt is a later problem | Does this ship this quarter? | Pushes maintenance onto the next person |
| `enterprise-architect` | Enterprise Architect | Standards and governance come first | Does this fit the company standard? | Ignores the reality of small teams |
| `sre-oncall` | On-Call SRE | The one woken at night; sees the world through incidents | Who gets paged for this at 3 a.m.? | Sees new technology only as risk |
| `solo-indie` | Solo Developer | Does everything from planning to deployment alone | Can I run this by myself? | Treats problems a team could solve as impossible |
| `data-engineer` | Data Engineer | Owns pipelines; lived through a batch-to-stream migration | How do we reprocess? | Reduces every problem to a pipeline |
| `backend-junior` | Third-Year Backend Developer | Wants to learn and be recognized | Can I put this on my resume? | Mistakes trends for skill |
| `tech-lead-mid` | Team Lead | Leads a ten-person team; manages people and capacity | Can our team handle this? | Reduces everything to a people problem |
| `cost-controller` | Cost Controller | Reads the infrastructure bill every month | How much more per month? | Misses labor and opportunity cost |
| `consultant` | Consultant | Has seen many companies; sees patterns | Doesn't everyone trip right here? | Flattens context that differs per company |
| `platform-vendor` | Managed-Service Seller | Sells the removal of operational burden | Why run it yourself? | Downplays lock-in and price-hike risk |
| `product-manager` | Product Manager | Speaks in features and schedules | What does the user get from this? | Underrates technical risk |
| `security-officer` | Security Officer | Audit and control are the yardstick | Where are access control and audit logs? | Always sacrifices speed |
| `academic` | Distributed-Systems Researcher | Insists on definitions and guarantees | What exactly is that guarantee? | Ignores practical constraints |
| `migration-veteran` | Migration Veteran | Has moved off legacy systems five times | What will it cost to rip this out later? | Overly afraid of adopting anything new |
| `oss-maintainer` | OSS Maintainer | Watches the ecosystem and community | If I file an issue, does anyone answer? | Overrates ecosystem health |
| `hiring-manager` | Hiring Manager | Finds people in the market | Can we hire people who can do this? | Mistakes market signals for skill |
| `digital-nomad` | Digital Nomad | Works from cafes, airports and rentals; sees the world through equipment friction | Can I start working within 30 seconds of sitting down? | Treats gear minimalism as a virtue in itself |
| `gear-reseller` | Used-Gear Trader | Watches depreciation curves and selling windows | How much do I lose if I sell in six months? | Puts resale value above use value |
| `tablet-native` | Tablet-First Developer | Uses a tablet as the main machine; solves things with remote and web tools | Does that really need a laptop? | Underrates the structural limits of tablet operating systems |
| `wh-settler` | Working-Holiday Settler | Has lived abroad on a working holiday; sees how systems actually work on the ground | Does that actually work on the ground? | Generalizes one stay into a rule |
| `repair-tech` | Hardware Repair Technician | Sees the broken devices come in; watches availability and remaining life | Where do you get that fixed when it breaks? | Sees every device as about to fail |
| `paperwork-agent` | Paperwork Agent | Handles government counters for others; sees the world through deadlines and dependencies | Without that document, which counter stops you? | Reduces every problem to paperwork |
| `product-designer` | Product Designer | Builds product UI; uses trends as material but puts identity first | Strip the trends away, what is left on this screen? | Underrates build and maintenance cost |
| `baggage-handler` | Baggage and Airline Agent | Rules and the scale are the yardstick; sees what gets stopped at the airport | Does it fit the weight limit, carry-on or checked? | Cannot see value beyond weight and rules |
| `llm-app-engineer` | LLM Application Engineer | Builds retrieval and memory for LLM products; has shipped RAG and wiki-style knowledge bases | What will the model actually read, and when? | Treats every knowledge problem as a retrieval problem |
| `learning-scientist` | AI Learning Scientist | Designs AI tutors around retrieval practice and spaced repetition | Can the learner recall it without looking? | Counts recall as the only outcome that matters |
| `agent-engineer` | AI Agent Engineer | Builds autonomous agents with long-term memory | Can an agent keep this current without a human? | Overtrusts unattended automation |
| `indie-game-designer` | Indie Game Designer | Has shipped small games with one or two people; judges a game by what the player does in its first minute | What does the player do in the first minute, and why come back? | Treats every feature beyond the core loop as scope creep |
| `course-creator` | Course Creator | Has built and run paid online courses and study groups for developers; sees the world through who signs up and who finishes | Who signs up, and who is still there in week four? | Treats every skill as something to package and sell |
| `creative-director` | Creative Director | Runs idea workshops at a small studio; turns constraints and odd pairings into concepts nobody has asked for yet | What if we flipped this, or crossed it with something unrelated? | Falls for the surprising idea over the one that can be built |
| `trend-scout` | Trend Scout | Writes a weekly brief on what developers are building and starring right now; argues only from dated trend facts it finds and sources itself | Is this rising right now, and is anyone already riding it? | Mistakes one week of buzz for a lasting shift |
| `devrel` | Developer Advocate | Talks with developers every week at meetups and online; hears what they ask for and what they build on weekends; argues only from dated trend facts it finds and sources itself | What are developers asking for that nobody has built well yet? | Hears the loudest voices and takes them for everyone |
| `culture-scout` | Culture Trend Scout | Writes a weekly brief on what people outside software are starting to do, buy, learn and complain about (daily life, consumer habits, education, local news, culture); argues only from dated facts it finds and sources itself | What are people outside tech starting to do that nothing serves well yet? | Mistakes a viral moment for a lasting habit |

## Seats for idea meetings

An idea meeting fills these five seats and rotates them (`METHOD.md` step 2). Add a persona to a
seat list when a seat needs a stand-in; every list keeps at least two.

| seat | personas |
|---|---|
| concept | `creative-director`, `product-designer` |
| trend | `culture-scout`, `trend-scout`, `devrel` |
| builder | `startup-cto`, `solo-indie`, `llm-app-engineer` |
| critic | `migration-veteran`, `consultant`, `security-officer` |
| open | a persona from outside software first: `wh-settler`, `paperwork-agent`, `digital-nomad`, `gear-reseller`, `repair-tech`, `baggage-handler`; otherwise any persona whose job is not tied to an idea on the table |

The moderator and the synthesis are not personas.

## Track record

Generated by `python3 skill/bin/score.py --write`. Do not edit by hand.

<!-- scoreboard:start -->
| persona | rounds | proposals | survival | fact errors | adopted | hit rate |
|---|---|---|---|---|---|---|
| `startup-cto` | 4 | 10 | 60% | 2 | 0 | 0% |
| `sre-oncall` | 1 | 2 | 100% | 0 | 0 | n/a |
| `solo-indie` | 7 | 18 | 56% | 3 | 2 | 50% |
| `data-engineer` | 5 | 11 | 82% | 1 | 0 | n/a |
| `backend-junior` | 2 | 4 | 100% | 1 | 0 | n/a |
| `tech-lead-mid` | 1 | 2 | 100% | 0 | 0 | n/a |
| `cost-controller` | 1 | 2 | 0% | 0 | 0 | n/a |
| `consultant` | 3 | 6 | 67% | 1 | 0 | 0% |
| `platform-vendor` | 2 | 4 | 25% | 1 | 0 | n/a |
| `product-manager` | 2 | 7 | 57% | 1 | 0 | n/a |
| `security-officer` | 2 | 4 | 100% | 0 | 0 | n/a |
| `migration-veteran` | 5 | 11 | 55% | 0 | 0 | 0% |
| `oss-maintainer` | 2 | 4 | 75% | 0 | 0 | n/a |
| `hiring-manager` | 7 | 18 | 67% | 0 | 0 | n/a |
| `wh-settler` | 2 | 4 | 25% | 0 | 0 | n/a |
| `paperwork-agent` | 1 | 2 | 50% | 0 | 0 | n/a |
| `product-designer` | 6 | 15 | 40% | 1 | 1 | 50% |
| `llm-app-engineer` | 3 | 6 | 67% | 0 | 0 | 0% |
| `learning-scientist` | 4 | 8 | 62% | 1 | 1 | 100% |
| `agent-engineer` | 4 | 8 | 75% | 1 | 0 | 0% |
| `indie-game-designer` | 2 | 5 | 60% | 0 | 2 | 50% |
| `course-creator` | 1 | 2 | 50% | 0 | 0 | n/a |
| `creative-director` | 3 | 6 | 50% | 0 | 1 | 50% |
| `trend-scout` | 3 | 6 | 33% | 0 | 2 | 100% |
| `devrel` | 1 | 2 | 50% | 0 | 0 | 0% |
| `culture-scout` | 1 | 2 | 50% | 1 | 0 | n/a |

Method: 5 rated round(s), 11 awaiting an outcome; average rating 3.2 of 5; ideas used 23%.
<!-- scoreboard:end -->

## Retired personas

Stance-based ids used before the job-based roster. They are listed so old private transcripts
still make sense; they never appear in the public scorecards, and `score.py` rejects them:
`skeptic-cost`, `naive-user`, `mad-experimenter`, `ex-failure`, `regulator`, `future-self`,
`money-payer`, `competitor`, `maintainer`, `time-poor`, `solo-builder`, `wh-constraint`,
`adjacent-expert`, `simplifier`, `storyteller`, `data-realist`, `scale-believer`.
Do not cast them.
