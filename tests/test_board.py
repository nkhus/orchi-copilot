"""The board snapshot: GitHub state read from standard signals and, on the owner's board, Orchi's live overlay."""
import json
from datetime import datetime, timedelta, timezone

import board
import status

NOW = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
TAKEN = {'assignees': {'nodes': [{'login': 'dev'}]}}
PLAN = '## Requirements\n- R1: the plan.'
SUMMARY = {'paragraphs': [{'lead': 'Tokens are almost done.', 'text': '#9 waits for your review.'}],
           'since': 'Merged #29.', 'at': '2026-01-05T11:00:00+00:00'}
OWNER = {'reported': '2026-01-05T11:55:00+00:00', 'mode': 'off', 'limit': 3, 'summary': SUMMARY,
         'queue': [{'issue': 13, 'action': 'plan', 'title': 'Export', 'after': 8}]}


def labels(*names):
    return {'nodes': [{'name': name} for name in names]}


def comment(body, created='2026-01-05T11:00:00Z', author='OWNER'):
    return {'body': body, 'createdAt': created, 'authorAssociation': author}


def assigned(login, at):
    return {'__typename': 'AssignedEvent', 'createdAt': at, 'assignee': {'login': login}}


def node(number, title, *names, state='OPEN', **extra):
    return {'number': number, 'title': title, 'url': f'u/{number}', 'state': state, 'labels': labels(*names), **extra}


def issue(number, title, *names, comments=(), events=(), parent=None, **extra):
    return {**node(number, title, *names, **extra), 'parent': parent and {'number': parent},
            'comments': {'nodes': list(comments)}, 'timelineItems': {'nodes': list(events)}}


def pull(number, title, closes=(), draft=False, decision=None, committed=None, events=(), comments=(), **extra):
    return {'number': number, 'title': title, 'url': f'p/{number}', 'isDraft': draft, 'baseRefName': 'main',
            'reviewDecision': decision, 'closingIssuesReferences': {'nodes': [{'number': n} for n in closes]},
            'createdAt': '2026-01-05T09:00:00Z', 'updatedAt': committed or '2026-01-05T09:00:00Z',
            'commits': {'nodes': [{'commit': {'committedDate': committed, 'statusCheckRollup': extra.pop('rollup', None)}}]
                        if committed else []},
            'timelineItems': {'nodes': list(events)}, 'comments': {'nodes': list(comments)}, **extra}


def repository():
    closing = {'closedByPullRequestsReferences': {'nodes': [{'number': 33, 'state': 'OPEN'}]}}
    return {
        'defaultBranchRef': {'name': 'main'},
        'initiatives': {'nodes': [{**node(1, '[PAY] Payments', 'Initiative'), 'subIssues': {'totalCount': 3, 'nodes': [
            {**node(2, '[PAY][TOKEN] Tokens', 'Epic', **TAKEN), 'subIssuesSummary': {'total': 3, 'completed': 1}},
            {**node(3, '[PAY][CARD] Cards', 'Epic', state='CLOSED'), 'subIssuesSummary': {'total': 2, 'completed': 2}},
            {**node(4, 'Explore: fees'), 'subIssuesSummary': {'total': 0, 'completed': 0}}]}}]},
        'epics': {'nodes': [
            {**node(2, '[PAY][TOKEN] Tokens', 'Epic', **TAKEN), 'parent': {'number': 1}, 'subIssues': {'nodes': [
                node(5, '[PAY][TOKEN] Column', 'Task', body=PLAN), node(6, '[PAY][TOKEN] Old', 'Task', state='CLOSED'),
                node(9, '[PAY][TOKEN] API', 'Task', linkedBranches={'nodes': [{'ref': {'name': 'task/api'}}]})]}},
            {**node(10, '[REF] Refunds', 'Epic'), 'parent': None, 'subIssues': {'nodes': []}}]},
        'recent': {'nodes': [
            issue(5, '[PAY][TOKEN] Column', 'Task', parent=2, body=PLAN),
            issue(10, '[REF] Refunds', 'Epic'),
            issue(7, 'Explore: idea', comments=[
                comment("Deferred at the user's request on 2026-01-04.", '2026-01-04T10:00:00Z'),
                comment("Resumed at the user's request on 2026-01-05.", '2026-01-05T10:00:00Z', 'NONE')]),
            issue(8, 'Bug', **TAKEN, events=[assigned('nkhus', '2026-01-05T08:30:00Z')],
                  blockedBy={'nodes': [{'number': 3, 'state': 'CLOSED'}, {'number': 2, 'state': 'OPEN'}]}),
            issue(11, '[UI] Typo on the login page', 'Task', body=PLAN),
            issue(12, 'Search is slow', **closing),
            issue(13, 'Export', **TAKEN),
            issue(14, "Someone else's fix", assignees={'nodes': [{'login': 'alice'}]}),
            issue(15, 'Lesson: flaky CI'),
            issue(1, '[PAY] Payments', 'Initiative')]},
        'open': {'nodes': [
            pull(30, 'Tokens API', [9], decision='CHANGES_REQUESTED', committed='2026-01-05T11:00:00Z',
                 rollup={'state': 'SUCCESS'}, additions=120, deletions=4, changedFiles=5,
                 body='## Summary\n<!-- What and why -->\n- Adds the token API.\n- Rotates keys.\n\n## Tests\n- ok',
                 events=[{'__typename': 'ConvertToDraftEvent', 'createdAt': '2026-01-05T09:30:00Z'},
                         {'__typename': 'ReadyForReviewEvent', 'createdAt': '2026-01-05T10:00:00Z'},
                         {'__typename': 'PullRequestReview', 'state': 'CHANGES_REQUESTED',
                          'submittedAt': '2026-01-05T10:30:00Z'},
                         {'__typename': 'PullRequestReview', 'state': 'COMMENTED', 'submittedAt': '2026-01-05T10:40:00Z'}]),
            pull(31, 'Draft', draft=True),
            pull(32, 'Fix VAT rounding', body='Rounds VAT per line.', comments=[
                comment("Held at the user's request on 2026-01-05.")]),
            pull(33, 'Faster search', [12], decision='CHANGES_REQUESTED', committed='2026-01-05T11:00:00Z',
                 events=[{'__typename': 'PullRequestReview', 'state': 'CHANGES_REQUESTED',
                          'submittedAt': '2026-01-05T11:30:00Z'}])]},
        'merged': {'nodes': [{'number': 29, 'title': 'Old', 'url': 'p/29', 'mergedAt': '2026-01-04T10:00:00Z',
                              'baseRefName': 'main'}]},
    }


def entries():
    """What status.py reads: open Epics and standalone Tasks."""
    return [{'number': 2, 'title': '[PAY][TOKEN] Tokens', 'url': 'u/2', 'labels': labels('Epic'), **TAKEN,
             'parent': {'number': 1, 'title': '[PAY] Payments'},
             'subIssues': {'totalCount': 2, 'nodes': [{'number': 5, 'title': '[PAY][TOKEN] Column', 'state': 'OPEN'},
                                                      {'number': 6, 'title': '[PAY][TOKEN] Old', 'state': 'CLOSED'}]},
             'blockedBy': {'nodes': []}},
            {'number': 11, 'title': '[UI] Typo on the login page', 'url': 'u/11', 'labels': labels('Task'),
             'body': PLAN, 'parent': None, 'blockedBy': {'nodes': []}}]


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
            'pageInfo': {'hasNextPage': False, 'endCursor': None}, 'nodes': entries()}}}})
    return run


def test_collect_builds_the_work_tree_from_github_signals():
    github = board.collect('owner/name', runner())
    work = {item['number']: item for item in github['work']}
    assert work[1]['kind'] == 'Initiative' and work[1]['progress'] == {'done': 1, 'total': 3}
    assert work[2]['parent'] == 1 and work[2]['progress'] == {'done': 1, 'total': 2}
    assert work[2]['status'] == 'taken' and work[9]['status'] == 'taken' and work[11]['status'] == 'ready'
    assert work[5]['parent'] == 2 and work[5]['status'] == 'todo' and 6 not in work
    assert 'crew' not in work[2] and 'session' not in work[2]
    # Untyped Issues nobody holds and nobody planned need a plan; a held one does not, whoever holds it.
    assert [(item['number'], item['kind']) for item in github['planning']] == [
        (7, 'Exploration'), (15, 'needs-planning')]
    # A wait is the first open native blocker.
    assert github['tree']['waits'] == {8: 2}
    pulls = {pull['number']: pull for pull in github['pulls']}
    assert pulls[30]['checks'] == 'passing' and pulls[30]['closes'] == [9]
    assert pulls[30]['changes'] == ['Adds the token API.', 'Rotates keys.']
    assert pulls[32]['changes'] == ['Rounds VAT per line.'] and pulls[31]['changes'] == []
    assert pulls[31]['checks'] == 'none' and github['merged'][0]['number'] == 29
    # Changes requested and pushed since is ready again; changes requested after the last push is sent back.
    assert pulls[30]['sent_back'] is False and pulls[33]['sent_back'] is True
    # Only the comments of the owner, members, and collaborators count.
    assert github['deferred'] == [7] and github['held'] == [32]
    assert board.lineage(github['work'], 5) == [1, 2]
    assert 'pool' not in github


def test_anyone_else_gets_the_work_read_only():
    github = board.collect('owner/name', runner())
    # A state file without `reported` is no overlay: nothing in it shows.
    state = {'questions': [{'id': 'q1', 'text': 'Which PSP?'}], 'crews': [{'name': '[dev-lead] x', 'state': 'working'}],
             'mode': 'on', 'limit': 3, 'summary': SUMMARY, 'queue': [{'issue': 13, 'after': 8}]}
    document = board.snapshot('owner/name', github, state, NOW)
    assert document['owner'] is False and document['crews'] == [] and document['questions'] == []
    assert (document['mode'], document['limit'], document['summary']) == (None, None, {})
    assert document['answered'] == [] and 'pool' not in document
    tasks = {card['number']: card for card in document['board']['tasks']}
    assert {number: card['stage'] for number, card in tasks.items() if number in {5, 8, 10, 13, 14}} == {
        5: 'backlog', 8: 'progress', 10: 'plan', 13: 'progress', 14: 'progress'}
    assert all(card['crew'] is None for card in tasks.values())
    assert document['queue'] == [{'issue': 11, 'action': 'take', 'title': '[UI] Typo on the login page'}]
    # Without the overlay's mode, ready PRs wait for a merge as in a pool whose autonomous mode is off.
    assert [item['kind'] for item in document['waiting']] == ['merge']


def test_owner_crews_join_their_issues_and_order_by_attention():
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
    # The planner's Issue is blocked by #2, so a quiet planner is not stuck; a crew without `issue` holds nothing.
    assert crews[3]['issue'] == 8 and crews[3]['title'] == 'Bug' and crews[3]['stuck'] == '' and crews[4]['issue'] is None
    old = board.crews(github, [{'name': '[designer] look', 'state': 'idle', 'background': 'build',
                                'since': (NOW - timedelta(hours=4)).isoformat()}], NOW)
    assert old[0]['state'] == 'stuck' and 'background run' in old[0]['stuck']
    document = board.snapshot('o/n', github, {**OWNER, 'crews': reported}, NOW)
    assert document['owner'] is True and [crew['name'] for crew in document['crews']][0] == '[dev-lead] stray'
    assert (document['mode'], document['limit'], document['summary']) == ('off', 3, SUMMARY)
    odd = board.snapshot('o/n', github, {**OWNER, 'mode': 'maybe', 'limit': True, 'summary': 'text'}, NOW)
    assert (odd['mode'], odd['limit'], odd['summary']) == (None, None, {})


def test_waiting_lists_questions_and_merges():
    github = board.collect('owner/name', runner())
    crews = [{'name': '[dev-lead] pay tokens', 'session_id': 'sess-42', 'state': 'waiting', 'question': 'Which PSP?'},
             {'name': '[designer] look', 'state': 'waiting', 'question': 'Calm or dense?'}]
    state = {**OWNER, 'crews': crews, 'questions': [
        {'id': 'q1', 'crew': '[dev-lead] pay tokens', 'issue': 5, 'text': 'Which PSP?'},
        {'id': 2, 'text': 'Ship on Friday?'}]}
    document = board.snapshot('owner/name', github, state, NOW)
    kinds = [(item['kind'], item.get('crew'), item.get('pull')) for item in document['waiting']]
    # The pay crew's question is reported, so only the designer's gets one from its crew entry. While autonomous mode
    # is off, ready PRs into main wait for the user; #32 is held and #33 was sent back.
    assert sorted(kinds, key=str) == sorted([
        ('question', '[dev-lead] pay tokens', None), ('orchi', 'Orchi', None), ('question', '[designer] look', None),
        ('merge', None, 30)], key=str)
    assert [item['kind'] for item in board.snapshot('o/n', github, {**state, 'mode': 'on'}, NOW)['waiting']] == [
        'question', 'orchi', 'question']


def test_questions_come_from_the_owner_overlay_until_answered():
    github = board.collect('owner/name', runner())
    reported = [{'id': 'q1', 'crew': '[dev-lead] pay tokens', 'issue': 5, 'kind': 'question', 'blocking': True,
                 'text': 'Which PSP?', 'request_id': 'req-7', 'context': ['Stripe is in use.'],
                 'choices': [{'label': 'Stripe', 'detail': 'Known', 'recommended': True}, {'label': 'Adyen'}]},
                {'id': 'q3', 'crew': '[planner] refunds', 'issue': 10, 'kind': 'plan',
                 'text': 'Approve the plan for #10?', 'plan': ['#20 Model', '#21 API']},
                {'id': 'q4', 'crew': 'Orchi', 'text': 'Release #8?', 'assumed': 'Keep', 'context': 'Quiet for an hour.'}]
    document = board.snapshot('o/n', github, {**OWNER, 'questions': reported}, NOW)
    open_ = {question['id']: question for question in document['questions']}
    assert set(open_) == {'q1', 'q3', 'q4'}
    q1 = open_['q1']
    assert q1['issue'] == 5 and q1['request_id'] == 'req-7' and q1['blocking'] and q1['text'] == 'Which PSP?'
    assert q1['choices'][0] == {'label': 'Stripe', 'detail': 'Known', 'recommended': True}
    assert open_['q4']['blocking'] is False and open_['q4']['context'] == ['Quiet for an hour.']
    assert open_['q3']['kind'] == 'plan' and open_['q3']['plan'] == ['#20 Model', '#21 API']
    # Blocking first.
    assert [question['blocking'] for question in document['questions']] == [True, True, False]
    assert document['answered'] == []
    sent = {**OWNER, 'questions': reported,
            'sent': [{'id': 'q1', 'crew': '[dev-lead] pay tokens', 'answer': 'Stripe', 'at': '2026-01-05T11:50:00Z'},
                     {'id': 'q9', 'answer': 'Yes', 'question': 'Gone?', 'at': '2026-01-05T11:40:00Z'},
                     {'id': 'q8', 'answer': 'No', 'question': 'Old?', 'at': '2026-01-04T11:40:00Z'}]}
    document = board.snapshot('o/n', github, sent, NOW)
    assert 'q1' not in {question['id'] for question in document['questions']}
    assert [(entry['id'], entry['picked']) for entry in document['answered']] == [('q1', False), ('q9', True)]
    later = board.snapshot('o/n', github, sent, NOW + timedelta(hours=2))
    assert 'q1' in {question['id'] for question in later['questions']}


def test_board_places_every_card_in_one_column():
    github = board.collect('owner/name', runner())
    crews = [{'name': '[planner] bug', 'session_id': 'sess-8', 'state': 'working', 'doing': 'Writing the plan',
              'issue': 8}]
    questions = [{'id': 'q1', 'crew': '[dev-lead] pay tokens', 'issue': 5, 'text': 'Which PSP?'},
                 {'id': 'q3', 'crew': '[planner] refunds', 'issue': 10, 'kind': 'plan', 'text': 'Approve?'}]
    document = board.snapshot('o/n', github, {**OWNER, 'crews': crews, 'questions': questions}, NOW)
    tasks = {card['number']: card for card in document['board']['tasks']}
    stages = {number: card['stage'] for number, card in tasks.items()}
    assert stages == {5: 'ask', 6: 'done', 9: 'review', 3: 'done', 4: 'plan', 10: 'review', 11: 'backlog',
                      7: 'backlog', 15: 'plan', 8: 'progress', 12: 'progress', 13: 'backlog', 14: 'progress',
                      31: 'progress', 32: 'review'}
    assert tasks[5]['state'] == 'Which PSP?' and tasks[5]['detail'] == 'question' and tasks[5]['tone'] == 'orange'
    assert tasks[9]['detail'] == 'pr' and tasks[9]['state'] == 'ready to merge' and tasks[9]['pull']['number'] == 30
    assert tasks[10]['state'] == 'approve plan' and tasks[10]['group'] == '10' and tasks[10]['epic'] == 10
    assert tasks[8]['state'] == 'Writing the plan' and tasks[8]['crew'] == '[planner] bug'
    assert tasks[8]['waits_for'] == 2 and tasks[14]['crew'] is None and tasks[14]['state'] == 'in progress'
    assert tasks[32]['state'] == 'on hold' and tasks[32]['kind'] == 'PR' and tasks[7]['state'] == 'deferred'
    assert tasks[13]['state'] == 'queued after #8' and tasks[11]['state'] == 'queued'
    assert tasks[12]['state'] == 'PR #33 changes requested' and tasks[12]['back'] is True
    assert tasks[4]['kind'] == 'Exploration' and tasks[15]['kind'] == 'Issue'
    assert tasks[11]['kind'] == 'Task' and tasks[11]['group'] == 'outside' and tasks[11]['epic'] is None
    assert document['queue'] == [{'issue': 13, 'action': 'plan', 'title': 'Export', 'after': 8},
                                 {'issue': 11, 'action': 'take', 'title': '[UI] Typo on the login page'}]
    groups = {group['key']: group for group in document['board']['groups']}
    assert list(groups) == ['1', '10', 'outside']
    # Progress counts work items: a closed Epic by its sub-issue summary, an open one by its Tasks.
    assert groups['1']['stage'] == 'ask' and (groups['1']['done'], groups['1']['total']) == (3, 6)
    assert groups['10']['kind'] == 'Epic' and groups['10']['stage'] == 'review'
    assert groups['outside']['stage'] == 'review' and groups['outside']['counts']['backlog'] == 3
    epics = {epic['number']: epic for epic in document['board']['epics']}
    assert epics[2]['stage'] == 'ask' and epics[2]['counts'] == {
        'plan': 0, 'backlog': 0, 'progress': 0, 'ask': 1, 'review': 1, 'done': 1}
    assert epics[3]['stage'] == 'done' and (epics[3]['done'], epics[3]['total']) == (2, 2)
    assert epics[4]['stage'] == 'plan' and epics[4]['group'] == '1' and epics[2]['total'] == 3


def test_history_comes_from_the_timelines():
    document = board.snapshot('o/n', board.collect('owner/name', runner()), {}, NOW)
    tasks = {card['number']: card for card in document['board']['tasks']}

    def moves(card):
        return [(entry.get('to'), entry.get('note') or entry.get('text'), entry.get('back')) for entry in card['history']]

    # Opened ready, back to draft, ready again, sent back by a review, then pushed and ready again.
    assert moves(tasks[9]) == [
        (None, 'PR #30 opened', None), ('review', 'PR #30', False), ('progress', 'PR #30 back to draft', True),
        ('review', 'PR #30 ready', False), ('progress', 'changes requested on PR #30', True),
        ('review', 'PR #30 updated', False)]
    assert tasks[9]['back'] is False and tasks[12]['back'] is True
    assert moves(tasks[8]) == [('progress', 'assigned to @nkhus', False)]
    # A trusted Deferred counts; the untrusted Resumed after it does not.
    assert moves(tasks[7]) == [(None, 'Deferred at your request', None)]
    assert all('events' not in pull for pull in document['pulls'])


def test_cli_prints_the_snapshot_and_reports_errors(tmp_path, capsys):
    state = tmp_path / 'state.json'
    state.write_text(json.dumps({**OWNER, 'crews': [{'name': '[dev-lead] pay tokens', 'state': 'working',
                                                     'issue': 2}]}))
    calls = []
    assert board.main(['--json', '--state', str(state)], runner(calls), NOW) == 0
    document = json.loads(capsys.readouterr().out)
    assert document['board']['groups'] and 'tree' not in document and document['owner'] is True
    assert document['repository'] == 'owner/name' and document['crews'][0]['issue'] == 2
    assert '-F' not in [arg for call in calls for arg in call]
    assert board.main(['--state', str(tmp_path / 'missing.json'), '--repo', 'o/n'], runner(), NOW) == 0
    assert capsys.readouterr().out.endswith('0 active · 1 wait for you · 4 PRs\n')
    assert board.main(['--json', '--repo', 'not-a-repo'], runner(), NOW) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)['error'] and 'OWNER/NAME' in captured.err
    state.write_text('[]')
    assert board.main(['--state', str(state), '--repo', 'o/n'], runner(), NOW) == 2
