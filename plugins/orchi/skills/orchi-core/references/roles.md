# Orchi subagent roles

Each role is a custom agent of the Orchi plugin. Start one with the `task` tool,
`agent_type` set to its name; its profile sets its model and its tools, and the
roles that write nothing cannot edit files.

| Agent | Model tier | Writes |
| --- | --- | --- |
| `orchi-scout` | fast | nothing |
| `orchi-researcher` | most capable | nothing |
| `orchi-implementer` | most capable | one commit per run |
| `orchi-fixer` | balanced | one commit per run (Task or repair) |
| `orchi-reviewer` | most capable | nothing |
| `orchi-designer` | most capable | one commit per UI Task run; files in `.orchi-tmp/` in Wireframe, Variant, and Mockup modes; nothing in Audit mode |

## Choosing a writer

The main session is the only one that starts a writer, and runs one writer per
worktree at a time. Start `orchi-fixer` when the change is small and fully
determined by its Issue: a standalone Task, an Epic Task, or a confirmed review
defect whose fix is localized, whose acceptance is directly checkable, and which
needs no new contract, schema, migration, dependency, or design choice. Start
`orchi-designer` for a Task whose outcome is mainly user interface design
(layout, typography, color, motion, states, or component choice) and for every
Task that builds against a surface brief or an approved comp. Start
`orchi-implementer` for every other Task, standalone or in an Epic. Start a
writer with `task` in background mode, so that it stays available for more
turns. A writer's report is a claim; inspect its diff and check output before
pushing.

A fixer `ESCALATE` report names its cause:

- `decision`: the change needs a product or design choice. Decide it yourself
  only when the user delegated it, otherwise ask; record the answer in the
  Issue's decisions, then continue the writer with the answer.
- `size`: the change is correct but larger than the fixer's scope. Restart the
  same Issue with `orchi-implementer`, or `orchi-designer` for a UI Task; for a
  repair, first reopen the owning Task (or create a repair Task) with the
  defect in its requirements.

A designer `ESCALATE` is always a `decision`: it lists options and a
recommendation. Handle it like a fixer's, except that a direction, a comp, or a
generated asset goes to the user whatever they delegated, or to Orchi in
autonomous mode.

## Continue a writer

When a writer's own Task needs more work in the same delivery — the answer to
its `NOT READY`, `BLOCKED`, or `ESCALATE` (`decision`) report, or a confirmed
defect in its result — continue that writer instead of starting a new one: send
the answer or the defect, as the Issue now records it, with `write_agent` to the
`agent_id` its `task` call returned. It keeps the context it already built and
adds a commit on the same branch. Start a new writer when the old one cannot be
continued (its `agent_id` is gone after compaction or in a resumed session), when
the work belongs to another role (a `size` escalation), or when the Task
[changed course](execution.md#change-course).

## Design skills

Orchi designs with two design skills that the plugin does not bundle:
[Hallmark](https://github.com/Nutlope/hallmark), strongest on pages that are
read, and Emil Kowalski's [prototype](https://github.com/emilkowalski/skills),
strongest on screens that are worked in. Before its first design round, the
session that talks to the user checks them with
`gh skill list --agent github-copilot --json skillName,version,pinned`; for each
one missing, it asks the user (`ask_user`) whether to install it for all their
projects, at the version Orchi was tested with, and on their yes runs:

```bash
gh skill install Nutlope/hallmark skills/hallmark --pin 6033bab2a8051b5454552d2e8e6cb8f27c483a42 --agent github-copilot --scope user
gh skill install emilkowalski/skills skills/prototype --pin 2d228630ba1446365f614a108cb8252f1feda202 --agent github-copilot --scope user
```

Skills load when a session starts, so a new skill reaches the `orchi-designer`
subagents the session starts afterwards; when one does not see it, start the
next round in a new session or work without it. On a no, a failed install, or
a `gh` without `skill`, the designer works without that skill and the round
says so. A project's own copy in `.github/skills/` comes first. A
project designs with one of them, its design engine: the user picks it in the
project's first design Epic, from variants both skills built independently, and
`DESIGN.md` records it. The steps split by who can take them:

| Steps | Who runs them |
| --- | --- |
| `PRODUCT.md`, references, surface briefs, the engine and direction rounds, comp and asset approval, `DESIGN.md` | The session that talks to the user: the main session, or a planner or designer crew |
| Wireframes of a screen's panels (prototype at wireframe fidelity), variants for a round, and the clickable mockup of the system | `orchi-designer` in Wireframe, Variant, and Mockup modes |
| Builds from an approved comp, and UI Tasks at depth none | `orchi-designer` in Task mode |
| The design audit, with Hallmark's `audit` and `sloplint` in a Hallmark project | `orchi-designer` in Audit mode |

prototype is marked for the user's invocation only, so `orchi-designer` reads
its `SKILL.md` and follows it instead of starting it with the `skill` tool.
`orchi-designer` never asks the user: what a skill would ask it returns as
`ESCALATE`. [SmoothUI](https://smoothui.dev/), a library of animated React
components, is a component source rather than a design skill: where
`PRODUCT.md` or `DESIGN.md` names it (React with Tailwind CSS 4 and shadcn/ui),
the designer adds its components through the shadcn CLI or MCP server and
restyles them with the project's tokens.

For a UI diff, the main session may also start `orchi-designer` in Audit mode
next to `orchi-reviewer`; the designer reports design and accessibility
defects, and the reviewer remains the one full review.
