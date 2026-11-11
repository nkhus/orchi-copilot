# Documentation

<!-- Orchi template: the map of this project's current documentation. Keep it
short; agents read it before every Task. List each page, and assign code to the
pages that describe it in the Ownership table, which the review reads to
check that changed code kept its pages current. Working documents never appear here: they live in
`docs/work/` on branches. -->

How this product behaves and is built now. Planned work is in GitHub Issues and,
while it is under way, in `docs/work/` on its branch.

| Page | Covers |
| --- | --- |
| `ENGINEERING.md` | Stack, commands, checks, architecture rules, exceptions |
| `PRODUCT.md` | Who the product is for and what it must be |
| `DESIGN.md` | The design engine and the visual system |
| `docs/design/references/` | The products and sites the design takes after, with screenshots |
| `docs/design/surfaces/` | Each surface's brief and approved comp |
| `docs/product/<feature>.md` | What a user can see and do now, with the acceptance test for each criterion |
| `docs/<area>/README.md` | How an area is built, its contracts, and the decisions in force |

## Ownership

| Code | Pages | Area |
| --- | --- | --- |
| `src/<area>/**` | `docs/<area>/README.md`, `docs/product/<feature>.md` | <Area> |
