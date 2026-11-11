# Plan the next verifiable result

Use after research and direction agreement. Read the actual integration branch,
relevant code, owning documentation, and completed dependency results. A plan
describes intended behavior; it is not evidence that behavior exists.

Plan proportionately. A fix still needs a Task that passes the Task readiness
checklist; keep each answer short. An Epic needs the design below in its issue or a linked branch document,
then its Tasks. Do not create a planning Task per field or empty design documents.

## Declined work

Before proposing, look for the same request among Issues closed as not planned
and in the repository's out-of-scope records, if it keeps them. When it was
declined before, put the earlier reason, with its link, into the proposal: new
evidence can reopen it, asking again cannot. When the user declines a request
for a lasting reason, record it with the user's words so the next session finds
it: close its Issue or Exploration as not planned with the reason. When no Issue
exists, add a record where the repository keeps out-of-scope records, or else
open an Issue with the request and close it as not planned at once. A request
parked for later is not declined.

## Clarify with the user

The questions and answers with the user are the most valuable input to an Issue.
Only the main session talks to the user; a delegated agent that drafts Issues
returns its questions instead of guessing, and the main session asks them and
continues that agent with the answers.

- **Find the gaps first.** Check what you know against the readiness checklist
  for the planned scope. Every item you would otherwise have to guess becomes a
  question.
- **Look up facts; ask for decisions.** Never ask the user what the code,
  documentation, Issues, or an external source can answer: send scouts, and
  keep asking the questions that do not depend on what they find.
- **Ask only what changes the result.** Ask when the answer changes
  requirements, scope, acceptance, or risk, and only at the user's level, as
  the [Orchi skill](../SKILL.md#research-propose-agree) says. Decide technical
  choices yourself and record them as decisions with a reason.
- **Ask once.** Before asking, read the decision log, the Issue, and its
  comments: never ask again what is decided, and never ask to confirm a step the
  agreed plan already covers. A question still waiting for an answer is not
  repeated; a later report says only who waits.
- **Decide what the user delegated.** When the user lets the main session decide
  a class of questions (in this conversation, the repository's instructions, or
  a pool's [autonomous mode](pool.md#autonomous-mode)), decide them instead of
  asking, and record each with the delegation (who, when, their words, its
  limits), the options, and the reason. A delegation never covers merge or
  deployment authority the user has not granted separately.
- **Make each question easy to answer.** Give one or two sentences of context,
  two to four concrete options with their consequences, and your recommendation
  first, worded so that "yes" accepts it; always allow a free answer. Ask with `ask_user`, one question per call,
  with the options as its choices.
- **Ask in rounds along dependencies.** A round holds open questions whose
  prerequisites are settled, most consequential first, a few at a time; a
  question that depends on another open question waits for a later round.
  Follow up when an answer opens a new gap or contradicts earlier evidence.
  Clarifying ends when no open question would change the requirements,
  approach, scope, acceptance, or risk.
- **Record answers at once.** Keep a decision log: question, answer, who decided
  (the user, or the main session with or without a delegation), date, and
  reason. Quote the user's answers
  faithfully; do not drop their qualifiers. Carry the log into the Issues.
- **Never present a guess as a fact.** An unanswered question stays an open
  question; if it affects the approach, the work is not ready.

## Write Issues for agents

The owner of an Issue is usually an agent that never saw the planning
conversation; the user must still be able to read and approve it.

- **Self-contained.** Put every requirement, decision, source, and constraint in
  the body. Link exact sections, not whole documents. Never refer to "as
  discussed".
- **Context before instructions.** Say why the work exists, where it fits, and
  how the system behaves today, with evidence (`path:line`, symbols, routes,
  tables, commands).
- **Separate facts, intent, and decisions.** Current behavior and evidence,
  numbered requirements (R1, R2, ...), the solution vision, and the decision log
  are distinct sections.
- **Solution vision is guidance.** Describe the intended approach and change
  points and why they were chosen. The owner may deviate within the
  requirements and records the deviation; it is not a permission list.
- **Plain, precise language.** Short sentences; one requirement per item; "must"
  and "must not" for requirements; define project terms on first use; exact
  values, names, and commands instead of descriptions of them.

## Initiative

Record the plan in the working folder's `docs/work/<tag>-<slug>/README.md` on the
Initiative branch ([working documents](knowledge.md#working-documents)), or in an
existing project location that already serves this purpose. Capture the
original request faithfully, the agreed outcome, exclusions, observable
acceptance, constraints, major decisions, and remaining unknowns. Keep the source
request distinguishable from later decisions. Link existing requirements and
stable IDs instead of copying them or inventing IDs for every sentence.

Outline Epics as independently verifiable outcomes. Explain each direct dependency
through the result or contract it supplies. Keep future Epics at outcome level and
expand an Epic into Tasks only when preparing to execute it. GitHub stores the
hierarchy and status; the document stores reasoning and requirements. Do not keep
a second child or status checklist.

Check that every agreed requirement has a planned home in an Epic. A short mapping
is enough when coverage is hard to see. Do not silently drop requirements.

From an exploration, give each of its decisions (D1, D2, ...) a fate in the plan:
a requirement it becomes, an area decision to record with the code that
implements it (name the area page), or none. A decision without a fate is a
gap in the plan.

## Epic design

Before coding, write enough design for the owner and reviewer to agree on what
the result means:

- outcome, boundaries, and numbered requirements addressed;
- the decisions that shape it, with the user's answers from the decision log;
- relevant current implementation and the change needed;
- public interfaces, data and ownership boundaries, and invariants;
- test seams: where tests go, what each seam catches and misses, and an
  existing test to follow ([testing](testing.md#seams));
- chosen approach and significant tradeoffs, including an explicit
  no-architecture-change statement when that is the decision;
- observable acceptance, relevant failure and recovery cases, and verification;
- affected documentation, direct dependencies, and unresolved material questions.

Resolve questions that affect the approach before dependent implementation. A
bounded investigation Task can answer a later technical unknown; it produces
findings and a recommendation, not silently adopted product code. Discuss a
material change of direction with the user.

## User interface design

Work that changes a user interface gets a design depth in its Epic or Task. The
project's design engine, Hallmark or prototype, is the one `DESIGN.md` names;
a new product picks it in its exploration's design session, and a project
without either picks it in its first design Epic. The steps that
need the user run in the session that talks to them, and writers build only
against what the user approved.

| Depth | When | Planning does |
| --- | --- | --- |
| None | The change stays within existing components and screens | Nothing more; a Task that is mainly UI goes to `orchi-designer`, which builds inside `DESIGN.md` with the engine's craft rules, and the review's design audit covers every UI range |
| Brief | A new screen or feature inside an established visual world (`DESIGN.md` exists) | Ask the user whether to add references to `docs/design/references/`, agree the surface brief with them, and record it in `docs/design/surfaces/<surface>.md`; when the composition stays materially open, run a direction round (three variants from `orchi-designer` in Variant mode with the project's engine) and commit the chosen variant as the approved comp. Commit the brief on the work's branch, which planning creates now, and link it |
| Epic | A new product, a redesign, or several screens whose composition is open | Plan a standalone `design` Epic (labels `Epic` and `design`) for a designer crew, outside any Initiative, and make each Epic that builds on it blocked by it |

- A design Epic names the surfaces it designs, what must stay, and whether it
  replaces `DESIGN.md`. Its Tasks are the builds of the approved surfaces; the
  designer splits them after the user approves each comp, so plan them at
  outcome level.
- From scratch, plan the key surfaces as one design Epic, and the rest now as an
  Initiative from the Exploration's shape. When the exploration ran a design
  session, the design Epic names its Design section as its source: the user
  has already approved the screen map, wireframes, references, engine, and
  mockup, so the Epic builds them on the stack and designs only the surfaces
  the session left out. An Epic that builds on the designed
  surfaces is blocked by the design Epic and answers
  its UI fields `Deferred until #<design Epic>`, resolved from `PRODUCT.md`,
  `DESIGN.md`, the surface briefs, and the built surfaces, which are kept. When
  the rest is one Epic that builds on them, plan it instead as an Issue labelled
  `needs-planning`, with `Requested by: Orchi`, blocked by the design
  Epic, for a planner once the design merges.
- Without `PRODUCT.md`, the design Epic starts by writing it with the user; for
  a redesign without `DESIGN.md`, by recording the incumbent look in it as
  evidence. A design Epic without a design session behind it then agrees
  references with the user, and one without `DESIGN.md`, or one that replaces
  it, runs the engine round, in which the variant the user picks, from those
  both skills built, sets the project's engine.
- Every Task that builds UI links the `DESIGN.md` sections, surface brief, and
  approved comp it builds against, and names its states, breakpoints, themes,
  and accessibility level. A brief that turns out to need a new world or a
  redesign is raised to a design Epic, and the user is told why. A UI Task that
  reaches delivery without the brief its depth needs goes back to a planner as a
  `needs-planning` follow-up.
- Only the user names references, chooses the engine and a direction, and
  approves a comp or a generated asset, or Orchi in autonomous mode. The session
  writing a brief answers the questions `PRODUCT.md`, `DESIGN.md`, or the Issues
  already settle itself; the rest go to the user.

## Engineering standards

- A new project has no setup Epic. Its first Epic or Task, standalone, is its
  first run, and its Issue says `First run of <product>.`: the thinnest slice
  the user can open that does the product's core action end to end on seeded
  data, through the real services the exploration's prototypes proved, on a
  plain screen when the design comes later. It scaffolds the stack and adds the
  core checks as the [standards](standards.md#new-project) say, and every
  Initiative, Epic, and Task that writes product code is blocked by it. A design
  Epic is not: its steps with the user start at once, and its builds wait for
  the first run, which its UI design field names as `Builds wait for first run
  #<m>`. For a project meant to last, also plan the
  [hardening](standards.md#hardening) Issue; later, the first Task to need a
  check that is not yet in `ENGINEERING.md` names adding it (its row, CI job,
  and configuration) in its requirements. An existing project without
  `ENGINEERING.md` gets a standards Epic, blocking nothing, only on request.
- Never ask the user to choose a tool, threshold, or code layout: the
  [standards defaults](standards.md) decide.
- State user-facing acceptance as what a user can see or do, and name the
  acceptance test for each criterion (in a proof of concept, what the running
  app shows instead).
- With `ENGINEERING.md`, take each Task's checks from its Checks table and plan
  within its Architecture rules. A Task that needs an exception names it with its
  reason, as [gate integrity](standards.md#gate-integrity) says.

## Tasks

Derive sequential Tasks from the design. Each owns one reviewable result and
carries its own context, requirements, solution vision, relevant decisions,
acceptance, verification, sources, and constraints, so that its owner does not
have to reconstruct them from the Epic. Order Tasks by
real dependencies; native child order or brief ordering text is enough.

Slice Tasks vertically: each is a narrow but complete path through the layers it
touches (data, logic, interface, tests, documentation) that can be verified on
its own, small enough for one owner to finish in one fresh context. Put the
refactoring that makes the change easy in its own first Task. Sequence a wide
mechanical change, such as a rename with many call sites, as expand, migrate in
batches, then contract, so that checks stay green after every Task.

## Agree the breakdown

Before creating Issues, show the user the plan in product terms: what they can
see or do after each piece, in delivery order. Ask whether that content and
order serve them, and revise until they agree; a list is cheaper to change than
Issues. The split into Tasks, Epics, and an Initiative and the blockers between
them are yours. When the breakdown is already known while the scope is
proposed, agree both in one question. In a pool's autonomous mode, Orchi agrees
them instead.

Check every Task against the [Task readiness checklist](readiness.md#task-readiness-checklist)
and every Epic against the [Epic readiness checklist](readiness.md#epic-readiness-checklist)
before anyone starts or delegates it; a project's own stricter checklist applies
in addition.

Design shared contracts before independent Epics depend on them. When a contract
is not implemented yet, make its producer Epic a native blocker instead of
assuming its output exists. Check coverage from Epic acceptance to Tasks, avoiding
both missing integration work and Tasks that merely restate template fields.

A documentation-only outcome needs no fake code Tasks. If the decomposition changes
within the agreed direction, update pending Tasks and links in place, preserving
completed history and explaining why.
