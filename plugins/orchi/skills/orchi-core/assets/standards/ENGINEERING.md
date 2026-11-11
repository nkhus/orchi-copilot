# Engineering

<!-- Orchi template: the defaults for a TypeScript web app. Replace every <...>,
drop rows that do not apply, and for Python take the Python column of the Orchi
standards reference. Each row lands with the first change that needs it; a
proof of concept keeps only the core rows. Commit this file with the checks
it declares, never ahead of them. `standards.py` reads the Checks and Exceptions tables: keep their
columns. -->

Agents write and review this repository's code; these rules and the checks that
enforce them are the review. Follow them on every change. A change that cannot
follow a rule records an exception below, and the PR reports it in plain words.

## Product constraints

<Who uses it and on which devices; where it runs and what is mandated; data
sensitivity; budget; proof of concept or meant to last. Link the Exploration.>

## Stack

| Part | Choice | Version | Reason |
| --- | --- | --- | --- |
| Language | TypeScript, `strict` | <5.x> | Types are the cheapest check an agent gets |
| Runtime | Node.js LTS | <22.x>, pinned in `.nvmrc` | |
| Framework | Next.js with React | <x.y> | |
| Styling | Tailwind CSS 4, shadcn/ui, SmoothUI | <x.y> | The design track builds on them |
| Package manager | pnpm | <x.y>, pinned in `packageManager` | |

## Commands

| Purpose | Command |
| --- | --- |
| Set up | `pnpm install --frozen-lockfile` |
| Boot with seeded data | `pnpm dev:seed` |
| Format | `pnpm format` |
| Every blocking check | `pnpm check` |
| Build | `pnpm build` |

## Checks

| Check | Tool | Command | CI job | Config | Threshold | Blocking |
| --- | --- | --- | --- | --- | --- | --- |
| Format | Prettier | `pnpm format:check` | format | .prettierrc.json | - | yes |
| Lint | ESLint, typescript-eslint `strictTypeChecked` | `pnpm lint` | lint | eslint.config.mjs | - | yes |
| File size | ESLint `max-lines` | `pnpm lint` | lint | eslint.config.mjs | <= 300 | yes |
| Function size | ESLint `max-lines-per-function` | `pnpm lint` | lint | eslint.config.mjs | <= 50 | yes |
| Complexity | ESLint `complexity` | `pnpm lint` | lint | eslint.config.mjs | <= 10 | yes |
| Types | TypeScript `strict` | `pnpm typecheck` | types | tsconfig.json | - | yes |
| Tests | Vitest | `pnpm test` | test | vitest.config.ts | - | yes |
| Coverage of changed lines | Vitest coverage, diff-cover | `pnpm coverage:changed` | test | vitest.config.ts | >= 90 | yes |
| Acceptance | Playwright | `pnpm test:acceptance` | acceptance | playwright.config.ts | - | yes |
| Accessibility | axe in Playwright, WCAG 2.2 AA | `pnpm test:acceptance` | acceptance | playwright.config.ts | - | yes |
| Module boundaries | dependency-cruiser | `pnpm boundaries` | boundaries | .dependency-cruiser.cjs | - | yes |
| Dead code | knip | `pnpm knip` | dead-code | knip.json | - | yes |
| Secrets | gitleaks | `gitleaks git` | secrets | - | - | yes |
| Dependencies | pnpm audit | `pnpm audit --audit-level high` | dependencies | - | - | yes |
| Static analysis | Semgrep CE | `semgrep scan --config p/default --error` | sast | - | - | yes |
| Licenses | license-checker-rseidelsohn | `pnpm licenses:check` | licenses | - | - | yes |
| Declared checks run in CI | Orchi `standards.py` | `standards.py check` | standards | - | - | yes |
| Documentation links | Orchi `knowledge.py` | `knowledge.py lint` | documentation | docs/README.md | - | yes |
| Mutation | Stryker on files changed that week | `pnpm mutation` | mutation | stryker.config.json | - | weekly |

`Config` lists committed configuration files, comma-separated, or `-`.
`Threshold` is `-` or an operator and a number. `Blocking` is `yes`, `no`, or
`weekly`.

## Architecture

Layers depend in one direction; the review enforces it until the boundaries
check is added.

| Layer | Path | May import |
| --- | --- | --- |
| types | `src/types/` | nothing |
| config | `src/config/` | types |
| data | `src/data/` | types, config |
| domain | `src/domain/` | types, config, data |
| api | `src/app/api/` | types, config, domain |
| ui | `src/app/`, `src/components/` | types, config, domain |

- MUST validate every input at its boundary with Zod: requests, files,
  environment, third-party responses. Enforced by review.
- MUST log through the structured logger; no `console`. Enforced by lint.
- MUST read configuration from the environment, documented in `.env.example`.
  Enforced by the secrets check and review.

## Dependencies

Add a dependency only with a reason in the PR. Pin exact versions in the
lockfile. With hardening, Dependabot proposes updates weekly, grouped, and
production dependencies may use only these licenses: MIT, ISC, BSD-2-Clause,
BSD-3-Clause, Apache-2.0, 0BSD, BlueOak-1.0.0, CC0-1.0, CC-BY-4.0, MPL-2.0,
Python-2.0, Unlicense.

## Security

No secret in the repository, in logs, or in test fixtures. <Data handling rules
from the product constraints.>

## Conventions

Only what no tool checks. Conventional Commits. <Naming, error handling, and
documentation rules the project adds.>

## Exceptions

| Rule | Where | Reason | Expires |
| --- | --- | --- | --- |
