"""Behavioral tests for snapshot isolation, reads, and documentation validation."""
import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from conftest import SCRIPTS
from knowledge import Documents, anchors, impact, lint, main, search


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_git('init', '-q')
        (self.root / 'docs').mkdir()
        (self.root / 'docs/README.md').write_text('# Guide\n\n[Accounts](accounts.md#session)\n')
        (self.root / 'docs/accounts.md').write_text('# Accounts\n\n## Session\nOriginal session behavior.\n')
        self.run_git('add', '.')
        self.run_git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'baseline')

    def run_git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.PIPE, text=True)

    def test_snapshot_does_not_read_working_changes(self):
        (self.root / 'docs/accounts.md').write_text('# Accounts\nChanged behavior.\n')
        (self.root / 'docs/new.md').write_text('# New\nUncommitted finding.\n')
        snapshot = Documents(self.root, 'HEAD')
        self.assertIn('Original', snapshot.read('docs/accounts.md'))
        self.assertNotIn('docs/new.md', snapshot.names)
        working = Documents(self.root)
        self.assertIn('Changed', working.read('docs/accounts.md'))
        self.assertIn('docs/new.md', working.names)
        self.assertTrue(search(snapshot, 'original session', 10))
        self.assertFalse(search(working, 'original session', 10))

    def test_bad_ref_and_outside_file_fail(self):
        with self.assertRaises(subprocess.CalledProcessError):
            Documents(self.root, 'missing-branch')
        with self.assertRaises(ValueError):
            Documents(self.root).read('../outside.md')

    def test_links_anchors_references_and_examples(self):
        self.assertEqual(lint(Documents(self.root)), [])
        (self.root / 'docs/README.md').write_text(
            '# Guide\n[Missing](absent.md)\n[Bad](accounts.md#absent)\n'
            '[Account][account]\n[account]: accounts.md#session\n[PAY][TOKEN] is literal text\n'
            '```md\n[Example](not-real.md)\n```\n`[Code](not-real.md)`\n')
        errors = lint(Documents(self.root))
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(any('absent.md' in error for error in errors))
        self.assertTrue(any('#absent' in error for error in errors))
        self.assertEqual(anchors('# A\n# A\n```\n# Fake\n```\n## `Code`'), {'a', 'a-1', 'code'})

    def test_cli_hash_rejects_changed_content(self):
        doc = Documents(self.root)
        digest = search(doc, 'original session', 1)[0]['sha256']
        (self.root / 'docs/accounts.md').write_text('# Changed\n')
        with patch('sys.argv', ['knowledge.py', '--repo', str(self.root), 'get', 'docs/accounts.md', '--sha256', digest]):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(), 2)

    def test_corpus_skips_installed_skills_and_honours_path_scope(self):
        for relative in ('.agents/skills/orchi-core/SKILL.md', '.github/agents/orchi-scout.agent.md',
                         '.github/orchi/notes.md', 'node_modules/pkg/README.md', 'README.md'):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('# Session\n[Broken](absent.md)\n')
        docs = Documents(self.root)
        self.assertIn('README.md', docs.names)
        self.assertNotIn('.agents/skills/orchi-core/SKILL.md', docs.names)
        self.assertNotIn('.github/agents/orchi-scout.agent.md', docs.names)
        self.assertNotIn('.github/orchi/notes.md', docs.names)
        self.assertNotIn('node_modules/pkg/README.md', docs.names)
        self.assertEqual(Documents(self.root, prefixes=['docs']).names, ['docs/README.md', 'docs/accounts.md'])
        self.assertEqual(lint(Documents(self.root, prefixes=['docs/'])), [])

    def test_lint_since_reports_only_new_errors(self):
        (self.root / 'docs/README.md').write_text('# Guide\n[Old](gone.md)\n')
        self.run_git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qam', 'existing debt')
        (self.root / 'docs/README.md').write_text('# Guide\nIntro moved the old link down.\n\n[Old](gone.md)\n')
        output = io.StringIO()
        with patch('sys.argv', ['knowledge.py', '--repo', str(self.root), 'lint', '--since', 'HEAD']), \
                contextlib.redirect_stdout(output):
            self.assertEqual(main(), 0)
        self.assertIn('1 pre-existing ignored', output.getvalue())
        (self.root / 'docs/accounts.md').write_text('# Accounts\n[New](missing.md)\n')
        with patch('sys.argv', ['knowledge.py', '--repo', str(self.root), 'lint', '--since', 'HEAD']), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(), 1)
        self.assertIn('docs/accounts.md:2: missing local target missing.md', output.getvalue())
        self.assertNotIn('gone.md', output.getvalue())

    def test_documentation_impact_requires_filled_section(self):
        self.assertIsNotNone(impact('## Summary\nDone.'))
        self.assertIsNotNone(impact('## Documentation impact\n<!-- pages or reason -->\n\n## Handoff\n'))
        self.assertIsNotNone(impact('## Documentation impact\nN/A\n'))
        self.assertIsNone(impact('## Documentation impact\r\n- Updated docs/accounts.md\r\n## Handoff\r\n'))
        self.assertIsNone(impact('### documentation impact\nNone: internal refactor with no behavior change.'))

    def test_search_and_lint_do_not_create_files(self):
        before = self.run_git('status', '--porcelain', '--untracked-files=all')
        docs = Documents(self.root, 'HEAD')
        search(docs, 'session', 1)
        lint(docs)
        self.assertEqual(self.run_git('status', '--porcelain', '--untracked-files=all'), before)

    def test_vendored_scripts_run_from_the_repository_root(self):
        vendored = self.root / '.github/orchi/scripts'
        vendored.mkdir(parents=True)
        for name in ('knowledge.py', 'standards.py'):
            shutil.copy(SCRIPTS / name, vendored / name)
        self.run_git('add', '.')
        self.run_git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'vendor')

        def run(*args):
            return subprocess.run([sys.executable, *args], cwd=self.root, capture_output=True, text=True)

        lint_run = run('.github/orchi/scripts/knowledge.py', 'lint', '--since', 'HEAD')
        self.assertEqual(lint_run.returncode, 0, lint_run.stderr)
        self.assertIn('2 files, 0 errors', lint_run.stdout)
        self.assertEqual(run('.github/orchi/scripts/knowledge.py', 'work').returncode, 0)
        self.assertIn('No ENGINEERING.md', run('.github/orchi/scripts/standards.py', 'check').stdout)


if __name__ == '__main__':
    unittest.main()
