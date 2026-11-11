"""Delivery course corrections and verification verdicts agree across the skills, agents, and templates."""
from conftest import AGENTS, ASSETS, SKILLS, read

WRITERS = ("orchi-implementer", "orchi-fixer", "orchi-designer")


def prose(path):
    return " ".join(read(path).split())


def test_writers_are_continued_instead_of_restarted():
    deliver, roles = prose(SKILLS / "orchi-deliver/SKILL.md"), prose(SKILLS / "orchi-core/references/roles.md")
    assert "## Continue a writer" in read(SKILLS / "orchi-core/references/roles.md")
    assert "with `write_agent` to the `agent_id` its `task` call returned" in roles
    assert deliver.count("(../orchi-core/references/roles.md#continue-a-writer)") == 2
    assert "restart that writer" not in deliver and "restarting its writer" not in deliver
    for writer in WRITERS:
        text = prose(AGENTS / f"{writer}.agent.md")
        assert "When continued" in text and "the new work is one more commit" in text


def test_two_misses_change_course_and_initiatives_step_back():
    deliver, execution = prose(SKILLS / "orchi-deliver/SKILL.md"), prose(SKILLS / "orchi-core/references/execution.md")
    assert "do not send it a longer version of the same brief" in execution
    assert deliver.count("(../orchi-core/references/execution.md#change-course)") == 3
    assert "## Step back between Epics" in read(SKILLS / "orchi-core/references/review-delivery.md")
    assert "[step back](../orchi-core/references/review-delivery.md#step-back-between-epics), show the user what changed" in deliver
    assert "start the next only on their yes), then reclassify" in deliver


def test_declined_work_is_checked_before_proposing():
    planning = prose(SKILLS / "orchi-core/references/planning.md")
    assert "Issues closed as not planned" in planning and "A request parked for later is not declined." in planning
    for skill in ("orchi-plan", "orchi-explore"):
        assert "(../orchi-core/references/planning.md#declined-work)" in prose(SKILLS / f"{skill}/SKILL.md")


def test_verdicts_reach_the_pr_template():
    testing = prose(SKILLS / "orchi-core/references/testing.md")
    for verdict in ("Established", "Limited", "Not established"):
        assert f"**{verdict}:**" in testing
    assert "established, limited, or not established" in read(ASSETS / "github/pull_request_template.md")
    assert "[verdict](testing.md#verdicts)" in prose(SKILLS / "orchi-core/references/github.md")


def test_researcher_clones_only_outside_the_repository_and_never_runs_them():
    researcher = prose(AGENTS / "orchi-researcher.agent.md")
    assert "into a new directory under `.orchi-tmp/` in the worktree" in researcher
    assert "never run, build, or install anything from it" in researcher


def test_delivery_skills_use_copilot_host_mechanics():
    deliver, work = prose(SKILLS / "orchi-deliver/SKILL.md"), prose(SKILLS / "orchi-work/SKILL.md")
    assert "`task` tool, `agent_type` set to the agent's name" in deliver and "`send_session_message`" in deliver
    assert "`send_session_message`" in work and "never use `ask_user`" in work
    for text in (deliver, work):
        assert "$ARGUMENTS" not in text and "SendMessage" not in text and "dashboard" not in text.lower()
