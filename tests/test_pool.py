"""Text, not behavior: the entry skill and the pool reference agree on the Copilot app mechanics they rely on."""
import re

import yaml

from conftest import PLUGIN, REFERENCES, SKILLS, read

POOL_ANCHORS = {'sessions', 'roles', 'prepare-the-repository', 'assign-a-crew', 'a-stream-of-requests', 'messages',
                'questions-and-plans', 'autonomous-mode', 'merge', 'workers', 'release', 'stalls', 'limits', 'status',
                'update-orchi', 'remote-control', 'follow-ups', 'initiatives', 'lessons'}


def prose(path):
    return ' '.join(read(path).split())


def test_the_entry_skill_runs_only_when_the_user_types_it():
    meta = yaml.safe_load(read(SKILLS / 'orchi/SKILL.md').split('---', 2)[1])
    assert meta['disable-model-invocation'] is True and meta.get('user-invocable', True) is True
    assert 'Copilot Project' in prose(SKILLS / 'orchi/SKILL.md')


def test_pool_links_land_on_the_sections_the_seam_keeps():
    headings = {re.sub(r'[^a-z0-9 -]', '', h.lower()).replace(' ', '-')
                for h in re.findall(r'^## (.+)$', read(REFERENCES / 'pool.md'), re.M)}
    assert POOL_ANCHORS <= headings
    for path in PLUGIN.rglob('*.md'):
        for anchor in re.findall(r'pool\.md#([a-z0-9-]+)', read(path)):
            assert anchor in POOL_ANCHORS, f'{path}: pool.md#{anchor}'


def test_crews_are_child_sessions_that_report_by_session_message():
    pool, entry = prose(REFERENCES / 'pool.md'), prose(SKILLS / 'orchi/SKILL.md')
    for phrase in ('`create_session`', '`coordinate_with_creator: true`', '`notify_on_idle: "always"`',
                   '`send_session_message`', '`archive_session`', 'Nobody deletes a session'):
        assert phrase in pool, phrase
    assert '`get_sessions_status`' in entry and '`archive_session`' in entry
    assert 'Assigned to [<role>] <topic> (<session id>) by Orchi on <date>' in pool
    assert 'For each claim starting `Assigned to [`' in entry


def test_orchi_merges_on_the_users_yes_and_never_deploys():
    pool, entry = prose(REFERENCES / 'pool.md'), prose(SKILLS / 'orchi/SKILL.md')
    assert 'Orchi merges into main on the user\'s yes' in pool
    assert 'on their yes, confirm its checks pass and merge it yourself' in entry
    assert 'merge into main without the user\'s word while it is off; deploy;' in entry


def test_every_session_starts_in_an_explicit_mode_never_plan():
    pool = prose(REFERENCES / 'pool.md')
    assert 'whose `mode` is always given, since the app otherwise starts it in plan mode' in pool
    assert '`interactive` while autonomous mode is off, `autopilot` while it is on' in pool
    assert 'a `kickoff` in `autopilot` mode, since a worker never asks the user' in pool
    assert 'Crews never run in plan mode.' in pool


def test_reports_carry_a_purpose_and_the_assignment_id():
    pool, work = prose(REFERENCES / 'pool.md'), prose(SKILLS / 'orchi-work/SKILL.md')
    assert 'Every report up passes a `purpose`' in pool and 'passes the `assignment_id`' in pool
    for purpose in ('progress', 'needs_input', 'handoff', 'error'):
        assert f'| `{purpose}` |' in pool, purpose
    for purpose in ('handoff', 'needs_input', 'error'):
        assert f'`{purpose}`' in work, purpose


def test_agent_merge_lands_a_merge_only_on_the_users_word():
    pool, entry = prose(REFERENCES / 'pool.md'), prose(SKILLS / 'orchi/SKILL.md')
    assert '`manage_agent_merge`' in pool and 'only with its `merge_pr` action' in pool
    assert 'without `merge_pr`, which needs the user\'s word per PR' in pool
    assert 'turn on Agent Merge\'s `merge_pr` without the user\'s yes to that PR' in entry
    assert 'the crew never merges' in pool


def test_autonomous_mode_keeps_a_reconcile_automation():
    pool = prose(REFERENCES / 'pool.md')
    assert '`save_session_automation`' in pool and '`clear: true`' in pool and '`get_session_automation`' in pool
    assert 'an automation with that prompt means the mode is on' in pool
    assert '`get_session_automation`' in prose(SKILLS / 'orchi/SKILL.md')


def test_workers_are_per_task_sessions_that_never_clear():
    pool, work = prose(REFERENCES / 'pool.md'), prose(SKILLS / 'orchi-work/SKILL.md')
    assert 'By default the writer is a subagent' in pool and '`[worker] <topic> <task>`' in pool
    assert 'Git lets only one worktree check out a branch' in pool
    for text in (pool, work):
        assert '/clear' not in text and 'clears itself' not in text
    assert 'Your crew then archives this session' in work and 'never use `ask_user`' in work


def test_setup_runs_from_the_bundled_script_and_checks_first():
    pool = prose(REFERENCES / 'pool.md')
    assert '`python3 <orchi-core>/scripts/setup.py --check`' in pool
    assert 'python3 <orchi-core>/scripts/setup.py --project <worktree>' in pool
    assert 'the setup PR (Orchi merges it on their yes)' in pool


def test_no_skill_names_a_host_the_plugin_does_not_run_in():
    for path in PLUGIN.rglob('*'):
        if path.is_file() and path.suffix in {'.md', '.yml', '.py', '.json'}:
            text = read(path)
            for word in ('Remote Control', 'SendMessage', 'TeamCreate', '.claude/', 'CLAUDE.md', 'Skill tool'):
                assert word not in text, f'{path}: {word}'
