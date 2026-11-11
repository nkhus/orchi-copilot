#!/usr/bin/env python3
"""Prepare a repository's development rules and checks: a rules section, a PR template section, and checks.

Idempotent: a second run changes nothing. Setup manages whole files and the sections between `managed:begin` and
`managed:end` markers, and writes no record into the repository: it recognises its own files and sections by the
digests of the versions it ships (`PREVIOUS` holds the earlier ones). One that matches none of them was edited or is
someone else's, and is never overwritten: the run stops before writing anything and lists them, unless `--replace` is
given. Setup also migrates a repository it prepared before, when it wrote process files, a manifest, and process
labels. Everything it writes is tool-neutral. `--dry-run` lists the changes and writes nothing.
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
START, END = "<!-- managed:begin -->", "<!-- managed:end -->"
INSTRUCTIONS = "AGENTS.md"
DOCS_WORKFLOW = ".github/workflows/docs-check.yml"
STANDARDS_WORKFLOW = ".github/workflows/standards-check.yml"
VENDORED = ".github/scripts/"
EXCLUDE = ".orchi-tmp/"
# GitHub reads the first PR template it finds; extend an existing one instead of adding a rival.
PR_TEMPLATE_PATHS = (".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md", "pull_request_template.md",
                     "PULL_REQUEST_TEMPLATE.md", "docs/pull_request_template.md", "docs/PULL_REQUEST_TEMPLATE.md")
INSTRUCTIONS_BODY = """## Development rules

- Agree the outcome, approach, and scope with whoever asked before making changes.
- Where `ENGINEERING.md` exists, follow it and run its checks; never weaken a check without recording an exception there.
- Update the documentation in the same change as the code: `docs/README.md`, when present, maps the pages, and every pull request fills its Documentation impact section.
- Do not infer permission to merge or deploy from permission to implement."""
# The sha256 of each earlier version of a managed file or section block, keyed by its path ("AGENTS.md" and
# "pull_request_template" for the sections). When an asset or a section body changes, add its previous digest here,
# so setup still recognises and updates the old version.
PREVIOUS: dict[str, set[str]] = {
    "AGENTS.md": {"c12c66fe875d875f313440d0b5c5ef527c68bfaa24e0b4922e7689d81a6b779f"},
    "pull_request_template": {"5ada249067ce56d04a96f90c722a019e7253740aa150ac51107755eb18227e6e"},
}

# The footprint of the earlier setup, which this one migrates.
LEGACY_MANIFEST = ".github/orchi/manifest.json"
LEGACY_START, LEGACY_END = "<!-- orchi:begin -->", "<!-- orchi:end -->"
LEGACY_HASH_START, LEGACY_HASH_END = "# orchi:begin", "# orchi:end"
LEGACY_FORMS = tuple(".github/ISSUE_TEMPLATE/orchi-" + name + ".yml"
                     for name in ("epic", "exploration", "initiative", "task"))
LEGACY_WORKFLOWS = {".github/workflows/orchi-docs.yml": ".github/orchi/scripts/knowledge.py",
                    ".github/workflows/orchi-standards.yml": ".github/orchi/scripts/standards.py"}
LEGACY_SETTINGS = ".github/copilot/settings.json"
LEGACY_MARKETPLACE = "orchi-copilot"
LEGACY_MARKETPLACE_ENTRY = {"source": {"source": "github", "repo": "nkhus/orchi-copilot"}}
LEGACY_PLUGIN = "orchi@" + LEGACY_MARKETPLACE
LEGACY_APP_CONFIG = ".github/github-app.yml"
LEGACY_APP_CONFIG_BODY = """instructions: |
  This repository runs its work through Orchi. Follow the Orchi workflow section of AGENTS.md and the
  orchi-core skill of the orchi plugin (orchi@orchi-copilot).
"""
LEGACY_DIGESTS = {
    "83dd62137fc10c2a54a1d4e2109995106579dd4b0998c71b14db24211b2b15cb",  # AGENTS.md section
    "355639dfec63b81bd2637b6c8369bb5ebc3be9364631b692523c79028c150ac7",  # PR template section
    "fe216193d395cf6942bd3b3ecb21623958b3310f527d57baefbdd6d819e54478",  # .gitignore section
    "17a449edfdea0df35a30ce855659f471f64d8ec1114d8f54af81cb60a25acdc8",  # orchi-epic.yml
    "6491dcf9513c19a96fc0f1d11b018915f8e1766464359d96711516dfcf8a5e5b",  # orchi-exploration.yml
    "b58b527256de6adbd9dc063ed3d0ac473f3962d8e34b888b685a40e34a4541e8",  # orchi-initiative.yml
    "3a50d22ed7a18f4377789bef88e93ab659a602c815053e55e5f483c6976367a5",  # orchi-task.yml
    "1a4c43665471b0f2ec622ec052a11f949aca597244decb2cba9e5cc1a54eed30",  # orchi-docs.yml
    "d9aa08a048cc58e1b442bf6f458a0628da655f7cbd6a9d88158cbf4868969ee1",  # orchi-standards.yml
    "b8b0ac4d8b3568a43a31f45ff40d589310321d62c614d08a0d592185afdb88b1",  # knowledge.py
    "9f7952ea3b9ed41f54722661c21b98ed8ef1e4111f10253f589125bd7a998b87",  # standards.py
}
# The type labels' neutral descriptions, which replace the earlier setup's. Setup creates no labels: Orchi creates a
# missing type label itself when it first files such an Issue.
TYPE_LABELS = {
    "Initiative": "A request delivered through several Epics",
    "Epic": "An outcome delivered through several Tasks",
    "Task": "One reviewable change",
}
LEGACY_LABELS = {
    "Initiative": "Orchi: a request decomposed into Epics",
    "Epic": "Orchi: an outcome decomposed into Tasks",
    "Task": "Orchi: one reviewable result",
    "in-progress": "Orchi: owned work in progress",
    "Exploration": "Orchi: an idea being researched and shaped before planning",
    "needs-planning": "Orchi: a request waiting for a planner",
    "delivery-ready": "Orchi: planned work that passed its readiness gate",
    "retro": "Orchi: an accepted lesson that changes checks, forms, or instructions",
    "design": "Orchi: an Epic a designer runs with the user",
}
# Before a process label goes, the Issues that carry it keep what it meant: a title prefix, or an assignee.
LEGACY_LABEL_TITLES = {"Exploration": ("open", "Explore: "), "retro": ("all", "Lesson: ")}


class Refused(Exception):
    """A change setup will not make without --replace; nothing has been written."""


@dataclass
class Plan:
    root: Path
    writes: dict[str, bytes] = field(default_factory=dict)
    removals: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    github: list[tuple[str, list[str]]] = field(default_factory=list)
    exclude: Path | None = None


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


def text_of(root: Path, relative: str) -> str | None:
    raw = current(root, relative)
    try:
        return raw.decode("utf-8") if raw is not None else None
    except UnicodeDecodeError:
        raise Refused(relative + " is not UTF-8 text") from None


def ours(key: str, data: bytes, latest: bytes) -> bool:
    return data == latest or sha(data) in PREVIOUS.get(key, set())


def plan_file(plan: Plan, relative: str, content: bytes, replace: bool):
    """A whole file setup owns: created, updated from a version setup shipped, or refused when it differs."""
    existing = current(plan.root, relative)
    if existing == content:
        return
    if existing is None:
        plan.actions.append("create " + relative)
    elif ours(relative, existing, content):
        plan.actions.append("update " + relative)
    elif replace:
        plan.actions.append("replace " + relative)
    else:
        plan.conflicts.append(relative + " exists and differs from every version setup wrote")
        return
    plan.writes[relative] = content


def plan_removal(plan: Plan, relative: str, content: bytes, replace: bool):
    """Remove a file setup wrote and no longer wants; a changed one stays and is reported."""
    existing = current(plan.root, relative)
    if existing is None:
        return
    if ours(relative, existing, content) or replace:
        plan.removals.append(relative)
        plan.actions.append("remove " + relative)
    else:
        plan.notes.append(f"{relative} differs from what setup wrote; left as it is")


def span(text: str, start: str, end: str, relative: str) -> tuple[int, int] | None:
    if start not in text and end not in text:
        return None
    if text.count(start) != 1 or text.count(end) != 1 or text.index(start) > text.index(end):
        raise Refused(f"Malformed {start.strip('<!- ')} markers in {relative}; repair them first")
    return text.index(start), text.index(end) + len(end)


def legacy_ours(plan: Plan, manifest: dict, kind: str, relative: str, data: bytes) -> bool:
    return sha(data) in LEGACY_DIGESTS or sha(data) == manifest.get(kind, {}).get(relative)


def plan_section(plan: Plan, manifest: dict, key: str, relative: str, body: str, replace: bool):
    """The managed section of a file that may hold other content; an earlier setup's section is replaced in place."""
    block = f"{START}\n{body}\n{END}"
    text = plan.writes[relative].decode() if relative in plan.writes else text_of(plan.root, relative)
    found = span(text, START, END, relative) if text is not None else None
    legacy = span(text, LEGACY_START, LEGACY_END, relative) if text is not None else None
    if legacy is not None:
        old = text[legacy[0]:legacy[1]]
        if not (replace or legacy_ours(plan, manifest, "sections", relative, old.encode())):
            plan.conflicts.append(f"the section between {LEGACY_START} and {LEGACY_END} in {relative} was edited "
                                  "after setup wrote it")
            return
        if found is None:
            text, found = text[:legacy[0]] + block + text[legacy[1]:], None
            plan.writes[relative] = text.encode()
            plan.actions.append("replace the earlier setup's section of " + relative)
            return
        text = drop(text, legacy)
        found = span(text, START, END, relative)
        plan.writes[relative] = text.encode()
        plan.actions.append("remove the earlier setup's section of " + relative)
    if text is None:
        updated, action = block + "\n", "create "
    elif found is None:
        separator = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
        updated, action = text + separator + block + "\n", "add a section to "
    else:
        existing = text[found[0]:found[1]]
        if existing == block:
            return
        if not (replace or sha(existing.encode()) in PREVIOUS.get(key, set())):
            plan.conflicts.append(f"the managed section of {relative} differs from every version setup wrote")
            return
        updated, action = text[:found[0]] + block + text[found[1]:], "update the section of "
    plan.writes[relative] = updated.encode("utf-8")
    plan.actions.append(action + relative)


def drop(text: str, found: tuple[int, int]) -> str:
    """Text without a section, and without the line break and blank line setup added around it."""
    before, after = text[:found[0]], text[found[1]:]
    after = after[1:] if after.startswith("\n") else after
    if before.endswith("\n\n") and not after:
        before = before[:-1]
    return before + after


def pr_template_path(root: Path) -> str:
    # Compare exact names: on case-insensitive filesystems both spellings would appear to exist.
    def present(path: str) -> bool:
        parent = (root / path).parent
        return parent.is_dir() and Path(path).name in os.listdir(parent)
    existing = [path for path in PR_TEMPLATE_PATHS if present(path)]
    for marker in (START, LEGACY_START):
        for path in existing:
            if marker in (text_of(root, path) or ""):
                return path
    return existing[0] if existing else PR_TEMPLATE_PATHS[0]


def load_manifest(root: Path) -> dict:
    data = current(root, LEGACY_MANIFEST)
    if data is None:
        return {}
    try:
        manifest = json.loads(data)
    except ValueError:
        manifest = None
    if not isinstance(manifest, dict) or not all(isinstance(manifest.get(key, {}), dict) for key in ("files", "sections")):
        return {"unreadable": True}
    return manifest


def plan_legacy_files(plan: Plan, manifest: dict, replace: bool):
    """Remove the earlier setup's Issue forms, workflows, and scripts that nobody changed; report the rest."""
    def unchanged(relative: str) -> bool | None:
        data = current(plan.root, relative)
        return None if data is None else legacy_ours(plan, manifest, "files", relative, data)

    def remove(relative: str):
        plan.removals.append(relative)
        plan.actions.append("remove " + relative)

    for relative in LEGACY_FORMS:
        state = unchanged(relative)
        if state or (state is False and replace):
            remove(relative)
        elif state is False:
            plan.notes.append(f"{relative} was edited after setup wrote it; it is no longer managed, remove it by hand")
    for workflow, script in LEGACY_WORKFLOWS.items():
        states = [unchanged(workflow), unchanged(script)]
        present = [path for path, state in zip((workflow, script), states) if state is not None]
        if all(state is not False for state in states) or replace:
            for path in present:
                remove(path)
        else:
            plan.notes.append(" and ".join(present) + " were edited after setup wrote them; they are no longer "
                              "managed, remove them by hand")
    if current(plan.root, LEGACY_MANIFEST) is not None:
        remove(LEGACY_MANIFEST)


def plan_app_config(plan: Plan):
    """Remove the instructions the earlier setup put in the Copilot app's repository configuration; keep the rest."""
    text = text_of(plan.root, LEGACY_APP_CONFIG)
    if text is None or LEGACY_APP_CONFIG_BODY not in text:
        return
    rest = text.replace(LEGACY_APP_CONFIG_BODY, "", 1).lstrip("\n")
    if rest.strip():
        plan.writes[LEGACY_APP_CONFIG] = rest.encode()
        plan.actions.append("remove the earlier setup's instructions from " + LEGACY_APP_CONFIG)
    else:
        plan.removals.append(LEGACY_APP_CONFIG)
        plan.actions.append("remove " + LEGACY_APP_CONFIG)


def plan_settings(plan: Plan):
    """Remove the plugin and marketplace the earlier setup enabled for everyone; keep every other value."""
    raw = current(plan.root, LEGACY_SETTINGS)
    if raw is None:
        return
    try:
        settings = json.loads(raw)
    except ValueError:
        return
    if not isinstance(settings, dict):
        return
    plugins, marketplaces = settings.get("enabledPlugins"), settings.get("extraKnownMarketplaces")
    changed = False
    if isinstance(plugins, dict) and LEGACY_PLUGIN in plugins:
        if plugins[LEGACY_PLUGIN] is True:
            del plugins[LEGACY_PLUGIN]
            changed = True
        else:
            plan.notes.append(f"{LEGACY_SETTINGS} sets {LEGACY_PLUGIN} to {json.dumps(plugins[LEGACY_PLUGIN])}; "
                              "left as it is")
    others = isinstance(plugins, dict) and any(name.endswith("@" + LEGACY_MARKETPLACE) for name in plugins)
    if isinstance(marketplaces, dict) and marketplaces.get(LEGACY_MARKETPLACE) == LEGACY_MARKETPLACE_ENTRY \
            and not others:
        del marketplaces[LEGACY_MARKETPLACE]
        changed = True
    if not changed:
        return
    for key in ("enabledPlugins", "extraKnownMarketplaces"):
        if settings.get(key) == {}:
            del settings[key]
    if settings:
        plan.writes[LEGACY_SETTINGS] = (json.dumps(settings, indent=2) + "\n").encode()
        plan.actions.append("remove the earlier setup's plugin from " + LEGACY_SETTINGS)
    else:
        plan.removals.append(LEGACY_SETTINGS)
        plan.actions.append("remove " + LEGACY_SETTINGS)


def plan_gitignore(plan: Plan, manifest: dict, replace: bool):
    """Remove the earlier setup's `.gitignore` section; the temporary folder is excluded locally instead."""
    text = text_of(plan.root, ".gitignore")
    found = span(text, LEGACY_HASH_START, LEGACY_HASH_END, ".gitignore") if text is not None else None
    if found is None:
        return
    if not (replace or legacy_ours(plan, manifest, "sections", ".gitignore", text[found[0]:found[1]].encode())):
        plan.conflicts.append(f"the section between {LEGACY_HASH_START} and {LEGACY_HASH_END} in .gitignore was "
                              "edited after setup wrote it")
        return
    rest = drop(text, found)
    if rest.strip():
        plan.writes[".gitignore"] = rest.encode()
        plan.actions.append("remove the earlier setup's section of .gitignore")
    else:
        plan.removals.append(".gitignore")
        plan.actions.append("remove .gitignore")


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def exclude_file(root: Path) -> Path | None:
    try:
        path = Path(git("rev-parse", "--git-path", "info/exclude", cwd=root).strip())
    except (OSError, subprocess.CalledProcessError):
        return None
    return path if path.is_absolute() else root / path


def plan_exclude(plan: Plan):
    """Keep the temporary folder out of Git in this clone only, so the repository carries no trace of it."""
    path = exclude_file(plan.root)
    if path is None:
        return
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    if EXCLUDE not in lines:
        plan.exclude = path


def write_exclude(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(text + ("" if not text or text.endswith("\n") else "\n") + EXCLUDE + "\n", encoding="utf-8")


def gh(*args: str, cwd: Path) -> str:
    return subprocess.run(["gh", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def plan_labels(plan: Plan):
    """Make the earlier setup's type label descriptions neutral, and retire its process labels."""
    try:
        found = {label["name"].casefold(): label for label in json.loads(
            gh("label", "list", "--limit", "500", "--json", "name,description", cwd=plan.root))}
        for name, description in TYPE_LABELS.items():
            label = found.get(name.casefold())
            if label is not None and (label.get("description") or "") == LEGACY_LABELS[name]:
                plan.github.append(("update the description of label " + name,
                                    ["label", "edit", label["name"], "--description", description]))
        for name, description in LEGACY_LABELS.items():
            label = found.get(name.casefold())
            if name in TYPE_LABELS or label is None:
                continue
            if (label.get("description") or "") != description:
                plan.notes.append(f"label {label['name']} was changed after setup created it; left as it is")
                continue
            plan_issues(plan, label["name"])
            plan.github.append(("delete label " + label["name"], ["label", "delete", label["name"], "--yes"]))
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as error:
        reason = (getattr(error, "stderr", "") or str(error)).strip().splitlines() or [""]
        plan.notes.append("labels not checked: GitHub is unavailable (" + reason[-1] + ")")


def plan_issues(plan: Plan, label: str):
    """Carry what a process label meant over to the Issues that carry it, before the label goes."""
    if label == "in-progress":
        state, prefix = "open", None
    elif label in LEGACY_LABEL_TITLES:
        state, prefix = LEGACY_LABEL_TITLES[label]
    elif label == "design":
        state, prefix = "open", ""
    else:
        return
    issues = json.loads(gh("issue", "list", "--label", label, "--state", state, "--limit", "500",
                           "--json", "number,title,assignees", cwd=plan.root))
    for issue in issues:
        number = str(issue["number"])
        if label == "in-progress" and not issue.get("assignees"):
            plan.github.append((f"assign #{number} to you (it was labelled in-progress)",
                                ["issue", "edit", number, "--add-assignee", "@me"]))
        elif label == "design":
            plan.notes.append(f"#{number} was labelled design: start its UI design section with `Design Epic:`")
        elif prefix and not issue["title"].startswith(prefix):
            plan.github.append((f"retitle #{number} to start with {prefix.strip()} (it was labelled {label})",
                                ["issue", "edit", number, "--title", prefix + issue["title"]]))


def workflow_on(root: Path, flag: bool | None, workflow: str, manifest: dict, key: str, set_up: bool) -> bool:
    """An explicit flag wins; then the earlier setup's record; then, once set up, whether the workflow is present."""
    if flag is not None:
        return flag
    if isinstance(manifest.get(key), bool):
        return manifest[key]
    if set_up:
        return current(root, workflow) is not None
    return True


def build(root: Path, replace: bool = False, labels: bool = True, docs_workflow: bool | None = None,
          standards_workflow: bool | None = None) -> Plan:
    plan = Plan(root)
    manifest = load_manifest(root)
    set_up = START in (text_of(root, INSTRUCTIONS) or "")
    plan_legacy_files(plan, manifest, replace)
    for flag, workflow, script, key in ((docs_workflow, DOCS_WORKFLOW, "knowledge.py", "docs_workflow"),
                                        (standards_workflow, STANDARDS_WORKFLOW, "standards.py", "standards_workflow")):
        pairs = ((workflow, (ASSETS / "github/workflows" / Path(workflow).name).read_bytes()),
                 (VENDORED + script, (SCRIPTS / script).read_bytes()))
        on = workflow_on(root, flag, workflow, manifest, key, set_up)
        for relative, content in pairs:
            if on:
                plan_file(plan, relative, content, replace)
            else:
                plan_removal(plan, relative, content, replace)
    plan_section(plan, manifest, INSTRUCTIONS, INSTRUCTIONS, INSTRUCTIONS_BODY, replace)
    plan_section(plan, manifest, "pull_request_template", pr_template_path(root),
                 (ASSETS / "github/pull_request_template.md").read_text(encoding="utf-8").strip("\n"), replace)
    plan_app_config(plan)
    plan_settings(plan)
    plan_gitignore(plan, manifest, replace)
    plan_exclude(plan)
    if labels:
        plan_labels(plan)
    plan.actions.extend(action for action, _ in plan.github)
    return plan


def apply(plan: Plan):
    for relative, content in plan.writes.items():
        path = destination(plan.root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    for relative in plan.removals:
        path = destination(plan.root, relative)
        path.unlink()
        for parent in path.parents:
            if parent == plan.root or any(parent.iterdir()):
                break
            parent.rmdir()
    if plan.exclude:
        write_exclude(plan.exclude)
    for action, args in plan.github:
        try:
            gh(*args, cwd=plan.root)
        except (OSError, subprocess.CalledProcessError) as error:
            plan.notes.append(f"could not {action}: {(getattr(error, 'stderr', '') or str(error)).strip()}")


def paths(root: Path) -> list[str]:
    """Every path setup writes or removes, for checking that a setup is committed."""
    return sorted({DOCS_WORKFLOW, STANDARDS_WORKFLOW, VENDORED + "knowledge.py", VENDORED + "standards.py",
                   INSTRUCTIONS, pr_template_path(root), LEGACY_MANIFEST, *LEGACY_FORMS, *LEGACY_WORKFLOWS,
                   *LEGACY_WORKFLOWS.values(), LEGACY_SETTINGS, LEGACY_APP_CONFIG, ".gitignore"})


def repository_root(path: Path) -> Path:
    try:
        return Path(git("rev-parse", "--show-toplevel", cwd=path).strip()).resolve()
    except (OSError, subprocess.CalledProcessError):
        return path.resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="repository to prepare (default: current)")
    parser.add_argument("--dry-run", action="store_true", help="list the changes and write nothing")
    parser.add_argument("--check", action="store_true",
                        help="like --dry-run, but exit 1 when a committed file or an earlier setup's label would change")
    parser.add_argument("--replace", action="store_true", help="overwrite edited managed files and sections")
    parser.add_argument("--no-labels", dest="labels", action="store_false", help="do not migrate the earlier setup's labels")
    parser.add_argument("--paths", action="store_true", help="print every path setup writes or removes, and exit")
    parser.add_argument("--exclude", action="store_true",
                        help=f"only add {EXCLUDE} to this clone's Git exclude file, and exit")
    for name in ("docs", "standards"):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(f"--{name}-workflow", dest=f"{name}_workflow", action="store_true", default=None,
                           help=f"install the {name} check workflow (the default)")
        group.add_argument(f"--no-{name}-workflow", dest=f"{name}_workflow", action="store_false",
                           help=f"remove the {name} check workflow; later runs keep it off while it is absent")
    args = parser.parse_args(argv)
    root = repository_root(args.project)
    if args.paths:
        print("\n".join(paths(root)))
        return 0
    if args.exclude:
        path = exclude_file(root)
        if path is None:
            print("Refused: not a Git repository: " + str(root), file=sys.stderr)
            return 1
        if EXCLUDE not in (path.read_text(encoding="utf-8").splitlines() if path.is_file() else []):
            write_exclude(path)
        return 0
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
    actions = plan.actions + ([f"add {EXCLUDE} to {plan.exclude} (this clone only)"] if plan.exclude else [])
    prefix = "Would " if preview else ""
    for action in actions:
        print(prefix + action if preview else action[:1].upper() + action[1:])
    if not actions:
        print("Nothing to change.")
    for note in plan.notes:
        print("Note: " + note)
    return 1 if args.check and plan.actions else 0


if __name__ == "__main__":
    sys.exit(main())
