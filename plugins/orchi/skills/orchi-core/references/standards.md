# Engineering standards

Use when setting up a new project, auditing an existing one, planning work in a
project with `ENGINEERING.md`, writing code there, or reviewing it. The
repository's own instructions take precedence over these defaults.

## Premise

The user steers and agents write the code; nobody is expected to read it.

1. **Tools are the code review.** Every rule a tool can check is a blocking
   check from the commit that adds it; prose rules cover only what no tool can
   check.
2. **Defaults, not questions.** Orchi chooses the stack, tools, thresholds, and
   layout from this reference and records why. The user is asked about the
   product and its constraints, never about anything technical; they may
   override any choice.
3. **Gates are not lowered quietly.** Lowering a threshold, disabling a rule,
   adding a suppression, skipping or deleting a test, or changing what a check
   runs is a review blocker unless `ENGINEERING.md` records it as an exception.
   Writers check their own diffs for this, and the review checks it again; no
   script guesses at it.
4. **The user accepts behavior.** Acceptance criteria say what a user can see or
   do; each has an automated acceptance test once the acceptance harness has
   landed (until then, and in a proof of concept, evidence from the running
   app), and the PR shows the evidence.
5. **The repository is the memory.** A decision reached in a conversation goes
   into `ENGINEERING.md` or a tool's configuration, or the next session loses it.

## Product constraints

The only questions the user answers, in the exploration or before the first
code:

- who uses the product, and on which devices;
- where it must run, and any platform, vendor, or language their organization
  mandates;
- what data it holds, and how sensitive it is;
- the budget for hosting and paid services;
- whether it is a disposable proof of concept or meant to last.

A proof of concept gets only the core checks; the [hardening](#hardening) Epic
follows when the user says it is meant to last.

## Stack

| Project kind | Default |
| --- | --- |
| Web app | TypeScript (strict), React with Next.js, Tailwind CSS 4, shadcn/ui and SmoothUI, pnpm |
| Service or API | TypeScript (strict) on Node.js LTS with Hono, Zod at every boundary, pnpm |
| Data, ML, scripting | Python 3.13 with uv |
| CLI | TypeScript, or Python when the project is already Python |

Use one language across a product unless a domain needs another. Mobile apps
have no default yet: propose a stack with its reasons, as an override. A
mandated platform or language replaces the matching default and keeps the
checks. Pin the runtime and package manager versions in the repository.

## Checks

Every check runs in a CI job named in the `CI job` column (related checks may
share one, as lint and its limits do). A check lands, with its `ENGINEERING.md`
row and CI job, in the first Task whose change needs it, as the `Lands with`
column says: the core checks with the first code, the rest only in a project
meant to last, through [hardening](#hardening) and then with the first Task
that needs each, which names adding it in its requirements.
Prove a check fails on a planted violation, never committed, only when its
configuration is the project's own (a custom rule, a boundary table).

| Check | TypeScript | Python | Blocking | Lands with |
| --- | --- | --- | --- | --- |
| Format | Prettier | ruff format | yes | core |
| Lint | ESLint with typescript-eslint `strictTypeChecked` | ruff with the `ALL` rule set minus documented conflicts | yes | core |
| Types | `tsc --noEmit` with `strict`, no explicit `any` | pyright `strict` | yes | core |
| Unit and integration tests | Vitest | pytest | yes | core |
| Size and complexity | ESLint `max-lines` 300, `max-lines-per-function` 50, `complexity` 10 | ruff `C90` 10, `PLR0915` 50 statements | yes | core |
| Secrets | gitleaks | gitleaks | yes | core |
| Declared checks run in CI | `standards.py check` (the standards workflow) | same | yes | core |
| Coverage | `>= 90%` of changed lines; the project floor only rises | coverage.py, same rule | yes | hardening |
| Acceptance tests | Playwright, one test per acceptance criterion | pytest, or Playwright for a UI | yes | hardening |
| Accessibility | axe in the Playwright run, WCAG 2.2 AA | same | yes | hardening |
| Module boundaries | dependency-cruiser | import-linter | yes | a second layer |
| Dead code | knip | vulture | yes | hardening |
| Dependencies | `pnpm audit --audit-level high` | pip-audit, every known vulnerability | yes | hardening |
| Static security analysis | Semgrep CE with `p/default`, or CodeQL where GitHub Code Security is available | same | yes, errors | hardening |
| Licenses | license-checker-rseidelsohn `--production --onlyAllow` the template's list | pip-licenses `--allow-only` the same list | yes | hardening |
| Mutation tests | Stryker on files changed that week | mutmut on files changed that week | weekly | hardening |

A custom lint rule's message says how to fix the violation: its reader is an
agent. Add a custom rule when review finds the same judgement twice, as the
[lessons](review-delivery.md#lessons) ladder says.

## Architecture

- Layers in one direction, by default `types → config → data → domain → api → ui`,
  enforced by the review until the module boundary check lands; a new module
  states its layer.
- Validate at every boundary (requests, files, environment, third-party
  responses); code inside a boundary trusts its types.
- Structured logs, and one command that boots the app in a worktree with seeded
  data, so an agent can run it, reproduce a bug, and read what happened.
- Configuration comes from the environment and is documented in an example file;
  no secret is committed.

## Repository

- `ENGINEERING.md` at the root, beside `PRODUCT.md` and `DESIGN.md`.
- Lockfiles committed; Conventional Commits; with hardening, Dependabot grouped
  weekly.
- In a project meant to last, a ruleset on the default branch: every blocking
  check required, pull requests required, linear history, no force push, no
  deletion.
- CI runs on every pull request, whatever its base, so Epic PRs into an
  Initiative branch are checked too.

## `ENGINEERING.md`

The [template](../assets/standards/ENGINEERING.md) holds the sections and the
defaults above. Two tables have a fixed shape, because `standards.py` reads them:

- **Checks**: `Check`, `Tool`, `Command`, `CI job`, `Config`, `Threshold`,
  `Blocking`. `Config` lists the committed configuration files, comma-separated,
  or `-`. `Threshold` is `-` or an operator and a number (`>= 90`, `<= 300`).
  `Blocking` is `yes`, `no`, or `weekly`.
- **Exceptions**: `Rule`, `Where`, `Reason`, `Expires`. `Rule` names the waived
  rule or suppression (`no-console`, `eslint-disable`, `test deleted`,
  `threshold`); `Where` is a path or glob; `Expires` is a date (`YYYY-MM-DD`).

`ENGINEERING.md` describes what the repository enforces now: it lands in the
same commit as the checks it declares, never ahead of them.

## Checker

`python3 <orchi-core>/scripts/standards.py <command>`, from the repository root,
where `<orchi-core>` is the orchi-core skill's base directory:

| Command | Does |
| --- | --- |
| `check` | Every declared check has its CI job in `.github/workflows/`, the job runs its command, and its configuration files exist; no exception has expired |
| `ruleset` | Prints the GitHub ruleset that requires every blocking check |

`check` exits 1 with its findings and 0 when clean; without `ENGINEERING.md` it
reports that and exits 0. It only checks structure. Whether a change weakens a
gate is judged by the writer and the review, below. Without the documentation
workflow, drop the documentation row from the Checks table; without the
standards workflow, drop the `standards` row. The workflows run copies of the
scripts in `.github/orchi/scripts/`, which Orchi's
[repository preparation](pool.md#prepare-the-repository) commits.

## Gate integrity

A writer checks its own diff, and the review checks the whole range, for any of
these; each is a blocker unless an exception in `ENGINEERING.md` covers it:

- `ENGINEERING.md` removed, or a check removed, made non-blocking, or given a
  looser threshold or a different command, job, or configuration;
- a change to what a check runs: a workflow step removed, commented out, made
  non-failing (`continue-on-error`, `|| true`, an `if:` that skips it), or a
  package script or tool section that no longer runs the declared tool;
- a configuration that turns a rule off, loosens a limit, or is shadowed by a
  new configuration file;
- a suppression in any syntax (inline disables, file-level directives, coverage
  ignores, skip, only, or conditional-skip modifiers on tests);
- a test deleted, moved out of the test paths, or left with fewer assertions
  without the behavior it covered being removed.

Record an exception only for a reason the change cannot avoid, with the
shortest expiry that fits. Agents decide exceptions, never the user: the writer
records one its Task names and reports any other, which the dev lead decides,
and the review confirms no change avoids it. When one expires, the dev lead
fixes the code or renews it with a new reason. Removing `ENGINEERING.md` needs
the user's agreement. The PR lists each exception in plain words, as the
[review](review-delivery.md) says.

## New project

A new project has no setup Epic. Its first delivery is its
[first run](planning.md#engineering-standards), which also scaffolds the stack
from the defaults, the boot command with seeded data, `ENGINEERING.md` with the
core checks in CI (the standards workflow included), and the documentation map
with its first area page from the [templates](knowledge.md#current-documentation).

In a project meant to last, after a PR that changes the blocking checks merges
into main, the delivering session (`orchi-deliver`) applies or replaces the
ruleset and tells the user; when GitHub refuses, it tells them in one line what
enforcing the checks needs. A proof of concept gets no ruleset.

```
python3 <orchi-core>/scripts/standards.py ruleset | gh api -X POST repos/{owner}/{repo}/rulesets --input -
```

To replace it, pipe the same output to
`gh api -X PUT repos/{owner}/{repo}/rulesets/<id> --input -`, with the id from
`gh api repos/{owner}/{repo}/rulesets`.

## Hardening

For a project meant to last, planning adds an Issue labelled `needs-planning`
with `Requested by: Orchi`, blocked by the first run, so a planner plans the
hardening Epic once there is code to check. It blocks nothing, and a dev lead
runs it beside the product work: one Task per group of the non-core checks the
code needs, with Dependabot, each fixing what its checks find on main; an open
Initiative fixes the rest when it brings main in. When the user says a proof of
concept is now meant to last, planning adds the Issue then.

## Audit

For a project without `ENGINEERING.md`, inventory tool configurations, CI jobs,
the default branch's rulesets and protection (when `gh` can read them), and the
rules in `AGENTS.md` and scoped instruction files. Sort each rule:

| Verdict | When |
| --- | --- |
| Retain | Only a person can check it, and it is still true |
| Rewrite | It is true but vague or out of date |
| Relocate | It belongs in another document (`ENGINEERING.md`, `PRODUCT.md`, `DESIGN.md`) |
| Automate | A tool can check it; it becomes that tool's configuration |
| Delete | A tool already enforces it, or it is no longer true |

`orchi-standards` plans the standards Epic from the result.

## Drift

With the standards workflow, `standards.py check` runs weekly and
keeps one open Issue, labelled `needs-planning`, listing what drifted, such as
an expired exception or a check that lost its job. Planning takes it like any
request; no session starts unattended.
