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
| `test_setup.py` | `setup.py`: dry run, idempotence, refusal of edited files and sections, the Copilot settings merge, `.github/github-app.yml`, workflow opt-out, `--check`, labels, `gh` unavailable, symlinks |
| `test_roles.py` | The custom agents' frontmatter, models, read-only tools, and nesting rules |
| `test_pool.py` | The entry skill and the pool reference agree on the Copilot app mechanics they use |
| `test_consistency.py` | Skills, agents, and references agree where a session follows one and not the other |
| `test_delivery.py` | Writer continuation, verification verdicts, and delivery course corrections |
| `test_design.py` | The design track's wording across planning, readiness, the forms, the skills, and the designer agent |
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
  same turn: `setup.py --check` fails, a setup subagent commits `Set up Orchi`
  and pushes it, and the user is asked only what they alone can answer;
- an idea goes to a researcher crew and a request to a planner crew, each a
  child session named `[<role>] <topic>`, and while autonomous mode is off the
  crew asks the user directly and its question also shows in the Project;
- the assistant researches and agrees scope before creating branches or Issues,
  uses the branch and label conventions, and never merges without authority;
- "take #n" on `delivery-ready` work goes to a dev lead crew, and on work
  without it is refused with the reason;
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
- a `design` Epic goes to a designer crew whose rounds put variants under
  `.orchi-tmp/board/v/<round>/`, each labelled by its idea;
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
