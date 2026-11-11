# Workflow

The core workflow every Orchi session follows: research and agree scope with the
user, track proportional work as a Task, Epic, or Initiative in GitHub Issues,
deliver it on Git branches, review it once, and leave merging and deployment to
the user's authority. The user talks only to Orchi, the conversation of the
repository's Copilot Project (or types `/orchi`); Orchi runs the workflow through
[crews](pool.md), child sessions that each hold one role.

## Structure

| Part | Defined in |
| --- | --- |
| Routing, scope, and core rules | `skills/orchi-core/SKILL.md` |
| Exploration of an idea before any scope | `skills/orchi-explore/SKILL.md`, `references/exploration.md` |
| Planning, readiness, and Issue conventions | `skills/orchi-plan/SKILL.md`, `references/planning.md`, `references/readiness.md`, `references/github.md` |
| Delivery, review, and verification | `skills/orchi-deliver/SKILL.md`, `references/execution.md`, `references/review-delivery.md`, `references/testing.md` |
| Subagent roles | `agents/orchi-*.agent.md`, the plugin's custom agents; `references/roles.md` says which writer to start and how to continue it |
| Readiness of tracked work | `scripts/status.py`, read-only, from GitHub |
| Issue forms and the PR template | `skills/orchi-core/assets/github/`, written into a repository by [setup](installation.md#repository-setup) |

Paths are inside `plugins/orchi/`; paths under `references/`, `scripts/`, and
`assets/` are inside `skills/orchi-core/`. Each detailed rule has one home in a
reference, and `SKILL.md` files link to it instead of repeating it. Scripts run
from the repository root as `python3 <orchi-core>/scripts/<script>.py`, where
`<orchi-core>` is the orchi-core skill's base directory, which Copilot shows
when the skill loads.

The six custom agents and the work they do:

| Agent | Model | Writes | Role |
| --- | --- | --- | --- |
| `orchi-scout` | `claude-haiku-5.5` | nothing | Returns paths, line ranges, and excerpts |
| `orchi-researcher` | `claude-opus-5.5` | nothing | Answers a question from cited primary sources, or designs one option under a given lens |
| `orchi-implementer` | `claude-opus-5.5` | one commit per run | Runs the Task readiness gate, then implements and verifies one Task |
| `orchi-fixer` | `claude-sonnet-5.5` | one commit per run | Makes one small, fully specified change or a confirmed repair, and escalates anything larger |
| `orchi-reviewer` | `claude-opus-5.5` | nothing | Reviews a Task, an assembled Epic, or a final Initiative candidate |
| `orchi-designer` | `claude-opus-5.5` | one commit per UI Task; files in `.orchi-tmp/` for wireframes, variants, and mockups; nothing when auditing | Builds design variants and UI Tasks, or audits a UI diff ([design](design.md)) |

Sessions start them with the `task` tool and `agent_type` set to the agent's
name. The read-only agents (`orchi-scout`, `orchi-researcher`,
`orchi-reviewer`) have no `edit` tool. Subagents never talk to the user, change
Issues, push, or merge; their reports are claims the session verifies.

## Contracts

- Git branches and GitHub Issues are the only shared state; the bundled scripts
  only read, except `setup.py`, which prepares a repository.
- Branches: `fix/<slug>` from main for a standalone Task; `epic/<tag>-<slug>`
  from main for a standalone Epic; `initiative/<tag>-<slug>` from main with one
  `epic/<tag>-<epic-tag>-<slug>` branch per Epic into it; Tasks on their Epic
  branch, and `task/<slug>` for a dev lead's parallel Tasks;
  `explore/<slug>` for an exploration's working documents.
- A target repository's own instructions (`AGENTS.md` and scoped instruction
  files) take precedence over Orchi's defaults.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds. Entries carried over from the Claude Code
edition link the upstream PR that made them ([upstream](upstream.md)).

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| The roles are custom agents shipped in the plugin's `agents/` directory, each with its model and tool list in its profile; sessions start them with `task` | A plugin installs custom agents directly, so nothing needs to render role files into the repository | Rendering role files into each repository, as the Claude Code installer does | [nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2) |
| An entirely new product, site, or interface may start in prototype mode: the exploration's Frame phase runs as a detailed interview, variant rounds, and a living prototype the user changes by remark, while the session keeps asking about states, edge cases, roles, and flows; when the user says to build it, the Issue records every decision, requirement, parked idea, and open question, and Research, Diverge, Design, Converge, and Shape follow with the prototype as the user's input; features, fixes, and redesigns of an existing product never use it | Prompt-to-app builders feel fast because the user reacts to a running app at once, but they build before asking and skip product research; the user sees the prototype as an enriched interview, which must not cancel the research and design work after it | A route that replaces the research and design phases; building from the first prompt without an interview | [nkhus/orchi#64](https://github.com/nkhus/orchi/pull/64), [nkhus/orchi#65](https://github.com/nkhus/orchi/pull/65) |
| The user works on the concept, the vision, and the design; agents decide everything technical (stack, architecture, tools, checks and exceptions, tests, branches, and how work splits into Issues) and record why, and ask the user only about a technical problem's consequence for what they get, its cost, or its timing; the user agrees a plan as what they will see and do, in order, not its Tasks or blockers | The user never reads the code; in a live run, questions about licenses and Task granularity reached a user who cannot weigh them | Asking the user to confirm the breakdown's granularity and blockers; escalating a failing check to the user | [nkhus/orchi#55](https://github.com/nkhus/orchi/pull/55) |
| A dev lead reads a writer's diff and check output and pushes; CI runs the suite on the pushed commit, and the dev lead reruns locally only a check CI lacks or whose output is missing | Rerunning the full suite on a clean worktree after every Task doubled each Task's checks, and CI runs them anyway | Rerunning every writer's checks locally before pushing | [nkhus/orchi#55](https://github.com/nkhus/orchi/pull/55) |
| The user talks only to Orchi (the Project's conversation, or `/orchi`); every other skill is hidden from the menu and runs only as a crew's assignment, and a session outside Orchi's crews answers questions and points work to Orchi | The user talks to one conversation and never needs to know which role skill comes next; crews report to Orchi, and Orchi brings back only decisions | Entry skills the user could type in a solo session | [nkhus/orchi#51](https://github.com/nkhus/orchi/pull/51) |
| Every PR lists each review finding with its resolution or `unresolved`; `blocker` and `major` findings are repaired before the PR is marked ready (in a proof of concept, a `major` is listed as `follow-up`); a `major` is a demonstrated defect a user or the next change will hit, with its scenario and the rule it breaks; a review that finds nothing is valid; the one follow-up checks only the repairs and their regressions, and its verdict is final | Orchi's merge in autonomous mode relies on the PR body, and nobody reads the code after the review; a reviewer asked for defects always finds some, and review loops otherwise never end | Repairing only `blocker` findings with no record of the rest; an undefined `major`; a recheck that reviews the changed paths again | [nkhus/orchi#49](https://github.com/nkhus/orchi/pull/49), [nkhus/orchi#57](https://github.com/nkhus/orchi/pull/57) |
| An exploration names each assumption its direction cannot work without that nothing has shown yet (an external service or model, access, data) and proves it with a prototype before shaping, without asking; it asks only for access the user alone can grant | In a live run a demo built around a hosted model went through planning and an hour of setup without anyone checking the model could be reached | Prototypes only when the user agrees; finding out in delivery | [nkhus/orchi#57](https://github.com/nkhus/orchi/pull/57) |
| When Orchi sends an assignment again after an interruption, the crew resumes from the claim, the Issue, and the PR's `Handoff` | A resumed assignment can run in a new session, which must not read its own claim as another owner's | Session-only claim matching | [nkhus/orchi#49](https://github.com/nkhus/orchi/pull/49), [nkhus/orchi#51](https://github.com/nkhus/orchi/pull/51) |
| The branch hierarchy stays: Initiative branch from main, Epic branches from it, Tasks on their Epic branch | Working documents change several times before they settle; a branch per level lets each settle locally and move into the current documentation at its merge | Flat branches from main for every piece of work | [nkhus/orchi#45](https://github.com/nkhus/orchi/pull/45) |
| `orchi-reviewer`'s own profile carries every check the review must make, including `ENGINEERING.md` and gate integrity, exceptions, acceptance evidence, and the documentation map | Nobody reads the code after the reviewer, and an agent reads its own profile, not the whole review reference | Relying on the review reference alone | [nkhus/orchi#47](https://github.com/nkhus/orchi/pull/47) |
| The core skill is `orchi-core`, hidden from the menu and loaded by sessions themselves; `orchi` is the explicit-only entry | Every session reads the core workflow, while the entry holds the authority to start crews and to merge in autonomous mode, so it stays explicit | `orchi` as the core skill | [nkhus/orchi#43](https://github.com/nkhus/orchi/pull/43) |
| A rule stays in skill text only if it prevents an observed or near-certain costly error and is the cheapest way to do so; new roles aside, skill text does not grow | Every line costs context in every session, and rules nobody needed dilute the ones that matter | Adding a rule for each anticipated mistake | [nkhus/orchi#42](https://github.com/nkhus/orchi/pull/42) |
