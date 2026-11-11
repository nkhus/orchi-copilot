# Test and diagnose

Use when planning, writing, or reviewing tests, and when a Task fixes a defect.
The repository's own testing rules and commands take precedence.

## Seams

A seam is the public interface where a test observes behavior without reaching
inside: a module's entry points, a route, a command, a rendered screen. Prefer
the highest existing seam that reaches the behavior; add a seam only when no
existing one can observe it. When planning names the seams, test there.

## Good tests

- Assert observable behavior through the seam, so the test survives a refactor
  that keeps the behavior.
- Take expected values from an independent source: a literal, a worked example,
  or the requirement, never a recomputation the way the code computes them.
- Mock only system boundaries: third-party services, time, randomness, and the
  network, database, or file system when no local stand-in exists. Run the
  project's own modules for real.
- Build one behavior at a time: a failing test, the smallest change that makes
  it pass, then the next behavior.

A test is suspect when it mocks the project's own modules, asserts calls or
their order on internal collaborators, verifies through a side channel (reading
the database instead of reading back through the interface), or would still
pass with the change reverted.

## Red evidence

A new or changed test proves something only if it fails without the change. Run
it before the change, or against the base commit, and record the command and the
failure it showed:

`Red: <command> -> <failing assertion or symptom>`

When no test can fail first (a refactor that keeps behavior, configuration,
documentation), record the reason instead. If you forced a failure by breaking
code or a fixture, check with `git diff` that the change reached the tested path,
and restore it before committing.

## Observation aids

When no seam or check can observe a claimed behavior directly, because it
happens in a background job, an external service, a timing window, or a state
no test can set up, add the smallest aid that makes it observable and
repeatable: a fixture or seed, a test-only hook, a command that prints the
state, or tagged logging. Decide before building it whether it is temporary
(removed before committing, like debug logging) or durable (kept, tested, and
documented). A durable aid that adds a dependency, a public interface, or
production behavior is a design decision for the Issue, not the writer's.

## Verdicts

Report each acceptance claim with the evidence behind it and one verdict:

- **Established:** a check ran on the candidate commit and passed, with red
  evidence that it fails without the change, or the recorded reason why none
  can (see Red evidence).
- **Limited:** the evidence covers part of the claim; name the gap, such as a
  stubbed provider, an unrendered screen, or an untested platform.
- **Not established:** no check covers it, or a check failed.

Only an established claim counts as verified. A limited or not established
claim is reported as such, never rounded up.

A claim about real use is established only on the real path: the product's own
entry point, with the real services, models, and data it will meet, or a copy of
them. Tests on fixtures, stubs, or prepared input establish the code's logic,
not the claim. A claim that something works without a person, or on a new site,
file, or customer, also needs a run on new input nobody prepared or tuned for.
A PR into main whose main outcome is not established this way merges only on
the user's yes to the named gap ([pool](pool.md#autonomous-mode)).

## Defects

A defect Task starts from a reproduction: one command that has already failed on
the reported symptom, gives the same result on every run, finishes in seconds,
and runs without a person. Planning records it in the Task's scenarios, or states
why none exists and which evidence replaces it.

1. Run the reproduction and confirm that it shows the reported symptom, not a
   nearby failure.
2. Shrink it until every remaining input, step, and setting is needed for the
   failure.
3. Write three to five ranked hypotheses, each with a prediction that would
   prove it wrong.
4. Test one prediction at a time. Tag temporary logging with a unique prefix,
   such as `[DEBUG-a4f2]`, so one search removes it. For a performance
   regression, measure a baseline before changing anything.
5. Turn the minimal reproduction into a regression test at a seam that runs the
   real failure path: red, fix, green, then rerun the original reproduction. If
   no seam reaches that path, report it as a finding instead of adding a shallow
   test.
6. Remove temporary logging and harnesses, and state the confirmed cause in the
   commit and the PR.

## Review the tests

For each changed behavior, check that tests exist at the planned seams, assert
behavior rather than implementation, and have red evidence or a stated reason,
and that each defect fix has a regression test or a reported missing seam. A
suspect test is a defect when it leaves a requirement unverified; otherwise it
is advisory.
