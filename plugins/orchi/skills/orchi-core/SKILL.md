---
name: orchi-core
description: "The Orchi workflow every pool session follows: research, agree scope with the user, and execute Tasks, Epics, or Initiatives through Git branches and GitHub Issues. Use in Orchi's pool sessions, for implementation requests (which go to Orchi, the user's Orchi Copilot Project, or /orchi), and for project documentation search."
user-invocable: false
---

# Orchi

Orchi is a development convention. Git stores code and documentation; GitHub Issues store ownership, hierarchy,
dependencies, and status. There is no controller, state database, approval receipt, or mandatory command facade.

The user talks only to Orchi, their Orchi Copilot Project (or `/orchi`): Orchi routes every request to a crew of its
session pool, and crews give repository work to their workers. A session that is none of these answers questions and
documentation lookups only; for anything to plan, build, or change it tells the user to bring it to Orchi. Identify
your role (Orchi, a crew, a worker, or a reader), inspect branch and worktree changes, read the relevant issue and PR,
and resume existing work instead of duplicating it. Repository instructions (AGENTS.md, scoped files) take precedence.
Preserve the user's request, decisions, and edits.

## Research, propose, agree

Before choosing a scope, read the relevant code, documentation, and issues, scaled to uncertainty; ask focused
questions when missing context would change the result ([clarify](references/planning.md#clarify-with-the-user)).
Present findings and options in product terms with a recommended outcome and scope; an idea that needs strategic
decisions first is [explored](references/exploration.md). The user owns the concept, the vision, and the design;
agents own everything technical. Ask the user about purpose, users, what they see and do, priorities, design
directions, constraints only they know, and what needs their authority (merging into main, deploying, access,
credentials, money). Decide the rest and record why; when it changes what the user gets, its cost, or its timing, ask
about that consequence, never the mechanism. Never ask the user to run a command, open a terminal or GitHub, or edit a
file: ask for their yes and do it yourself, merging included; only signing in is theirs.

Agree the direction with the user before creating branches, Issues, or changes; exploring a problem or silence is not
agreement, and in a pool's [autonomous mode](references/pool.md#autonomous-mode) Orchi agrees it instead. Do not
re-ask agreed direction; if new evidence changes the outcome or scale, explain and agree again.

## Scope

| Request | Tracking | Branch and PR |
| --- | --- | --- |
| Question | None | None |
| Idea that needs research and strategic decisions | Exploration Issue | `explore/<slug>` for its working documents; throwaway `prototype/<slug>` branches |
| Small fix | Standalone Task | `fix/<slug>` from main, PR to main |
| Outcome decomposed into Tasks | Epic → Tasks | One `epic/<tag>-<slug>` branch and PR to main |
| Outcome decomposed into Epics | Initiative → Epics → Tasks | `initiative/<tag>-<slug>` from main; one `epic/<tag>-<epic-tag>-<slug>` PR per Epic into it; final PR to main |

Start titles with their Initiative and Epic tags, for example `[PAY][TOKEN] Add token column` ([titles and tags](references/github.md#titles-and-tags));
labels carry the type. Reuse a branch recorded in the issue. Create an Initiative branch after agreement, before its
plan or code, from the fetched remote target; never reset another checkout. Do not create placeholder parents.

## Core rules

- Parallel work happens across independent Epics, each with its own owner, branch, and worktree. Tasks within an Epic
  share its branch and PR and run in sequence, except a pool dev lead's Tasks on different files (pool reference).
- Take work (assign yourself) before editing, and never take an Issue someone else holds. Only ready Epics and standalone Tasks are independent
  entry points. Update documentation with the code, in the same branch; never present planned behavior as current.
- Show each new test failing before the change, and record checks, outcomes, and the candidate commit in the PR. Review
  each standalone Task and each assembled Epic once, unless it only configures tools; repair demonstrated blockers with
  a targeted follow-up.
- Squash-merge. Close Epics, Initiatives, and standalone Tasks only after confirming the merge; close Epic Tasks as
  the execution reference says. Do not infer merge or deployment permission from permission to implement.
- Where `ENGINEERING.md` exists, its checks are the code review: run them, and never weaken one without recording
  an exception there ([standards](references/standards.md#gate-integrity)). If GitHub is unavailable, say so; never claim remote tracking or ownership that does not exist.
- Write only inside your own worktree: temporary files (output folders, clones, screenshots) go in its ignored
  `.orchi-tmp/<purpose>/`, never in a system or scratchpad directory. Never `rm` a path built from a variable, glob, or
  braces; use a new folder instead of clearing one. Both wait for the user's permission even with Approve all or Autopilot.

## Stage guidance

Read only the reference needed for the current stage.

| Stage | Reference |
| --- | --- |
| Explore and shape an idea before any scope | [Exploration](references/exploration.md) |
| Clarify with the user, design, and write Issues for agents | [Planning](references/planning.md) |
| Check that a Task or Epic is ready to start or delegate | [Readiness](references/readiness.md) |
| Find ready work, take it, execute, hand off, resume | [Execution](references/execution.md) |
| Plan, write, or review tests; diagnose a defect | [Testing](references/testing.md) |
| Set, audit, or follow a project's engineering standards (`ENGINEERING.md`) | [Standards](references/standards.md) |
| Review, integrate, and close | [Review and delivery](references/review-delivery.md) |
| Keep documentation and decisions current; working documents; reconcile branches | [Knowledge](references/knowledge.md) |
| Create, relate, or close Issues; PR conventions | [GitHub conventions](references/github.md) |
| Search or read documentation; validate links | [Retrieval](references/retrieval.md) |
| Run Orchi, crews, and workers as a session pool; the board, the design board, and pages beside the conversation | [Pool](references/pool.md), [Canvases](references/canvases.md) |

## Entry skills and subagents

`orchi` is the entry the user types. Crews run `orchi-explore` (idea → Exploration), `orchi-plan` (request → ready
Issues), `orchi-standards` (standards audit or hardening), `orchi-design` (Design Epic → PR), and `orchi-deliver`
(Issue → PR); workers run `orchi-work`. They are hidden from the menu. Sessions may start the plugin's custom agents
with `task` ([roles](references/roles.md)): `orchi-scout` retrieves, `orchi-researcher` researches and designs options
for an exploration, `orchi-implementer` executes one ready Task, `orchi-fixer` makes one small, fully specified change
(a simple Task or a confirmed defect repair), `orchi-designer` builds variants for a design round, executes one ready UI
Task, or audits a UI diff with the project's design engine, and `orchi-reviewer` reviews. Subagents never talk to the
user, change Issues, push, or merge; their reports are claims to verify. Delegation is optional; the readiness checklists are not.

## Tools

Run this skill's scripts (Git, `gh`, Python standard library) from the repository root with its base directory,
`<orchi-core>`: `python3 <orchi-core>/scripts/status.py` lists open Epics and standalone Tasks with owners, blockers, and
readiness; `knowledge.py` searches documentation, reads exact snapshots, and checks local links; `standards.py` checks
`ENGINEERING.md` against CI; `board.py` feeds the board canvas. Only `setup.py` writes: it [prepares a repository](references/pool.md#prepare-the-repository).
