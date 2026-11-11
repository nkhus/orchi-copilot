# Canvases

Use when the app lists the plugin's canvases, `orchi-board` and `orchi-design-board`, or a session shows the user
pages it built. The canvases are views beside the conversation: GitHub, the branches, and what Orchi reports hold the
state, and every decision still happens in the conversation. When a canvas is missing or fails to open, say so in one
line and go on in the conversation as if it did not exist.

## The Orchi board

The board is a view of the pool for one repository, with two tabs. **Crews** lists Orchi and each crew with its
status and open questions, and a crew's page shows all its questions to answer at once, with what it answered today;
the Orchi Summary closes the tab. **Board** is a kanban on three levels (Initiatives, an Initiative's Epics, an Epic's
Tasks, and Outside Initiatives for Issues and PRs with none) in six columns: Needs planning, Backlog, In progress,
Questions for you, Your review, and Done. A Task's page shows what the user decides there. The board reads GitHub
through `scripts/board.py` every five minutes and on Refresh: the backlog, PRs, claims, and the question and answer
comments of the pool's [Questions and plans](pool.md#questions-and-plans). It adds what only Orchi knows from its
`update_pool` reports, and writes nothing to GitHub. Orchi moves cards by changing the real state; the user's moves
and answers on the board are requests to Orchi.

1. **Open it** at the start of Orchi's conversation, and whenever the user asks for it: `open_canvas` with canvasId
   `orchi-board`, instanceId `orchi-board`, and input `{"repo": "<owner>/<name>"}`. Opening the same instanceId again
   focuses it.
2. **Report** after each reconcile and whenever the Status answer would change for the user: `invoke_canvas_action`
   `update_pool` on `orchi-board`. Each list or object you pass replaces the stored one, so pass whole lists.
   - `crews`: every crew from `get_sessions_status`, with `name`, `session_id`, `state`, and when known `issue`,
     `doing` in a few plain words, `question`, `background`, `since`, `stuck`, `runs`, `pr`, and `branch`. A crew's
     `state` is `waiting` while it needs the user's input, `stuck` as the pool's Stalls section says, `working` while
     it runs, `idle` when it holds work but runs nothing, and `free` when it holds none.
   - `questions`: every open question with its `id`. Add `request_id` while the crew waits on `ask_user` or a plan,
     and the other fields (`crew`, `issue`, `kind`, `blocking`, `assumed`, `text`, `context`, `choices`, `plan`,
     `links`, `asked`) for a question no comment holds yet, such as a tool approval or a crew's `ask_user`. The
     board joins them by `id` with the question comments.
   - `summary`: your answer to "How are things going?" as `paragraphs` (each a bold `lead` sentence and its `text`),
     `since` (one line on what merged, was answered, or closed today), and `at`. In a few short paragraphs, say what
     moved forward, what is in progress, what is stuck and why, problems or risks, what waits for the user and what it
     unblocks, and what comes next. Write calm, concrete prose; name Issues and PRs as `#<n>` and crews by name (the
     board links both); when nothing is stuck or at risk, say so plainly instead of leaving it out.
   - `mode`, `limit`, `merges` (PRs waiting for the user's yes), `deferred`, `held`, and `queue` (`issue`, `action`,
     `title`: work that starts when a crew is free).
   - `stages` (number → column) only where GitHub does not show where the work is yet, and `moves` (`number`, `to`,
     `note`, `back` when it came back from the user's review) for a card's history.
3. **Take its requests.** A message that ends with `(Sent from the Orchi board ...)` is the user's own request for that
   one action, confirmed on the board after a five-second Undo. Check the current state first (the Issue, the PR, the
   crew's status, the question's `request_id`); when it no longer fits, say why in one line and do nothing. Otherwise
   do it as you would the same words typed by the user:

| Request | What Orchi does |
| --- | --- |
| `Answer question <id> of <crew>: <answer>` | Passes the answer on as the pool's [Questions and plans](pool.md#questions-and-plans) says, with the `request_id` the message names, and records it |
| `Approve the plan <crew> asked about in question <id>.` | `respond_to_session_plan_v2` approving it, or `<id> answer: approved` when the plan is a kept question |
| `Ask <crew> to change the plan of question <id>: <text>` | Rejects the plan with the text as feedback, or sends it as the answer |
| `Send PR #<n> back with these changes: <text>` | `#<m> rework: <text>` to the crew that holds it |
| `Open the session of <crew> for me.` | `navigate_to` that crew's session, where the user answers a tool approval |
| `Open the design board for the round of <crew>.` | Asks the crew to publish or reopen its round on the design board |
| `Refresh the pool summary on the board.` | Reports `update_pool` with a fresh `summary` |
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
says Deferred, and a PR is held until the user says to merge it. The open questions come back from their comments.

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
