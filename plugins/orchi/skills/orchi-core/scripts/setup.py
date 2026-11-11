#!/usr/bin/env python3
"""Prepare a repository for Orchi: labels, GitHub files, instructions, and the Copilot plugin defaults.

Idempotent: a second run changes nothing. Orchi manages whole files it created and sections between
`orchi:begin` and `orchi:end` markers; `.github/orchi/manifest.json` records their digests. A managed file or
section that someone edited, or a file Orchi did not create, is never overwritten: the run stops before writing
anything and lists them, unless `--replace` is given. `--dry-run` lists the changes and writes nothing.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / "assets"
SCRIPTS = SKILL / "scripts"
MANIFEST = ".github/orchi/manifest.json"
START, END = "<!-- orchi:begin -->", "<!-- orchi:end -->"
HASH_START, HASH_END = "# orchi:begin", "# orchi:end"
MARKETPLACE = "orchi-copilot"
MARKETPLACE_REPO = "nkhus/orchi-copilot"
PLUGIN = "orchi@" + MARKETPLACE
COPILOT_SETTINGS = ".github/copilot/settings.json"
APP_CONFIG = ".github/github-app.yml"
INSTRUCTIONS = "AGENTS.md"
GITIGNORE = ".gitignore"
DOCS_WORKFLOW = ".github/workflows/orchi-docs.yml"
STANDARDS_WORKFLOW = ".github/workflows/orchi-standards.yml"
VENDORED = ".github/orchi/scripts/"
ISSUE_FORMS = ("orchi-epic.yml", "orchi-exploration.yml", "orchi-initiative.yml", "orchi-task.yml")
LABELS = {
    "Initiative": ("5319e7", "Orchi: a request decomposed into Epics"),
    "Epic": ("0e8a16", "Orchi: an outcome decomposed into Tasks"),
    "Task": ("1d76db", "Orchi: one reviewable result"),
    "in-progress": ("fbca04", "Orchi: owned work in progress"),
    "Exploration": ("c5def5", "Orchi: an idea being researched and shaped before planning"),
    "needs-planning": ("d4c5f9", "Orchi: a request waiting for a planner"),
    "delivery-ready": ("0e8a16", "Orchi: planned work that passed its readiness gate"),
    "retro": ("bfd4f2", "Orchi: an accepted lesson that changes checks, forms, or instructions"),
    "design": ("e99695", "Orchi: an Epic a designer runs with the user"),
}
# GitHub reads the first PR template it finds; extend an existing one instead of adding a rival.
PR_TEMPLATE_PATHS = (".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md", "pull_request_template.md",
                     "PULL_REQUEST_TEMPLATE.md", "docs/pull_request_template.md", "docs/PULL_REQUEST_TEMPLATE.md")
INSTRUCTIONS_BODY = """## Orchi workflow

Orchi runs this repository's work: the user talks to the Orchi Copilot Project, or types `/orchi`, and Orchi routes each request to a session for its role.
Orchi, its sessions, and their subagents follow the `orchi-core` skill of the `orchi` plugin (`orchi@orchi-copilot`). Anywhere else, answer questions only, and ask the user to bring work to Orchi.
Research first and agree the outcome, approach, and scope (Task, Epic, or Initiative) with the user before creating branches, issues, or changes.
Track work in Git branches and GitHub Issues; resume from the existing issue, branch, and PR instead of duplicating work.
For documentation-only questions, use its retrieval guidance without creating tracking.
Where `ENGINEERING.md` exists, follow it and run its checks; never weaken a check without recording an exception there.
`docs/README.md`, when present, maps the current documentation; working documents live in `docs/work/` on branches and never reach main.
Do not infer merge or deployment permission from permission to implement."""
GITIGNORE_BODY = """# Temporary files of Orchi's sessions and subagents.
.orchi-tmp/"""
APP_CONFIG_BODY = """instructions: |
  This repository runs its work through Orchi. Follow the Orchi workflow section of AGENTS.md and the
  orchi-core skill of the orchi plugin (orchi@orchi-copilot).
"""


class Refused(Exception):
    """A change Orchi will not make without --replace; nothing has been written."""


@dataclass
class Plan:
    root: Path
    writes: dict[str, bytes] = field(default_factory=dict)
    removals: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def destination(root: Path, relative: str) -> Path:
    path = root / relative
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise Refused("Refusing to write through a symlink: " + relative)
    return path


def current(root: Path, relative: str) -> bytes | None:
    path = destination(root, relative)
    return path.read_bytes() if path.is_file() else None


def load_manifest(root: Path) -> dict:
    data = current(root, MANIFEST)
    if data is None:
        return {}
    try:
        manifest = json.loads(data)
    except ValueError as error:
        raise Refused(f"{MANIFEST} is not valid JSON: {error}") from None
    if not isinstance(manifest, dict) or not all(isinstance(manifest.get(key, {}), dict) for key in ("files", "sections")):
        raise Refused(MANIFEST + " has an unknown format; repair or remove it")
    return manifest


def plan_file(plan: Plan, old: dict, new: dict, relative: str, content: bytes, replace: bool, soft: bool = False):
    """A whole file Orchi owns. `soft` files that are not Orchi's are left alone with a note instead of a conflict."""
    existing, recorded = current(plan.root, relative), old.get(relative)
    if existing == content:
        new[relative] = sha(content)
        return
    if existing is None:
        plan.actions.append(("recreate " if recorded else "create ") + relative)
    elif recorded is not None and sha(existing) == recorded:
        plan.actions.append("update " + relative)
    elif soft:
        plan.notes.append(f"{relative} exists and is not Orchi's; left as it is")
        return
    elif replace:
        plan.actions.append("replace " + relative)
    else:
        plan.conflicts.append(relative + (" was edited after Orchi wrote it" if recorded else " exists and is not Orchi's"))
        return
    plan.writes[relative] = content
    new[relative] = sha(content)


def plan_removal(plan: Plan, old: dict, relative: str, replace: bool):
    """Remove a file Orchi created and no longer manages; an edited one stays and is reported."""
    existing, recorded = current(plan.root, relative), old.get(relative)
    if recorded is None or existing is None:
        return
    if sha(existing) == recorded or replace:
        plan.removals.append(relative)
        plan.actions.append("remove " + relative)
    else:
        plan.notes.append(f"{relative} was edited after Orchi wrote it; it is no longer managed, remove it by hand")


def span(text: str, start: str, end: str, relative: str) -> tuple[int, int] | None:
    if start not in text and end not in text:
        return None
    if text.count(start) != 1 or text.count(end) != 1 or text.index(start) > text.index(end):
        raise Refused(f"Malformed Orchi markers in {relative}; repair them first")
    return text.index(start), text.index(end) + len(end)


def plan_section(plan: Plan, old: dict, new: dict, relative: str, body: str, replace: bool):
    """A section between markers in a file that may hold other content."""
    start, end = (HASH_START, HASH_END) if Path(relative).name == GITIGNORE else (START, END)
    block = f"{start}\n{body}\n{end}"
    raw = current(plan.root, relative)
    try:
        text = raw.decode("utf-8") if raw is not None else None
    except UnicodeDecodeError:
        raise Refused(relative + " is not UTF-8 text") from None
    found = span(text, start, end, relative) if text is not None else None
    if text is None:
        updated, action = block + "\n", "create "
    elif found is None:
        separator = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
        updated, action = text + separator + block + "\n", "add a section to "
    else:
        existing = text[found[0]:found[1]]
        if existing == block:
            new[relative] = sha(block.encode())
            return
        recorded = old.get(relative)
        if not replace and (recorded is None or sha(existing.encode()) != recorded):
            plan.conflicts.append(f"the Orchi section of {relative} was edited after Orchi wrote it")
            return
        updated, action = text[:found[0]] + block + text[found[1]:], "update the section of "
    plan.writes[relative] = updated.encode("utf-8")
    plan.actions.append(action + relative)
    new[relative] = sha(block.encode())


def pr_template_path(root: Path, managed: dict) -> str:
    recorded = [path for path in PR_TEMPLATE_PATHS if path in managed]
    if recorded:
        return recorded[0]

    # Compare exact names: on case-insensitive filesystems both spellings would appear to exist.
    def present(path: str) -> bool:
        parent = (root / path).parent
        return parent.is_dir() and Path(path).name in os.listdir(parent)
    return next((path for path in PR_TEMPLATE_PATHS if present(path)), PR_TEMPLATE_PATHS[0])


def plan_settings(plan: Plan):
    """Merge the marketplace and the enabled plugin into the repository's Copilot settings; keep every other value."""
    raw = current(plan.root, COPILOT_SETTINGS)
    try:
        settings = json.loads(raw) if raw is not None else {}
    except ValueError:
        plan.conflicts.append(COPILOT_SETTINGS + " is not valid JSON")
        return
    if not isinstance(settings, dict):
        plan.conflicts.append(COPILOT_SETTINGS + " is not a JSON object")
        return
    marketplaces = settings.setdefault("extraKnownMarketplaces", {})
    plugins = settings.setdefault("enabledPlugins", {})
    if not isinstance(marketplaces, dict) or not isinstance(plugins, dict):
        plan.conflicts.append(COPILOT_SETTINGS + " has extraKnownMarketplaces or enabledPlugins that are not objects")
        return
    marketplaces.setdefault(MARKETPLACE, {"source": {"source": "github", "repo": MARKETPLACE_REPO}})
    # An explicit false is the team's choice; leave it.
    plugins.setdefault(PLUGIN, True)
    if plugins[PLUGIN] is not True:
        plan.notes.append(f"{COPILOT_SETTINGS} disables {PLUGIN}; left as it is")
    updated = (json.dumps(settings, indent=2) + "\n").encode()
    if raw is None or json.loads(raw) != settings:
        plan.writes[COPILOT_SETTINGS] = updated
        plan.actions.append(("update " if raw is not None else "create ") + COPILOT_SETTINGS)


def gh(*args: str, cwd: Path) -> str:
    return subprocess.run(["gh", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def plan_labels(plan: Plan):
    try:
        names = {label["name"] for label in json.loads(gh("label", "list", "--limit", "500", "--json", "name",
                                                          cwd=plan.root))}
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        reason = getattr(error, "stderr", "") or str(error)
        plan.notes.append("labels not checked: GitHub is unavailable (" + reason.strip().splitlines()[-1] + ")")
        return
    plan.labels = [name for name in LABELS if name not in names]
    plan.actions.extend("create label " + name for name in plan.labels)


def build(root: Path, replace: bool = False, labels: bool = True, docs_workflow: bool | None = None,
          standards_workflow: bool | None = None) -> Plan:
    manifest = load_manifest(root)
    plan = Plan(root)
    old_files, old_sections = manifest.get("files", {}), manifest.get("sections", {})
    files, sections = {}, {}
    docs = manifest.get("docs_workflow", True) if docs_workflow is None else docs_workflow
    standards = manifest.get("standards_workflow", True) if standards_workflow is None else standards_workflow

    for name in ISSUE_FORMS:
        plan_file(plan, old_files, files, ".github/ISSUE_TEMPLATE/" + name,
                  (ASSETS / "github/ISSUE_TEMPLATE" / name).read_bytes(), replace)
    for enabled, workflow, script in ((docs, DOCS_WORKFLOW, "knowledge.py"),
                                      (standards, STANDARDS_WORKFLOW, "standards.py")):
        pairs = ((workflow, ASSETS / "github/workflows" / Path(workflow).name), (VENDORED + script, SCRIPTS / script))
        for relative, source in pairs:
            if enabled:
                plan_file(plan, old_files, files, relative, source.read_bytes(), replace)
            else:
                plan_removal(plan, old_files, relative, replace)
    plan_file(plan, old_files, files, APP_CONFIG, APP_CONFIG_BODY.encode(), replace, soft=True)

    plan_section(plan, old_sections, sections, INSTRUCTIONS, INSTRUCTIONS_BODY, replace)
    plan_section(plan, old_sections, sections, pr_template_path(root, old_sections),
                 (ASSETS / "github/pull_request_template.md").read_text(encoding="utf-8").strip("\n"), replace)
    plan_section(plan, old_sections, sections, GITIGNORE, GITIGNORE_BODY, replace)
    plan_settings(plan)

    updated = {"files": dict(sorted(files.items())), "sections": dict(sorted(sections.items())),
               "docs_workflow": docs, "standards_workflow": standards}
    content = (json.dumps(updated, indent=2, sort_keys=True) + "\n").encode()
    if current(root, MANIFEST) != content:
        plan.writes[MANIFEST] = content
        plan.actions.append(("update " if manifest else "create ") + MANIFEST)
    if labels:
        plan_labels(plan)
    return plan


def apply(plan: Plan):
    for relative, content in plan.writes.items():
        path = destination(plan.root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    for relative in plan.removals:
        destination(plan.root, relative).unlink()
    for name in plan.labels:
        color, description = LABELS[name]
        try:
            gh("label", "create", name, "--color", color, "--description", description, cwd=plan.root)
        except (OSError, subprocess.CalledProcessError) as error:
            plan.notes.append(f"label {name} not created: {(getattr(error, 'stderr', '') or str(error)).strip()}")


def repository_root(path: Path) -> Path:
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path, check=True, capture_output=True,
                             text=True).stdout.strip()
        return Path(top).resolve()
    except (OSError, subprocess.CalledProcessError):
        return path.resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="repository to prepare (default: current)")
    parser.add_argument("--dry-run", action="store_true", help="list the changes and write nothing")
    parser.add_argument("--check", action="store_true", help="like --dry-run, but exit 1 when anything would change")
    parser.add_argument("--replace", action="store_true", help="overwrite edited Orchi files and sections")
    parser.add_argument("--no-labels", dest="labels", action="store_false", help="do not check or create labels")
    for name in ("docs", "standards"):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(f"--{name}-workflow", dest=f"{name}_workflow", action="store_true", default=None,
                           help=f"install the Orchi {name} workflow (the default)")
        group.add_argument(f"--no-{name}-workflow", dest=f"{name}_workflow", action="store_false",
                           help=f"remove the Orchi {name} workflow and keep it off on later runs")
    args = parser.parse_args(argv)
    root = repository_root(args.project)
    try:
        plan = build(root, args.replace, args.labels, args.docs_workflow, args.standards_workflow)
    except Refused as error:
        print("Refused: " + str(error), file=sys.stderr)
        return 1
    if plan.conflicts:
        print("Refused, nothing written. Restore these, or rerun with --replace to overwrite them:", file=sys.stderr)
        for conflict in plan.conflicts:
            print("  " + conflict, file=sys.stderr)
        return 1
    preview = args.dry_run or args.check
    if not preview:
        try:
            apply(plan)
        except Refused as error:
            print("Refused: " + str(error), file=sys.stderr)
            return 1
    prefix = "Would " if preview else ""
    for action in plan.actions:
        print(prefix + action if preview else action[:1].upper() + action[1:])
    if not plan.actions:
        print("Nothing to change.")
    for note in plan.notes:
        print("Note: " + note)
    return 1 if args.check and plan.actions else 0


if __name__ == "__main__":
    sys.exit(main())
