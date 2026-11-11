# Design

How Orchi designs user interfaces: product context and references with the
user, an engine round and direction rounds of variants, approved comps, and
builds from them. The design track runs in a Design Epic held by a designer
crew, or in an exploration's design session; `orchi-designer` builds the
variants and the UI Tasks.

## Structure

| Part | Defined in |
| --- | --- |
| The design Epic: load, product and references, briefs, engine and direction rounds, approval, builds | `plugins/orchi/skills/orchi-design/SKILL.md` |
| An exploration's design session, prototype mode, and the design board | `plugins/orchi/skills/orchi-core/references/exploration.md` |
| Design depth (none, brief, Epic) in planning | `plugins/orchi/skills/orchi-core/references/planning.md` |
| Who runs which design step, and the design skills | `plugins/orchi/skills/orchi-core/references/roles.md` |
| The designer's Wireframe, Variant, Mockup, Task, and Audit modes | `plugins/orchi/agents/orchi-designer.agent.md` |
| The design board canvas and pages in the Browser canvas | `plugins/orchi/skills/orchi-core/references/canvases.md`, `plugins/orchi/extensions/orchi-canvases/` ([canvases](canvases.md)) |

## The design Epic

A planner sets each piece of UI work's design depth. Work at depth Epic gets a
standalone Design Epic, an Epic whose UI design section starts with
`Design Epic:`, which Orchi gives to a designer crew running
`orchi-design`:

1. **Load.** Check the Epic, take it (assign yourself), and read the project's design engine
   from `DESIGN.md`. When the exploration ran a design session, copy what the
   user approved there.
2. **With the user, surface by surface.** Write `PRODUCT.md` from the
   exploration's Product section; agree references (the user's and three to five
   proposed) in `docs/design/references/`; agree each surface's brief. In a
   project's first design Epic, the engine round runs two `orchi-designer`
   subagents in Variant mode, one per engine, and shows all six variants
   labelled by idea; the pick sets the design engine. Later surfaces get a
   direction round with the project's engine. The approved comp goes into
   `docs/design/surfaces/<surface>/`.
3. **Plan the builds** as Tasks with `orchi-designer` as the writer, and write
   `DESIGN.md` with the user after the last build; its first line after the
   title is `Design engine: <Hallmark | prototype>`.
4. **Build** through `orchi-deliver` in the same session; the review adds
   `orchi-designer`'s audit.

Only the user names references, chooses the engine and a direction, and
approves a comp or a generated asset, or Orchi while the user has autonomous
mode on.

## Design skills

The design engines are [Hallmark](https://github.com/Nutlope/hallmark) and Emil
Kowalski's [prototype](https://github.com/emilkowalski/skills). The plugin does
not bundle or vendor them. Before the first design round, the session that
talks to the user checks them with `gh skill list` and, for each one missing,
asks the user whether to install it; on a yes it runs `gh skill install` for
the GitHub Copilot agent at user scope, pinned to the commit Orchi was tested
with. The pins live once, in the roles reference's Design skills section.
Skills load when a session starts, so a skill installed mid-session may reach
only later sessions. Without them, `orchi-designer` designs without an engine
skill and says so. prototype is marked for the user's invocation only, so the
designer reads its `SKILL.md` and follows it rather than starting it with the
`skill` tool. [SmoothUI](https://smoothui.dev/) is a component source for React
projects with Tailwind CSS 4 and shadcn/ui, not a design skill.

## The design board

The user sees, rates, and picks variants on the design board, a canvas beside
the conversation ([canvases](canvases.md#the-design-board)). The session gathers
each round's files under `.orchi-tmp/board/v/<round>/`, publishes the round with
its question and a label per variant, and reads the scores (1 to 5), notes, and
picks once the user presses Round done, which sends a message into the
conversation. The board shows each variant in a sandboxed frame at 1440 or 720
px, scaled to fit, or full screen. Ratings stay in `.orchi-tmp/board/`; the
session records what the user picked and why in the Design section or the Epic.

In prototype mode, the living prototype opens in the app's Browser canvas, and
the session checks each change there before showing it. Without the canvases,
each file opens in the Browser canvas and the session asks for scores, notes,
and the pick in the conversation.

## Decisions

Only decisions that still hold. Replace an entry when its decision changes;
delete it when it no longer holds.

| Decision | Reason | Rejected | Since |
| --- | --- | --- | --- |
| Hallmark and prototype are not bundled; before the first design round the session asks the user and, on a yes, installs each missing one with `gh skill install` at a pinned commit, user scope; without them the designer works without an engine skill | A plugin cannot ship other repositories' skills without vendoring them, which makes Orchi carry their updates and licenses; `gh skill` installs them from their own repositories with source tracking, and pins keep the version Orchi was tested with | Vendoring both skills into the plugin or through `setup.py`; leaving installation wholly to the user, so a first engine round runs without engines unless the user prepared them | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| The design board is a canvas of the plugin, reading round files and ratings from `.orchi-tmp/board/`; the user rates there and the session reads the ratings with `read_picks` | The user compares variants side by side and rates them without typing scores, and the files stay out of commits | Opening each file in the browser and collecting scores in the conversation, now the fallback | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| A living prototype opens in the Browser canvas, and the session checks its flows there before showing a change | The user keeps it beside the conversation, and the session reads and drives the same page | A separate browser window | [nkhus/orchi-copilot#4](https://github.com/nkhus/orchi-copilot/issues/4) |
| Variants are labelled by their idea, never by the design skill that made it | The user picks a look, not a tool, and said skill names do not matter to them | Showing which engine built each variant | [nkhus/orchi#59](https://github.com/nkhus/orchi/pull/59) |
| Every design session and design Epic asks the user for references and proposes three to five that fit the product; the agreed set, with screenshots, is recorded in `docs/design/references/` and given to every variant and build | References raised the variants' scores more than any design skill did | Designing from the brief alone | [nkhus/orchi#59](https://github.com/nkhus/orchi/pull/59) |
| `PRODUCT.md` and `DESIGN.md` are written with the user by the session that talks to them, never by a subagent; a generated asset is committed only after the user approves it | Both bind all later work, so the user must see them | Writing them unattended in the last build Task | [nkhus/orchi#50](https://github.com/nkhus/orchi/pull/50), [nkhus/orchi#59](https://github.com/nkhus/orchi/pull/59) |
| Surface briefs and approved comps in `docs/design/surfaces/` are current documentation, updated with their surface; in a redesign, the Epic's approved briefs and comps override the incumbent `DESIGN.md` until the new one lands | Later work builds against a surface as it is, and a redesign must not be pulled back to the look it replaces | Treating briefs as one-off planning files | [nkhus/orchi#50](https://github.com/nkhus/orchi/pull/50) |
| UI design is a kind of Epic, a Design Epic, whose UI design section starts with `Design Epic:`, held by a designer crew with its own skill, `orchi-design`; a Design Epic stays standalone, outside any Initiative, and blocks the work that builds on it | The design steps need a session that talks to the user, and an Initiative goes to one dev lead crew; a line in the body marks it without a process label in the repository | A `design` label (reversed in [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7)) | [nkhus/orchi#43](https://github.com/nkhus/orchi/pull/43), [nkhus/orchi-copilot#7](https://github.com/nkhus/orchi-copilot/issues/7) |
| The planner sets each piece of work's design depth: none, brief, or Epic | Most changes need no design step, and variant rounds are costly | None recorded | [nkhus/orchi#43](https://github.com/nkhus/orchi/pull/43) |
| The design audit runs in review, not in CI | Neither engine ships a detector that knows the project's `DESIGN.md`, and the review already reads the brief and comp | A CI design workflow | [nkhus/orchi#59](https://github.com/nkhus/orchi/pull/59) |
