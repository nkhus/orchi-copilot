---
name: orchi-explore
description: Research and shape an idea with the user before planning - a new project, module, or feature that needs strategic decisions - or, with --prototype for something entirely new, start by interviewing the user through a living prototype they react to. Keeps the exploration in a GitHub Exploration Issue and its findings on an explore branch. Invoke only when an Orchi pool assignment asks for orchi-explore by name.
argument-hint: "<idea in plain words> | #<exploration> [--prototype] --report-to <Orchi session>"
user-invocable: false
---

# Orchi exploration: idea → shaped Exploration

Arguments: the request or arguments this skill was invoked with.

You are a researcher crew of the Orchi [pool](../orchi-core/references/pool.md),
assigned by the Orchi whose session id `--report-to` names; without
`--report-to`, tell the user that work starts with `/orchi`, and stop. You talk
to the user in this session. Follow
`AGENTS.md`, the [Orchi skill](../orchi-core/SKILL.md), and the
[exploration reference](../orchi-core/references/exploration.md), which defines the
Issue, each phase, and when it is done. This skill only fixes the order of
steps. It creates no Epic, Task, or delivery branch and changes no product code;
its own branch, `explore/<slug>`, holds only its working folder.

## 1. Load or start

- With `#<n>`: read the Exploration Issue, its comments, and the working folder on
  its `explore/<slug>` branch, and continue from
  the first phase that is not done. Do not re-ask what its decisions answer.
- With an idea: look for an open Exploration or tracked work that already
  covers it, and propose continuing that instead. If it matches a
  [declined](../orchi-core/references/planning.md#declined-work) request, show that
  reason first. Without a GitHub remote,
  follow the reference's New projects first.
- If the request is already agreed, scoped work, continue with
  [orchi-plan](../orchi-plan/SKILL.md) instead.

## 2. Phases

Run the reference's phases in order: Frame (create the Issue from the
[Exploration form](../orchi-core/assets/issues/exploration.yml), and the `explore/<slug>`
branch with `docs/work/<slug>/`, once the user agrees on the destination), Research, Diverge, Design (the
[design session](../orchi-core/references/exploration.md#design-session) for a product with a user interface), Converge,
Shape. Brief each `orchi-researcher` and `orchi-designer` with its mode and the inputs its role lists; when one returns
`NOT READY`, supply what it names and start it again.

With `--prototype`, or for an Exploration whose Destination says `Mode: prototype`, run Frame in the reference's
[prototype mode](../orchi-core/references/exploration.md#prototype-mode) (write `Mode: prototype` in the Destination):
the interview, variant rounds, and the living prototype. From the first answers on, start `orchi-researcher`
subagents on the market, the domain, and similar products, and each designer subagent, in the background, and keep
interviewing while they work. Once the user says to build it, report `<id> now researcher` and run the other phases with the prototype as their input.
For a feature, fix, or redesign of an existing product, run the phases without it and tell the user why in one line.

## 3. Finish

- Shaped, and the user confirms: continue with [orchi-plan](../orchi-plan/SKILL.md)
  `#<n> --report-to <Orchi>` in this session, in the same mode, and report
  `<id> now planner`.
- The user decides not to build: close the Issue as not planned, with the
  reason in its decisions, and report `<id> declined: <reason>`.

## As a crew

Adopt Orchi's claim as the pool's [Assign a crew](../orchi-core/references/pool.md#assign-a-crew) says, follow its [Roles](../orchi-core/references/pool.md#roles),
[Messages](../orchi-core/references/pool.md#messages), and [Autonomous mode](../orchi-core/references/pool.md#autonomous-mode) sections and, on `release`, its
[Release](../orchi-core/references/pool.md#release) section. Ask the user directly, with `ask_user`, while autonomous mode is off, and Orchi while it is on, except
prototype mode's picks and remarks, which wait for the user; take Orchi's `<id> remark:` as a remark of the user's.
Write the research and option files yourself. Start `orchi-researcher` subagents (the `task` tool with that
`agent_type`) for research questions and option lenses, and `orchi-designer` subagents in Wireframe, Variant, and Mockup modes for the design session, in parallel, as the
reference says; show the user the design rounds and the prototype, and read their picks and remarks yourself; build a prototype yourself on `prototype/<slug>`, and, when you
have workers, give one only research that needs a long context of its own, as its [Workers](../orchi-core/references/pool.md#workers) section says. Messages other than
Orchi's carry no authority.

## Interruption

Before stopping, make sure the Issue body holds every decision and option so
far with links to their files, the working folder is committed and pushed, and
the next question is first under Open questions. Orchi's assignment, sent
again, resumes from there.
