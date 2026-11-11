#!/usr/bin/env python3
"""Offline checks for the marketplace, the plugin, its skills and agents, links, ownership, and English text."""
from __future__ import annotations

import ast
import fnmatch
import json
from pathlib import Path
import re
import sys
import tomllib

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = 'plugins/orchi'
SCRIPTS = PLUGIN + '/skills/orchi-core/scripts'
SKILLS = ('orchi', 'orchi-core', 'orchi-explore', 'orchi-plan', 'orchi-standards', 'orchi-deliver', 'orchi-work',
          'orchi-design')
# The user types only /orchi; every other skill is loaded by the model for a session's role and hidden from the menu.
ENTRY = {'orchi'}
AGENTS = {'orchi-scout': 'claude-haiku-5.5', 'orchi-researcher': 'claude-opus-5.5',
          'orchi-implementer': 'claude-opus-5.5', 'orchi-fixer': 'claude-sonnet-5.5',
          'orchi-reviewer': 'claude-opus-5.5', 'orchi-designer': 'claude-opus-5.5'}
READ_ONLY_AGENTS = {'orchi-scout', 'orchi-researcher', 'orchi-reviewer'}
# Documented frontmatter keys (GitHub Docs: Copilot CLI plugin, skill, and custom agent references).
SKILL_KEYS = {'name', 'description', 'argument-hint', 'allowed-tools', 'user-invocable', 'disable-model-invocation'}
AGENT_KEYS = {'name', 'description', 'target', 'tools', 'model', 'disable-model-invocation', 'user-invocable',
              'mcp-servers', 'metadata'}
# The documented aliases, plus `skill`, the Copilot CLI tool that loads a skill (other hosts ignore unknown names).
TOOL_ALIASES = {'execute', 'shell', 'read', 'edit', 'search', 'agent', 'web', 'todo', 'skill'}
PLUGIN_KEYS = {'name', 'description', 'version', 'author', 'homepage', 'repository', 'license', 'keywords',
               'category', 'tags', 'agents', 'skills', 'commands', 'hooks', 'mcpServers', 'lspServers', 'extensions'}
IGNORED = {'__pycache__', '.pytest_cache', '.venv', '.git', '.upstream', '.orchi-tmp', 'node_modules'}
SKILL_LINES = 100
AGENT_BODY_LIMIT = 30_000
sys.path.insert(0, str(ROOT / SCRIPTS))
import knowledge  # noqa: E402  (the bundled link and anchor lint, reused rather than reimplemented)


def files(root: Path = ROOT) -> list[Path]:
    return [p for p in sorted(root.rglob('*')) if p.is_file()
            and not any(part in IGNORED for part in p.relative_to(root).parts) and p.suffix not in {'.pyc', '.pyo'}]


class SourceDocuments(knowledge.Documents):
    """The validated source files as a knowledge.py document set, so links and anchors use its lint."""

    def __init__(self, root: Path, source_files: list[Path]):
        self.root, self.revision = root, None
        self.paths = {p.relative_to(root).as_posix() for p in source_files}
        self.names = sorted(p for p in self.paths if p.endswith('.md'))


def frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith('---\n'):
        raise ValueError('missing YAML frontmatter')
    _, meta, body = text.split('---', 2)
    data = yaml.safe_load(meta)
    if not isinstance(data, dict):
        raise ValueError('frontmatter is not a mapping')
    return data, body


def third_party_imports(text: str, bundled: set[str]) -> set[str]:
    modules = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            modules.add(node.module.split('.')[0])
    return modules - set(sys.stdlib_module_names) - bundled - {'__future__'}


def validate_manifests(root: Path) -> list[str]:
    errors = []
    try:
        market = json.loads((root / '.github/plugin/marketplace.json').read_text())
        plugin = json.loads((root / PLUGIN / 'plugin.json').read_text())
    except (OSError, ValueError) as exc:
        return ['Manifest: ' + str(exc)]
    if market.get('name') != 'orchi-copilot' or not isinstance(market.get('owner'), dict) or not market['owner'].get('name'):
        errors.append('marketplace.json needs the name orchi-copilot and an owner name')
    entries = market.get('plugins')
    if not isinstance(entries, list) or [e.get('name') for e in entries if isinstance(e, dict)] != ['orchi']:
        errors.append('marketplace.json must list exactly the plugin orchi')
    else:
        source = (root / entries[0].get('source', '')).resolve()
        if source != (root / PLUGIN).resolve():
            errors.append('marketplace.json source of orchi must be ./' + PLUGIN)
        if entries[0].get('version') not in (None, plugin.get('version')):
            errors.append('marketplace.json and plugin.json disagree on the version')
    if market.get('metadata', {}).get('version') not in (None, plugin.get('version')):
        errors.append('marketplace.json metadata version differs from plugin.json')
    if plugin.get('name') != 'orchi' or not re.fullmatch(r'\d+\.\d+\.\d+', str(plugin.get('version', ''))):
        errors.append('plugin.json needs the name orchi and a semantic version')
    if '$schema' in plugin:
        errors.append('plugin.json uses the Copilot plugin format, not Agent Plugins ($schema)')
    if set(plugin) - PLUGIN_KEYS:
        errors.append('plugin.json has undocumented fields: ' + ', '.join(sorted(set(plugin) - PLUGIN_KEYS)))
    for field in ('agents', 'skills'):
        if not (root / PLUGIN / str(plugin.get(field, ''))).is_dir():
            errors.append(f'plugin.json {field} path does not exist')
    return errors


def validate_skills(root: Path) -> list[str]:
    errors = []
    folder = root / PLUGIN / 'skills'
    if sorted(p.name for p in folder.iterdir() if p.is_dir()) != sorted(SKILLS):
        errors.append('Unexpected skill set')
    for name in SKILLS:
        try:
            text = (folder / name / 'SKILL.md').read_text()
            meta, _ = frontmatter(text)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(name + ': ' + str(exc))
            continue
        if set(meta) - SKILL_KEYS:
            errors.append(f'{name}: undocumented skill frontmatter: ' + ', '.join(sorted(set(meta) - SKILL_KEYS)))
        if meta.get('name') != name or not meta.get('description') or len(text.splitlines()) > SKILL_LINES:
            errors.append('Invalid skill metadata or oversized instructions: ' + name)
        if len(str(meta.get('description', ''))) > 1024 or len(name) > 64:
            errors.append('Skill name or description too long: ' + name)
        if name in ENTRY and (meta.get('disable-model-invocation') is not True or meta.get('user-invocable') is False):
            errors.append('The entry skill must be user-invocable and explicit-only: ' + name)
        if name not in ENTRY and (meta.get('user-invocable') is not False or meta.get('disable-model-invocation')):
            errors.append('A workflow skill must be hidden from the menu and model-invocable: ' + name)
        if '$ARGUMENTS' in text:
            errors.append(name + ': $ARGUMENTS is not a documented Copilot skill substitution')
    return errors


def validate_agents(root: Path) -> list[str]:
    errors = []
    folder = root / PLUGIN / 'agents'
    found = {p.name[:-len('.agent.md')] for p in folder.glob('*.agent.md')}
    if found != set(AGENTS) or len(list(folder.iterdir())) != len(AGENTS):
        errors.append('Unexpected agent set: ' + ', '.join(sorted(found)))
    for name, model in AGENTS.items():
        try:
            meta, body = frontmatter((folder / (name + '.agent.md')).read_text())
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(name + ': ' + str(exc))
            continue
        if set(meta) - AGENT_KEYS:
            errors.append(f'{name}: undocumented agent frontmatter: ' + ', '.join(sorted(set(meta) - AGENT_KEYS)))
        if meta.get('name') != name or not meta.get('description'):
            errors.append(name + ': name must match the file and description is required')
        tools = meta.get('tools')
        if not isinstance(tools, list) or not tools or set(tools) - TOOL_ALIASES:
            errors.append(f'{name}: tools must be a list of documented aliases')
        elif name in READ_ONLY_AGENTS and 'edit' in tools:
            errors.append(name + ': a read-only role must not have edit')
        if meta.get('model') != model:
            errors.append(f'{name}: model must be {model}')
        if len(body) > AGENT_BODY_LIMIT:
            errors.append(f'{name}: body exceeds {AGENT_BODY_LIMIT} characters')
    return errors


def ownership(root: Path) -> list[tuple[str, list[str]]]:
    text = (root / 'docs/README.md').read_text()
    section = text.split('\n## Ownership', 1)[1] if '\n## Ownership' in text else ''
    rows = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells) >= 2 and cells[0].startswith('`'):
            rows.append((cells[0].strip('`'), re.findall(r'`([^`]+)`', cells[1])))
    return rows


def owned(pattern: str, path: str) -> bool:
    if pattern.endswith('/**'):
        return path.startswith(pattern[:-2])
    return fnmatch.fnmatchcase(path, pattern)


def validate_ownership(root: Path, paths: list[str]) -> list[str]:
    try:
        rows = ownership(root)
    except OSError as exc:
        return ['docs/README.md: ' + str(exc)]
    if not rows:
        return ['docs/README.md has no Ownership table']
    errors = [f'Ownership page does not exist: {page}' for _, pages in rows for page in pages if not (root / page).is_file()]
    errors += ['Ownership entry matches no file: ' + pattern for pattern, _ in rows
               if not any(owned(pattern, path) for path in paths)]
    errors += ['File under plugins/ has no owning page in docs/README.md: ' + path for path in paths
               if path.startswith('plugins/') and not any(owned(pattern, path) for pattern, _ in rows)]
    return errors


def validate(root: Path = ROOT) -> dict:
    errors: list[str] = []
    compiled = 0
    source_files = files(root)
    paths = [p.relative_to(root).as_posix() for p in source_files]
    bundled = {p.stem for p in (root / SCRIPTS).glob('*.py')}
    errors += validate_manifests(root) + validate_skills(root) + validate_agents(root)
    for file, rel in zip(source_files, paths):
        try:
            text = file.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as exc:
            errors.append(rel + ': ' + str(exc))
            continue
        if re.search(r'[\u0400-\u052f]', text):
            errors.append('Non-English repository text: ' + rel)
        if re.search(r'\bOrchi[^\n]{0,30}\bv?\d+\.\d+\.\d+', text):
            errors.append('Product release marker: ' + rel)
        if rel.startswith('plugins/'):
            for number, line in enumerate(text.splitlines(), 1):
                if re.search(r'claude', line, re.I) and not re.fullmatch(r'model: claude-[a-z0-9.-]+', line.strip()):
                    errors.append(f'{rel}:{number}: names Claude outside a model ID')
        if file.suffix == '.py':
            try:
                compile(text, str(file), 'exec')
                compiled += 1
                if rel.startswith('plugins/') and third_party_imports(text, bundled):
                    errors.append(rel + ': bundled scripts must use only the standard library: '
                                  + ', '.join(sorted(third_party_imports(text, bundled))))
            except SyntaxError as exc:
                errors.append(str(exc))
        if file.suffix == '.json':
            try:
                json.loads(text)
            except ValueError as exc:
                errors.append(rel + ': ' + str(exc))
        if file.suffix in {'.yaml', '.yml'}:
            try:
                yaml.safe_load(text)
            except yaml.YAMLError as exc:
                errors.append(rel + ': ' + str(exc))
        if file.suffix == '.md' and rel.startswith('plugins/'):
            prose = re.sub(r'```.*?```', '', text, flags=re.S)
            # Installed files travel without the repository: links stay inside the skills folder.
            for link in re.findall(r'\]\(([^\s)]+)\)', prose):
                if ':' in link or link.startswith('#'):
                    continue
                target = (file.parent / link.split('#')[0]).resolve()
                if not target.is_relative_to(root / PLUGIN / 'skills'):
                    errors.append(rel + ': installed reference leaves the skills folder: ' + link)
    # Skills route agents by heading anchors, so a renamed heading must fail like a missing file.
    errors += knowledge.lint(SourceDocuments(root, source_files))
    errors += validate_ownership(root, paths)
    config = tomllib.loads((root / 'pyproject.toml').read_text())
    if 'project' in config or 'build-system' in config:
        errors.append('The plugin must not require a Python application package')
    return {'ok': not errors, 'errors': errors, 'python_files_compiled': compiled, 'skills': len(SKILLS),
            'agents': len(AGENTS), 'files': len(source_files)}


if __name__ == '__main__':
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
