"""The board snapshot: GitHub state joined with the crews Orchi reports, and what waits for the user."""
import json
from datetime import datetime, timedelta, timezone

import board
import status

NOW = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
TAKEN = {'assignees': {'nodes': [{'login': 'dev'}]}}


def labels(*names):
    return {'nodes': [{'name': name} for name in names]}


def comment(body, created='2026-01-05T11:00:00Z'):
    return {'body': body, 'createdAt': created}


def question(number, **data):
    return comment(f'Question for the user\n<!-- orchi:question {json.dumps(data)} -->')


def node(number, title, *names, state='OPEN', **extra):
    return {'number': number, 'title': title, 'url': f'u/{number}', 'state': state, 'labels': labels(*names), **extra}


def repository():
    q1 = question(5, id='q1', crew='[dev-lead] pay tokens', kind='question', blocking=True, text='Which PSP?',
                  context=['Stripe is in use.'], choices=[{'label': 'Stripe', 'detail': 'Known', 'recommended': True},
                                                          {'label': 'Adyen'}])
    plan = question(10, id='q3', crew='[planner] refunds', kind='plan', text='Approve the plan for #10?',
                    plan=['#20 Model', '#21 API'])
    return {
        'defaultBranchRef': {'name': 'main'},
        'initiatives': {'nodes': [{**node(1, '[PAY] Payments', 'Initiative'), 'subIssues': {'totalCount': 3, 'nodes': [
            {**node(2, '[PAY][TOKEN] Tokens', 'Epic', **TAKEN), 'subIssuesSummary': {'total': 3, 'completed': 1}},
            {**node(3, '[PAY][CARD] Cards', 'Epic', state='CLOSED'), 'subIssuesSummary': {'total': 2, 'completed': 2}},
            {**node(4, 'Explore: fees'), 'subIssuesSummary': {'total': 0, 'completed': 0}}]}}]},
        'epics': {'nodes': [
            {**node(2, '[PAY][TOKEN] Tokens', 'Epic', **TAKEN), 'parent': {'number': 1}, 'subIssues': {'nodes': [
                node(5, '[PAY][TOKEN] Column', 'Task'), node(6, '[PAY][TOKEN] Old', 'Task', state='CLOSED'),
                node(9, '[PAY][TOKEN] API', 'Task', linkedBranches={'nodes': [{'ref': {'name': 'task/api'}}]})]}},
            {**node(10, '[REF] Refunds', 'Epic'), 'parent': None, 'subIssues': {'nodes': []}}]},
        'recent': {'nodes': [
            {**node(5, '[PAY][TOKEN] Column', 'Task'), 'parent': {'number': 2}, 'comments': {'nodes': [q1]}},
            {**node(10, '[REF] Refunds', 'Epic'), 'parent': None, 'comments': {'nodes': [plan]}},
            {**node(11, 'Typo on the login page'), 'parent': None, 'comments': {'nodes': [
                question(11, id='q2', crew='Orchi', text='Fix now?', assumed='Later'),
                comment('<!-- orchi:answer {"id": "q2", "answer": "Now"} -->', '2026-01-05T11:30:00Z')]}},
            {**node(12, 'Broken marker'), 'parent': None, 'comments': {'nodes': [
                comment('<!-- orchi:question {not json} -->')]}},
            {**node(1, '[PAY] Payments', 'Initiative'), 'parent': None, 'comments': {'nodes': []}},
            {**node(8, 'Bug'), 'parent': None, 'comments': {'nodes': []},
             'blockedBy': {'nodes': [{'number': 3, 'state': 'CLOSED'}, {'number': 2, 'state': 'OPEN'}]}},
            {**node(7, 'Explore: idea'), 'parent': None, 'comments': {'nodes': []}},
            {**node(13, 'Lesson: flaky CI', body='## Requirements\n- R1: retry once'), 'parent': None,
             'comments': {'nodes': []}},
            {**node(14, 'Someone else\'s fix', **TAKEN), 'parent': None, 'comments': {'nodes': []}}]},
        'open': {'nodes': [
            {'number': 30, 'title': 'Tokens API', 'url': 'p/30', 'isDraft': False, 'baseRefName': 'main',
             'reviewDecision': None, 'closingIssuesReferences': {'nodes': [{'number': 9}]},
             'body': '## Summary\n<!-- What and why -->\n- Adds the token API.\n- Rotates keys.\n\n## Tests\n- ok',
             'additions': 120, 'deletions': 4, 'changedFiles': 5, 'comments': {'nodes': []},
             'commits': {'nodes': [{'commit': {'statusCheckRollup': {'state': 'SUCCESS'}}}]}},
            {'number': 31, 'title': 'Draft', 'url': 'p/31', 'isDraft': True, 'baseRefName': 'main',
             'reviewDecision': None, 'closingIssuesReferences': {'nodes': []}, 'commits': {'nodes': []}},
            {'number': 32, 'title': 'Fix VAT rounding', 'url': 'p/32', 'isDraft': False, 'baseRefName': 'main',
             'reviewDecision': None, 'closingIssuesReferences': {'nodes': []}, 'commits': {'nodes': []},
             'body': 'Rounds VAT per line.'}]},
        'merged': {'nodes': [{'number': 29, 'title': 'Old', 'url': 'p/29', 'mergedAt': '2026-01-04T10:00:00Z',
                              'baseRefName': 'main'}]},
    }


def epic():
    return {'number': 2, 'title': '[PAY][TOKEN] Tokens', 'url': 'u/2', 'labels': labels('Epic'),
            **TAKEN, 'parent': {'number': 1, 'title': '[PAY] Payments'},
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


def test_collect_builds_the_work_tree_from_github_signals():
    github = board.collect('owner/name', runner())
    work = {item['number']: item for item in github['work']}
    assert work[1]['kind'] == 'Initiative' and work[1]['progress'] == {'done': 1, 'total': 3}
    assert work[2]['parent'] == 1 and work[2]['progress'] == {'done': 1, 'total': 2}
    assert work[2]['status'] == 'taken' and work[9]['status'] == 'taken' and work[1]['status'] == 'ready'
    assert work[5]['parent'] == 2 and work[5]['status'] == 'todo' and 6 not in work
    # Untyped Issues nobody holds or planned need a plan; a planned or taken one does not.
    assert [(item['number'], item['kind']) for item in github['planning']] == [
        (7, 'Exploration'), (8, 'needs-planning'), (11, 'needs-planning'), (12, 'needs-planning')]
    assert github['planning'][1]['waits_for'] == 2
    assert github['pulls'][0]['checks'] == 'passing' and github['pulls'][0]['closes'] == [9]
    assert github['pulls'][0]['changes'] == ['Adds the token API.', 'Rotates keys.']
    assert github['pulls'][2]['changes'] == ['Rounds VAT per line.'] and github['pulls'][1]['changes'] == []
    assert github['pulls'][1]['checks'] == 'none' and github['merged'][0]['number'] == 29
    assert board.lineage(github['work'], 5) == [1, 2]


def test_crews_join_their_issues_and_order_by_attention():
    github = board.collect('owner/name', runner())
    quiet = (NOW - timedelta(hours=1)).isoformat()
    reported = [
        {'name': '[researcher] idea', 'state': 'free'},
        {'name': '[planner] bug', 'session_id': 'sess-8', 'state': 'idle', 'since': quiet, 'issue': 8},
        {'name': '[designer] look', 'state': 'idle', 'background': 'build (pid 4)', 'since': NOW.isoformat()},
        {'name': '[dev-lead] pay tokens', 'session_id': 'sess-42', 'state': 'waiting', 'question': 'Which PSP?',
         'issue': 2},
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
    crews = [{'name': '[dev-lead] pay tokens', 'session_id': 'sess-42', 'state': 'waiting', 'question': 'Which PSP?'},
             {'name': '[designer] look', 'state': 'waiting', 'question': 'Calm or dense?'}]
    document = board.snapshot('owner/name', github, {'mode': 'off', 'crews': crews,
                                                     'questions': [{'id': 1, 'text': 'Ship on Friday?'}]}, NOW)
    kinds = [(item['kind'], item.get('crew'), item.get('pull')) for item in document['waiting']]
    # The pay crew's question is already kept in a comment, so only the designer's gets one from its crew entry.
    # Without Orchi naming merges, ready PRs into main wait for the user while autonomous mode is off.
    assert sorted(kinds, key=str) == sorted([
        ('question', '[dev-lead] pay tokens', None), ('question', '[planner] refunds', None),
        ('orchi', 'Orchi', None), ('question', '[designer] look', None), ('merge', None, 30), ('merge', None, 32)],
        key=str)
    assert [item['kind'] for item in board.snapshot('o/n', github, {'mode': 'on'}, NOW)['waiting']] == [
        'question', 'question']
    assert [item for item in board.snapshot('o/n', github, {'mode': 'off', 'merges': []}, NOW)['waiting']
            if item['kind'] == 'merge'] == []
    assert [item for item in board.snapshot('o/n', github, {'mode': 'on', 'merges': [30], 'held': [30]}, NOW)[
        'waiting'] if item['kind'] == 'merge'] == []


def test_questions_come_from_comments_and_reports_until_answered():
    github = board.collect('owner/name', runner())
    reported = [{'id': 'q1', 'request_id': 'req-7'}, {'id': 'q4', 'crew': 'Orchi', 'text': 'Release #8?',
                                                      'assumed': 'Keep', 'context': 'Quiet for an hour.'}]
    document = board.snapshot('o/n', github, {'questions': reported}, NOW)
    open_ = {question['id']: question for question in document['questions']}
    assert set(open_) == {'q1', 'q3', 'q4'}
    q1 = open_['q1']
    assert q1['issue'] == 5 and q1['request_id'] == 'req-7' and q1['blocking'] and q1['text'] == 'Which PSP?'
    assert q1['choices'][0] == {'label': 'Stripe', 'detail': 'Known', 'recommended': True}
    assert open_['q4']['blocking'] is False and open_['q4']['context'] == ['Quiet for an hour.']
    assert open_['q3']['kind'] == 'plan' and open_['q3']['plan'] == ['#20 Model', '#21 API']
    # Blocking first.
    assert [question['blocking'] for question in document['questions']] == [True, True, False]
    assert [(entry['id'], entry['answer'], entry['picked']) for entry in document['answered']] == [('q2', 'Now', True)]
    sent = {'sent': [{'id': 'q1', 'crew': '[dev-lead] pay tokens', 'answer': 'Stripe', 'at': '2026-01-05T11:50:00Z'},
                     {'id': 'q9', 'answer': 'Yes', 'question': 'Gone?', 'at': '2026-01-05T11:40:00Z'}]}
    document = board.snapshot('o/n', github, sent, NOW)
    assert 'q1' not in {question['id'] for question in document['questions']}
    assert [(entry['id'], entry['picked']) for entry in document['answered']] == [
        ('q1', False), ('q9', True), ('q2', True)]
    later = board.snapshot('o/n', github, sent, NOW + timedelta(hours=2))
    assert 'q1' in {question['id'] for question in later['questions']}


def test_board_places_every_card_in_one_column():
    github = board.collect('owner/name', runner())
    crews = [{'name': '[planner] bug', 'session_id': 'sess-8', 'state': 'working', 'doing': 'Writing the plan',
              'issue': 8}]
    document = board.snapshot('o/n', github, {'crews': crews, 'deferred': [7]}, NOW)
    tasks = {card['number']: card for card in document['board']['tasks']}
    stages = {number: card['stage'] for number, card in tasks.items()}
    assert stages == {5: 'ask', 6: 'done', 9: 'review', 3: 'done', 4: 'plan', 10: 'review', 7: 'backlog',
                      8: 'progress', 11: 'plan', 12: 'plan', 13: 'plan', 14: 'progress', 31: 'progress',
                      32: 'review'}
    assert tasks[5]['state'] == 'Which PSP?' and tasks[5]['detail'] == 'question' and tasks[5]['tone'] == 'orange'
    assert tasks[9]['detail'] == 'pr' and tasks[9]['state'] == 'ready to merge' and tasks[9]['pull']['number'] == 30
    assert tasks[10]['state'] == 'approve plan' and tasks[10]['group'] == '10' and tasks[10]['epic'] == 10
    assert tasks[8]['state'] == 'Writing the plan' and tasks[8]['crew'] == '[planner] bug'
    assert tasks[32]['state'] == 'PR, no Issue' and tasks[32]['kind'] == 'PR' and tasks[7]['state'] == 'deferred'
    assert tasks[11]['kind'] == 'Issue' and tasks[11]['group'] == 'outside' and tasks[11]['epic'] is None
    groups = {group['key']: group for group in document['board']['groups']}
    assert list(groups) == ['1', '10', 'outside']
    # Progress counts work items: a closed Epic by its sub-issue summary, an open one by its Tasks.
    assert groups['1']['stage'] == 'ask' and (groups['1']['done'], groups['1']['total']) == (3, 6)
    assert groups['10']['kind'] == 'Epic' and groups['10']['stage'] == 'review'
    assert groups['outside']['stage'] == 'review' and groups['outside']['counts']['plan'] == 3
    epics = {epic['number']: epic for epic in document['board']['epics']}
    assert epics[2]['stage'] == 'ask' and epics[2]['counts'] == {
        'plan': 0, 'backlog': 0, 'progress': 0, 'ask': 1, 'review': 1, 'done': 1}
    assert epics[3]['stage'] == 'done' and (epics[3]['done'], epics[3]['total']) == (2, 2)
    assert epics[4]['stage'] == 'plan' and epics[4]['group'] == '1' and epics[2]['total'] == 3
    # Orchi may move a card to where the work is when GitHub does not show it yet.
    moved = board.snapshot('o/n', github, {'stages': {'12': 'backlog', '6': 'ask'}}, NOW)
    assert {card['number']: card['stage'] for card in moved['board']['tasks']}[12] == 'backlog'
    assert {card['number']: card['stage'] for card in moved['board']['tasks']}[6] == 'done'


def test_history_records_moves_and_back_moves():
    github = board.collect('owner/name', runner())
    crews = [{'name': '[dev-lead] api', 'state': 'working', 'issue': 9}]
    first = board.snapshot('o/n', github, {'crews': crews}, NOW)
    card = next(card for card in first['board']['tasks'] if card['number'] == 9)
    assert card['stage'] == 'review' and [entry['text'] for entry in card['history']] == ['Taken by [dev-lead] api']
    later = NOW + timedelta(minutes=10)
    state = {'crews': crews, 'stages': {'9': 'progress'},
             'moves': [{'number': 9, 'to': 'progress', 'at': '2026-01-05T12:09:00+00:00',
                        'note': 'You asked to split the migration', 'back': True}]}
    second = board.snapshot('o/n', github, state, later, previous=json.loads(json.dumps(first)))
    card = next(card for card in second['board']['tasks'] if card['number'] == 9)
    assert card['stage'] == 'progress' and card['back'] is True
    assert [(entry.get('from'), entry.get('to'), entry.get('back'), entry.get('note')) for entry in card['history'] if 'to' in entry] == [
        (None, 'progress', True, 'You asked to split the migration'), ('review', 'progress', True, None)]
    third = board.snapshot('o/n', github, {'crews': crews}, later + timedelta(minutes=5), previous=second)
    card = next(card for card in third['board']['tasks'] if card['number'] == 9)
    assert card['stage'] == 'review' and card['back'] is False and len(card['history']) == 4
    fresh = board.snapshot('o/n', github, {}, later, previous={'board': {'tasks': []}})
    assert next(card for card in fresh['board']['tasks'] if card['number'] == 9)['history'][0]['to'] == 'review'


def test_cli_prints_the_snapshot_and_reports_errors(tmp_path, capsys):
    state = tmp_path / 'state.json'
    state.write_text(json.dumps({'mode': 'on', 'crews': [{'name': '[dev-lead] pay tokens', 'state': 'working',
                                                          'issue': 2}]}))
    calls = []
    previous = tmp_path / 'previous.json'
    previous.write_text('not json')
    assert board.main(['--json', '--state', str(state), '--previous', str(previous)], runner(calls), NOW) == 0
    document = json.loads(capsys.readouterr().out)
    assert document['board']['groups'] and 'tree' not in document
    assert document['repository'] == 'owner/name' and document['crews'][0]['issue'] == 2
    assert '-F' not in [arg for call in calls for arg in call]
    assert board.main(['--state', str(tmp_path / 'missing.json'), '--repo', 'o/n'], runner(), NOW) == 0
    assert capsys.readouterr().out.endswith('0 active · 2 wait for you · 3 PRs\n')
    assert board.main(['--json', '--repo', 'not-a-repo'], runner(), NOW) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)['error'] and 'OWNER/NAME' in captured.err
    state.write_text('[]')
    assert board.main(['--state', str(state), '--repo', 'o/n'], runner(), NOW) == 2
