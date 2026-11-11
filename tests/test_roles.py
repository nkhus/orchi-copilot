"""Role custom agents: documented frontmatter, agreed models and tools, and the nesting rules."""
import yaml

from conftest import AGENTS, REFERENCES, read

FRONTMATTER_KEYS = {"name", "description", "target", "tools", "model", "disable-model-invocation", "user-invocable",
                    "mcp-servers", "metadata"}
EXPECTED = {
    "orchi-scout": ("claude-haiku-5.5", ["read", "search", "execute", "agent", "skill"]),
    "orchi-researcher": ("claude-opus-5.5", ["read", "search", "execute", "web", "agent", "skill"]),
    "orchi-implementer": ("claude-opus-5.5", ["read", "edit", "search", "execute", "agent", "skill"]),
    "orchi-fixer": ("claude-sonnet-5.5", ["read", "edit", "search", "execute", "agent", "skill"]),
    "orchi-reviewer": ("claude-opus-5.5", ["read", "search", "execute", "agent", "skill"]),
    "orchi-designer": ("claude-opus-5.5", ["read", "edit", "search", "execute", "agent", "skill"]),
}
READ_ONLY = ("orchi-scout", "orchi-researcher", "orchi-reviewer")


def load(name):
    _, front, body = read(AGENTS / f"{name}.agent.md").split("---", 2)
    return yaml.safe_load(front), body


def prose(text):
    return " ".join(text.split())


def test_every_role_is_an_agent_with_documented_frontmatter():
    assert sorted(path.name for path in AGENTS.glob("*.agent.md")) == sorted(f"{name}.agent.md" for name in EXPECTED)
    for name, (model, tools) in EXPECTED.items():
        assert read(AGENTS / f"{name}.agent.md").startswith("---\n")
        meta, body = load(name)
        assert set(meta) <= FRONTMATTER_KEYS, name
        assert meta["name"] == name
        assert meta["description"].strip()
        assert (meta["model"], meta["tools"]) == (model, tools)
        assert body.strip() and len(body) <= 30_000, name


def test_read_only_roles_cannot_edit():
    for name in READ_ONLY:
        assert "edit" not in load(name)[0]["tools"], name
    for name in set(EXPECTED) - set(READ_ONLY):
        assert "edit" in load(name)[0]["tools"], name
    assert "web" in load("orchi-researcher")[0]["tools"]


def test_roles_nest_only_read_only_agents_and_stay_host_neutral():
    for name in EXPECTED:
        body = load(name)[1]
        text = prose(body)
        assert "## Nested agents" in body
        assert "The main session alone starts `orchi-implementer`, `orchi-fixer`, and `orchi-designer`." in text
        assert "Only `orchi-implementer`, `orchi-fixer`, and `orchi-designer` edit files or commit." in text
        assert "spawn" not in body.lower()
        assert "{{" not in body and ".claude" not in body and "CLAUDE.md" not in body
        assert "orchi-core skill" in text, name


def test_designer_builds_with_the_project_engine_and_never_asks_the_user():
    meta, body = load("orchi-designer")
    text = prose(body)
    assert "a project designs with the one its `DESIGN.md` names" in text and "SmoothUI" in text
    assert "`/hallmark <prompt>`" in text and "read its `SKILL.md` and `PICKER.md` and follow them yourself" in text
    assert "Impeccable" not in text and "Taste Skill" not in text
    assert "Never install, update, or configure a design skill yourself" in text
    assert "never use the question tool" in text and "return `ESCALATE` (`decision`)" in text
    assert "Never pick references, an engine, or a direction, and never write `PRODUCT.md` or `DESIGN.md`" in text
    for mode in ("## Variant mode", "## Task mode", "## Audit mode"):
        assert mode in body
    roles = prose(read(REFERENCES / "roles.md"))
    assert "Taste" not in roles and "Impeccable" not in roles
    assert "[Hallmark](https://github.com/Nutlope/hallmark)" in roles and "[prototype](https://github.com/emilkowalski/skills)" in roles
