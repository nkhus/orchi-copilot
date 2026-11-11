# Upstream

Orchi for the Copilot app is a port of [nkhus/orchi](https://github.com/nkhus/orchi),
the Claude Code edition, at commit
[`60a8edb`](https://github.com/nkhus/orchi/commit/60a8edb). nkhus/orchi stays the
Claude Code edition and is not changed from here.

## Ported

- The core workflow: the `orchi-core` skill and its references (exploration,
  planning, readiness, GitHub conventions, execution, review and delivery,
  testing, knowledge, retrieval, standards), with their wording, headings, and
  anchors, and host mechanics replaced as the table below says.
- The crew skills `orchi-explore`, `orchi-plan`, `orchi-standards`,
  `orchi-design`, and `orchi-deliver`, the worker skill `orchi-work`, and the
  entry `orchi`.
- The six subagent roles, as the plugin's custom agents.
- The scripts `status.py`, `knowledge.py`, and `standards.py`, and the assets:
  Issue forms, the PR template, the documentation and standards workflows, the
  documentation templates, and the `ENGINEERING.md` template.
- The pool reference, rebuilt on the app's sessions: Orchi as a Copilot
  Project, crews and per-task workers as child sessions, messages with a
  purpose, questions and plans, autonomous mode with a reconcile automation,
  Agent Merge, release, stalls, limits, updates, remote control, follow-ups,
  Initiatives, and lessons ([pool](pool.md#decisions) says what changed).
- The package validator, the tests that still apply, the documentation, and
  the out-of-scope records whose reasoning still holds.

## Left out

| Upstream part | Why |
| --- | --- |
| The npm installer (`bin/`, `package.json`, `tools/install.py`, `orchi_install.py`, `orchi_core/`, `tools/smoke_install.py`) | The plugin marketplace installs the plugin, and `setup.py` prepares a repository |
| `orchi-dashboard` and `dashboard.py` | The board of the pool comes with the canvases Epic ([nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4)) |
| `design-board.html` | Variants are opened from `.orchi-tmp/board/` for now; the visual design board comes with the canvases Epic |
| The role sources (`skills/orchi-core/roles/`) rendered into agents | The plugin ships the custom agents directly |
| Vendoring Hallmark and prototype | The user installs design skills ([design](design.md#design-skills)) |
| Claude Desktop session mechanics: sidebar groups, start cards, title renames, `/clear`, a standing worker pool built ahead, the takeover protocol, `Background:` process lines, the bypass-mode check, Orchi's notes file, and per-session remote control | The app's sessions have none of them; [pool](pool.md#decisions) records what replaces each |
| `CONTRIBUTING.md` | [`AGENTS.md`](../AGENTS.md) holds the contributor rules |

## Claude Code to Copilot

| Claude Code | Copilot |
| --- | --- |
| `CLAUDE.md` | `AGENTS.md`; scoped instruction files still take precedence |
| `.claude/skills/orchi-core/scripts/<script>.py` | `<orchi-core>/scripts/<script>.py`, where `<orchi-core>` is the orchi-core skill's base directory, shown when the skill loads |
| Role files rendered into `.claude/agents/` | The plugin's custom agents in `plugins/orchi/agents/` |
| The Agent (Task) tool | `task` with `agent_type` set to the custom agent's name |
| `SendMessage` to a subagent | `write_agent` to the agent ID that `task` returned |
| `AskUserQuestion` | `ask_user` |
| The Skill tool | `skill` |
| Bash, Read, Edit, Write, Grep, Glob | shell, view, edit, create, grep, glob |
| WebFetch, WebSearch | `web_fetch`, `web_search` |
| TodoWrite | The session's todos table |
| Plan mode | Copilot plan mode |
| Bypass permissions mode | Approve all, or Autopilot mode |
| A Claude Desktop session and its sidebar group | A Copilot Project and its child sessions |
| Crews started with a host tool | `create_session` child sessions in their own worktrees |
| Crew messages | `send_session_message` |
| Worker sessions cleared after each task | Per-task worker sessions started by the crew with `create_session` and archived on release |
| Questions answered in the crew's session | `ask_user` there, mirrored in the Project; `relay_session_input`, `answer_session_input`, `respond_to_session_plan_v2` |
| Orchi's notes file and the dashboard stall check | A reconcile automation (`save_session_automation`) and `get_sessions_status` |
| Merging on the user's yes | `gh pr merge`, or Agent Merge (`manage_agent_merge`) when the PR cannot merge yet |
| Remote Control | `automation.remote_control` in `.github/github-app.yml` |
| The npx installer and its `CLAUDE.md` section | The plugin marketplace, and `setup.py` with its managed `AGENTS.md` section |
| "Claude", "Claude Code", "Claude Desktop" | "Copilot", "the Copilot app", "the agent" |

## Files

| Upstream path | Path here |
| --- | --- |
| `skills/<skill>/` | `plugins/orchi/skills/<skill>/` |
| `skills/orchi-core/roles/orchi-<role>.md` | `plugins/orchi/agents/orchi-<role>.agent.md` |
| `skills/orchi-core/roles/README.md` | `plugins/orchi/skills/orchi-core/references/roles.md` |
| `skills/orchi-core/scripts/{status,knowledge,standards}.py` | `plugins/orchi/skills/orchi-core/scripts/` |
| `skills/orchi-core/assets/{docs,github,standards}/` | `plugins/orchi/skills/orchi-core/assets/` |
| The installer and its `--github` setup | `plugins/orchi/skills/orchi-core/scripts/setup.py`, `.github/plugin/marketplace.json`, `plugins/orchi/plugin.json` |
| `tools/validate_package.py` | `tools/validate_package.py` |
| `tests/` | `tests/` |
| `docs/` | `docs/` |
| `AGENTS.md`, `README.md` | `AGENTS.md`, `README.md` |
