# Readiness checklists

Use before starting or delegating a Task, Epic, or Initiative, and when planning
creates them. The Issue is the specification for an owner who never saw the
planning conversation. A project's own stricter checklist, if its instructions define one,
applies in addition to these.

## Task readiness checklist

A Task is ready only when its body, together with the linked sources, answers
every applicable item below without relying on chat history. Each item is a
presence check that can be answered yes or no. A Task that fails any item is not
ready: do not start or delegate it. Record what is missing and fix the Issue
first. Items marked "when applicable" may be answered "not applicable" for a
standalone small fix.

1. States one concrete, reviewable outcome.
2. Gives context: why the result is needed, where it fits in the product or
   system, the relevant current behavior with code evidence (files and symbols,
   or `path:line`), and the output that later work or users consume.
3. Lists prerequisites, with Task/Epic references, or states "None".
4. Names the parent Epic as a native sub-issue (when applicable).
5. Lists numbered requirements (R1, R2, ...), each individually verifiable,
   citing the stable requirement IDs they implement when the project has them.
6. Describes the solution vision: the intended approach, the likely change
   points as concrete symbols, routes, migrations, tables, or file paths, and
   why this approach was chosen over the alternatives considered.
7. Records the decisions that shape the Task — each with its question, answer,
   who decided, date, and reason, quoting the user's answers faithfully — or
   states that none were needed.
8. Links the exact design sections, requirement/decision IDs, or documents it
   implements (when applicable), and the code or issues inspected while planning.
9. States constraints and non-goals.
10. Describes at least one success scenario and at least one failure scenario,
    each with expected behavior, or states explicitly why no failure case exists.
    A defect's failure scenario gives a reproduction command that has already
    failed on the reported symptom, or states why none exists and which
    evidence replaces it ([testing](testing.md#defects)).
11. Gives observable acceptance mapped to the requirements, and the exact checks
    or commands that verify it, naming the seams where new tests go (when
    applicable). User-facing behavior is stated as what a user can see or do,
    each with the acceptance test that checks it (until the acceptance harness
    lands, and in a proof of concept, what the running app shows); in a project with
    `ENGINEERING.md`, the checks it runs come from there.
12. States its documentation impact: the owning pages named by the project's
    documentation routing (the ownership map in `docs/README.md`, by default),
    including a behavior page for a change a user can see, or why none change.
13. Lists no open question in the Task or its parent Epic that is marked as
    affecting this Task's approach; resolve such a question, or move it to a
    bounded investigation Task, first.
14. For a Task that changes a user interface, states its
    [design depth](planning.md#user-interface-design) and links the `DESIGN.md`
    sections it follows; at depth brief or Epic, also the surface brief and, when
    a direction round chose one, the approved comp; and names
    the states, breakpoints, themes, and accessibility level it covers (when
    applicable).

## Epic readiness checklist

An Epic is ready for delivery only when every item below holds. A future Epic in
an Initiative may answer a field with `Deferred until #<n>: <reason>` only for a
decision that depends on that predecessor's result; it is not ready for delivery
until the deferral is resolved.

1. States one bounded outcome, with in-scope and out-of-scope lists.
2. Links its sources (exact sections, requirement/decision IDs), and names its
   parent Initiative when applicable.
3. Gives context and describes current state with evidence: files, symbols, or
   behavior.
4. Lists numbered requirements (R1, R2, ...) the Epic delivers, each traceable
   to a source or a recorded decision.
5. Contains a design, or a link to one, covering approach, interfaces and
   boundaries, invariants, test seams, and tradeoffs, and why this approach was
   chosen over the alternatives considered; or states "no architecture change".
6. Records the decisions that shape the Epic — each with its question, answer,
   who decided, date, and reason, quoting the user's answers faithfully.
7. Names affected code, schema, contract, test, and documentation surfaces.
8. Describes success and failure scenarios, inputs and outputs, risks, and
   expected recovery.
9. Names its branch and PR target, and has native blocked-by relationships for
   every direct dependency.
10. Gives exit criteria mapped to requirements, each with its verification.
11. Has every blocker merged into the target branch, and contains no
    `Deferred until` answer and no open question marked as affecting the
    approach.
12. Has native sub-issue Tasks in execution order, each passing the Task
    readiness checklist; a `design` Epic has none yet, because its designer
    plans the builds after the user approves each comp.
13. For an Epic that changes a user interface, states its
    [design depth](planning.md#user-interface-design): at depth brief, links the
    surface brief; at depth Epic, is itself the `design` Epic, naming the surfaces
    it designs and what must stay, or is blocked by the design Epic it builds on
    (when applicable).
14. While the project's [first run](planning.md#engineering-standards) is
    open, is blocked by it, or is that first run; a `design` Epic is not (when
    applicable).

## Initiative readiness checklist

An Initiative is ready for its first Epic only when its Issue and plan document
together answer every item below.

1. Keeps the original request, as agreed with the requester, distinct from later
   decisions.
2. States the agreed outcome and explicit exclusions.
3. Lists numbered requirements (R1, R2, ...), each observable at completion.
4. Records the decisions that shape the Initiative — each with its question,
   answer, who decided, date, and reason, quoting the user's answers faithfully.
5. Maps every requirement to the Epic that delivers it, and explains each
   dependency between Epics through the result or contract it supplies.
6. Names the integration branch and the completion criteria, including the final
   verification on the combined candidate.
7. Links the plan document on the integration branch.
