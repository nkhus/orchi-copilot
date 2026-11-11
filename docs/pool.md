# Pool

How Orchi runs work in the Copilot app: one conversation, Orchi, takes the
user's requests and runs each one through a crew, a child session that holds one
role. GitHub Issues, branches, and PRs hold every fact the pool relies on;
messages only wake a session and point it at that state, so a session that
restarts rebuilds its picture from Issues, PRs, claims, and the app's session
list. The [pool reference](../plugins/orchi/skills/orchi-core/references/pool.md)
defines the rules; this page says how they fit the app.

A standing pool of sessions with workers, unattended operation, and a board of
the pool are not built yet; they come with the pool Epic
([nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3)).

## Structure

| Part | Defined in |
| --- | --- |
| Orchi, the entry: start, requests, reconcile, crew events, what it never does | `plugins/orchi/skills/orchi/SKILL.md` |
| Sessions, roles, repository preparation, assignment, messages, autonomous mode, workers, release, stalls, follow-ups, Initiatives, lessons | `plugins/orchi/skills/orchi-core/references/pool.md` |
| Repository preparation | `plugins/orchi/skills/orchi-core/scripts/setup.py` ([installation](installation.md#repository-setup)) |
| The worker skill, for a crew's task message that names it | `plugins/orchi/skills/orchi-work/SKILL.md` |

## Orchi

The user creates a Copilot Project for the repository and talks to it; its
conversation is Orchi. Typing `/orchi` in the Project, or in a plain session,
starts the entry skill explicitly; the skill sets `disable-model-invocation`, so
the model never starts it on its own. Orchi works in a plain session too; its
crews are then that session's child sessions.

Orchi plans, researches, designs, and writes no code. It routes each request,
relays what crews report, and says what waits for the user. When the user asks
how things go, it answers from `status.py`, Issues, PRs, and
`get_sessions_status` in at most 15 lines.

On every start, Orchi checks the repository read-only: a GitHub remote, `gh`
authenticated, a pushed default branch, `setup.py --check` passing, and the
setup committed and pushed. When something fails, it starts one setup subagent
(`task` with `agent_type: general-purpose`) that runs setup in a temporary
worktree of the default branch, checks the staged files for secrets, and commits
`Set up Orchi` to the default branch, or opens a `chore/orchi-setup` PR when
GitHub refuses the push. The user is asked only what they alone can answer: no
remote, `gh` not signed in, a possible secret, a refused setup, and the setup PR.

## Crews

Orchi starts one crew per request with `create_session`: a worktree session of
the repository, named `[<role>] <topic>`, with `coordinate_with_creator: true`,
`notify_on_idle: "always"`, and the assignment as its kickoff prompt. The crew
invokes its role's skill:

| Role | Skill | Holds |
| --- | --- | --- |
| Researcher | `orchi-explore` | One idea, with the user |
| Planner | `orchi-plan` or `orchi-standards` | One request, Exploration, `needs-planning` Issue, or a standards audit |
| Designer | `orchi-design` | One standalone `design` Epic, with the user |
| Dev lead | `orchi-deliver` | One standalone Task, standalone Epic, or Initiative |

Before giving a crew an Issue, Orchi claims it: `in-progress`, the assignee,
and `Assigned to [<role>] <topic> (<session id>) by Orchi on <date>`. A
researcher continues as the planner, and a planner continues with one ready item
it planned. While autonomous mode is off, a crew talks to the user in its own
session, and the Project shows its questions in Orchi's conversation too.

A crew writes no product code. A dev lead or designer gives each change to a
writer subagent (`task` with `orchi-implementer`, `orchi-fixer`, or
`orchi-designer`, in background mode, continued with `write_agent`), reads its
report and diff, and pushes. `orchi-work` describes standing worker sessions; it
runs only when a crew's task message names it, and those sessions come with the
pool Epic.

## Messages

A crew reports to Orchi with `send_session_message`, using Orchi's session id
from its kickoff: `purpose: progress` for `started` and `now <role>`,
`needs_input` for a question, `handoff` for a result, and `error` for what stops
it. Each message is one line that names the Issue or PR; anything longer goes
into an Issue comment. Only the owner's messages carry authority: a crew obeys
Orchi, and Orchi obeys the user.

When a crew's work is done, Orchi sends `release`; the crew confirms nothing
would be lost and replies `released`, and Orchi archives it with
`archive_session`. Nobody deletes a session.

## Autonomous mode

Off by default; the user turns it on or off by telling Orchi, and Orchi states
it in every report. While it is off, crews ask the user, and Orchi merges into
main only on the user's yes. While it is on, crews ask only Orchi, Orchi decides
direction, scope, and design as stated assumptions and lists them for the user,
crews run in `autopilot` mode, and Orchi merges a PR into main when its checks
pass, its review leaves no unresolved `blocker` or `major`, and its main outcome
is proven on the real path. In both modes only the user decides money, access
and credentials, deploying, anything destructive or irreversible, removing
something users have today, and a change of an Initiative's direction; a claim
verified only as `Limited` or `Not established` merges only on the user's yes.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| Orchi is the conversation of a Copilot Project, and crews are its child sessions started with `create_session` and messaged with `send_session_message` | The Project lists its child sessions by state (needs input, working, done) and shows their questions in its conversation, which is the overview the user needs | A host-specific session sidebar; pasting commands into new sessions | [nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2) |
| Orchi prepares the repository itself on start, through a setup subagent that commits and pushes, and asks the user only what they alone can answer | Crews' worktrees and CI start from the default branch on GitHub, so an uncommitted setup breaks every crew | Asking the user to run setup, commit, and push | [nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2) |
| Writers run as `task` subagents of a crew, not as standing sessions | The standing pool and its workers belong to a later Epic; subagents give each change a fresh context now | Building worker sessions before the pool Epic | [nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2) |
