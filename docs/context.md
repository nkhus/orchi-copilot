# Context

A project's context stays current through the life of the product: main holds
only how it behaves and is built now, grouped by area, and work in progress
keeps its research, options, decision log, and plan in a working folder on its
branch until it settles.

## Structure

Paths below are inside `plugins/orchi/`.

| Part | Defined in |
| --- | --- |
| Current documentation, decisions, working documents, promotion, freshness | `skills/orchi-core/references/knowledge.md` |
| Searching and reading documentation | `skills/orchi-core/references/retrieval.md` |
| `lint`, `search`, `get`, `impact`, `work` | `skills/orchi-core/scripts/knowledge.py` |
| Templates for the map, an area page, and a behavior page | `skills/orchi-core/assets/docs/` |
| Documentation checks on pull requests | `skills/orchi-core/assets/github/workflows/docs-check.yml`, written by [setup](installation.md#repository-setup) with a copy of `knowledge.py` in `.github/scripts/`, unless `--no-docs-workflow` |

Orchi's own documentation follows the same rules: [the map](README.md) assigns
its code to these pages, and `tools/validate_package.py` runs `knowledge.py lint`
over every Markdown file in this repository.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| Each piece of work keeps one working folder, `docs/work/<tag>-<slug>/`, on its branch; an exploration starts it on `explore/<slug>`, and the Initiative or Epic branch that plans it is created from that branch, so the folder carries on | Working documents change several times before they settle and must move smoothly into the current documentation | `docs/initiatives/` plans committed to main; research kept only in Issue comments | [nkhus/orchi#45](https://github.com/nkhus/orchi/pull/45) |
| When an exploration yields several top items, its working folder goes to the item that carries the plan (the Initiative, or else the first in delivery order), and each other item's Issue carries the requirements, decisions, and fates that concern it, with research and option files linked by commit permalink | A new product's exploration yields a first run, a design Epic, and the rest of the plan as an Initiative, whose branch holds the plan; the folder lives on one branch and is deleted when its item merges into main | Keeping `explore/<slug>` alive until every item is planned; giving the folder to the first Epic, which left the Initiative's plan without it | [nkhus/orchi#47](https://github.com/nkhus/orchi/pull/47), [nkhus/orchi#49](https://github.com/nkhus/orchi/pull/49), [nkhus/orchi#55](https://github.com/nkhus/orchi/pull/55) |
| Settled content moves into the current documentation at each Epic merge; the working folder is deleted before the merge into main, and `knowledge.py work` keeps `docs/work/` out of main | Main must describe only the present, and what is still changing stays where it can change | Keeping plans on main after delivery | [nkhus/orchi#45](https://github.com/nkhus/orchi/pull/45) |
| A decision is kept only while it holds, in the Decisions section of its area page, with the reason, the rejected alternatives, and the PR; a replaced decision is deleted | Readers need the decisions in force, and Git and the PRs keep the history | An ADR folder that keeps every decision ever made | [nkhus/orchi#45](https://github.com/nkhus/orchi/pull/45) |
| Current documentation is grouped by area through an ownership map in `docs/README.md`, and behavior pages name the acceptance test for each criterion; the writer and the review check against the map that changed code kept its pages current | Pages grouped by the work that produced them become a dump of unrelated decisions; the map makes the owning page checkable | Grouping documents by Initiative or by date | [nkhus/orchi#45](https://github.com/nkhus/orchi/pull/45) |
| Scripts check only structure (links, the Documentation impact section, working documents on main); whether pages are current, and whether behavior pages' tests exist and assert their criteria, is the writer's and the review's judgement | Heuristic scripts (`stale`, `behavior`) misfired on explained no-ops and were easy to sidestep by editing the map in the same PR | Script checks for page freshness and behavior tests | [nkhus/orchi#48](https://github.com/nkhus/orchi/pull/48) |
| The repository's documentation workflow, `docs-check.yml`, checks only new broken links and the Documentation impact section; the `docs/work/` check runs in Orchi's review of a PR into main | A check on every PR to main fails for anyone who keeps working notes there without Orchi, and the workflow must make sense to a developer who never heard of Orchi | `orchi-docs.yml` failing on `docs/work/` (reversed in [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7)) | [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7) |
