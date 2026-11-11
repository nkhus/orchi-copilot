"""Behavioral tests for `knowledge.py work`, and the wording that keeps project context current."""
import os
import subprocess
import sys

import pytest

from conftest import ASSETS, REFERENCES, SCRIPTS, SKILLS
from knowledge import Documents, work_files

SCRIPT = SCRIPTS / 'knowledge.py'
MAP = """# Documentation

## Ownership

| Code | Pages | Area |
| --- | --- | --- |
| `src/cart/**` | `docs/cart/README.md`, `docs/product/cart.md` | Cart |
| `src/auth/*.ts` | `docs/auth/README.md` | Sign-in |
"""


def git(root, *args, when=None):
    env = dict(os.environ)
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True, env=env).stdout


def commit(root, when=None):
    git(root, 'add', '-A')
    git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'change', when=when)


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q', '-b', 'main')
    write(tmp_path, 'docs/README.md', MAP)
    write(tmp_path, 'docs/cart/README.md', '# Cart\n')
    write(tmp_path, 'docs/product/cart.md', '# Cart\n')
    write(tmp_path, 'docs/auth/README.md', '# Sign-in\n')
    write(tmp_path, 'src/cart/total.ts', 'export const total = 1;\n')
    write(tmp_path, 'src/auth/login.ts', 'export const login = 1;\n')
    commit(tmp_path, when='2026-10-01T10:00:00')
    git(tmp_path, 'checkout', '-qb', 'feature')
    return tmp_path


def test_working_documents_are_found_anywhere_under_docs_work(repo):
    assert work_files(Documents(repo)) == []
    write(repo, 'docs/work/pay-tokens/research/vault.md', '# Vault\n')
    write(repo, 'docs/work/pay-tokens/data.json', '{}\n')
    assert work_files(Documents(repo)) == ['docs/work/pay-tokens/data.json', 'docs/work/pay-tokens/research/vault.md']


def run(repo, *args, body=''):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True,
                          env={**os.environ, 'PR_BODY': body})


def test_work_command_exits_by_its_findings(repo):
    assert run(repo, 'work').returncode == 0
    write(repo, 'docs/work/cart/README.md', '# Plan\n')
    commit(repo)
    work = run(repo, 'work')
    assert work.returncode == 1 and 'docs/work/cart/README.md: working documents never reach this branch' in work.stdout


def prose(path):
    return " ".join(path.read_text().split())


def test_context_wording_agrees_across_exploration_planning_and_delivery():
    """Text, not behavior: working folders, decision fates, promotion, and the checks are wired through."""
    knowledge = prose(REFERENCES / 'knowledge.md')
    assert "a decision that no longer holds is not kept" in knowledge
    assert "`knowledge.py work` fails while anything under `docs/work/` is present" in knowledge
    assert "never by the work that produced them" in knowledge
    exploration = prose(REFERENCES / 'exploration.md')
    assert "one branch, `explore/<slug>` from main, holds its working folder `docs/work/<slug>/`" in exploration
    assert "Write each verified finding to `research/<question>.md`" in exploration
    assert "creates its Initiative or Epic branch from `explore/<slug>`" in exploration
    assert "give each of its decisions (D1, D2, ...) a fate" in prose(REFERENCES / 'planning.md')
    plan = prose(SKILLS / 'orchi-plan/SKILL.md')
    assert "`docs/work/<tag>-<slug>/README.md`" in plan and "from `explore/<slug>`" in plan
    review = prose(REFERENCES / 'review-delivery.md')
    assert "`knowledge.py work` must pass" in review and "move the rest of the working folder there and delete it" in review
    docs = (ASSETS / 'github/workflows/orchi-docs.yml').read_text()
    assert 'knowledge.py stale' not in docs and 'knowledge.py behavior' not in docs
    assert "if: github.actor != 'dependabot[bot]'" in docs
    assert 'if: github.base_ref == github.event.repository.default_branch' in docs
    standards_workflow = (ASSETS / 'github/workflows/orchi-standards.yml').read_text()
    assert 'ratchet' not in standards_workflow and 'knowledge.py stale' not in standards_workflow
    for path in SKILLS.rglob('*'):
        if path.is_file() and path.suffix in {'.md', '.yml', '.py'}:
            assert 'docs/initiatives/' not in path.read_text(), path
