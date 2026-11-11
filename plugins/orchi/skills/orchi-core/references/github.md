# GitHub conventions

Use when creating, editing, relating, or closing Issues and PRs. A repository's
own issue rules and templates take precedence; these are defaults. Prefer current
`gh` help over remembered flags, since relationship support changes. Ownership and
claiming are in [execution](execution.md).

## Setup

Orchi uses the type labels `Initiative`, `Epic`, and `Task`; `in-progress` for
claims; `Exploration` for explorations; `design` for an Epic a designer runs;
and `needs-planning`, `delivery-ready`, and `retro` for hand-offs. A repository
Orchi [prepared](pool.md#prepare-the-repository) already has them, plus issue
templates, a PR template, and the documentation and standards check workflows.
Otherwise, create missing labels deliberately
with a stable description; do not invent variants.

## Titles and tags

Every Initiative and Epic has a short tag. A title starts with the tags of its
Initiative and Epic, in that order, then a short outcome. The type comes from the
label, not the title.

| Issue (label) | Title | Branch |
| --- | --- | --- |
| Initiative, tag `PAY` | `[PAY] Card payments` | `initiative/pay-card-payments` |
| Epic in it, tag `TOKEN` | `[PAY][TOKEN] Tokenize stored cards` | `epic/pay-token-tokenize-cards` |
| Task in that Epic | `[PAY][TOKEN] Add token column to wallet` | The Epic branch |
| Standalone Epic, tag `CSV` | `[CSV] Export orders as CSV` | `epic/csv-export-orders` |
| Task in a standalone Epic | `[CSV] Add export endpoint` | The Epic branch |
| Standalone Task | `Fix rounding in invoice totals` | `fix/invoice-rounding` |
| Exploration | `Explore: card payments` | `explore/card-payments`, for its working folder |
| Task a pool dev lead runs in parallel | As its Epic's Task | `task/<slug>` from the Epic branch, merged back into it |
| Prototype | None | `prototype/<slug>`, never merged |

- A tag is 2–8 uppercase letters or digits, starting with a letter, and names the
  outcome. Choose it when creating the Initiative or Epic. An Initiative's or
  standalone Epic's tag must not be used by any other open or closed issue
  (`gh issue list --state all --search '<TAG> in:title'`); an Epic's tag must be
  unique within its Initiative.
- Tasks have no tag of their own; they repeat their Epic's tags.
- Keep tags stable when an issue is renamed. If an issue moves to another parent,
  update its leading tags. `status.py` reports titles whose tags do not match
  their parents. Use tags in lowercase in branch names and the
  working folder, `docs/work/<tag>-<slug>/`.

## Hierarchy and dependencies

Give each tracked issue exactly one type label.
Attach children as native sub-issues
(`gh issue create --parent <n>` or `gh issue edit <parent> --add-sub-issue <n>`);
do not keep a second checklist of the same children in the body.

A parent relationship means "part of this outcome", not "blocked by". Use native
`blocked by`/`blocking` relationships only for real ordering constraints, and add
only direct ones. Create all issues first, then add dependencies, then verify with
`gh issue view <n> --json parent,subIssues,blockedBy,blocking`. Report any
relationship the API could not establish.

GitHub links closing PRs only for the default branch, so an Epic merged into its
Initiative branch has no closing link. `status.py` then counts a blocker as
satisfied only when a merged PR from the branch recorded in the blocker's Issue
references it; record the branch in the Issue and link the Issue from the PR.

Search open and closed issues for duplicates before creating. Never close, delete,
or rewrite existing issues merely to tidy the hierarchy without user authorization.

## Issue content

Write bodies for agent owners, per
[Write Issues for agents](planning.md#write-issues-for-agents). Put the context,
requirements, solution vision, and decisions in the body; link authoritative
documents and stable requirement IDs instead of copying them. The
[readiness checklists](readiness.md) define what a Task, Epic, or Initiative
must contain before delivery. A repository's own stricter checklist applies in addition.

## Pull requests

Use Conventional Commits for commit subjects, PR titles, and squash titles:
`<type>(<scope>)<!>: <imperative description>`. Squash-merge, describing the whole
reviewed outcome rather than an intermediate commit. The PR body contains:

- **Summary** and linked issues;
- **Verification:** commands, results, red evidence for new tests, and the
  candidate commit; each acceptance claim's [verdict](testing.md#verdicts);
  before and after output or screenshots for a visible change;
- **Merge risk:** whether the change is a one-way door (hard to undo: data
  migrations, deletions, public contracts, external side effects) or a two-way
  door (a revert undoes it), and the blast radius if it is wrong;
- **Exceptions:** each `ENGINEERING.md` exception the PR adds or changes, in
  plain words, with the review's `confirmed:` verdict, or `None`
  ([gate integrity](standards.md#gate-integrity));
- **Documentation impact:** pages updated, or why none change (required);
- **Handoff:** filled only while work is interrupted, in the format from
  [execution](execution.md#hand-off-and-resume).
