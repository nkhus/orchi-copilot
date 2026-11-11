# Pool

How Orchi runs work in the Copilot app: one conversation, Orchi, takes the
user's requests and runs each one through crews, child sessions that each hold
one role for their whole life. Only Orchi starts sessions; a crew gives code,
long runs, and parallel work to subagents. GitHub Issues, branches, and PRs hold every fact the pool relies on;
messages only wake a session and point it at that state, so a session that
restarts rebuilds its picture from Issues, assignees, branches, PRs, and the
app's session status. The [pool reference](../plugins/orchi/skills/orchi-core/references/pool.md)
defines the rules; this page says how they fit the app.

## Structure

| Part | Defined in |
| --- | --- |
| Orchi, the entry: start, requests, reconcile, crew events, what it never does | `plugins/orchi/skills/orchi/SKILL.md` |
| Sessions, roles, repository preparation, assignment, messages, questions and plans, autonomous mode, merge, writers, release, stalls, limits, status, updates, remote control, follow-ups, Initiatives, lessons | `plugins/orchi/skills/orchi-core/references/pool.md` |
| Repository preparation | `plugins/orchi/skills/orchi-core/scripts/setup.py` ([installation](installation.md#repository-setup)) |

## Orchi

The user creates a Copilot Project for the repository and types `/orchi` once
in its conversation; from then on that conversation is Orchi. The skill sets
`disable-model-invocation`, so the model never starts it on its own. Orchi works
in a plain session too; its crews are then that session's child sessions, and
the Project's grouping and question mirror are missing. When the Project
conversation has no checkout of its own, Orchi works read-only in the
repository's local checkout (`main_repo_path` from `list_repositories`) and
passes the Project's id to `create_session`.

Orchi plans, researches, designs, and writes no code. It routes each request,
relays what crews report, merges on the user's yes, and says what waits for the
user. Asked how things go, it answers from `status.py` and
`get_sessions_status` in at most 15 lines: in work, stuck, waiting for the user,
and done.

On every start, Orchi checks the repository read-only: a GitHub remote, `gh`
authenticated, a pushed default branch, `setup.py --check` passing, and the
setup on the default branch on GitHub. When something fails, it starts one setup
subagent (`task` with `agent_type: general-purpose`) that runs setup in a
temporary worktree on the branch `chore/repository-setup`, checks the staged
files for secrets, commits `chore: set up development rules and checks`, and
opens a PR to the default branch; only a repository without commits gets a
direct initial push. It never pushes to a default branch that has commits. The
user is asked only what they alone can answer: no remote, `gh` not signed in, a
possible secret, a refused setup, and merging the setup PR, which Orchi does not
wait for. Every session that writes in another clone, such as a Cloud crew, runs
`setup.py --exclude` there so `.orchi-tmp/` stays out of Git.
Orchi then reads its automations for the autonomous mode, checks for a newer
Orchi, and, once per repository, recommends remote control.

## Crews

Orchi starts one crew per role a request needs with `create_session`: a worktree session of
the repository, named `[<role>] <topic>`, with `coordinate_with_creator: true`,
`notify_on_idle: "always"`, and the assignment as its kickoff prompt. The
kickoff always names a mode, `interactive` while autonomous mode is off and
`autopilot` while it is on, because the app starts a kickoff in plan mode
otherwise. A crew runs in a Cloud sandbox instead of a local worktree only when
the user asks to keep work off their machine or to run many crews at once. The
crew invokes its role's skill:

| Role | Skill | Holds |
| --- | --- | --- |
| Researcher | `orchi-explore` | One idea, with the user |
| Planner | `orchi-plan` or `orchi-standards` | One request, Exploration, Issue that needs a plan, or a standards audit |
| Designer | `orchi-design` | One standalone Design Epic, with the user |
| Dev lead | `orchi-deliver` | One standalone Task or Epic, one Epic of an Initiative, or an Initiative whose Epics are all closed, for its final integration |

Before giving a crew an Issue, Orchi takes it by assigning the user
(`gh issue edit <n> --add-assignee @me`) and writes nothing in its body; the
crew's assignment and reports name its session, role, and Issue. Work that
someone else assigned, branched, or opened a PR for is taken, so Orchi leaves
it alone.

A crew never takes another role. A researcher reports `shaped` when the user
confirms the shape, and Orchi starts a planner for the Exploration. A planner
reports `planned`, and Orchi starts a designer for each ready Design Epic and a
dev lead for each other ready standalone Task or Epic, an Initiative's Epics
included, each in its own worktree and branch. Ready items with no open blocker
run in parallel; an item whose blocker is open starts when Orchi sees the
blocker close, on a reconcile or a `done` or `merged` message. A crew whose
request belongs to another role reports `needs a <role>`, and Orchi starts that
role. Each request the user makes gets a crew at once; a plan's ready items,
and work Orchi takes by itself, wait while three crews hold work, unless the
user names another pool size. An Initiative goes to a dev lead for its final
integration once every Epic is closed and no crew holds one.

Only Orchi starts sessions. Child sessions of a Copilot Project cannot call
`create_session`, and one owner for every session keeps the pool visible in the
Project's list.

## Writers

A crew writes no product code and starts no session. A dev lead or designer
gives each change to a writer subagent (`task` with `orchi-implementer`,
`orchi-fixer`, or `orchi-designer`, in background mode, continued with
`write_agent` for a rework) and reads its report and diff before it pushes.

Git lets only one worktree check out a branch, so a crew runs an Epic's Tasks
one at a time in its own worktree by default. Tasks that touch different files
may run in parallel, each writer in a `task/<slug>` worktree under
`.orchi-tmp/worktrees/` that the crew merges into the Epic branch. Runs the crew
should not wait on (the full suites, a stand, a real-path run) go to a verifier,
a background `task` subagent with `agent_type: general-purpose` in a detached
worktree of the head it checks. A crew runs at most three writers and verifiers
at once, and removes their worktrees when it is released.

## Messages

A crew and Orchi message each other with `send_session_message`; crews never
message each other. Each message is one line that names
the Issue or PR; anything longer goes into an Issue comment. A report passes a
`purpose`, so the app wakes the owner only when it should: `progress` for
`started` and `waits for`, `handoff` for a result (`shaped`, `planned`,
`needs a <role>`, `PR ready`, `done`, `released`), `needs_input` for a question for the user, and `error`
for what stops it. It also passes the `assignment_id` of the owner's latest
message about that work. Only the owner's messages carry authority: a crew obeys
Orchi, and Orchi obeys the user.

## Questions and plans

While autonomous mode is off, a crew asks the user in its own session with
`ask_user`. In a Project, the app shows that question in Orchi's conversation
as well, and Orchi only says once which crew waits and for what. In a plain
session, Orchi can show the question in its own conversation with
`relay_session_input` when the user prefers to answer there. A question the user
must answer in the crew's own session (signing in, credentials) is marked
`(user, here)`, and Orchi only names the crew.

While the mode is on, a crew asks Orchi by message; a question already waiting
in a crew's session is answered with `answer_session_input`, and a pending plan
with `respond_to_session_plan_v2`, unless the question is the user's own. Crews
never start in plan mode, so a pending plan is rare.

## Autonomous mode

Off by default; the user turns it on or off by telling Orchi, and Orchi states
it in every report. While it is off, crews ask the user, and Orchi merges into
main only on the user's yes. While it is on, crews ask only Orchi, Orchi decides
direction, scope, and design as stated assumptions and lists them for the user,
crews record those decisions in the Issue's decision log as decided on the
user's behalf, without naming Orchi,
crews run in `autopilot` mode, and Orchi merges a PR into main when its checks
pass, its review leaves no unresolved `blocker` or `major`, and its main outcome
is proven on the real path. In both modes only the user decides money, access
and credentials, deploying, anything destructive or irreversible, removing
something users have today, and a change of an Initiative's direction; a result
verified only as `Limited` or `Not established` merges only on the user's yes.

Switching the mode changes each crew's session mode through
`send_session_message`. While the mode is on, Orchi keeps a reconcile
automation on itself with `save_session_automation`, every 30 minutes, so the
pool keeps moving while the user is away; it removes the automation when the
mode goes off, and on start it reads the mode from whether that automation
exists.

## Merge

Agent Merge, the app's PR shepherd, addresses review comments, fixes CI,
resolves conflicts, and lands the merge only with its `merge_pr` action. Orchi
turns it on for the crew whose session the PR belongs to with
`manage_agent_merge`:

- with autonomous mode off, after the user's yes to that PR, when GitHub cannot
  merge it right away; with `merge_pr`, which the app asks the user to confirm;
- with autonomous mode on, without `merge_pr`, and Orchi merges the PR with
  `gh pr merge` itself once the autonomous conditions hold.

When the PR can merge at once, Orchi merges it with `gh pr merge`. When the app
refuses Agent Merge, Orchi tells the user once and sends repairs to the crew as
rework. After any merge, Orchi sends the crew `merged`.

An Epic of an Initiative opens its PR into the Initiative branch, and Orchi
merges it as well: on the user's yes, while autonomous mode is on, or when the
Initiative carries the user's grant for Epic merges. Before each such merge it
checks that the Epic branch is not behind the Initiative branch, sends
`rework: update from the Initiative branch` when it is, and merges one PR at a
time. Once every Epic is closed, Orchi starts a dev lead for the Initiative's
final integration and its final PR into main.

## Release and stalls

When a crew's work is done, Orchi sends `release`; the crew stops its
subagents, removes their worktrees, confirms nothing would be lost, and replies `released`, and Orchi
archives it with `archive_session`, which keeps its history. Nobody deletes a
session, and Orchi archives only a released crew.

`notify_on_idle` wakes Orchi whenever a crew goes idle. On each wake, Orchi reads
`get_sessions_status` for questions, pending plans, errors, and interruptions,
and asks a crew that holds work, waits for nothing, and went quiet
`<id> status?` once; a crew that still does not answer is reported to the user.

## Updates and remote control

Orchi compares its installed version with the `orchi-copilot` marketplace's at
start. On the user's yes it runs `copilot plugin update orchi@orchi-copilot`, or
asks the user to update it on the app's Customize page, then rereads its skills,
prepares the repository again, and tells every busy crew to invoke its skill
again; Issues, branches, PRs, and conversations stay.

Once per repository, Orchi recommends remote control, so the user can follow
and steer the pool from GitHub on the web or GitHub Mobile. On their yes, its
setup agent sets `automation.remote_control: true` in `.github/github-app.yml`
on the branch `chore/remote-control` and opens a PR, which Orchi merges on the
user's yes; the app applies it after the user accepts the changed
configuration, and an organization's policy can still keep it off.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| Orchi is the conversation of a Copilot Project, and crews are its child sessions started with `create_session` and messaged with `send_session_message` | The Project lists its child sessions by state (needs input, working, done) and shows their questions in its conversation, which is the overview the user needs | A host-specific session sidebar; pasting commands into new sessions | [nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2) |
| Orchi prepares the repository itself on start, through a setup subagent that opens a `chore/repository-setup` PR, and asks the user to merge it; only an empty repository gets a direct initial push | Crews' worktrees and CI start from the default branch on GitHub, and a change to a shared repository goes through review like any other; the setup agent never pushes to a default branch with commits | Asking the user to run setup; committing setup straight to the default branch (reversed in [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7)) | [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7) |
| The user starts Orchi by typing `/orchi` once in the Project; the entry skill keeps `disable-model-invocation` | The model cannot be relied on to start a skill from plain words, and a conversation that turns into Orchi by accident would start crews the user did not ask for | Letting the model invoke the entry skill; project instructions that make every Project conversation Orchi | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| A Project conversation without a checkout works read-only in the repository's local checkout and passes `project_id` to `create_session` | Orchi needs the repository's files and `gh` context; a crew must land in the same repository | Asking the user for a path; a worktree for Orchi itself | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| Every kickoff names its mode: `interactive` or `autopilot` | The app starts a kickoff in plan mode otherwise, and a plan waiting for approval stalls the pool | Plan mode for crews; `autopilot` worker kickoffs (workers removed in PRREF) | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3), PRREF |
| Crews run in local worktrees; a Cloud sandbox only when the user asks, and a crew there uses subagents only | Local crews give `see it at` links and the user's own tools; whether Orchi's plugin is installed in a sandbox is unverified, so a Cloud crew reports `cannot continue` when it is not | Cloud by default | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| Each role is its own crew: a researcher ends at `shaped`, a planner at `planned`, and Orchi then starts the next role's crew, one dev lead or designer per ready item, in parallel when nothing blocks | One crew carrying a request through its roles ended up exploring, planning a ten-Epic Initiative, and delivering it in one session, instead of dedicated sessions; a crew's name now matches its role for its whole life | One crew that continues into the next role and reports `now <role>` (reversed in PRREF) | PRREF |
| Only Orchi calls `create_session`; crews work through subagents only | Child sessions of a Copilot Project cannot start sessions, and one owner keeps every session in the Project's list | Crew-started worker sessions and planner-started sub-planners (reversed in PRREF) | PRREF |
| Reports pass a `purpose` and the `assignment_id`; messages down pass none or the existing one | The app wakes a coordinator only for results, questions, and errors, and ties each report to its assignment | One-line messages without metadata | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| Questions stay in the crew's session; Orchi relays or answers them with the app's tools, never by asking again | The Project already mirrors questions; asking twice splits the answer | Orchi re-asking each crew question in its own conversation | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| Agent Merge shepherds a PR; `merge_pr` only on the user's yes to that PR, and Orchi merges itself in autonomous mode | Agent Merge repairs CI, reviews, and conflicts without a crew's turn, but merging stays within the user's authority | Agent Merge with `merge_pr` whenever autonomous mode is on; no Agent Merge | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| Writers are background subagents in the crew's worktree, one at a time by default; parallel Tasks get `task/<slug>` worktrees under `.orchi-tmp/worktrees/`, and long runs a verifier subagent in a detached worktree | Git lets one worktree check out a branch, so parallel writers need their own worktrees, and a subagent needs no session | A standing pool of workers built ahead and cleared after each task; a per-task worker session of the crew (reversed in PRREF) | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3), PRREF |
| Each Epic of an Initiative has its own dev lead and PR into the Initiative branch; Orchi merges those PRs one at a time after a behind check, and a new dev lead does the final integration once every Epic is closed | Epics without blockers between them run in parallel, and one merger keeps the Initiative branch consistent | One dev lead delivering every Epic in turn; dev leads merging into the Initiative branch with `--merge-epics` (reversed in PRREF) | PRREF |
| Autonomous mode keeps a 30-minute reconcile automation on Orchi, whose existence records the mode | The pool must move while the user is away, and the mode must survive a restart without a state file | A notes file; a dashboard snapshot check | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| Stalls come from `notify_on_idle` and `get_sessions_status` | The app reports idle, busy time, questions, plans, and errors per session | Polling sessions; process lines in Issues | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| The pool size is 3 for work Orchi takes by itself and a plan's ready items; the user's requests start at once | Bounds parallel sessions and rate limits without making the user wait | A fixed pool built at start | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| Orchi updates itself through the plugin marketplace on the user's yes and re-invokes busy crews | Plugin files change, while Issues, branches, PRs, and conversations stay | Reinstalling per repository | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3) |
| Remote control is recommended once and set in `.github/github-app.yml` through a `chore/remote-control` PR that Orchi merges on the user's yes | The app reads it from the repository's configuration, the user must accept it there, and a change to the repository goes through a PR | Toggling it per session; pushing it to the default branch | [nkhus/orchi-copilot#3](https://github.com/nkhus/orchi-copilot/issues/3), [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7) |

| Orchi takes an Issue by assigning the user; a crew's session, role, and Issue live in its assignment and reports, and crew names, the Summary, the mode, and the pool size appear only on the user's board | Other people and assistants must see ordinary GitHub state: an assignee and a branch say the work is taken | Claim lines in Issue bodies, an `in-progress` label, a pinned pool Issue, `decided by Orchi` in decision logs (reversed in [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7)) | [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7) |
| Work anyone else took, assigned or with a linked branch or PR, is taken for the pool too, and Orchi takes by itself only Issues that say `Requested by: @<the user's login>` | A person or another assistant may work in the repository without knowing about Orchi | Labels that mark Orchi's own work (reversed in [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7)) | [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7) |
| What setup writes prescribes no way of tracking work: no Issue rules in `AGENTS.md` and no labels; Orchi tracks its own work in Issues and creates a missing type label when it first files such an Issue | The repository belongs to the team, and only Orchi's pool needs its work in Issues; other developers keep their own way of tracking | Setup creating the type labels, and `AGENTS.md` telling everyone to track work in Issues and leave taken Issues alone, both reversed | [#7](https://github.com/nkhus/orchi-copilot/issues/7) |