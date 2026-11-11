# Documentation

How Orchi for the GitHub Copilot app behaves and is built now. Planned work is
in GitHub Issues and, while it is under way, in `docs/work/` on its branch; the
[knowledge reference](../plugins/orchi/skills/orchi-core/references/knowledge.md)
sets the rules. The plugin's `SKILL.md` files, references, and custom agent
profiles define the behavior; these pages describe how the areas fit together
and keep the decisions still in force.

| Page | Covers |
| --- | --- |
| [`README.md`](../README.md) | What Orchi is, how it works in the Copilot app, and how to start |
| [`docs/workflow.md`](workflow.md) | The core workflow: exploration, planning, delivery, review, subagent roles, Issue forms |
| [`docs/pool.md`](pool.md) | Orchi as a Copilot Project, crews and workers as child sessions, messages, questions, autonomous mode, merge, release, updates |
| [`docs/design.md`](design.md) | User interface design: the design track, the `design` Epic, and the designer agent |
| [`docs/standards.md`](standards.md) | Engineering standards: `ENGINEERING.md`, the default stack and checks, gate integrity |
| [`docs/context.md`](context.md) | Project context: current documentation, working documents, the ownership map and its checks |
| [`docs/installation.md`](installation.md) | Installing, updating, and removing the plugin; repository setup; packaging decisions |
| [`docs/testing.md`](testing.md) | Package validation, the test suite, CI, and live checks |
| [`docs/references.md`](references.md) | External standards and tools Orchi relies on |
| [`docs/upstream.md`](upstream.md) | The ported Claude Code edition, what was left out, and how its parts map here |
| [`docs/out-of-scope/`](out-of-scope/README.md) | Proposals Orchi does not adopt, and why |

## Ownership

| Code | Pages | Area |
| --- | --- | --- |
| `plugins/orchi/skills/orchi-core/SKILL.md` | `docs/workflow.md`, `README.md` | Workflow |
| `plugins/orchi/skills/orchi-explore/**` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-plan/**` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-deliver/**` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-core/references/execution.md` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-core/references/exploration.md` | `docs/workflow.md`, `docs/design.md` | Workflow |
| `plugins/orchi/skills/orchi-core/references/github.md` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-core/references/planning.md` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-core/references/readiness.md` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-core/references/review-delivery.md` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-core/references/testing.md` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-core/references/roles.md` | `docs/workflow.md`, `docs/design.md` | Workflow |
| `plugins/orchi/agents/**` | `docs/workflow.md`, `README.md` | Workflow |
| `plugins/orchi/skills/orchi-core/scripts/status.py` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-core/assets/github/ISSUE_TEMPLATE/**` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi-core/assets/github/pull_request_template.md` | `docs/workflow.md` | Workflow |
| `plugins/orchi/skills/orchi/**` | `docs/pool.md`, `README.md` | Pool |
| `plugins/orchi/skills/orchi-work/**` | `docs/pool.md` | Pool |
| `plugins/orchi/skills/orchi-core/references/pool.md` | `docs/pool.md` | Pool |
| `plugins/orchi/skills/orchi-design/**` | `docs/design.md` | Design |
| `plugins/orchi/agents/orchi-designer.agent.md` | `docs/design.md` | Design |
| `plugins/orchi/skills/orchi-standards/**` | `docs/standards.md` | Standards |
| `plugins/orchi/skills/orchi-core/references/standards.md` | `docs/standards.md` | Standards |
| `plugins/orchi/skills/orchi-core/scripts/standards.py` | `docs/standards.md` | Standards |
| `plugins/orchi/skills/orchi-core/assets/standards/**` | `docs/standards.md` | Standards |
| `plugins/orchi/skills/orchi-core/assets/github/workflows/orchi-standards.yml` | `docs/standards.md` | Standards |
| `plugins/orchi/skills/orchi-core/references/knowledge.md` | `docs/context.md` | Context |
| `plugins/orchi/skills/orchi-core/references/retrieval.md` | `docs/context.md` | Context |
| `plugins/orchi/skills/orchi-core/scripts/knowledge.py` | `docs/context.md` | Context |
| `plugins/orchi/skills/orchi-core/assets/docs/**` | `docs/context.md` | Context |
| `plugins/orchi/skills/orchi-core/assets/github/workflows/orchi-docs.yml` | `docs/context.md` | Context |
| `plugins/orchi/skills/orchi-core/scripts/setup.py` | `docs/installation.md`, `docs/pool.md` | Installation |
| `plugins/orchi/plugin.json` | `docs/installation.md` | Installation |
| `.github/plugin/marketplace.json` | `docs/installation.md` | Installation |
| `tools/validate_package.py` | `docs/testing.md` | Testing |
| `tests/**` | `docs/testing.md` | Testing |
| `.github/workflows/**` | `docs/testing.md` | Testing |
