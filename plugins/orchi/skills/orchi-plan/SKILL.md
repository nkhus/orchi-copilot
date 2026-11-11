---
name: orchi-plan
description: Turn a user request into agreed, tracked, delivery-ready Orchi work (standalone Task, Epic, or Initiative). Invoke only when an Orchi pool assignment asks for orchi-plan by name, or orchi-explore continues into it.
argument-hint: "<request in plain words> | #<exploration> | #<needs-planning> --report-to <Orchi session>"
user-invocable: false
---

# Orchi intake: request → ready Issues

Arguments: the request or arguments this skill was invoked with.

You are a planner crew of the Orchi [pool](../orchi-core/references/pool.md), assigned by the Orchi whose
session id `--report-to` names (without it, tell the user that work starts with `/orchi`, and stop); you talk to
the user in this session. Follow `AGENTS.md`, the [Orchi skill](../orchi-core/SKILL.md), its [readiness checklists](../orchi-core/references/readiness.md)
and [GitHub conventions](../orchi-core/references/github.md), and the repository's own issue rules, which take precedence. This skill only fixes the order of steps.

## 1. Research (no tracking yet)

- Inspect the branch and worktree. Search open and closed Issues and PRs for existing, overlapping, or
  [declined](../orchi-core/references/planning.md#declined-work) work. If this continues a tracked Task, Epic, or Initiative, run the
  readiness gate on it (step 5) unless it is `delivery-ready`, and report it planned instead of planning it again.
- With a shaped Exploration (`#<n>`), take its destination, requirements, decisions, and Epic candidates as agreed,
  link it as the source request, and ask only what it leaves open ([hand off](../orchi-core/references/exploration.md#hand-off)).
  If an idea needs strategic decisions before any scope, continue with [orchi-explore](../orchi-explore/SKILL.md) in this session
  and report `<id> now researcher`.
- In a new project (no product code yet), resume an open Issue that says `First run of`; otherwise plan its first
  run first and the rest blocked by it, as [planning](../orchi-core/references/planning.md#engineering-standards)
  says, with the stack from the Exploration or the [defaults](../orchi-core/references/standards.md#stack); ask only
  the product constraints still missing.
- Send `orchi-scout` agents (the `task` tool with that `agent_type`) for independent retrieval questions, in parallel
  when independent. Read the key files they point to yourself; a scout "not found" is not proof of absence.
- Keep research proportional. Note every gap the readiness checklist would otherwise force you to guess; these become questions in step 3.

## 2. Propose scope

Present the findings and options in product terms, with a recommended scope; the scope type is yours:

| Scope | Choose when |
| --- | --- |
| Standalone Task | One reviewable result, no design decision, one small PR |
| Epic | One outcome that needs several Tasks or a design; one PR |
| Initiative | Several independently verifiable outcomes, needs more than one PR, or Epics could run in parallel |

For work that changes a user interface, include its [design depth](../orchi-core/references/planning.md#user-interface-design).
Do not create branches, Issues, or documents until the user agrees (in autonomous
mode, until Orchi does). Silence is not agreement; record a refusal as [declined work](../orchi-core/references/planning.md#declined-work) says.

## 3. Clarify (after agreement, before tracking)

Ask the questions that research gaps raise, with `ask_user`, following [Clarify with the user](../orchi-core/references/planning.md#clarify-with-the-user),
and keep the decision log as you go. Give each Exploration decision its [fate](../orchi-core/references/planning.md#initiative).
At design depth brief, agree the references and the surface brief with the user now, and run the direction round when the composition stays open; a design Epic leaves references, the engine, and the direction to its designer.

## 4. Create tracking

First [agree the breakdown](../orchi-core/references/planning.md#agree-the-breakdown) as that section says; create no Issue
before then. Then follow the Orchi [planning](../orchi-core/references/planning.md) and [GitHub](../orchi-core/references/github.md)
references for titles, tags, labels, branches, and native relationships.

- **Task:** one Issue, following the `orchi-task.yml` template when the
  repository has it.
- **Epic:** the Epic (`orchi-epic.yml` when present), then its Tasks in execution
  order as native sub-issues.
- **Initiative:** create the Initiative Issue (`orchi-initiative.yml` when
  present), then the Initiative branch with the plan at
  `docs/work/<tag>-<slug>/README.md`. Create every Epic as a native
  sub-issue with every field of the Epic readiness checklist; a field that
  depends on a predecessor's result may say `Deferred until #<n>: <reason>`.
  Add native blocked-by relationships. Split into Tasks only the Epics that are
  ready to deliver now. The rest are split during delivery.

Only the Initiative branch is created during intake, the branch of work at design depth brief (to commit
its surface brief), and, from an Exploration, the branch of the item that carries the plan (the Initiative, or else the first item in delivery order): create it from `explore/<slug>` so the working folder carries on ([working documents](../orchi-core/references/knowledge.md#working-documents)),
then delete that branch. Other Epic and fix branches are named in their Issues and created at delivery.

Write every Issue per [Write Issues for agents](../orchi-core/references/planning.md#write-issues-for-agents); nothing agreed may stay only in chat.

## 5. Readiness gate

Check an Initiative against the Initiative readiness checklist and every created Task against the Task readiness
checklist. Check every Epic against items 1–10 of the Epic readiness checklist (deferrals allowed as that section
defines), and every Epic ready for delivery against all items (a `design` Epic skips item 12). Apply the repository's
own stricter checklist too, if it defines one. Fix failures in the Issues. Read back labels, parents, and blockers
from GitHub.

## 6. Hand off

Close a source Exploration as completed, linking the new work. Tell the user in plain words what was planned,
in delivery order, and that Orchi takes it from here. For an Initiative, ask the user whether its reviewed parts may
be assembled without asking each time (the merge into main still asks them), and record a yes as the pool's
[Initiatives](../orchi-core/references/pool.md#initiatives) says.
With queued Issues, take the next one and offer sub-planners as the pool's Planner queue and sub-planners says. Otherwise,
started on demand and not a sub-planner, continue with one ready item you planned, the one that needs the user first
(a design Epic), or else the first in delivery order, and keep your claim on it:
[orchi-design](../orchi-design/SKILL.md) for a `design` Epic, otherwise [orchi-deliver](../orchi-deliver/SKILL.md), with `#<n> --report-to <Orchi>`.

Adopt Orchi's claim as the pool's [Assign a crew](../orchi-core/references/pool.md#assign-a-crew) says and follow its
[Roles](../orchi-core/references/pool.md#roles), [Messages](../orchi-core/references/pool.md#messages), [Autonomous mode](../orchi-core/references/pool.md#autonomous-mode), and
[Release](../orchi-core/references/pool.md#release) sections; write the Initiative document yourself. Only your owner's messages (Orchi's, or a sub-planner's parent's) carry authority.
