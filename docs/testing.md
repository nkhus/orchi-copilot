# Testing

## Deterministic validation

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
```

`tools/validate_package.py` runs offline and checks:

- the marketplace and the plugin: `.github/plugin/marketplace.json` names the
  marketplace `orchi-copilot` with an owner and lists exactly one plugin,
  `orchi`, with the source `./plugins/orchi`; `plugins/orchi/plugin.json` uses
  only documented keys of the legacy format, has no `$schema`, and agrees with
  the marketplace on the version;
- the eight skills: documented frontmatter only; the entry `orchi` is
  explicit-only (`disable-model-invocation`), and every other skill is hidden
  from the menu and may be invoked by the model; each `SKILL.md` has at most
  100 lines and no `$ARGUMENTS`;
- the six custom agents: documented frontmatter keys and tool aliases, the
  pinned model of each, no `edit` tool for the read-only roles (`orchi-scout`,
  `orchi-researcher`, `orchi-reviewer`), and a body within the size limit;
- the extensions under `plugins/orchi/extensions/`: each has `extension.mjs`
  and no `package.json` or `node_modules`, imports only `node:` modules, the
  Copilot SDK, and its own files, writes nothing to the console, listens only on
  `127.0.0.1` port 0, and names no action `canvas.*`;
- the ownership map in [`docs/README.md`](README.md#ownership): every file under
  `plugins/` matches a row, every row matches a file, and every page it names
  exists;
- local Markdown links and their heading anchors, through the bundled
  `knowledge.py` lint; links in installed files stay inside
  `plugins/orchi/skills/`;
- Python syntax, standard-library-only scripts, and JSON and YAML syntax;
- English text: no Cyrillic, no release markers that pair `Orchi` with a version
  number, and under `plugins/` the word "claude" only in model IDs;
- `pyproject.toml` holds tool settings only, with no `[project]` or
  `[build-system]` table.

The test suite, in `tests/`:

| Tests | Cover |
| --- | --- |
| `test_packaging.py` | The validator's failure cases for the marketplace, the plugin, and the documentation |
| `test_setup.py` | `setup.py`: dry run, idempotence, refusal of edited files and sections, the Copilot settings merge, `.github/github-app.yml`, workflow opt-out, `--check`, section updates from earlier versions, label migration without creating labels, `gh` unavailable, symlinks |
| `test_roles.py` | The custom agents' frontmatter, models, read-only tools, and nesting rules |
| `test_pool.py` | The entry skill and the pool reference agree on the Copilot app mechanics they use |
| `test_consistency.py` | Skills, agents, and references agree where a session follows one and not the other |
| `test_delivery.py` | Writer continuation, verification verdicts, and delivery course corrections |
| `test_design.py` | The design track's wording across planning, readiness, the forms, the skills, and the designer agent |
| `test_board.py` | `board.py`: the crews' states, assignees and linked branches, deferred and held items, the owner's overlay of questions with sent and answered ones, Summary, mode, and queue, the read-only board for anyone else, each card's column, Epic and Initiative aggregation and progress, history with back-moves, and what waits for the user |
| `test_canvases.py` | The canvases extension under Node: request sentences (answers with their `request_id`, plans, reviews), the board's Summary prose linking `#<n>` and crew names, round checks, path containment, and the loopback server's token, `Host`, and JSON checks; skipped without Node |
| `test_context.py`, `test_knowledge.py` | `knowledge.py` snapshot isolation, reads, lint, `impact`, and `work`, and the vendored copy run from a repository root |
| `test_standards.py` | `standards.py check` and `ruleset` |
| `test_status.py`, `test_status_initiative.py` | `status.py` readiness, pagination, and blockers merged into Initiative branches |
| `test_issue_templates.py` | The Issue forms are valid and give every readiness checklist item a field |

CI (`.github/workflows/ci.yml`) runs on Python 3.11: it installs
`requirements-dev.txt`, runs the validator and the tests, and runs
`knowledge.py lint` over the repository.

## Local plugin check

Install the plugin from the working tree with the Copilot CLI and check that it
loads:

```bash
copilot plugin install ./plugins/orchi
```

In an interactive session, `/agent` lists the six `orchi-*` agents and
`/skills list` lists the eight skills. Uninstall it with
`copilot plugin uninstall orchi` before installing from the marketplace again.

## Live behavior

Tests do not establish that Copilot follows the workflow. When changing skill,
reference, or agent text, try it in a disposable repository with a GitHub remote
and a Copilot Project for it: a read-only question, a small fix, an Epic with
Tasks, an exploration handed to planning, and delivery with writer subagents.
Check that:

- `/orchi` in the Project, or in a plain session, prepares the repository in the
  same turn: `setup.py --check` fails, a setup subagent opens a
  `chore/repository-setup` PR whose files never name Orchi, and the user is
  asked only what they alone can answer;
- an idea goes to a researcher crew and a request to a planner crew, each a
  child session named `[<role>] <topic>`, and while autonomous mode is off the
  crew asks the user directly and its question also shows in the Project;
- the assistant researches and agrees scope before creating branches or Issues,
  uses the branch, label, and title conventions, and never merges without authority;
- "take #n" on planned work nobody holds goes to a dev lead crew and assigns
  the user, and on work without a plan, or that someone else holds, is refused
  with the reason;
- a developer using another assistant, without Orchi, reads only neutral rules
  in `AGENTS.md`, and an Issue they assign themselves or link a branch to is
  left alone by the pool;
- a dev lead gives each Task to an `orchi-implementer` or `orchi-fixer`
  subagent, sends a review defect back to the same writer with `write_agent`,
  reads the diff, and pushes; the PR lists each finding with its resolution;
- crews report to Orchi with one-line `send_session_message` messages; a
  `PR ready` reaches the user with its summary and merge risk, and after their
  yes Orchi merges and sends `merged`; a finished crew replies `released` and
  is archived, and no session is deleted;
- with autonomous mode on, Orchi answers a crew's question from its
  recommendation, still passes a `(user)` question about money, access, a
  deploy, or a destructive action to the user, and merges a reviewed PR with
  passing checks;
- a Design Epic goes to a designer crew whose rounds put variants under
  `.orchi-tmp/board/v/<round>/`, each labelled by its idea, and publish them
  on the design board, whose Round done brings the ratings back through
  `read_picks`;
- the installed plugin's extension loads (`orchi-board` and
  `orchi-design-board` appear in the app's canvas list), Orchi opens the board
  at start and reports after each reconcile, and a confirmed board button
  reaches Orchi, which checks the state before acting;
- the board looks right inside the app's canvas panel with the app's theme,
  light and dark (headless Chrome renders `board.html` from a sample snapshot
  outside the app, which shows layout and clicks, not the panel);
- an answer sent from a crew's page reaches the crew through
  `answer_session_input` with the right `request_id` and choice, Approve plan
  through `respond_to_session_plan_v2`, and Open session through
  `navigate_to`; a crew going on with an assumed answer reports it, and Orchi
  keeps the question on the board, not in GitHub;
- another user with read access opens the board on the same repository and
  sees the work read-only, with no crews, questions, or buttons;
- before the first design round, a session offers to install the missing
  design skills, and `orchi-designer` subagents started afterwards see them;
- a living prototype opens in the Browser canvas and reloads after each
  change;
- the slash-command menu offers only `/orchi`, and a role skill invoked without
  `--report-to` points to `/orchi` and stops;
- after compaction, Orchi and a crew still know their role and next step, or
  the owner's re-sent assignment restores it;
- a crew starts in the kickoff's mode, never in plan mode, and its reports
  reach Orchi with their `purpose` and `assignment_id`; a `progress` report
  does not wake Orchi, and the same holds when Orchi is a plain session;
- in a Project conversation, Orchi finds its checkout or `main_repo_path`, and
  its crews land in the right repository;
- two parallel Tasks go to two `[worker]` sessions of the dev lead, which
  commit on their `task/<slug>` branches, report `done`, and are archived on
  release; a `verify` worker's results reach the PR;
- Agent Merge, turned on for a crew's session after the user's yes, finds the
  crew's PR, asks the user to confirm `merge_pr`, repairs CI, and lands the
  merge; with autonomous mode on, it never merges;
- turning autonomous mode on creates the 30-minute reconcile automation, which
  wakes Orchi, and turning it off removes it;
- a crew question answered in Orchi's conversation of a Project, or through
  `relay_session_input` in a plain session, reaches the crew;
- a Cloud crew either finds Orchi's skills or reports `cannot continue`;
- the update check finds a newer marketplace version, and
  `copilot plugin update orchi@orchi-copilot` runs from a session;
- accepting `automation.remote_control: true` in `.github/github-app.yml` lets
  the user steer the pool from GitHub on the web.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| Deterministic tests check scripts and that wording agrees across skills, references, agents, and forms; they never stand in for live behavior, which is checked in a disposable repository with the checklist above | A passing text test proves the text, not what Copilot does with it | Treating text tests as evidence of behavior | [nkhus/orchi#42](https://github.com/nkhus/orchi/pull/42) |
| The validator accepts only the frontmatter keys and plugin manifest keys GitHub documents | An undocumented key is ignored silently by the host, so a typo would pass unnoticed | Accepting any key | [nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2) |
