"""Text, not behavior: the skills, agents, and references agree where a session follows one and not the other."""
import re

from conftest import AGENTS, SKILLS


def source(path):
    """A skill-relative path; upstream's role files are the plugin's custom agents and roles reference."""
    if path == "orchi-core/roles/README.md":
        return SKILLS / "orchi-core/references/roles.md"
    if path.startswith("orchi-core/roles/"):
        return AGENTS / (path.rsplit("/", 1)[1][:-3] + ".agent.md")
    return SKILLS / path


def prose(path):
    return " ".join(source(path).read_text().split())


def test_reviewer_role_carries_the_standards_and_context_checks():
    reviewer = prose("orchi-core/roles/orchi-reviewer.md")
    for phrase in ("`ENGINEERING.md`", "the gate integrity list", "the map still covers the changed code",
                   "`docs/work/`", "Exceptions:", "acceptance test that asserts it", "the working folder holds only the plan's `README.md`"):
        assert phrase in reviewer, phrase
    assert "Core documentation" not in reviewer


def test_delivery_steps_match_the_review_and_knowledge_references():
    deliver = prose("orchi-deliver/SKILL.md")
    assert "the review's Exceptions" in deliver and "every review finding with its resolution or `unresolved`" in deliver
    assert "run `knowledge.py lint`, plus `work` when the target is `main`" in deliver
    assert "move the rest of the working folder into current documentation except the plan's `README.md`" in deliver
    assert "Delete the working folder in its own commit" in deliver
    assert "Core" not in deliver.replace("orchi-core", "")
    assert "apply or replace the branch ruleset as the" in deliver and "without asking" in deliver
    assert "the delivering session (`orchi-deliver`) applies or replaces the ruleset and tells the user" in prose(
        "orchi-core/references/standards.md")


def test_orchi_picks_up_a_requested_plan_once_unblocked():
    assert "open `needs-planning` Issues that say `Requested by: Orchi` once their blockers are closed" in prose(
        "orchi/SKILL.md")
    assert "the weekly drift Issue, wait for the user" in prose("orchi-core/references/pool.md")


def test_an_exploration_with_several_items_hands_its_folder_to_the_first():
    assert "the folder goes to the item that carries the plan" in prose("orchi-core/references/knowledge.md")
    assert "by commit permalink" in prose("orchi-core/references/exploration.md")
    assert "the branch of the item that carries the plan" in prose("orchi-plan/SKILL.md")


def test_research_answers_reach_the_crew_in_full():
    assert "followed by the role's full report: checks, red evidence, or the answer with its sources" in prose("orchi-work/SKILL.md")
    assert "build a prototype yourself on `prototype/<slug>`" in prose("orchi-explore/SKILL.md")


def test_references_agree_on_branches_labels_pr_sections_and_readiness():
    github = prose("orchi-core/references/github.md")
    for phrase in ("`design` for an Epic a designer runs", "`explore/card-payments`", "`task/<slug>` from the Epic branch",
                   "`prototype/<slug>`, never merged", "**Exceptions:**", "documentation and standards check workflows"):
        assert phrase in github, phrase
    assert "branches that merge into the Epic branch" in prose("orchi-core/references/execution.md")
    assert "items 1–11, 13, and 14 of the Epic readiness checklist" in prose("orchi-design/SKILL.md")
    assert "reads its `SKILL.md` and follows it instead of starting it with the `skill` tool" in prose("orchi-core/roles/README.md")


def test_flows_do_not_stall_and_keep_user_only_questions():
    pool, entry, deliver = prose("orchi-core/references/pool.md"), prose("orchi/SKILL.md"), prose("orchi-deliver/SKILL.md")
    assert "for an Initiative Orchi checks that every native blocker is closed as completed" in pool
    assert "a `design` Epic has none yet" in prose("orchi-core/references/readiness.md")
    assert "and that Orchi takes it from here" in prose("orchi-plan/SKILL.md")
    assert "An Epic labelled `design` → report `#<n> declined: a design Epic goes to a designer crew`" in deliver
    assert "anything destructive or irreversible, removing or replacing something users can do or see today" in pool
    assert "and checks they asked to do by hand" in pool
    assert "Never ask a technical question" in pool
    assert "the review confirmed each exception it adds or changes" in pool
    assert "and whether its PR was merged (then send `#<n> merged`)" in entry
    assert "has been idle without a report is asked `<id> status?` once" in pool
    assert "`notify_on_idle: \"always\"`" in pool
    assert "the session it names has stopped" in deliver and "the session it names has stopped" in prose(
        "orchi-core/references/execution.md")
    assert "only `orchi-plan` closes the Exploration" in prose("orchi-standards/SKILL.md")
    assert "Orchi [prepares it](pool.md#prepare-the-repository) before any crew starts" in prose(
        "orchi-core/references/exploration.md")


def test_orchi_is_the_only_command_the_user_types():
    import yaml
    for skill in ("orchi-explore", "orchi-plan", "orchi-standards", "orchi-design", "orchi-deliver", "orchi-work"):
        text = (SKILLS / skill / "SKILL.md").read_text()
        meta = yaml.safe_load(text.split("---", 2)[1])
        assert meta["user-invocable"] is False, skill
        if skill != "orchi-work":
            assert "--report-to <Orchi session>" in meta["argument-hint"] and "[--report-to" not in meta["argument-hint"], skill
            assert "tell the user that work starts with `/orchi`, and stop" in prose(f"{skill}/SKILL.md"), skill
    for path in SKILLS.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".yml", ".py"}:
            assert not re.search(r"(?<![\w./-])/orchi-(explore|plan|standards|design|deliver|work)\b", path.read_text()), path
    assert "The user talks only to Orchi, their Orchi Copilot Project (or `/orchi`)" in prose("orchi-core/SKILL.md")


def test_the_user_answers_only_product_questions_and_nothing_waits_needlessly():
    core, planning = prose("orchi-core/SKILL.md"), prose("orchi-core/references/planning.md")
    assert "agents own everything technical" in core and "never the mechanism" in core
    assert "The split into Tasks, Epics, and an Initiative and the blockers between them are yours" in planning
    deliver = prose("orchi-deliver/SKILL.md")
    assert "Where CI runs the suite on the pushed commit, do not rerun it" in deliver
    assert "Without CI, the writer runs the checks its Task touches, and the full suites run once, at step 5" in deliver
    assert "create its Tasks yourself: the user agreed its outcome" in deliver
    assert "merge main into the Initiative branch first" in deliver
    assert "`#<n> waits for #<m>`" in prose("orchi-core/references/pool.md")
    assert "appends `, waits for #<m>` to its work reference" in prose("orchi-core/references/pool.md")
    assert "when it says `waits for #<m>` and #<m> has merged, send that crew `#<m> merged`" in prose("orchi/SKILL.md")
    assert "an unconfirmed one is a `blocker`" in prose("orchi-core/references/review-delivery.md")
    assert "report `#<n> waits for #<first run>`" in prose("orchi-design/SKILL.md")
    assert "for one outside the Initiative, report `#<n> waits for #<m>`" in deliver
    assert "make each Epic that builds on it blocked by it" in planning
    assert "confirmed: <yes, no change avoids it" in prose("orchi-core/roles/orchi-reviewer.md")
    assert "CI runs on every pull request, whatever its base" in prose("orchi-core/references/standards.md")
    assert "never which fix to use" in prose("orchi-core/references/execution.md")


def test_no_session_hands_the_user_a_command_and_orchi_merges_on_their_yes():
    assert "Never ask the user to run a command, open a terminal or GitHub, or edit a file" in prose("orchi-core/SKILL.md")
    orchi, pool = prose("orchi/SKILL.md"), prose("orchi-core/references/pool.md")
    assert "on their yes, confirm its checks pass and merge it yourself" in orchi
    assert "waits for their merge" not in orchi
    assert "the user merges into main" not in pool and "Orchi merges into main on the user's yes" in pool
    assert "`gh auth login` is theirs" not in pool and "they only sign in in their browser" in pool
    assert "the setup PR (Orchi merges it on their yes)" in pool
    assert "Orchi merges a PR to `main` on the user's yes" in prose("orchi-deliver/SKILL.md")
    for name in ("orchi", "orchi-deliver", "orchi-plan", "orchi-design", "orchi-explore", "orchi-standards"):
        text = prose(f"{name}/SKILL.md")
        assert not re.search(r"(?<![Nn]ever )(ask|tell) the user to (run|merge|commit|push|open a terminal)", text), name


def test_review_follows_risk_and_the_user_sees_what_changed():
    deliver, review = prose("orchi-deliver/SKILL.md"), prose("orchi-core/references/review-delivery.md")
    assert "A range that changes only tool configuration" in deliver
    assert "in a proof of concept, only blockers: list each `major` in the PR with the resolution `follow-up`" in deliver
    assert "In a proof of concept, a confirmed `major` is listed in the PR with the resolution `follow-up`" in review
    assert "in a proof of concept, evidence from the running app" in review
    assert "opening with what the user can now see or do" in deliver
    assert "append `, see it at <local link>`" in deliver
    assert "`#<n> PR ready: <url>[, see it at <local link>]`" in prose("orchi-core/references/pool.md")
    assert "what they can now see or do (its Summary) and the crew's `see it at` link" in prose("orchi/SKILL.md")


def test_review_findings_need_a_demonstrated_defect_and_the_recheck_is_final():
    review, reviewer = prose("orchi-core/references/review-delivery.md"), prose("orchi-core/roles/orchi-reviewer.md")
    assert "A `major` is a demonstrated defect that a user or the next change will hit" in review
    assert "A review that finds nothing is an expected result" in review
    assert "any regression the repair introduced; its verdict is final" in review
    assert "Finding nothing is a valid review" in reviewer
    assert "raise nothing new on code the repair did not change. Its verdict is final." in reviewer
    assert "with no source or test file and no exception, needs no reviewer" in prose("orchi-deliver/SKILL.md")


def test_the_first_run_is_findable_and_acceptance_waits_for_its_harness():
    planning = prose("orchi-core/references/planning.md")
    assert "its Issue says `First run of <product>.`" in planning and "`Builds wait for first run #<m>`" in planning
    assert "resume an open Issue that says `First run of`" in prose("orchi-plan/SKILL.md")
    for path in ("orchi-core/references/readiness.md", "orchi-core/roles/orchi-reviewer.md",
                 "orchi-core/references/review-delivery.md", "orchi-core/assets/github/ISSUE_TEMPLATE/orchi-task.yml"):
        assert "until the acceptance harness lands" in prose(path), path
    assert "planning adds an Issue labelled `needs-planning`" in prose("orchi-core/references/standards.md")
    deliver = prose("orchi-deliver/SKILL.md")
    assert "from a detached checkout of the PR head" in deliver and "stop it on `#<n> rework`" in deliver
    assert "answer it before its `done` with `#<task> answer`" in deliver
