"""Source validation of the marketplace, the plugin, and the repository documentation."""
from pathlib import Path
import importlib.util
import json
import shutil

import pytest

from conftest import ROOT


def load_validator():
    spec = importlib.util.spec_from_file_location('validate_package', ROOT / 'tools/validate_package.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def source_copy(tmp_path):
    """A disposable copy of the source tree, so validation failures never touch the real files."""
    copy = tmp_path / 'source'
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns('.git', *validator.IGNORED, '*.pyc'))
    return copy


def test_source_validation():
    report = validator.validate()
    assert report['ok'], report['errors']


def test_marketplace_points_at_the_plugin():
    market = json.loads((ROOT / '.github/plugin/marketplace.json').read_text())
    plugin = json.loads((ROOT / 'plugins/orchi/plugin.json').read_text())
    assert [entry['source'] for entry in market['plugins']] == ['./plugins/orchi']
    assert market['plugins'][0]['version'] == plugin['version'] == market['metadata']['version']


@pytest.mark.parametrize('linking, target', [
    ('plugins/orchi/skills/orchi-core/references/execution.md', 'plugins/orchi/skills/orchi-core/references/planning.md'),
    ('docs/testing.md', 'docs/installation.md'),
])
def test_renamed_heading_breaks_validation(tmp_path, linking, target):
    copy = source_copy(tmp_path)
    with (copy / target).open('a', encoding='utf-8') as stream:
        stream.write('\n## Probe heading\n\nText.\n')
    with (copy / linking).open('a', encoding='utf-8') as stream:
        stream.write('\nSee [the probe](' + Path(target).name + '#probe-heading).\n')
    report = validator.validate(copy)
    assert report['ok'], report['errors']
    text = (copy / target).read_text(encoding='utf-8')
    (copy / target).write_text(text.replace('## Probe heading', '## Renamed probe'), encoding='utf-8')
    report = validator.validate(copy)
    assert any(error.startswith(linking + ':') and 'missing anchor' in error for error in report['errors']), report['errors']


def test_unowned_plugin_file_breaks_validation(tmp_path):
    copy = source_copy(tmp_path)
    (copy / 'plugins/orchi/notes.md').write_text('# Notes\n', encoding='utf-8')
    report = validator.validate(copy)
    assert 'File under plugins/ has no owning page in docs/README.md: plugins/orchi/notes.md' in report['errors']


def test_installed_link_out_of_the_skills_breaks_validation(tmp_path):
    copy = source_copy(tmp_path)
    with (copy / 'plugins/orchi/skills/orchi-core/references/github.md').open('a', encoding='utf-8') as stream:
        stream.write('\nSee [the guide](../../../../../docs/workflow.md).\n')
    report = validator.validate(copy)
    assert any('installed reference leaves the skills folder' in error for error in report['errors']), report['errors']


def test_third_party_import_in_a_bundled_script_breaks_validation(tmp_path):
    copy = source_copy(tmp_path)
    script = copy / 'plugins/orchi/skills/orchi-core/scripts/status.py'
    script.write_text(script.read_text(encoding='utf-8') + '\nimport yaml\n', encoding='utf-8')
    report = validator.validate(copy)
    assert any('only the standard library: yaml' in error for error in report['errors']), report['errors']


@pytest.mark.parametrize('edit, message', [
    (lambda text: text.replace('user-invocable: false', 'user-invocable: true'), 'hidden from the menu'),
    (lambda text: text.replace('name: orchi-plan', 'name: orchi-plan\nlicense: MIT'), 'undocumented skill frontmatter'),
])
def test_skill_frontmatter_is_checked(tmp_path, edit, message):
    copy = source_copy(tmp_path)
    skill = copy / 'plugins/orchi/skills/orchi-plan/SKILL.md'
    skill.write_text(edit(skill.read_text(encoding='utf-8')), encoding='utf-8')
    report = validator.validate(copy)
    assert any(message in error for error in report['errors']), report['errors']


def test_read_only_agent_with_edit_breaks_validation(tmp_path):
    copy = source_copy(tmp_path)
    agent = copy / 'plugins/orchi/agents/orchi-reviewer.agent.md'
    meta, body = validator.frontmatter(agent.read_text(encoding='utf-8'))
    meta['tools'] = list(meta['tools']) + ['edit']
    agent.write_text('---\n' + validator.yaml.safe_dump(meta, sort_keys=False) + '---' + body, encoding='utf-8')
    report = validator.validate(copy)
    assert 'orchi-reviewer: a read-only role must not have edit' in report['errors']


def test_claude_outside_a_model_id_breaks_validation(tmp_path):
    copy = source_copy(tmp_path)
    with (copy / 'plugins/orchi/skills/orchi-core/references/github.md').open('a', encoding='utf-8') as stream:
        stream.write('\nWrite it to CLAUDE.md.\n')
    report = validator.validate(copy)
    assert any('names Claude outside a model ID' in error for error in report['errors']), report['errors']


EXTENSION = 'plugins/orchi/extensions/orchi-canvases/'


@pytest.mark.parametrize('path, edit, message', [
    ('lib/server.mjs', lambda t: t.replace('listen(0, "127.0.0.1"', 'listen(0, "0.0.0.0"'), 'listen on 127.0.0.1 port 0'),
    ('lib/board.mjs', lambda t: t + '\nconsole.log("debug");\n', 'console output corrupts'),
    ('lib/board.mjs', lambda t: t.replace('name: "refresh"', 'name: "canvas.refresh"'), 'are reserved'),
    ('lib/store.mjs', lambda t: 'import express from "express";\n' + t, 'import only node:'),
])
def test_extension_rules_break_validation(tmp_path, path, edit, message):
    copy = source_copy(tmp_path)
    script = copy / EXTENSION / path
    script.write_text(edit(script.read_text(encoding='utf-8')), encoding='utf-8')
    report = validator.validate(copy)
    assert any(message in error for error in report['errors']), report['errors']


def test_extension_without_entry_or_with_a_package_breaks_validation(tmp_path):
    copy = source_copy(tmp_path)
    (copy / EXTENSION / 'extension.mjs').rename(copy / EXTENSION / 'main.mjs')
    (copy / EXTENSION / 'package.json').write_text('{}', encoding='utf-8')
    errors = validator.validate(copy)['errors']
    assert any('needs extension.mjs' in error for error in errors), errors
    assert any('ship no package.json' in error for error in errors), errors


def test_plugin_change_requires_a_version_bump(tmp_path):
    import subprocess
    repo = tmp_path / 'repo'
    manifest = repo / 'plugins/orchi/plugin.json'
    manifest.parent.mkdir(parents=True)
    git = lambda *args: subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True)
    git('init', '-q', '-b', 'main')
    git('config', 'user.email', 'test@example.com')
    git('config', 'user.name', 'Test')
    manifest.write_text(json.dumps({'version': '0.1.0'}))
    git('add', '-A')
    git('commit', '-q', '-m', 'base')
    git('checkout', '-q', '-b', 'change')
    (repo / 'plugins/orchi/skill.md').write_text('changed')
    git('add', '-A')
    git('commit', '-q', '-m', 'change')
    assert validator.validate_version_bump(repo, 'main')
    manifest.write_text(json.dumps({'version': '0.2.0'}))
    assert validator.validate_version_bump(repo, 'main') == []
    git('checkout', '-q', 'main')
    (repo / 'README.md').write_text('docs only')
    assert validator.validate_version_bump(repo, 'main') == []
