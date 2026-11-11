"""The board snapshot: GitHub state joined with the crews Orchi reports, and what waits for the user."""
import json
from datetime import datetime, timedelta, timezone

import board
import status

NOW = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
CLAIM = 'Assigned to [dev-lead] pay tokens (sess-42) by Orchi on 2026-01-05, started 2026-01-05'


def labels(*names):
    return {'nodes': [{'name': name} for name in names]}


def repository():
    return {
        'defaultBranchRef': {'name': 'main'},
        'initiatives': {'nodes': [{'number': 1, 'title': '[PAY] Payments', 'url': 'u/1', 'labels': labels('Initiative'),
                                   'subIssues': {'totalCount': 2, 'nodes': [{'state': 'CLOSED'}, {'state': 'OPEN'}]}}]},
        'epics': {'nodes': [{'number': 2, 'subIssues': {'nodes': [
            {'number': 5, 'title': '[PAY][TOKEN] Column', 'url': 'u/5', 'state': 'OPEN', 'labels': labels('Task')},
            {'number': 6, 'title': '[PAY][TOKEN] Old', 'url': 'u/6', 'state': 'CLOSED', 'labels': labels('Task')}]}}]},
        'planning': {'nodes': [{'number': 7, 'title': 'Idea', 'url': 'u/7', 'labels': labels('Exploration')},
                               {'number': 8, 'title': 'Bug', 'url': 'u/8', 'labels': labels('needs-planning')}]},
        'claimed': {'nodes': [{'number': 2, 'body': 'Context\n\n' + CLAIM},
                              {'number': 8, 'body': 'Assigned to [planner] bug (sess-8) by Orchi on 2026-01-05, '
                                                    'started 2026-01-05, waits for #2'}]},
        'open': {'nodes': [
            {'number': 30, 'title': 'Tokens', 'url': 'p/30', 'isDraft': False, 'baseRefName': 'main',
             'reviewDecision': None, 'closingIssuesReferences': {'nodes': [{'number': 2}]},
             'commits': {'nodes': [{'commit': {'statusCheckRollup': {'state': 'SUCCESS'}}}]}},
            {'number': 31, 'title': 'Draft', 'url': 'p/31', 'isDraft': True, 'baseRefName': 'main',
             'reviewDecision': None, 'closingIssuesReferences': {'nodes': []}, 'commits': {'nodes': []}}]},
        'merged': {'nodes': [{'number': 29, 'title': 'Old', 'url': 'p/29', 'mergedAt': '2026-01-04T10:00:00Z',
                              'baseRefName': 'main'}]},
    }


def epic():
    return {'number': 2, 'title': '[PAY][TOKEN] Tokens', 'url': 'u/2', 'labels': labels('Epic', 'in-progress'),
            'assignees': {'nodes': []}, 'parent': {'number': 1, 'title': '[PAY] Payments'},
            'subIssues': {'totalCount': 2, 'nodes': [{'number': 5, 'title': '[PAY][TOKEN] Column', 'state': 'OPEN'},
                                                     {'number': 6, 'title': '[PAY][TOKEN] Old', 'state': 'CLOSED'}]},
            'blockedBy': {'nodes': []}}


def runner(calls=None):
    def run(args):
        if calls is not None:
            calls.append(args)
        if args[:2] == ['repo', 'view']:
            return json.dumps({'nameWithOwner': 'owner/name'})
        if 'query=' + board.QUERY in args:
            return json.dumps({'data': {'repository': repository()}})
        assert 'query=' + status.QUERY in args
        return json.dumps({'data': {'repository': {'issues': {
            'pageInfo': {'hasNextPage': False, 'endCursor': None}, 'nodes': [epic()]}}}})
    return run


def test_collect_builds_the_work_tree_with_claims():
    github = board.collect('owner/name', runner())
    work = {item['number']: item for item in github['work']}
    assert work[1]['kind'] == 'Initiative' and work[1]['progress'] == {'done': 1, 'total': 2}
    assert work[2]['parent'] == 1 and work[2]['progress'] == {'done': 1, 'total': 2}
    assert work[2]['crew'] == '[dev-lead] pay tokens' and work[2]['session'] == 'sess-42'
    assert work[5]['parent'] == 2 and work[5]['status'] == 'todo' and 6 not in work
    assert [(item['number'], item['kind']) for item in github['planning']] == [(7, 'Exploration'), (8, 'needs-planning')]
    assert github['planning'][1]['waits_for'] == 2
    assert github['pulls'][0]['checks'] == 'passing' and github['pulls'][0]['closes'] == [2]
    assert github['pulls'][1]['checks'] == 'none' and github['merged'][0]['number'] == 29
    assert board.lineage(github['work'], 5) == [1, 2]


def test_crews_join_claims_and_order_by_attention():
    github = board.collect('owner/name', runner())
    quiet = (NOW - timedelta(hours=1)).isoformat()
    reported = [
        {'name': '[researcher] idea', 'state': 'free'},
        {'name': '[planner] bug', 'session_id': 'sess-8', 'state': 'idle', 'since': quiet},
        {'name': '[designer] look', 'state': 'idle', 'background': 'build (pid 4)', 'since': NOW.isoformat()},
        {'name': '[dev-lead] pay tokens', 'session_id': 'sess-42', 'state': 'waiting', 'question': 'Which PSP?'},
        {'name': '[dev-lead] stray', 'state': 'idle', 'issue': 5, 'since': quiet},
        {'name': '[planner] other', 'state': 'bogus'},
    ]
    crews = board.crews(github, reported, NOW)
    assert [(crew['name'], crew['state']) for crew in crews] == [
        ('[dev-lead] stray', 'stuck'), ('[dev-lead] pay tokens', 'waiting'), ('[designer] look', 'background'),
        ('[planner] bug', 'idle'), ('[planner] other', 'idle'), ('[researcher] idea', 'free')]
    pay = crews[1]
    assert pay['issue'] == 2 and pay['role'] == 'Dev lead' and pay['path'] == [1] and pay['progress']['total'] == 2
    # The planner's Issue waits for #2, so a quiet planner is not stuck.
    assert crews[3]['issue'] == 8 and crews[3]['stuck'] == ''
    old = board.crews(github, [{'name': '[designer] look', 'state': 'idle', 'background': 'build',
                                'since': (NOW - timedelta(hours=4)).isoformat()}], NOW)
    assert old[0]['state'] == 'stuck' and 'background run' in old[0]['stuck']


def test_waiting_lists_questions_and_merges():
    github = board.collect('owner/name', runner())
    crews = [{'name': '[dev-lead] pay tokens', 'session_id': 'sess-42', 'state': 'waiting', 'question': 'Which PSP?'}]
    document = board.snapshot('owner/name', github, {'mode': 'off', 'crews': crews,
                                                     'questions': [{'id': 1, 'text': 'Ship on Friday?'}]}, NOW)
    kinds = [(item['kind'], item.get('pull')) for item in document['waiting']]
    # Without Orchi naming merges, a ready PR into main waits for the user while autonomous mode is off.
    assert kinds == [('question', None), ('orchi', None), ('merge', 30)]
    assert board.snapshot('o/n', github, {'mode': 'on'}, NOW)['waiting'] == []
    assert board.snapshot('o/n', github, {'mode': 'off', 'merges': []}, NOW)['waiting'] == []
    assert board.snapshot('o/n', github, {'mode': 'on', 'merges': [30], 'held': [30]}, NOW)['waiting'] == []


def test_cli_prints_the_snapshot_and_reports_errors(tmp_path, capsys):
    state = tmp_path / 'state.json'
    state.write_text(json.dumps({'mode': 'on', 'crews': [{'name': '[dev-lead] pay tokens', 'state': 'working'}]}))
    calls = []
    assert board.main(['--json', '--state', str(state)], runner(calls), NOW) == 0
    document = json.loads(capsys.readouterr().out)
    assert document['repository'] == 'owner/name' and document['crews'][0]['issue'] == 2
    assert '-F' not in [arg for call in calls for arg in call]
    assert board.main(['--state', str(tmp_path / 'missing.json'), '--repo', 'o/n'], runner(), NOW) == 0
    assert capsys.readouterr().out.endswith('0 active · 0 wait for you · 2 PRs\n')
    assert board.main(['--json', '--repo', 'not-a-repo'], runner(), NOW) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)['error'] and 'OWNER/NAME' in captured.err
    state.write_text('[]')
    assert board.main(['--state', str(state), '--repo', 'o/n'], runner(), NOW) == 2
