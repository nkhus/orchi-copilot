# Canvases

Use when the app lists the plugin's canvases, `orchi-board` and `orchi-design-board`, or a session shows the user
pages it built. The canvases are views beside the conversation: GitHub, the branches, and what Orchi reports hold the
state, and every decision still happens in the conversation. When a canvas is missing or fails to open, say so in one
line and go on in the conversation as if it did not exist.

## The Orchi board

The board shows the pool for one repository: what waits for the user (crews' questions, Orchi's questions, PRs to
merge, stuck crews), each crew and what it does, the backlog tree from `status.py`, and open PRs with their checks. It
reads GitHub through `scripts/board.py` every five minutes and on Refresh, and adds what only Orchi knows from its
`update_pool` reports. It writes nothing to GitHub.

1. **Open it** at the start of Orchi's conversation, and whenever the user asks for it: `open_canvas` with canvasId
   `orchi-board`, instanceId `orchi-board`, and input `{"repo": "<owner>/<name>"}`. Opening the same instanceId again
   focuses it.
2. **Report** after each reconcile and whenever the Status answer would change for the user: `invoke_canvas_action`
   `update_pool` on `orchi-board` with every crew from `get_sessions_status` (`name`, `session_id`, `state`, and
   `issue`, `doing`, `question`, `background`, `since`, `stuck` when known), `mode`, `limit`, Orchi's own open
   `questions` (a short id and the text), `merges` (PRs waiting for the user's yes), `deferred`, and `held`. A crew's
   `state` is `waiting` while it needs the user's input, `stuck` as the pool's Stalls section says, `working` while it
   runs, `idle` when it holds work but runs nothing, and `free` when it holds none. Each list you pass replaces the
   stored one, so pass whole lists.
3. **Take its requests.** A message that ends with `(Sent from the Orchi board ...)` is the user's own request for that
   one action, confirmed on the board. Check the current state first (the Issue, the PR, the crew's status); when it no
   longer fits, say why in one line and do nothing. Otherwise do it as you would the same words typed by the user:

| Request | What Orchi does |
| --- | --- |
| `Answer the question of <crew>: <text>` | Answers that crew's open question with the text: `answer_session_input` with its exact `request_id` when it waits on `ask_user`, otherwise a message to the crew |
| `About your question <id>: <text>` | Takes the text as the user's answer to its own question `<id>` |
| `Merge PR #<n>.` | The user's yes to merge it; every other merge check still applies |
| `Hold PR #<n> ...` | Comments `Held at the user's request on <date>` on the PR, adds it to `held`, and merges it only when the user says so |
| `Take #<n>.` or `Take #<n> when a crew is free.` | Assigns a crew, now or within the pool's limits |
| `Plan #<n>.` | Assigns a planner crew |
| `Defer #<n> ...` / `Resume #<n>.` | Comments `Deferred at the user's request on <date>` or `Resumed at the user's request on <date>` on the Issue, updates `deferred`, and starts no work on a deferred Issue |
| `Ask <crew> for its status and tell me.` | Sends `<id> status?` and passes the answer on |
| `Turn autonomous mode <on or off>.` | Changes the mode as the pool's Autonomous mode section says |

After a restart, rebuild `deferred` and `held` from those comments: an Issue is deferred while its latest such comment
says Deferred, and a PR is held until the user says to merge it.

## The design board

The session that talks to the user shows variants on the design board: an exploration's design session and prototype
mode, and a designer crew's rounds. The user moves through them with the arrow keys, sees each at 1440 or 720 px or full
screen, scores it 1 to 5, notes what works and what does not, picks, and says the round is done.

1. **Gather** a round's files under `.orchi-tmp/board/v/<round>/` in the session's checkout, copied from the
   designers' output folders with what each needs beside it. A round id is a slug such as `r1-directions`; an item is an HTML
   page or an image.
2. **Open** it once per session: `open_canvas` with canvasId `orchi-design-board`, instanceId `design-board`, and input
   `{"product": "<name>"}`; add `"root": "<absolute checkout path>"` when the checkout is not the session's folder.
3. **Publish** each round: `invoke_canvas_action` `publish_round` on `design-board` with `id`, `title`, the `question`
   the user decides, and `items` (`id`, `file` relative to `.orchi-tmp/board/`, `label` naming the direction, never
   the skill that made it, and optional `notes`). Then say in the conversation what to look at and decide.
4. **Read** the ratings when a message says the user rated a round on the design board, or when the user says so in
   the conversation: `read_picks` with the round id. Record what they picked and why where the stage says, and ask
   in the conversation only what the ratings leave open.

Variants run in a sandbox without access to the board's data. Without the canvas, open each file in the Browser
canvas and ask for each item's score, a note, and the pick in the conversation.

## Pages in the Browser canvas

Open a page the user should keep beside the conversation, such as a living prototype or a built screen, in the app's
Browser canvas: `open_canvas` with canvasId `browser`, a stable instanceId per page (`prototype`), and
`{"url": "file://<absolute path>"}`, or the `http://localhost:<port>` address of a server you started for it. After
each change, reload it with `navigate_page` (`reload`). Before showing a change, go through it with `read_page`,
`click_element`, `type_in_page`, and `screenshot_page`. The canvas has the panel's width: check the other widths a
brief names by copying the page into a design board round and switching its width there.
