"""setup.py prepares a repository idempotently, writes only neutral files, and migrates an earlier setup."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import ASSETS, SCRIPTS, git, tree

spec = importlib.util.spec_from_file_location("orchi_setup", SCRIPTS / "setup.py")
setup = sys.modules["orchi_setup"] = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)
LEGACY = json.loads((Path(__file__).parent / "fixtures/legacy-setup.json").read_text())


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    git("init", "-q", "-b", "main", cwd=root)
    (root / "README.md").write_text("# Project\n")
    return root


@pytest.fixture
def legacy(repo):
    """A repository the earlier setup prepared."""
    for path, text in LEGACY.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text)
    return repo


def run(root, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / "setup.py"), "--project", str(root), "--no-labels", *args],
                          capture_output=True, text=True)


def snapshot(root):
    return {path: text for path, text in tree(root).items() if not path.startswith(".git/")}


def excluded(root):
    return (root / ".git/info/exclude").read_text().splitlines() if (root / ".git/info/exclude").exists() else []


def test_dry_run_lists_the_changes_and_writes_nothing(repo):
    before = snapshot(repo)
    result = run(repo, "--dry-run")
    assert result.returncode == 0, result.stderr
    for line in ("Would create .github/workflows/docs-check.yml", "Would create .github/scripts/knowledge.py",
                 "Would create .github/workflows/standards-check.yml", "Would create AGENTS.md",
                 "Would create .github/pull_request_template.md", "Would add .orchi-tmp/ to"):
        assert line in result.stdout
    assert snapshot(repo) == before and excluded(repo).count(".orchi-tmp/") == 0


def test_second_run_changes_nothing(repo):
    first = run(repo)
    assert first.returncode == 0, first.stderr
    after_first = snapshot(repo)
    second = run(repo)
    assert second.returncode == 0, second.stderr
    assert second.stdout.strip() == "Nothing to change."
    assert snapshot(repo) == after_first
    assert run(repo, "--check").returncode == 0


def test_the_written_footprint_is_neutral(repo):
    run(repo)
    files = snapshot(repo)
    assert sorted(files) == [".github/pull_request_template.md", ".github/scripts/knowledge.py",
                             ".github/scripts/standards.py", ".github/workflows/docs-check.yml",
                             ".github/workflows/standards-check.yml", "AGENTS.md", "README.md"]
    for path, text in files.items():
        assert "orchi" not in text.casefold(), path
    for script in ("knowledge.py", "standards.py"):
        assert (repo / ".github/scripts" / script).read_bytes() == (SCRIPTS / script).read_bytes()
    workflows = files[".github/workflows/docs-check.yml"] + files[".github/workflows/standards-check.yml"]
    assert ".github/scripts/knowledge.py" in workflows and ".github/scripts/standards.py" in workflows
    assert "knowledge.py work" not in workflows and "schedule" not in workflows and "issues: write" not in workflows
    assert "## Development rules" in files["AGENTS.md"] and "## Summary" in files[".github/pull_request_template.md"]
    for path in ("AGENTS.md", ".github/pull_request_template.md"):
        assert "issue" not in files[path].casefold(), path
    assert excluded(repo).count(".orchi-tmp/") == 1
    assert git("check-ignore", "-q", ".orchi-tmp/x", cwd=repo) == ""


def test_exclude_only_adds_the_temporary_folder_once(repo):
    for _ in range(2):
        assert run(repo, "--exclude").returncode == 0
    assert excluded(repo).count(".orchi-tmp/") == 1 and snapshot(repo) == {"README.md": "# Project\n"}


def test_paths_lists_current_and_earlier_files(repo):
    listed = run(repo, "--paths").stdout.split()
    assert {".github/workflows/docs-check.yml", ".github/scripts/standards.py", "AGENTS.md",
            ".github/pull_request_template.md", ".github/orchi/manifest.json", ".github/copilot/settings.json",
            ".github/github-app.yml", ".github/ISSUE_TEMPLATE/orchi-task.yml"} <= set(listed)


def test_existing_files_keep_their_content(repo):
    (repo / "AGENTS.md").write_text("# Agents\n\nUse tabs.\n")
    (repo / ".github").mkdir()
    (repo / ".github/PULL_REQUEST_TEMPLATE.md").write_text("## Checklist\n")
    run(repo)
    agents = (repo / "AGENTS.md").read_text()
    assert agents.startswith("# Agents\n\nUse tabs.\n\n<!-- managed:begin -->\n## Development rules")
    assert (repo / ".github/PULL_REQUEST_TEMPLATE.md").read_text().startswith("## Checklist\n\n<!-- managed:begin -->")
    assert "pull_request_template.md" not in [p.name for p in (repo / ".github").iterdir()]
    assert run(repo).stdout.strip() == "Nothing to change."


def test_edited_section_is_refused_until_replace(repo):
    run(repo)
    agents = repo / "AGENTS.md"
    agents.write_text(agents.read_text().replace("Agree the outcome", "Agree everything"))
    edited = snapshot(repo)
    result = run(repo)
    assert result.returncode == 1
    assert "the managed section of AGENTS.md differs" in result.stderr
    assert snapshot(repo) == edited
    assert run(repo, "--replace").returncode == 0
    assert "Agree everything" not in agents.read_text()


OLD_RULES = """## Development rules

- Agree the outcome, approach, and scope with whoever asked before creating branches, Issues, or changes.
- Track work in GitHub Issues and pull requests; resume from the existing Issue, branch, and PR instead of starting over.
- An Issue with an assignee, a linked pull request, or a linked branch is taken: leave it to its owner unless they hand it over.
- Where `ENGINEERING.md` exists, follow it and run its checks; never weaken a check without recording an exception there.
- Update the documentation in the same change as the code: `docs/README.md`, when present, maps the pages, and every pull request fills its Documentation impact section.
- Do not infer permission to merge or deploy from permission to implement."""


def test_sections_that_prescribed_issues_are_updated(repo):
    pr_body = (ASSETS / "github/pull_request_template.md").read_text().strip("\n").replace(
        "<!-- What changed and why. -->",
        "<!-- What changed and why. Link issues; closing keywords only work for PRs into the default branch. -->")
    (repo / "AGENTS.md").write_text(f"# Agents\n\n{setup.START}\n{OLD_RULES}\n{setup.END}\n")
    (repo / ".github").mkdir()
    (repo / ".github/pull_request_template.md").write_text(f"{setup.START}\n{pr_body}\n{setup.END}\n")
    result = run(repo)
    assert result.returncode == 0, result.stderr
    assert "Update the section of AGENTS.md" in result.stdout
    assert "Update the section of .github/pull_request_template.md" in result.stdout
    for path in ("AGENTS.md", ".github/pull_request_template.md"):
        assert "issue" not in (repo / path).read_text().casefold(), path
    assert run(repo).stdout.strip() == "Nothing to change."


def test_a_version_setup_shipped_before_is_updated(repo, monkeypatch):
    run(repo)
    workflow = repo / ".github/workflows/docs-check.yml"
    workflow.write_text("name: an earlier version\n")
    assert run(repo).returncode == 1
    monkeypatch.setitem(setup.PREVIOUS, ".github/workflows/docs-check.yml", {setup.sha(workflow.read_bytes())})
    plan = setup.build(repo, labels=False)
    assert not plan.conflicts and "update .github/workflows/docs-check.yml" in plan.actions


def test_foreign_file_is_refused(repo):
    (repo / ".github/scripts").mkdir(parents=True)
    (repo / ".github/scripts/knowledge.py").write_text("print('mine')\n")
    result = run(repo)
    assert result.returncode == 1 and ".github/scripts/knowledge.py exists and differs" in result.stderr
    assert sorted(snapshot(repo)) == [".github/scripts/knowledge.py", "README.md"]


def test_workflow_opt_out_removes_and_persists(repo):
    run(repo)
    result = run(repo, "--no-docs-workflow")
    assert "remove .github/workflows/docs-check.yml" in result.stdout.lower()
    assert not (repo / ".github/workflows/docs-check.yml").exists()
    assert not (repo / ".github/scripts/knowledge.py").exists()
    assert (repo / ".github/workflows/standards-check.yml").exists()
    assert run(repo).stdout.strip() == "Nothing to change."
    run(repo, "--docs-workflow")
    assert (repo / ".github/workflows/docs-check.yml").exists()


def test_check_exits_nonzero_when_changes_are_pending(repo):
    assert run(repo, "--check").returncode == 1
    assert snapshot(repo) == {"README.md": "# Project\n"}


def test_an_earlier_setup_is_migrated(legacy):
    result = run(legacy)
    assert result.returncode == 0, result.stderr
    files = snapshot(legacy)
    assert sorted(files) == [".github/pull_request_template.md", ".github/scripts/knowledge.py",
                             ".github/scripts/standards.py", ".github/workflows/docs-check.yml",
                             ".github/workflows/standards-check.yml", "AGENTS.md", "README.md"]
    for path, text in files.items():
        assert "orchi" not in text.casefold(), path
    assert not (legacy / ".github/orchi").exists() and not (legacy / ".github/copilot").exists()
    assert excluded(legacy).count(".orchi-tmp/") == 1
    assert run(legacy).stdout.strip() == "Nothing to change."


def test_migration_keeps_what_others_added(legacy):
    agents = legacy / "AGENTS.md"
    agents.write_text("# Agents\n\nUse tabs.\n\n" + agents.read_text())
    (legacy / ".gitignore").write_text("node_modules/\n\n" + (legacy / ".gitignore").read_text())
    app = legacy / ".github/github-app.yml"
    app.write_text(app.read_text() + "automation:\n  remote_control: true\n")
    settings = legacy / ".github/copilot/settings.json"
    data = json.loads(settings.read_text())
    data["enabledPlugins"]["x@y"] = True
    settings.write_text(json.dumps(data))
    form = legacy / ".github/ISSUE_TEMPLATE/orchi-task.yml"
    form.write_text(form.read_text() + "# local change\n")
    result = run(legacy)
    assert result.returncode == 0, result.stderr
    assert agents.read_text().startswith("# Agents\n\nUse tabs.\n\n<!-- managed:begin -->\n## Development rules")
    assert "orchi" not in agents.read_text().casefold()
    assert (legacy / ".gitignore").read_text() == "node_modules/\n"
    assert app.read_text() == "automation:\n  remote_control: true\n"
    assert json.loads(settings.read_text()) == {"enabledPlugins": {"x@y": True}}
    assert form.exists() and "orchi-task.yml was edited after setup wrote it" in result.stdout
    assert not (legacy / ".github/ISSUE_TEMPLATE/orchi-epic.yml").exists()


def test_an_edited_earlier_section_is_refused_until_replace(legacy):
    agents = legacy / "AGENTS.md"
    agents.write_text(agents.read_text().replace("Research first", "Research always"))
    result = run(legacy)
    assert result.returncode == 1 and "in AGENTS.md was edited after setup wrote it" in result.stderr
    assert run(legacy, "--replace").returncode == 0
    assert "Research always" not in agents.read_text()


def test_an_earlier_opt_out_is_kept(legacy):
    manifest = legacy / ".github/orchi/manifest.json"
    manifest.write_text(json.dumps({**json.loads(manifest.read_text()), "standards_workflow": False}))
    (legacy / ".github/workflows/orchi-standards.yml").unlink()
    (legacy / ".github/orchi/scripts/standards.py").unlink()
    assert run(legacy).returncode == 0
    assert not (legacy / ".github/workflows/standards-check.yml").exists()
    assert run(legacy).stdout.strip() == "Nothing to change."


def test_a_disabled_plugin_setting_stays(legacy):
    settings = legacy / ".github/copilot/settings.json"
    data = json.loads(settings.read_text())
    data["enabledPlugins"]["orchi@orchi-copilot"] = False
    settings.write_text(json.dumps(data))
    result = run(legacy)
    assert json.loads(settings.read_text())["enabledPlugins"] == {"orchi@orchi-copilot": False}
    assert "left as it is" in result.stdout


def fake_github(labels, issues, calls):
    def gh(*args, cwd):
        calls.append(args)
        if args[:2] == ("label", "list"):
            return json.dumps(labels)
        if args[:2] == ("issue", "list"):
            return json.dumps(issues.get(args[args.index("--label") + 1], []))
        return ""
    return gh


def test_labels_are_migrated_but_never_created(repo, monkeypatch):
    calls = []
    labels = [{"name": "Epic", "description": "Orchi: an outcome decomposed into Tasks"},
              {"name": "Task", "description": "Ours"},
              {"name": "in-progress", "description": "Orchi: owned work in progress"},
              {"name": "Exploration", "description": "Orchi: an idea being researched and shaped before planning"},
              {"name": "retro", "description": "Orchi: an accepted lesson that changes checks, forms, or instructions"},
              {"name": "needs-planning", "description": "Ours too"}]
    issues = {"in-progress": [{"number": 3, "title": "A", "assignees": []},
                              {"number": 4, "title": "B", "assignees": [{"login": "dev"}]}],
              "Exploration": [{"number": 5, "title": "Payments", "assignees": []}],
              "retro": [{"number": 6, "title": "Lesson: flaky", "assignees": []}]}
    monkeypatch.setattr(setup, "gh", fake_github(labels, issues, calls))
    plan = setup.build(repo)
    setup.apply(plan)
    writes = [args for args in calls if args[:2] not in {("label", "list"), ("issue", "list")}]
    assert writes == [
        ("label", "edit", "Epic", "--description", setup.TYPE_LABELS["Epic"]),
        ("issue", "edit", "3", "--add-assignee", "@me"),
        ("label", "delete", "in-progress", "--yes"),
        ("issue", "edit", "5", "--title", "Explore: Payments"),
        ("label", "delete", "Exploration", "--yes"),
        ("label", "delete", "retro", "--yes"),
    ]
    assert any("needs-planning was changed" in note for note in plan.notes)
    assert not any(description.startswith("Orchi") for description in setup.TYPE_LABELS.values())
    guidance = (SCRIPTS.parent / "references/github.md").read_text()
    for name, description in setup.TYPE_LABELS.items():
        assert f'gh label create {name} --color' in guidance and f'--description "{description}"' in guidance


def test_unavailable_github_is_reported_not_fatal(repo, monkeypatch):
    def failing_gh(*args, cwd):
        raise subprocess.CalledProcessError(1, "gh", stderr="gh: not logged in")
    monkeypatch.setattr(setup, "gh", failing_gh)
    plan = setup.build(repo)
    assert any("labels not checked" in note and "not logged in" in note for note in plan.notes)
    assert not plan.github


def test_symlinked_destination_is_refused(repo, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / ".github").symlink_to(outside)
    result = run(repo)
    assert result.returncode == 1 and "symlink" in result.stderr
    assert list(outside.iterdir()) == []


def test_assets_setup_writes_are_neutral():
    for path in [*(ASSETS / "github").rglob("*"), *(ASSETS / "docs").rglob("*"), *(ASSETS / "standards").rglob("*")]:
        if path.is_file():
            assert "orchi" not in path.read_text().casefold(), path
    for script in ("knowledge.py", "standards.py"):
        assert "orchi" not in (SCRIPTS / script).read_text().casefold(), script
    assert "orchi" not in setup.INSTRUCTIONS_BODY.casefold()
