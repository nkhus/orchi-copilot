# Keep the project's context current

Use for requirements, design, documentation updates, research and planning
documents, or branch synchronization. Follow the repository's documentation
rules and ownership map when it has them; these are the defaults.

Two kinds of documents, with opposite rules:

| | Current documentation | Working documents |
| --- | --- | --- |
| Where | Normal paths, mapped in `docs/README.md`: area pages, product behavior pages, `ENGINEERING.md`, `PRODUCT.md`, `DESIGN.md`, references in `docs/design/references/`, surface briefs and approved comps in `docs/design/surfaces/` | `docs/work/<tag>-<slug>/` on the work's branch only |
| Changes | With the code, in the same branch | As often as the work needs |
| Holds | How the product behaves and is built now, and the decisions in force | Research findings, options, the decision log, the plan |
| Ends | Never; what is replaced is deleted | Deleted before the merge into main |

Evidence (checks, reviews, observations) lives in Issues and PRs and supports
claims without becoming requirements. Git keeps every earlier version;
documents describe the present, not how it came about.

## Current documentation

`docs/README.md` is the map: what each page covers, and an `Ownership` table
that assigns code to the pages describing it (`Code`, `Pages`, `Area`; code as
path globs, pages comma-separated). The [map template](../assets/docs/README.md)
shows the shape. Group pages by area, the part of the product the code
implements, never by the work that produced them:

- `docs/<area>/README.md` ([template](../assets/docs/area.md)): how the area is
  built, its contracts and limits, and its Decisions section;
- `docs/design/surfaces/`: each surface's brief and approved comp, updated, or
  replaced through a new brief, when the surface changes, so later work builds
  against the surface as it is;
- `docs/product/<feature>.md` ([template](../assets/docs/product.md)): what a
  user can see and do now, each criterion with the acceptance test that checks
  it (`path::test name`), written for the user, who reads no code.

Read integrated facts from main, an Initiative's working facts from its branch,
and an Epic candidate from its branch; state the branch or commit when the
distinction matters. Use [retrieval](retrieval.md) for documentation and `rg`
for code. Read the owning page, not only search snippets. Proposed requirements
do not prove implementation, and a passing unit test does not establish
external provider behavior, production rollout, or operational readiness.

## Decisions

A decision that still holds lives in the Decisions section of its area page:
the decision, the reason, the rejected alternatives in one line, and the PR
that made it. Record one there when it is hard to reverse, would surprise a
reader without context, or was a real choice between alternatives; land it with
the code that implements it. When a decision changes, replace its entry in the
same PR and delete the old one; a decision that no longer holds is not kept.
Other decisions stay in their Issue's decision log. A decision not to build
something is recorded in the area it would have changed.

## Working documents

Each piece of work keeps its working folder on its branch, and the folder moves
with the work:

1. An exploration creates `explore/<slug>` from main with `docs/work/<slug>/`:
   `research/<question>.md` for each finding with its sources, and
   `options/<option>.md` for each direction with its verdict.
2. Planning creates the Initiative or Epic branch from the exploration branch,
   so the folder carries on, renamed to `docs/work/<tag>-<slug>/` when the work
   gets a tag. When an exploration yields several top items (for a new product:
   the first run, the design Epic, and the rest of the plan), the folder
   goes to the item that carries the plan (the Initiative, or else the first in
   delivery order), and each other item's Issue carries the requirements,
   decisions, and fates that concern it, with links to the research and option
   files by commit permalink, because the folder is deleted when its item
   merges into main. It gives every exploration decision a fate (a requirement, an
   area decision to record with its code, or none) and writes the plan as the
   folder's `README.md`. Without an exploration, planning starts the folder on
   the Initiative branch, or on the Epic branch when an Epic needs a design
   document beyond its Issue.
3. Delivery changes the folder freely as its understanding changes.

## Update with the code

For each behavioral or architectural change, update the pages the map assigns
to the changed code in the same branch, and the map itself when pages move or
appear. Check whether examples, public contracts, runbooks, behavior pages, and
known limitations change too. Record the result in the PR's `Documentation
impact` section: the pages updated, or for each owning page left unchanged, the
reason it still holds. Do not drop a row from the map to avoid updating its
page; the review checks the map against the changed code.

## Move into current documentation

- **At each Epic merge** into its Initiative branch, move what that Epic settled
  from the working folder into the current documentation on the Initiative
  branch: behavior pages, area pages, and their Decisions sections. Leave what
  may still change in the folder.
- **Before the merge into main** (the final Initiative PR, a standalone Epic, or
  a fix that kept a folder), move the rest and delete the folder in the same PR.
  `knowledge.py work` fails while anything under `docs/work/` is present.
- **An exploration that ends in "do not build"** records that decision in its
  area page, deletes its folder, and opens its branch as a documentation PR.

## Reconcile

Before an Epic merge, compare its implementation and acceptance with its
changed pages. Before the Initiative merge, check all agreed requirements and
cross-Epic contracts against the combined result. Resolve omissions, or agree
any deferred or changed outcome explicitly instead of marking it implemented.

When main or the Initiative target moves, inspect both sides of code and docs,
reconcile overlapping meaning, and rerun affected checks. Never overwrite newer
target docs with a wholesale branch copy, or present an untested combination as
verified.

## Freshness

Pages stay true because every change updates its owning pages and the review
compares code with pages; behavior pages stay true because each criterion's
acceptance test runs in CI. No script judges whether a page is current.
