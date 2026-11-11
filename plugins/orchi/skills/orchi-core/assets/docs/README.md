# Documentation

<!-- Template: the map of this project's current documentation. Keep it short;
contributors and assistants read it before each change. List each page, and
assign code to the pages that describe it in the Ownership table, which reviews
read to check that changed code kept its pages current. -->

How this product behaves and is built now; planned work is not described here.

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
