# Find, take, execute, and hand off

## Ownership

An open Issue is taken when it has an assignee, a linked branch, or an open PR
that closes it; otherwise nobody holds it. Work a person or another assistant
took counts the same as the pool's. Closed Issues are completed or cancelled;
the close reason distinguishes them. The owner is the assignee; the branch, and
the PR once it exists, are the work record. Write no claim line in the body.

Only ready Epics and standalone Tasks are independent entry points. A Task under
an Epic belongs to the Epic owner. Assign an Initiative while its planning or
Epics are active; that does not block taking its Epics independently.

## Find ready work

Run `python3 <orchi-core>/scripts/status.py` for an overview, where `<orchi-core>` is
the orchi-core skill's base directory. It reports
each open Epic and standalone Task as:

- `ready`: nobody holds it, it is planned (sub-issues, or a `Requirements`
  section listing `R1`), and every native blocker is closed as completed with a
  merged PR;
- `check`: as `ready`, but a blocker closed as completed without a linked merged
  PR, so confirm its result reached the integration branch before starting;
- `blocked`: a blocker is open or was cancelled (a cancelled predecessor does not
  satisfy a dependency);
- `unplanned`: nobody holds it and it has no plan yet;
- `taken`: it has an assignee, a linked branch, or an open closing PR; it is
  yours only when you are the assignee and the branch or PR is the one your
  assignment names.

The report is a snapshot of GitHub, not a lock. Confirm that required predecessor
results are merged into this Epic's intended integration branch.

## Take

Take work by assigning yourself (`gh issue edit <n> --add-assignee @me`) and
pushing its branch, then re-read the Issue before editing. Assignment is not an
atomic lock: if another assignee, branch, or PR appears, resolve ownership
before either continues. There is no scheduler or central unlock. Use native
Epic dependencies for real ordering constraints; if parallel Epics share a
changing contract, add the dependency before concurrent edits. Worktrees
separate workspaces; they are not a security boundary.

## Execute

Read the Epic issue, design, Tasks in order, branch and PR, dependency results,
and scoped instructions. Check that the actual branch matches the issue.

Implement Tasks in sequence on the Epic branch; Tasks have no PR of their own. A
pool dev lead's Tasks on different files run in parallel on `task/<slug>`
branches that merge into the Epic branch ([pool](pool.md#writers)). Assign yourself to the current Task. Update code, tests, and owning
documentation together, writing tests per [testing](testing.md). Run the checks
that establish the Task's acceptance and record the result, the red evidence,
and the commit in the shared PR. A failing check is unresolved
work; an unavailable environment is a verification limitation, not evidence of
success or of a product defect.

Close an Epic Task once its result is implemented and
verified on the Epic branch, recording the commit. Close a standalone Task only
after its PR merges to main. Reopen a Task whose result is invalidated before
integration; keep its earlier evidence.

If new information changes shared contracts, coordinate with affected Epic owners
and update dependencies before conflicting edits. Escalate material direction
changes to the user. Keep pre-existing changes separate from this result. Keep
research prototypes labelled as prototypes until deliberately adopted and verified.

## Change course

When a writer misses the same Task twice — two reports that are not `DONE` for
the same cause, or two `DONE` results that fail the same acceptance — do not
send it a longer version of the same brief. Change the boundary instead: settle
the missing decision or context in the Issue, split the Task, give it to the
writer that fits, or do it yourself; if none fits, ask the user what to drop,
reduce, or wait for, never which fix to use. A second `NOT READY` already means
asking the user.

Re-plan when work outgrows its plan: an Epic keeps gaining Tasks or repair
rounds it did not plan, or a Task's change spreads well beyond the areas its
Issue names. Within the agreed outcome, update the pending Tasks or
Epics and record why; a change of outcome or scope goes to the user.

## Hand off and resume

When interrupted or handing over, update the `Handoff` section of the PR body
(create the PR as a draft if needed) with exactly these fields:

```md
## Handoff
- Branch / commit: <branch> @ <sha>
- Done: <Tasks and results completed>
- Remaining: <next Tasks or open work>
- Uncommitted or local-only changes: <none, or where they are>
- Checks: <commands run and results; known limitations>
- Next step: <one concrete action>
```

Push local-only changes before releasing ownership; a worktree path on one machine
is not available on another. Confirm the former writer has stopped, and remove
ownership only on explicit release or agreed transfer.

To resume, read the Handoff section first, then verify the current diff and target
before continuing, and clear the section. A rerun after an interruption runs in a
new session: the work is still yours when you are its assignee and its branch
and PR are the ones your assignment names. Do not restart planning, recreate Tasks, or discard a
candidate. If a GitHub failure left bookkeeping incomplete, report and reconcile
it. Do not take shared work whose ownership cannot be established.
