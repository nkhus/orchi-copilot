"""The plugin's Issue body forms are valid and give every readiness checklist item a field."""
import re

import pytest
import yaml

from conftest import ASSETS, REFERENCES, read

TEMPLATES = ASSETS / "issues"
READINESS = REFERENCES / "readiness.md"
FIELD_TYPES = {"markdown", "textarea", "input", "dropdown", "checkboxes"}

# Checklist item number -> (field id, phrases the field's label or description must contain).
TASK_FIELDS = {
    1: ("outcome", ("reviewable result",)),
    2: ("context", ("current behavior", "path:line", "consume")),
    3: ("prerequisites", ('"none"',)),
    4: ("outcome", ("native sub-issue",)),
    5: ("requirements", ("numbered requirements", "individually verifiable")),
    6: ("vision", ("routes, migrations, tables", "why this approach")),
    7: ("decisions", ("who decided", "quote the user's answers")),
    8: ("sources", ("inspected while planning",)),
    9: ("constraints", ("non-goals",)),
    10: ("scenarios", ("failure scenarios", "reproduction command")),
    11: ("acceptance", ("mapped to the requirements", "exact checks or commands", "seams where new tests go",
                        "what a user can see or do", "engineering.md")),
    12: ("docs", ("documentation routing",)),
    13: ("questions", ("affects this task's approach",)),
    14: ("ui", ("design depth", "surface brief", "approved comp", "breakpoints, themes")),
}
EPIC_FIELDS = {
    1: ("scope", ("out of scope",)),
    2: ("sources", ("requirement/decision ids", "parent initiative")),
    3: ("current", ("why this outcome is needed", "files, symbols, behavior")),
    4: ("requirements", ("numbered requirements", "traceable")),
    5: ("design", ("no architecture change", "why this approach", "test seams")),
    6: ("decisions", ("who decided", "quote the user's answers")),
    7: ("surfaces", ("documentation",)),
    8: ("failure", ("inputs and outputs, risks",)),
    9: ("branch", ("blocked-by",)),
    10: ("exit", ("mapped to requirements", "verification")),
    11: ("questions", ("affects the approach",)),
    12: ("branch", ("tasks in execution order as native sub-issues",)),
    13: ("ui", ("design depth", "surface brief", "what must stay", "blocked by")),
    14: ("branch", ("in a new project", "first run")),
}
INITIATIVE_FIELDS = {
    1: ("request", ("distinct from later decisions",)),
    2: ("outcome", ("exclusions",)),
    3: ("requirements", ("numbered requirements", "observable at completion")),
    4: ("decisions", ("who decided", "quote the user's answers")),
    5: ("epics", ("delivers each requirement", "dependency between epics")),
    6: ("completion", ("integration branch", "final verification")),
    7: ("plan", ("docs/work/",)),
}

def load(name):
    return yaml.safe_load(read(TEMPLATES / f"{name}.yml"))


def flat(text):
    """Collapse whitespace so rewrapped template prose still matches."""
    return " ".join(text.split())


def checklist(title):
    section = read(READINESS).split(f"## {title}\n", 1)[1].split("\n## ", 1)[0]
    return [int(number) for number in re.findall(r"^(\d+)\. ", section, flags=re.M)]


@pytest.mark.parametrize("name, label", [("task", "Task"), ("epic", "Epic"), ("initiative", "Initiative"),
                                         ("exploration", "Exploration")])
def test_templates_are_valid_issue_forms(name, label):
    form = load(name)
    assert form["name"] == label and form["description"]
    assert form["labels"] == ([] if label == "Exploration" else [label])
    ids = [item["id"] for item in form["body"] if item["type"] != "markdown"]
    assert len(ids) == len(set(ids))
    for item in form["body"]:
        assert item["type"] in FIELD_TYPES
        assert item["type"] == "markdown" or item["attributes"]["label"]
    text = read(TEMPLATES / f"{name}.yml")
    assert ".github/AGENTS.md" not in text and "docs/system" not in text
    assert "Work reference" not in text and "Assigned to" not in text


@pytest.mark.parametrize("name, title, mapping", [
    ("task", "Task readiness checklist", TASK_FIELDS),
    ("epic", "Epic readiness checklist", EPIC_FIELDS),
    ("initiative", "Initiative readiness checklist", INITIATIVE_FIELDS),
])
def test_every_readiness_item_has_a_template_field(name, title, mapping):
    assert checklist(title) == sorted(mapping), "update the mapping when the checklist changes"
    fields = {item["id"]: item for item in load(name)["body"] if item["type"] != "markdown"}
    for number, (field, phrases) in mapping.items():
        attributes = fields[field]["attributes"]
        text = flat(attributes["label"] + " " + attributes.get("description", "")).casefold()
        for phrase in phrases:
            assert phrase in text, f"{title} item {number} is not covered by field {field}: {phrase!r}"


# Initiative readiness items an exploration answers before planning -> (field, phrases).
EXPLORATION_FIELDS = {
    1: ("request", ("distinct from later decisions",)),
    2: ("constraints", ("exclusions",)),
    3: ("requirements", ("numbered requirements", "observable at completion")),
    4: ("decisions", ("who decided", "quote the user's answers")),
    5: ("shape", ("candidate epics", "dependency between epics")),
}


def test_exploration_form_answers_initiative_readiness_before_planning():
    assert set(EXPLORATION_FIELDS) <= set(checklist("Initiative readiness checklist"))
    fields = {item["id"]: item for item in load("exploration")["body"] if item["type"] != "markdown"}
    for number, (field, phrases) in EXPLORATION_FIELDS.items():
        attributes = fields[field]["attributes"]
        text = flat(attributes["label"] + " " + attributes.get("description", "")).casefold()
        for phrase in phrases:
            assert phrase in text, f"Initiative item {number} is not prepared by exploration field {field}: {phrase!r}"
    assert "Orchi gives this Issue to a planner crew" in flat(load("exploration")["body"][0]["attributes"]["value"])


def test_templates_point_to_the_readiness_reference():
    assert "Task readiness checklist in Orchi's readiness reference" in flat(load("task")["body"][0]["attributes"]["value"])
    intro = flat(load("epic")["body"][0]["attributes"]["value"])
    assert "Epic readiness checklist in Orchi's readiness reference" in intro and "Deferred until #<n>" in intro
    assert "Initiative readiness checklist in Orchi's readiness reference" in flat(
        load("initiative")["body"][0]["attributes"]["value"])


@pytest.mark.parametrize("name", ["task", "epic", "initiative"])
def test_templates_address_agent_owners(name):
    intro = flat(load(name)["body"][0]["attributes"]["value"])
    assert "agent owner" in intro and "planning conversation" in intro
