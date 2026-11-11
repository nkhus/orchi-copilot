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

The board shows, for one repository:

- **Waiting for you:** each crew waiting for the user's input with its
  question, Orchi's own questions, PRs waiting for the user's yes to merge, and
  stuck crews. The user can answer, reply, merge, or hold there.
- **Crews:** each crew by what needs a look first (stuck, waiting, working,
  running in the background, idle, free), with its Issue, what it does, and
  since when; the autonomous mode, which the user can switch, and the pool
  size. The user can ask a crew for its status.
- **Backlog:** the Initiative, Epic, and Task tree from `status.py`, the
  planning queue, open PRs with their checks, and recent merges. The user can
  take, plan, defer, or resume an item.

`board.py` reads GitHub with `gh` (one GraphQL query plus `status.py`) and
combines it with what Orchi last reported through `update_pool`: the crews as
the app's session status shows them, the mode, the pool size, Orchi's
questions, merges, deferred Issues, and held PRs. The board refreshes every
five minutes, on Refresh, and after each report. A crew that holds work, runs
nothing, and waits for nothing shows as stuck after 30 minutes without
activity, and a background run after three hours.

The board writes nothing to GitHub. A button the user confirms sends one
sentence into the conversation, such as `Defer #12: start no work on it until I
resume it.`, followed by a note that it came from the board. Orchi checks the
current state and does it as if the user typed it. Deferring and holding are
recorded as comments on the Issue or PR, so they survive a restart without a
state file.

The board keeps its last snapshot and Orchi's last report in the session's
files (`files/orchi-board/<owner>__<name>.*.json`), only to draw itself after a
reload.

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
| Deferred Issues and held PRs are recorded as comments (`Deferred at the user's request on <date>`, `Resumed ...`, `Held ...`) | They must survive a restart, and GitHub holds every fact the pool relies on | Labels, which would need setup in each repository; a notes file | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| Each canvas's server binds to loopback with a random path token and a `Host` check, and accepts only JSON POSTs; variants run sandboxed without same-origin access | A button sends messages in the user's name, so no other local process, page, or variant may reach it | An unauthenticated loopback server; variants in same-origin frames | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| `board.py` runs with the Python 3 already required for the bundled scripts, and `gh` signed in through its keyring | The board reuses `status.py`, and the extension's environment does not pass `GITHUB_TOKEN` | A Node rewrite of the status logic | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
