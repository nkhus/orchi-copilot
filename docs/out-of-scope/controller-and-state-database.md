# Controller and state database

Orchi does not run a controller process, keep a state database, issue signed
approvals or task packets, or require a command facade for each workflow step.

## Why

Orchi began as a controller with its own runtime, operator keys, worker
adapters, task packets, and schemas. It was replaced by the simpler convention
proven in a downstream project: every session reads the same facts from Git and
GitHub, so any session can restart and catch up, several can work in parallel,
and no service runs besides the assistant.

## Instead

Git branches and GitHub Issues are the only shared state: type labels, native
sub-issues and `blocked by` dependencies, assignees, and linked branches and PRs. The
bundled scripts only read, except `setup.py`, which prepares a repository. The
role skills fix the order of steps for Orchi's sessions; their state is still
only in Git and GitHub, and the app's session list only says which sessions
exist.

## Decided in

- [nkhus/orchi#5](https://github.com/nkhus/orchi/pull/5) and
  [nkhus/orchi#7](https://github.com/nkhus/orchi/pull/7): the controller runtime
  was replaced by the single GitHub-based skill.
- Kept in this port ([nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2)).
- `AGENTS.md`: do not reintroduce a controller, state database, approval
  receipts, or mandatory command facades.
