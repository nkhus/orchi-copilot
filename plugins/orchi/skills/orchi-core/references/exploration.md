# Explore and shape an idea

Use when a request is an idea rather than agreed work: a new project, module, or
feature whose direction needs research, a comparison of approaches, or
strategic decisions before anyone can propose a scope. An exploration produces
decisions, not code. It ends when the idea is shaped enough for
[planning](planning.md) to turn it into an Initiative, Epic, or Task without
reopening its decisions.

## The Exploration Issue

One Issue labelled `Exploration` holds the exploration's state, so it survives
across sessions, and one branch, `explore/<slug>` from main, holds its working
folder `docs/work/<slug>/` ([working documents](knowledge.md#working-documents)).
Create both once the user agrees on the destination. The Issue body is the
current map; detail lives in the folder's `research/` and `options/` files, and
the body links to them by commit permalink (`/blob/<sha>/docs/work/...`), so the
links survive when the branch moves on and the folder is later deleted.

| Section | Content |
| --- | --- |
| Destination | What is being decided, what the end looks like, and how much it is worth: Task, Epic, or Initiative size, and any time limit |
| Request | The original idea in the user's words, kept apart from later decisions |
| Constraints and no-gos | Fixed limits, and what is explicitly out of scope |
| Stack | For a new product: its [product constraints](standards.md#product-constraints), and the stack the standards defaults derive from them, with reasons |
| Options | Each direction considered: its shape, what it makes easy and hard, the findings it rests on (links to research files), and the verdict with its reason; detail in `options/<option>.md` |
| Decisions | The decision log ([clarify](planning.md#clarify-with-the-user)), each decision with an id (D1, D2, ...) and the area of the product it concerns |
| Requirements | Numbered requirements (R1, R2, ...) of the chosen direction, each observable at completion |
| Design | For a product with a user interface: the screen map, the approved wireframe of each key screen, the references, the design engine, the approved comp, and the clickable mockup, each linked to its file in `design/` (see [Design](#design-session)) |
| Shape | The chosen direction, and candidate Epics as outcomes with the result or contract each supplies to the next |
| Product | For a product with a user interface: the product truth the first design Epic records in `PRODUCT.md` (see Shape) |
| Ideas | Every idea the user raised and parked, and every direction, variant, or remark they turned down, with why |
| Open questions | What is still open, with what each question blocks; questions you can only sense so far are listed as such |

## Phases

Each phase ends on its completion criterion. Return to an earlier phase when an
answer changes the destination or invalidates options. A request for a
prototype of something entirely new starts in
[prototype mode](#prototype-mode), which runs Frame as its interview; the other
phases follow once the user says to build it.

1. **Frame.** Ask about the destination and its size, the original request, and
   the constraints; for a new product, the product constraints too. Done when
   the user agrees on the destination; then create the Issue and the branch.
2. **Research.** Facts are the agent's job. Start `orchi-researcher` in Research
   mode for each external question and `orchi-scout` for code and Issues, in
   parallel, and keep asking the user what does not depend on their answers.
   Write each verified finding to `research/<question>.md` with its sources,
   keeping what the sources state apart from what is inferred, and commit and
   push it. Until options exist, list it under Open questions as answered, with
   its link; then link it from the options it shapes. Done when every
   option-shaping question is answered or recorded as not established.
3. **Diverge.** Start `orchi-researcher` in Option mode, at least three times in
   parallel, each with a different lens: minimal; most flexible; best for the
   most common case; buy or reuse rather than build; or the smallest useful
   step, including not building. Present the options one at a time, compare
   them, and recommend one or a hybrid; write each to `options/<option>.md` with
   its verdict once the user decides. Ask open questions here rather than
   offering a menu. Done when the user has picked a direction.
4. **Design.** For a product with a user interface, run the
   [design session](#design-session) with the user, so they see how the
   product will look before anything is planned. Skip it only for a product
   without one, or when the user says so. Done when the user has approved the
   screen map, the key screens' wireframes, the style, and the mockup.
5. **Converge.** Resolve the chosen direction's decisions in rounds along their
   dependencies, as planning's clarify rules describe, and record each one at
   once. Before shaping, prove with a prototype each assumption the direction
   cannot work without that nothing has shown yet (an external service or
   model, access, data); offer one when a question cannot be settled on paper
   (how a state model behaves). Done when no open question affects the
   approach.
6. **Shape.** Write the requirements and the Shape section. For a product with
   a user interface, also fill the Product section: the primary users and
   their situation, the purpose and the
   mechanism no competitor shares, positioning, platform, stack (from the Stack
   section), constraints, brand
   commitments, evidence, and the accessibility level (WCAG 2.2 AA unless the
   user says otherwise; do not ask). The first design Epic writes `PRODUCT.md`
   from it and asks only what is missing, and builds the approved mockup on the
   stack. For a new
   product, fill the Stack section from the
   [standards defaults](standards.md#stack) and state it once; never ask the user
   to choose a tool. Then read
   the whole Issue back to the user. Done when the user confirms it is shaped. When
   planning continues in the same session, that confirmation also agrees the
   plan's outcome and direction; planning asks only about scope it adds.

## Design session

A long conversation about how the user sees the product, with things to look
at from its middle on. Work through it in four steps, returning to an earlier
one whenever an answer changes it; record each decision in the Design section
at once and keep the approved files in the working folder's `design/`.
`orchi-designer` subagents build what the user looks at, in parallel where they
can, each with its own empty output folder in `.orchi-tmp/`, and you show
their files on the design board.

1. **Structure.** Ask who uses the product and for which jobs, and draw the
   screen map from it: the screens, what leads to what, and the navigation.
   For each key screen, ask what it shows and lets the user do, what matters
   most, and what folds away at the narrow width, and write its brief to
   `design/screens.md`. Then offer the user different panels: `orchi-designer`
   in Wireframe mode builds three or four grey layouts of the screen, each
   named by its idea. The user picks, combines ("the queue from B, the context
   from C"), or asks for more; run rounds until each key screen has an
   approved wireframe.
2. **Style.** Once the structure holds, ask whether the user has preferences
   and sites they like, and propose five to seven strong references that fit
   the product's category, each with what it would bring (for a work tool, say,
   Linear, Stripe, Vercel, Raycast, ElevenLabs, ChatGPT). Take a
   screenshot of each, ask what the user likes and dislikes in it, and record
   the agreed set in `design/references/`: a `README.md` with each link, what
   to take from it, and its screenshot.
3. **Engine round.** On the first key screen, start two `orchi-designer`
   subagents in Variant mode at once, one per design skill, each with the
   approved wireframe, its brief, and the references: Hallmark builds one
   variant on each of its three dealt themes, prototype its three divergent
   variants. Show all six side by side, each labelled by its idea, never by
   the skill that made it: the user picks a look, not a tool. The variant the
   user picks sets the style and the project's design engine; the user may instead ask for another round
   around a variant they liked. Skip this step when `DESIGN.md` already names
   the engine, and run a direction round with that engine instead.
4. **The whole system.** Start `orchi-designer` in Mockup mode with the engine,
   the screen map, the briefs, the approved wireframes, the references, and the
   approved comp: every key screen in that style, linked into a clickable
   mockup. Go over it screen by screen with the user and rerun what they change
   until they approve it.

Commit and push only what the user approved: `design/screens.md`, the
references, the approved wireframes in `design/wireframes/`, the approved comp
in `design/comp/`, and the mockup in `design/mockup/`. Nothing else from the
output folders enters the repository.

### The design board

The user sees, rates, and picks variants on the design board canvas, as the
[canvases reference](canvases.md#the-design-board) says: gather each round's
files under `.orchi-tmp/board/v/<round>/`, publish the round, say what to look
at, and read the scores, notes, and picks when the user is done. Record what
they picked and why in the Design section.

## Prototype mode

For an entirely new product, site, or interface built from scratch, the user
may ask for a prototype: a detailed interview, then a living prototype the user
reacts to while the interview goes on, as in a prompt-to-app builder, but asked
before it is guessed. The prototype is the interview's richest result, not a
decision: prototype mode runs the Frame phase, and the phases after it all run
once the user says to build it, with the prototype as the user's input. The
Issue, the branch, and the decision log work as for any exploration; tell the
user what they can look at and decide, never about Issues or files. Picks and
remarks are the user's alone, also in autonomous mode: mark each such question
`(user)`.

In a repository that already has a product, ask once at the start whether to
reuse its style and existing work; unless the user says so, design from
scratch. Features, fixes, and redesigns of an existing product take the phases
without prototype mode.

Research runs beside the interview, so the session knows the topic well
enough to ask good questions. As soon as the user has said what the product is
for, start `orchi-researcher` subagents in Research mode in the background,
several at once, one question each: the market and its competitors (who serves
these users today, how, at what price, and what their users praise and
complain about), the domain (the users' jobs, the trade's terms, metrics, and
rules, the systems they already use), and products whose interfaces solve the
same jobs. Start another whenever an answer or a remark opens a question the
user should not have to answer, and keep interviewing while they work. Write
each finding to `research/<question>.md` as phase 2 says, and use it at once:
ask in the domain's terms, offer the answers the findings support as the
recommended options, name what competitors miss, propose references from the
products found, and take the variants' directions and sample data from it.

1. **Interview.** Frame the destination as phase 1 says, then ask, as the
   design session's Structure step does, who uses the product and for which
   jobs, the screen map, and each key screen's brief, adding the data it
   shows. Ask for the sites it should feel like and propose five to seven, as
   its Style step says. Ask every question with `ask_user`, its
   recommended answer first, and answer yourself what the request settles.
   Done when the screen map and the key screens' briefs are agreed.
2. **Variants.** Ask how many variants to build (three unless the user says
   otherwise). Name that many directions that differ in one line each (what
   leads, density, tone), and start one `orchi-designer` subagent in Mockup
   mode per direction, at once, each with the screen map, the briefs, the
   references, its direction, the design skill you choose for it (split them
   between the two skills), and its own empty output folder in `.orchi-tmp/`.
   Show the mockups on the design board, each labelled by its direction, never
   by the skill that made it. After the round, ask whether to run another
   (around a variant the user liked, or new directions) or go on with one, and
   record the pick and why.
3. **Living prototype.** Commit the picked mockup to the working folder's
   `prototype/`, record its path in the Design section, and open it in the
   Browser canvas for the user to keep beside the conversation, as the
   [canvases reference](canvases.md#pages-in-the-browser-canvas) says. From here, each
   remark is a change: one the user types, or an answer of the interview. Give changes to an `orchi-designer` subagent in
   Mockup mode, with the current prototype and the remarks, and keep asking
   while it works: states (empty, loading, error, many items), edge cases,
   roles, the flows between screens, and what each rule is. Remarks that
   arrive meanwhile wait and go to the next subagent in one batch. When the
   user asks for options for a screen, ask how many and run a round on the
   board as step 2 does, for that screen.
4. **Before showing a change,** go through the flows it changed in the
   Browser canvas and at the widths the briefs name, and give any breakage
   back to the subagent. After two failed repairs of the same thing, change the
   approach or ask the user instead of repairing it a third time. Commit and
   reload the canvas for each change the user sees: every commit is a version, and to go back
   you commit an earlier version's files as a new one.
5. **Build it.** When the user says to build it, make sure the Issue holds
   every finding of the conversation and the prototype: each decision, a
   requirement for each behavior the prototype shows and each rule the
   interview settled, every idea the user raised and parked, every direction
   and remark the user turned down and why, and what is still open. Then go on
   from phase 2. Each phase takes the prototype as the user's input and asks
   only what it left open: research reuses the findings so far and checks what
   the prototype assumes (that its data can be had, that the services it
   implies exist),
   Diverge compares directions against it, the design session starts from its
   screen map, briefs, and references and designs the product again through
   its own steps, and Converge proves what it cannot work without. The
   prototype's pages are never product code or an approved comp.

A prototype holds only plausible sample data in its pages: no sign-in,
database, or outside service, which planning plans for the product.

## Prototypes

A prototype is throwaway code that answers one question. Build one that proves
an assumption without asking, and tell the user its verdict in product terms;
build any other with the user's agreement. Ask only for access the user alone
can grant. Build it on a `prototype/<slug>` branch from main, mark it as a
prototype in its name and first lines, make it run with one command, keep its
state in memory, and skip tests and polish. Record the question and the verdict
in the Issue with a link to the branch. Never merge the branch; the decision,
not the code, carries into planning.

## New projects

Exploration needs a Git repository with a GitHub remote, because the Issue is
its state; Orchi [prepares it](pool.md#prepare-the-repository) before any crew
starts.
Planning a new project starts with its
[first run](planning.md#engineering-standards), which the rest of the product
code waits for.

## Hand off

When the user confirms the shape, the researcher crew continues into planning in the same session.
Planning takes the destination, requirements, decisions, and Epic candidates as
agreed, links the Exploration as the source request, and asks only what the
exploration left open. It creates its Initiative or Epic branch from
`explore/<slug>`, so the working folder carries on, and gives every decision its
fate. After the tracked work exists, close the Exploration as
completed with a link to it. An exploration that ends in "do not build" closes
as not planned, with the reason in its decision log; record that decision in its
area page, delete the working folder, and open the branch as a documentation PR
([move into current documentation](knowledge.md#move-into-current-documentation)).
