# Canvases

The plugin ships two canvases, side panels the Copilot app shows beside a
conversation: the Orchi board, a view of the pool for one repository, and the
design board, where the user compares, rates, and picks design variants.
Sessions also open pages they built, such as a living prototype, in the app's
own Browser canvas. The
[canvases reference](../plugins/orchi/skills/orchi-core/references/canvases.md)
says when sessions open each one and how they take what the user does there.

## Structure

| Part | Defined in |
| --- | --- |
| The extension entry, which declares both canvases to the session | `plugins/orchi/extensions/orchi-canvases/extension.mjs` |
| The Orchi board: open, `refresh`, `update_pool`, `read_board`, its HTTP routes | `plugins/orchi/extensions/orchi-canvases/lib/board.mjs`, `ui/board.html` |
| The board's GitHub snapshot | `plugins/orchi/skills/orchi-core/scripts/board.py` |
| The design board: open, `publish_round`, `read_picks`, its HTTP routes | `plugins/orchi/extensions/orchi-canvases/lib/design-board.mjs`, `lib/rounds.mjs`, `ui/design-board.html` |
| The messages a confirmed button sends into the conversation | `plugins/orchi/extensions/orchi-canvases/lib/requests.mjs` |
| The loopback server and the files the canvases keep | `plugins/orchi/extensions/orchi-canvases/lib/server.mjs`, `lib/store.mjs` |
| When sessions open the canvases and what they do with requests | `plugins/orchi/skills/orchi-core/references/canvases.md` |

## How they load

The plugin manifest's `extensions` field points at `extensions/`; the Copilot
CLI that runs each app session loads every subfolder with an `extension.mjs`
as an extension of that session. `orchi-canvases` joins the session with the
two canvases, so the app lists `orchi-board` and `orchi-design-board` and the
model opens them with `open_canvas`. The extension uses only Node's standard
modules and the Copilot SDK the CLI provides, with no `package.json`.

Each open canvas gets a loopback server on `127.0.0.1` with an OS-chosen port.
Its URL carries a random token as the first path segment, and the server
answers only requests with that token and a `Host` of that address. It
accepts only JSON POSTs and pushes updates to the page through Server-Sent
Events. Pages use the app's theme tokens, with fallbacks.

## The Orchi board

The board is a view of the pool for one repository with two tabs.

- **Crews:** one sentence on what waits for the user, then one list of Orchi
  and its crews ordered by what needs a look first (waiting, stuck, working,
  in the background, idle, free), each with its status, what it does, since
  when, and an `N questions` badge, orange when one blocks work. Below it, the
  queue, the pool size, and the autonomous mode the user can switch, then the
  Orchi Summary: Orchi's answer in a few short paragraphs to "How are things
  going?" (what moved forward, what is in progress, what is stuck and why,
  problems or risks, what waits for the user, and what comes next), each
  opening with one bold sentence, then a muted line on what changed today. The
  board links each `#<n>` to its card and each crew name to its page, and the
  user can ask Orchi to refresh the summary.
- **A crew's page:** all its open questions in one list, each with its
  context, options with their consequences, the crew's recommendation, an
  optional note, and Send answer; a question that does not block work shows
  the answer the crew goes on with. A tool approval offers only Open session,
  because the app lets only that session answer it. Answered today closes the
  page.
- **Board:** a kanban on every level, in six columns: Needs planning,
  Backlog, In progress, Questions for you, Your review, and Done; the two
  columns that wait for the user have an orange top. Level one shows the
  Initiatives, plus Outside Initiatives for Epics, Tasks, Explorations, and PRs
  with no Initiative; an Initiative opens its Epics, and an Epic its Tasks.
  Breadcrumbs lead back, and each level opens with a sentence on its own
  scope. A Task opens a page with what the user decides there: a PR's changes,
  checks, and diff link with Approve and merge or Request changes; a plan's
  Tasks with Approve plan; a design round to rate on the design board; a
  question to answer; a tool approval to open in its session; a run's status;
  or Plan it. Its History, collapsed, lists its moves, with `↩` on a card that
  came back from review.

`board.py` builds the snapshot. It reads GitHub with `gh` (one GraphQL query
plus `status.py`): the Initiative, Epic, and Task tree, unlabelled Issues and
PRs with no Issue, PR checks and size, the claims, and the question and answer
comments. It combines them with what Orchi last reported through
`update_pool`: the crews as the app's session status shows them, the mode, the
pool size, the questions' `request_id`s and the fields no comment holds, the
summary, the queue, merges, deferred Issues, and held PRs.

Each Task card takes one column from the real state, in this order:

1. Closed: Done.
2. Deferred, with no blocking question: Backlog.
3. A blocking question: Questions for you, or Your review for a plan, a design
   round, or a merge.
4. A ready PR: Your review.
5. A PR, a claim, or a crew on it: In progress.
6. A Task, or a PR, not labelled `needs-planning`: Backlog.
7. Otherwise: Needs planning.

Orchi may name a column (`stages`) only where GitHub does not show the work
yet. An Epic or Initiative takes the first column its cards reach in the order
Questions for you, Your review, In progress, Needs planning, Backlog, Done; one
with no Tasks needs planning. Its progress counts Tasks, and a closed Epic
counts by its sub-issue summary. Comparing each snapshot with the last adds a
card's moves to its History; a move from Your review back to In progress is a
back-move.

The board refreshes every five minutes, on Refresh, and after each report. A
crew that holds work, runs nothing, and waits for nothing shows as stuck after
30 minutes without activity, and a background run after three hours.

The board writes nothing to GitHub. Every action is a request to Orchi: the
board shows the result at once with Undo for five seconds, then sends one
sentence into the conversation, such as `Answer question q4 of [dev-lead] pay:
Stripe`, with a note that it came from the board. Orchi checks the current
state and does it as if the user typed it, and the card moves when the real
state does. Answers go through Orchi as the pool reference's
[Questions and plans](../plugins/orchi/skills/orchi-core/references/pool.md#questions-and-plans)
says. A sent answer hides its question for up to an hour, until Orchi records
the answer. The user may drag a card only from Needs planning to Backlog (plan
it), from Backlog to In progress (take it), or back from In progress to
Backlog (defer it); any other drop shows `Orchi moves this card when the work
gets there.`

The board keeps its last snapshot, Orchi's last report, and the answers it
sent in the session's files (`files/orchi-board/<owner>__<name>.*.json`), only
to draw itself after a reload and to compare snapshots.

## The design board

A session gathers a round's files (HTML pages or images) under
`.orchi-tmp/board/v/<round>/` and publishes the round with its question and a
label per variant. The user moves between variants with the arrow keys, views
each at 1440 or 720 px scaled to fit, or full screen, scores it 1 to 5 with
the number keys, notes what works and what does not, picks with P, and presses
Round done, which sends a message into the conversation. The session then
reads the ratings with `read_picks`.

Variants run in a sandboxed frame without same-origin access, so a page cannot
read the board's data or send ratings. The server serves only files whose real
path lies under `v/`. Rounds and ratings live in `.orchi-tmp/board/`
(`rounds.json`, `ratings.json`), which Git ignores; what the user picked is
recorded in the Exploration's Design section or the design Epic. The board's
folder is the session's working directory unless the open input names a
`root`.

## The Browser canvas

The app's Browser canvas opens `http(s)` and `file://` URLs and lets the
session read the page, click, type, take screenshots, and reload. Sessions use
it for a living prototype and for built screens the user should keep beside
the conversation, and they check a change there before showing it.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| The canvases ship in the plugin through the legacy manifest's `extensions` field, a path to a folder of extension subfolders | It is the plugin format's only way to install an extension with the plugin; the CLI plugin reference lists the field, and a test plugin's extension loaded with it. In an Agent Plugins manifest (`$schema`), the field means something else | Asking the user to copy the extension into `~/.copilot/extensions/`; a project extension committed by `setup.py` | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| The board is a view: GitHub and Orchi's `update_pool` reports are its sources, and its stored files are only a cache to redraw | Git branches and GitHub Issues are the only shared state; a board that held state would become a controller | A board state database; the board changing Issues itself | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| A board button sends a sentence into the conversation, and Orchi checks the state before acting on it | Every action keeps one path, through the session that talks to the user and knows the pool's rules | Board actions that call `gh` directly | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| Orchi keeps the user's open questions as Issue or PR comments ending `<!-- orchi:question {...} -->`, and records each answer as `<!-- orchi:answer {...} -->` | A crew may have several questions open while it goes on, and they must survive restarts; Git branches and GitHub Issues are the only shared state, and a comment also tells people what was asked | A question file or database; holding them only in Orchi's context; one `ask_user` per crew, which stops its work | [nkhus/orchi-copilot#5](https://github.com/nkhus/orchi-copilot/pull/5) |
| Answers from the board go through Orchi: `answer_session_input` with the exact `request_id` and choice, plans through `respond_to_session_plan_v2`, kept questions by message; a tool approval only in the crew's session | Orchi checks the question is still open and keeps one path for the user's answers; the app lets only the asking session answer a tool approval | The board answering sessions itself | [nkhus/orchi-copilot#5](https://github.com/nkhus/orchi-copilot/pull/5) |
| Cards move from the real state; the user may drag only Needs planning → Backlog, Backlog → In progress, and In progress → Backlog, each a request | The other columns mean something happened (a question, a ready PR, a merge) that a drag cannot make true | Free drag-and-drop that edits labels | [nkhus/orchi-copilot#5](https://github.com/nkhus/orchi-copilot/pull/5) |
| The Orchi Summary is prose: Orchi's answer to "How are things going?" in a few short paragraphs with a bold lead each, not labelled fields | The user wants to read where things stand, what is stuck and why, and what waits for them, the way a lead would tell it; fixed labels left gaps and repeated the crew list | Labelled lines (Progress, Waits on you, Risks, Next, Today); a progress bar | [nkhus/orchi-copilot#5](https://github.com/nkhus/orchi-copilot/pull/5) |
| A request waits five seconds with Undo before it is sent | A click in a side panel is easy to make by mistake, and a sent message cannot be taken back | A confirm dialog per action | [nkhus/orchi-copilot#5](https://github.com/nkhus/orchi-copilot/pull/5) |
| Deferred Issues and held PRs are recorded as comments (`Deferred at the user's request on <date>`, `Resumed ...`, `Held ...`) | They must survive a restart, and GitHub holds every fact the pool relies on | Labels, which would need setup in each repository; a notes file | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| Each canvas's server binds to loopback with a random path token and a `Host` check, and accepts only JSON POSTs; variants run sandboxed without same-origin access | A button sends messages in the user's name, so no other local process, page, or variant may reach it | An unauthenticated loopback server; variants in same-origin frames | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| `board.py` runs with the Python 3 already required for the bundled scripts, and `gh` signed in through its keyring | The board reuses `status.py`, and the extension's environment does not pass `GITHUB_TOKEN` | A Node rewrite of the status logic | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
