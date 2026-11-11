"""Behavioral tests for standards.py: declared checks against CI, and the ruleset."""
import datetime
import json
import subprocess

import pytest

from conftest import AGENTS, ASSETS, REFERENCES, SKILLS
import standards

TODAY = datetime.date(2026, 10, 27)
DOCUMENT = """# Engineering

## Checks

| Check | Tool | Command | CI job | Config | Threshold | Blocking |
| --- | --- | --- | --- | --- | --- | --- |
| Lint | ESLint | `pnpm lint` | lint | eslint.config.mjs | - | yes |
| Coverage | Vitest | `pnpm coverage:changed` | test | - | >= 90 | yes |
| File size | ESLint | `pnpm lint` | lint | eslint.config.mjs | <= 300 | yes |
| Mutation | Stryker | `pnpm mutation` | mutation | - | - | weekly |

## Exceptions

| Rule | Where | Reason | Expires |
| --- | --- | --- | --- |
{exceptions}
"""
CI = """name: CI
on:
  pull_request:
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: pnpm lint
  test:
    name: Unit tests
    runs-on: ubuntu-latest
    steps:
      - run: |
          pnpm test
          pnpm coverage:changed
"""
WEEKLY = """name: Weekly
on:
  schedule:
    - cron: "0 6 * * 1"
jobs:
  mutation:
    runs-on: ubuntu-latest
    steps:
      - run: pnpm mutation
"""


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout


def commit(root, message='change'):
    git(root, 'add', '-A')
    git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', message)


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q', '-b', 'main')
    write(tmp_path, 'ENGINEERING.md', DOCUMENT.format(exceptions=''))
    write(tmp_path, '.github/workflows/ci.yml', CI)
    write(tmp_path, '.github/workflows/weekly.yml', WEEKLY)
    write(tmp_path, 'eslint.config.mjs', 'export default [{ rules: { "no-console": "error" } }];\n')
    write(tmp_path, 'src/cart.ts', 'export const total = (a: number, b: number) => a + b;\n')
    write(tmp_path, 'src/cart.test.ts', 'test("adds", () => {\n  expect(total(1, 2)).toBe(3);\n  expect(total(0, 0)).toBe(0);\n});\n')
    commit(tmp_path, 'baseline')
    git(tmp_path, 'checkout', '-qb', 'feature')
    return tmp_path


def test_check_passes_when_every_declared_check_runs_in_ci(repo):
    assert standards.check(repo, TODAY) == {'ok': True, 'findings': []}


def test_check_reports_missing_job_command_config_and_schedule(repo):
    write(repo, '.github/workflows/ci.yml', CI.replace('pnpm lint', 'pnpm eslint .'))
    write(repo, '.github/workflows/weekly.yml', WEEKLY.replace('schedule:\n    - cron: "0 6 * * 1"', 'pull_request:'))
    (repo / 'eslint.config.mjs').unlink()
    text = (repo / 'ENGINEERING.md').read_text()
    write(repo, 'ENGINEERING.md', text.replace('| Mutation |', '| Dead code | knip | `pnpm knip` | dead-code | - | - | yes |\n| Mutation |'))
    findings = standards.check(repo, TODAY)['findings']
    assert '.github/workflows/ci.yml: checks: Lint: job `lint` does not run `pnpm lint`' in findings
    assert 'eslint.config.mjs: checks: Lint: configuration file is not committed' in findings
    assert 'ENGINEERING.md: checks: Dead code: no CI job `dead-code` in .github/workflows/' in findings
    assert '.github/workflows/weekly.yml: checks: Mutation: job `mutation` is not scheduled' in findings


def test_check_fails_on_an_expired_or_undated_exception(repo):
    rows = '| no-console | src/log.ts | CLI output | 2026-10-01 |\n| noqa | tools/*.py | generated | soon |'
    write(repo, 'ENGINEERING.md', DOCUMENT.format(exceptions=rows))
    findings = standards.check(repo, TODAY)['findings']
    assert findings == ['src/log.ts: exceptions: no-console: expired on 2026-10-01',
                        'tools/*.py: exceptions: noqa: Expires is not a date']


def test_without_engineering_document_nothing_is_checked(tmp_path):
    git(tmp_path, 'init', '-q')
    assert standards.check(tmp_path, TODAY)['note'] == 'No ENGINEERING.md; nothing to check.'


def test_ruleset_requires_blocking_jobs_by_their_status_check_names(repo, capsys):
    assert standards.main(['--root', str(repo), 'ruleset']) == 0
    ruleset = json.loads(capsys.readouterr().out)
    required = next(rule for rule in ruleset['rules'] if rule['type'] == 'required_status_checks')
    assert required['parameters']['required_status_checks'] == [{'context': 'Unit tests'}, {'context': 'lint'}]
    assert {rule['type'] for rule in ruleset['rules']} >= {'deletion', 'non_fast_forward', 'required_linear_history'}


def test_main_exits_one_on_findings_and_prints_them(repo, capsys):
    (repo / 'eslint.config.mjs').unlink()
    assert standards.main(['--root', str(repo), 'check', '--today', '2026-10-27']) == 1
    assert 'configuration file is not committed' in capsys.readouterr().out


def test_template_declares_valid_checks_and_no_design_check():
    text = (ASSETS / 'standards/ENGINEERING.md').read_text()
    rows = standards.checks(text)
    assert rows and all(row['Blocking'] in standards.BLOCKING for row in rows)
    assert all(row['Threshold'] == '-' or standards.THRESHOLD.match(row['Threshold']) for row in rows)
    # The design audit happens in review, not in CI.
    assert 'design' not in {row['CI job'] for row in rows} and 'impeccable' not in text.lower()
    assert 'UI quality' not in (REFERENCES / 'standards.md').read_text()
    assert standards.exceptions(text) == []


def prose(path):
    return " ".join(path.read_text().split())


def test_standards_wording_agrees_across_planning_delivery_and_roles():
    """Text, not behavior: the standards track is wired into every stage that reads it."""
    planning, plan = prose(REFERENCES / 'planning.md'), prose(SKILLS / 'orchi-plan/SKILL.md')
    assert "every Initiative, Epic, and Task that writes product code is blocked by it. A design Epic is not" in planning
    assert "Never ask the user to choose a tool, threshold, or code layout" in planning
    assert "plan its first run first and the rest blocked by it" in plan
    assert "While the project's [first run](planning.md#engineering-standards) is open, is blocked by it" in prose(
        REFERENCES / 'readiness.md')
    review = prose(REFERENCES / 'review-delivery.md')
    assert "the range must not weaken a gate as [gate integrity](standards.md#gate-integrity) lists" in review
    assert "in its Exceptions section in plain words" in review
    assert "## Exceptions" in (ASSETS / 'github/pull_request_template.md').read_text()
    assert "relay its Exceptions to the user in plain words" in prose(SKILLS / 'orchi/SKILL.md')
    for role in ('orchi-implementer', 'orchi-fixer', 'orchi-designer'):
        assert "adding a suppression, loosening a check, or recording an exception" in prose(
            AGENTS / f'{role}.agent.md')
    standards_skill = prose(SKILLS / 'orchi-standards/SKILL.md')
    assert "never ask about tools, thresholds, or layout" in standards_skill
    assert "the product\nconstraints are the user's, or Orchi's in autonomous mode, except money and access".replace("\n", " ") in standards_skill
    assert "| Planner | `orchi-standards` |" in prose(REFERENCES / 'pool.md')


def test_a_new_project_starts_with_its_first_run_and_adds_checks_as_needed():
    """Text, not behavior: no setup Epic; each check lands with the first change that needs it."""
    reference, skill = prose(REFERENCES / 'standards.md'), prose(SKILLS / 'orchi-standards/SKILL.md')
    assert "A new project has no setup Epic" in reference and "## Hardening" in reference
    assert "in the first Task whose change needs it, as the `Lands with` column says" in reference
    assert "| Check | TypeScript | Python | Blocking | Lands with |" in reference
    assert "blocked by the first run, so a planner plans the hardening Epic once there is code to check" in reference
    assert "A proof of concept gets only the core checks" in reference and "A proof of concept gets no ruleset" in reference
    assert "only when its configuration is the project's own" in reference
    assert "sets the standards: continue with [orchi-plan]" in skill
    assert "foundation" not in " ".join(prose(p) for p in (
        REFERENCES / 'standards.md', REFERENCES / 'planning.md', SKILLS / 'orchi-standards/SKILL.md',
        SKILLS / 'orchi-plan/SKILL.md', SKILLS / 'orchi-design/SKILL.md', SKILLS / 'orchi-deliver/SKILL.md')).lower()
    planning = prose(REFERENCES / 'planning.md')
    assert "through the real services the exploration's prototypes proved" in planning
    exploration = prose(REFERENCES / 'exploration.md')
    assert "Build one that proves an assumption without asking" in exploration
    assert "Agents decide exceptions, never the user" in reference
    template = (ASSETS / 'standards/ENGINEERING.md').read_text()
    for license_id in ('CC-BY-4.0', 'MPL-2.0', 'BlueOak-1.0.0'):
        assert license_id in template, license_id
    assert "`--production --onlyAllow`" in reference
