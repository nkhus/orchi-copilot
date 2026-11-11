"""setup.py prepares a repository idempotently and never overwrites what someone else wrote."""
import importlib.util
import json
import subprocess
import sys

import pytest

from conftest import ASSETS, SCRIPTS, git, tree

spec = importlib.util.spec_from_file_location("orchi_setup", SCRIPTS / "setup.py")
setup = sys.modules["orchi_setup"] = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    git("init", "-q", "-b", "main", cwd=root)
    (root / "README.md").write_text("# Project\n")
    return root


def run(root, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / "setup.py"), "--project", str(root), "--no-labels", *args],
                          capture_output=True, text=True)


def snapshot(root):
    return {path: text for path, text in tree(root).items() if not path.startswith(".git/")}


def test_dry_run_lists_the_changes_and_writes_nothing(repo):
    before = snapshot(repo)
    result = run(repo, "--dry-run")
    assert result.returncode == 0, result.stderr
    for line in ("Would create .github/ISSUE_TEMPLATE/orchi-epic.yml", "Would create .github/workflows/orchi-docs.yml",
                 "Would create .github/orchi/scripts/knowledge.py", "Would create AGENTS.md",
                 "Would create .github/pull_request_template.md", "Would create .gitignore",
                 "Would create .github/copilot/settings.json", "Would create .github/github-app.yml",
                 "Would create .github/orchi/manifest.json"):
        assert line in result.stdout
    assert snapshot(repo) == before


def test_second_run_changes_nothing(repo):
    first = run(repo)
    assert first.returncode == 0, first.stderr
    after_first = snapshot(repo)
    second = run(repo)
    assert second.returncode == 0, second.stderr
    assert second.stdout.strip() == "Nothing to change."
    assert snapshot(repo) == after_first
    assert run(repo, "--check").returncode == 0


def test_installed_files_match_the_plugin(repo):
    run(repo)
    for name in setup.ISSUE_FORMS:
        assert (repo / ".github/ISSUE_TEMPLATE" / name).read_bytes() == (ASSETS / "github/ISSUE_TEMPLATE" / name).read_bytes()
    for script in ("knowledge.py", "standards.py"):
        assert (repo / ".github/orchi/scripts" / script).read_bytes() == (SCRIPTS / script).read_bytes()
    workflows = (repo / ".github/workflows/orchi-docs.yml").read_text() + (repo / ".github/workflows/orchi-standards.yml").read_text()
    assert ".github/orchi/scripts/knowledge.py" in workflows and ".github/orchi/scripts/standards.py" in workflows
    settings = json.loads((repo / ".github/copilot/settings.json").read_text())
    assert settings == {"extraKnownMarketplaces": {"orchi-copilot": {"source": {"source": "github", "repo": "nkhus/orchi-copilot"}}},
                        "enabledPlugins": {"orchi@orchi-copilot": True}}
    assert ".orchi-tmp/" in (repo / ".gitignore").read_text()
    assert "## Summary" in (repo / ".github/pull_request_template.md").read_text()
    assert git("check-ignore", "-q", ".orchi-tmp/x", cwd=repo) == ""


def test_existing_files_keep_their_content(repo):
    (repo / "AGENTS.md").write_text("# Agents\n\nUse tabs.\n")
    (repo / ".gitignore").write_text("node_modules/")
    (repo / ".github").mkdir()
    (repo / ".github/PULL_REQUEST_TEMPLATE.md").write_text("## Checklist\n")
    run(repo)
    agents = (repo / "AGENTS.md").read_text()
    assert agents.startswith("# Agents\n\nUse tabs.\n\n<!-- orchi:begin -->\n## Orchi workflow")
    assert (repo / ".gitignore").read_text().startswith("node_modules/\n\n# orchi:begin\n")
    assert (repo / ".github/PULL_REQUEST_TEMPLATE.md").read_text().startswith("## Checklist\n\n<!-- orchi:begin -->")
    assert "pull_request_template.md" not in [p.name for p in (repo / ".github").iterdir()]
    assert run(repo).stdout.strip() == "Nothing to change."


def test_edited_section_is_refused_until_replace(repo):
    run(repo)
    agents = repo / "AGENTS.md"
    agents.write_text(agents.read_text().replace("Research first", "Research always"))
    edited = snapshot(repo)
    result = run(repo)
    assert result.returncode == 1
    assert "the Orchi section of AGENTS.md was edited" in result.stderr
    assert snapshot(repo) == edited
    assert run(repo, "--replace").returncode == 0
    assert "Research always" not in agents.read_text()


def test_edited_managed_file_and_foreign_file_are_refused(repo):
    run(repo)
    form = repo / ".github/ISSUE_TEMPLATE/orchi-task.yml"
    form.write_text(form.read_text() + "# local change\n")
    result = run(repo)
    assert result.returncode == 1 and "orchi-task.yml was edited after Orchi wrote it" in result.stderr

    other = repo.parent / "other"
    other.mkdir()
    git("init", "-q", cwd=other)
    (other / ".github/workflows").mkdir(parents=True)
    (other / ".github/workflows/orchi-docs.yml").write_text("name: mine\n")
    result = run(other)
    assert result.returncode == 1 and "orchi-docs.yml exists and is not Orchi's" in result.stderr
    assert sorted(p.name for p in (other / ".github").iterdir()) == ["workflows"]


def test_settings_are_merged_and_a_disabled_plugin_stays_disabled(repo):
    (repo / ".github/copilot").mkdir(parents=True)
    (repo / ".github/copilot/settings.json").write_text(json.dumps({"enabledPlugins": {"orchi@orchi-copilot": False, "x@y": True},
                                                                     "other": 1}))
    result = run(repo)
    settings = json.loads((repo / ".github/copilot/settings.json").read_text())
    assert settings["enabledPlugins"] == {"orchi@orchi-copilot": False, "x@y": True}
    assert settings["other"] == 1 and "orchi-copilot" in settings["extraKnownMarketplaces"]
    assert "disables orchi@orchi-copilot" in result.stdout


def test_existing_app_configuration_is_left_alone(repo):
    (repo / ".github").mkdir()
    (repo / ".github/github-app.yml").write_text("instructions: Use bun.\n")
    result = run(repo)
    assert result.returncode == 0
    assert (repo / ".github/github-app.yml").read_text() == "instructions: Use bun.\n"
    assert "github-app.yml exists and is not Orchi's" in result.stdout


def test_workflow_opt_out_removes_and_persists(repo):
    run(repo)
    result = run(repo, "--no-docs-workflow")
    assert "remove .github/workflows/orchi-docs.yml" in result.stdout.lower()
    assert not (repo / ".github/workflows/orchi-docs.yml").exists()
    assert not (repo / ".github/orchi/scripts/knowledge.py").exists()
    assert (repo / ".github/workflows/orchi-standards.yml").exists()
    assert run(repo).stdout.strip() == "Nothing to change."
    run(repo, "--docs-workflow")
    assert (repo / ".github/workflows/orchi-docs.yml").exists()


def test_check_exits_nonzero_when_changes_are_pending(repo):
    assert run(repo, "--check").returncode == 1
    assert snapshot(repo) == {"README.md": "# Project\n"}


def test_labels_are_created_only_when_missing(repo, monkeypatch):
    calls = []

    def fake_gh(*args, cwd):
        calls.append(args)
        return json.dumps([{"name": "Epic"}, {"name": "design"}]) if args[:2] == ("label", "list") else ""
    monkeypatch.setattr(setup, "gh", fake_gh)
    plan = setup.build(repo)
    setup.apply(plan)
    created = [args[2] for args in calls if args[:2] == ("label", "create")]
    assert created == [name for name in setup.LABELS if name not in ("Epic", "design")]
    assert {"Exploration", "needs-planning", "delivery-ready", "design"} <= set(setup.LABELS)


def test_unavailable_github_is_reported_not_fatal(repo, monkeypatch):
    def failing_gh(*args, cwd):
        raise subprocess.CalledProcessError(1, "gh", stderr="gh: not logged in")
    monkeypatch.setattr(setup, "gh", failing_gh)
    plan = setup.build(repo)
    assert any("labels not checked" in note and "not logged in" in note for note in plan.notes)
    assert not plan.labels


def test_symlinked_destination_is_refused(repo, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / ".github").symlink_to(outside)
    result = run(repo)
    assert result.returncode == 1 and "symlink" in result.stderr
    assert list(outside.iterdir()) == []
