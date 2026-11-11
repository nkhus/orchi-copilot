# Review and deliver the assembled result

Use once Tasks are implemented and verification evidence exists. Read the actual
diff, acceptance and design, affected documentation, and check results tied to the
candidate commit. Missing checks go back to the implementer; review consumes
existing evidence and does not launch another test campaign.

## Documentation impact

Every PR needs a filled `Documentation impact` section in its body: either the
owning pages updated, or a short reason why no documentation changes. A missing,
empty, or placeholder section is a blocker. Check that the listed pages actually
describe the changed behavior and that `knowledge.py lint` passes on the
candidate. Check against the map in `docs/README.md` that every page owning
changed code changed or has a reason in the section, that the map still covers
the changed code, and that each behavior page names acceptance tests that
exist, run, and assert their criteria. A PR into main carries no working
documents: `knowledge.py work` must pass
([move into current documentation](knowledge.md#move-into-current-documentation)).

## Review

Perform one full Epic review, independently when a reviewer is available; if not,
disclose that limitation rather than claiming independent review. Assess
correctness, requirement coverage, shared contracts, failure behavior, attributable
regressions, and agreement between code and documentation. Report actual coverage
and limitations; do not infer a clean result from the author's summary.

When the range changes a user interface, start `orchi-designer` in Audit mode on
it beside the reviewer: against the Issues' design requirements, `DESIGN.md`,
the surface briefs and approved comps, and accessibility, with Hallmark's
`audit` and `sloplint` in a Hallmark project. Treat its confirmed findings like
review findings; a finding without a requirement, a design-system rule, or an
accessibility standard behind it is taste, not a defect.

Keep three axes apart, so that a pass on one cannot hide a failure on another:
**Spec** (the Issues' requirements, acceptance, and scenarios, including scope
creep: behavior no requirement asks for), **Standards** (the repository's rules
and documentation, and `ENGINEERING.md` where it exists), and **Tests** (per [testing](testing.md#review-the-tests)).
A new or changed test without red evidence or a stated reason goes back to its
writer like any other missing check. Remove scope creep, or agree it with the
user and record the decision; never accept it silently.

Where `ENGINEERING.md` exists, nobody reads the code but its checks and this
review ([standards](standards.md#premise)). Its blocking checks must pass on the
candidate, and the range must not weaken a gate as
[gate integrity](standards.md#gate-integrity) lists: check the diff of
`ENGINEERING.md`, the workflows, tool configurations, package scripts, and tests
for it yourself; either is a blocker. Each user-facing acceptance criterion needs an acceptance
test that asserts it (until the acceptance harness lands, and in a proof of
concept, evidence from the running app: the boot command and what it showed), and the PR's Verification section gives the evidence per
criterion: the test, and for a visible change a screenshot, a recording, or a
preview link. A writer that needs an exception reports it; record it in
`ENGINEERING.md` only when no change avoids it, and list every exception the PR
adds or changes in its Exceptions section in plain words: what is waived, where,
why, and until when, each with its `confirmed:` verdict; an unconfirmed one is a
`blocker`. The session that talks to the user relays them as information.

A blocker states the violated criterion, concrete causal path, consequence, and
evidence. A `major` is a demonstrated defect that a user or the next change will
hit, with its scenario and the requirement or rule it breaks; a finding without
both is `minor` or `advisory`, listed and never repaired. A review that finds
nothing is an expected result: never raise a severity to have something to
report. Deduplicate root causes. Advisory style, speculative concerns, and
unrelated existing defects do not become required repair Tasks. In a proof of
concept, a confirmed `major` is listed in the PR with the resolution `follow-up`,
with no Issue, not repaired. Repair supported
blockers, rerun affected checks, and do one targeted follow-up over the repaired
findings and any regression the repair introduced; its verdict is final. If blockers remain, report them and the next
action; never reset review rounds or declare success to exhaust a budget.

## Integrate

Check the PR target explicitly. If it moved after verification, resolve conflicts,
inspect compatibility, and rerun affected checks. Where no CI runs the suites,
run the full applicable suites once per PR, on the head that will merge: after
the review's repairs and the last update from the target. Before that, and after
a later small change, run only the checks the change touches; a full rerun is
for a change that reaches shared code or a merge that brought conflicts. Serialize merges into a shared
target, rechecking when another Epic has landed since validation. Squash the Epic
PR into its Initiative branch, or into main for a standalone Epic.

Before an Epic merges into its Initiative branch, move what it settled from the
working folder into the current documentation, as the knowledge reference says.
Confirm the merge, confirm its Tasks are completed, then close the Epic. A closed issue alone does not prove merged implementation. Closing
keywords only work for the default branch; close issues explicitly after merging
into an Initiative branch. Branch dependent Epics from the updated integration
branch.

At final Initiative integration, reconcile with current main, including code and
current documentation, move the rest of the working folder there and delete it,
and check agreed requirement coverage. Run the full applicable
suite on the combined candidate. Review cross-Epic integration and reconciliation,
reusing completed Epic reviews instead of restarting them. Revalidate any repair.
Squash the final PR into main within the user's publication authority, confirm the
merge, then close the Initiative. A small fix uses one proportional review and its
relevant checks.

Report the delivered scope, PR and merge reference, checks with each acceptance
claim's [verdict](testing.md#verdicts), and material limitations. If publication is pending, say so: local verification is not a
remote merge, and merging is not deployment.

## Step back between Epics

Each time an Epic merges into its Initiative branch, look at the combined result:
run it, or read it as its user would. When the Epic changes what users see, show
it to the user as the pool reference's
[Autonomous mode](pool.md#autonomous-mode) says; after the first such Epic, the
next starts only on their yes. Check whether the remaining Epics still
fit what it shows (their outcomes, dependencies, and deferred fields), whether
modules the Epic touched grew too large or lost clear boundaries, and whether
checks became slow enough to hold up later Epics. Re-plan what it shows as
[change course](execution.md#change-course) says: record changes to Epics not
yet started in the Initiative plan, make a restructuring or speed-up the first
Task of the next affected Epic, and add a Task to an Epic already in flight
instead of pausing it.

## Lessons

After delivery, turn what went wrong into changes to the environment rather
than into more instructions. Collect the events this delivery produced: `NOT
READY` and `ESCALATE` reports, review blockers and context gaps, repair rounds,
checks that failed late, held messages, and corrections the user made.

For an event that could recur, propose one change on the first rung that fits:

1. A deterministic check (test, lint rule, CI job, or hook) for a mechanical
   mistake.
2. A field or item in the repository's Issue forms or stricter readiness
   checklist, for context an Issue lacked.
3. A rule in the coding standards the reviewer reads, for a judgement call.
4. A pointer in `AGENTS.md` or a scoped instruction file, for something an
   agent could not find.
5. An Issue in the Orchi repository, for a defect in Orchi itself.

Propose removing an instruction that changed nothing, too. Before proposing,
search closed Issues titled `Lesson:` for the same failure. Each lesson names
its event (an Issue, PR, or finding link) and its rung; without an observed
event it is not a lesson. Report at most three, most costly first, and post
them as a `Lessons` comment on the delivered Issue. Only propose: never change
instructions, checklists, or checks on your own. The session that ran the
delivery, or Orchi in a session pool, files each lesson the user accepts as an
Issue titled `Lesson: <what failed>`, without a label or a plan, which planning
takes like any request; a rung 5 lesson goes to the Orchi repository instead,
and only with the user's agreement. When a failure recurs after its `Lesson:`
Issue closed, say so: that change did not work, and the next one belongs on a
more deterministic rung.
