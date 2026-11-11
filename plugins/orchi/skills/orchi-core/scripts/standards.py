#!/usr/bin/env python3
"""Check that ENGINEERING.md's declared checks run in CI, and print the ruleset that requires them."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime
import json
from pathlib import Path
import re
import sys

DOCUMENT = "ENGINEERING.md"
WORKFLOWS = ".github/workflows"
BLOCKING = {"yes": 2, "weekly": 1, "no": 0}
THRESHOLD = re.compile(r"^(>=|<=)\s*(\d+(?:\.\d+)?)\s*%?$")


@dataclass
class Finding:
    rule: str
    where: str
    detail: str

    def text(self) -> str:
        return f"{self.where}: {self.rule}: {self.detail}"


def cell(text: str) -> str:
    return text.strip().replace("`", "").strip()


def table(text: str, heading: str) -> list[dict[str, str]]:
    """The first Markdown table under `## <heading>`, as rows keyed by header."""
    section = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not section:
        return []
    lines = [line.strip() for line in section.group(1).splitlines()]
    rows = [line for line in lines if line.startswith("|")]
    if len(rows) < 2:
        return []
    header = [cell(part) for part in rows[0].strip("|").split("|")]
    result = []
    for line in rows[2:]:
        parts = [cell(part) for part in line.strip("|").split("|")]
        if any(parts):
            result.append(dict(zip(header, parts + [""] * (len(header) - len(parts)))))
    return result


def checks(text: str) -> list[dict[str, str]]:
    return table(text, "Checks")


def exceptions(text: str) -> list[dict[str, str]]:
    return table(text, "Exceptions")


def configs(row: dict[str, str]) -> list[str]:
    return [path.strip() for path in row.get("Config", "").split(",") if path.strip() not in {"", "-"}]


def normalize(text: str) -> str:
    return " ".join(text.split())


def workflow_jobs(root: Path) -> dict[str, dict]:
    """Jobs of every workflow: id -> its file, its text, its status check name, and whether the workflow is scheduled."""
    jobs: dict[str, dict] = {}
    folder = root / WORKFLOWS
    for path in sorted(folder.glob("*.y*ml")) if folder.is_dir() else []:
        lines = path.read_text(encoding="utf-8").splitlines()
        scheduled = any(re.match(r"^\s+schedule:", line) for line in lines)
        inside, indent, current = False, None, None
        for line in lines:
            if re.match(r"^jobs:\s*(#.*)?$", line):
                inside = True
                continue
            if inside and re.match(r"^\S", line):
                inside = False
            if not inside or not line.strip() or line.lstrip().startswith("#"):
                if current and inside:
                    jobs[current]["text"] += line + "\n"
                continue
            width = len(line) - len(line.lstrip())
            indent = width if indent is None else indent
            match = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(#.*)?$", line)
            if width == indent and match:
                current = match.group(1)
                jobs[current] = {"file": path.relative_to(root).as_posix(), "text": "", "name": current,
                                 "scheduled": scheduled}
            elif current:
                jobs[current]["text"] += line + "\n"
                named = re.match(r"^\s+name:\s*['\"]?(.+?)['\"]?\s*$", line)
                if named and width == indent + 2:
                    jobs[current]["name"] = named.group(1)
    return jobs


def expiry(row: dict[str, str]) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(row.get("Expires", ""))
    except ValueError:
        return None


def check(root: Path, today: datetime.date) -> dict:
    document = root / DOCUMENT
    if not document.is_file():
        return {"ok": True, "findings": [], "note": f"No {DOCUMENT}; nothing to check."}
    text = document.read_text(encoding="utf-8")
    rows, jobs, findings = checks(text), workflow_jobs(root), []
    if not rows:
        findings.append(Finding("checks", DOCUMENT, "no Checks table"))
    for row in rows:
        name, job, command = row.get("Check", ""), row.get("CI job", ""), normalize(row.get("Command", ""))
        blocking, threshold = row.get("Blocking", "").lower(), row.get("Threshold", "-")
        if blocking not in BLOCKING:
            findings.append(Finding("checks", DOCUMENT, f"{name}: Blocking must be yes, no, or weekly"))
        if threshold != "-" and not THRESHOLD.match(threshold):
            findings.append(Finding("checks", DOCUMENT, f"{name}: Threshold must be - or >= or <= a number"))
        if job not in jobs:
            findings.append(Finding("checks", DOCUMENT, f"{name}: no CI job `{job}` in {WORKFLOWS}/"))
        else:
            if command and command not in normalize(jobs[job]["text"]):
                findings.append(Finding("checks", jobs[job]["file"], f"{name}: job `{job}` does not run `{command}`"))
            if blocking == "weekly" and not jobs[job]["scheduled"]:
                findings.append(Finding("checks", jobs[job]["file"], f"{name}: job `{job}` is not scheduled"))
        for path in configs(row):
            if not (root / path).is_file():
                findings.append(Finding("checks", path, f"{name}: configuration file is not committed"))
    for row in exceptions(text):
        date = expiry(row)
        if date is None:
            findings.append(Finding("exceptions", row.get("Where", ""), f"{row.get('Rule', '')}: Expires is not a date"))
        elif date < today:
            findings.append(Finding("exceptions", row.get("Where", ""), f"{row.get('Rule', '')}: expired on {date}"))
    return {"ok": not findings, "findings": [f.text() for f in findings]}


def ruleset(root: Path) -> dict:
    """A GitHub ruleset for the default branch that requires every blocking check."""
    document = root / DOCUMENT
    if not document.is_file():
        raise ValueError(f"No {DOCUMENT}")
    jobs = workflow_jobs(root)
    contexts = sorted({jobs[row["CI job"]]["name"] if row.get("CI job") in jobs else row.get("CI job", "")
                       for row in checks(document.read_text(encoding="utf-8"))
                       if row.get("Blocking", "").lower() == "yes" and row.get("CI job")})
    return {
        "name": "Orchi standards",
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "required_linear_history"},
            {"type": "pull_request", "parameters": {
                "required_approving_review_count": 0, "dismiss_stale_reviews_on_push": False,
                "require_code_owner_review": False, "require_last_push_approval": False,
                "required_review_thread_resolution": False, "allowed_merge_methods": ["squash"]}},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": False,
                "required_status_checks": [{"context": context} for context in contexts]}},
        ],
    }


def report(result: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("note"):
            print(result["note"])
        for line in result["findings"]:
            print(line)
        if result["ok"] and not result.get("note"):
            print("ok")
    return 0 if result["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    commands = parser.add_subparsers(dest="command", required=True)
    checked = commands.add_parser("check", help="Every declared check runs in CI, and no exception has expired")
    checked.add_argument("--today", type=datetime.date.fromisoformat, default=datetime.date.today(),
                         help=argparse.SUPPRESS)
    commands.add_parser("ruleset", help="Print the GitHub ruleset that requires every blocking check")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "check":
            return report(check(root, args.today), args.json)
        print(json.dumps(ruleset(root), indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f"standards.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
