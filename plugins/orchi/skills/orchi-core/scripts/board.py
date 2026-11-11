#!/usr/bin/env python3
"""Read-only snapshot of an Orchi pool for its board canvas: the work tree, the planning queue, PRs, recent merges,
the crews as Orchi last reported them, the questions kept in Issue and PR comments, and a stage for every card."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta

import status

QUERY = '''
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { name }
    initiatives: issues(first: 20, states: OPEN, labels: ["Initiative"], orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes {
        number title url labels(first: 20) { nodes { name } } %s
        subIssues(first: 50) { totalCount nodes {
          number title url state labels(first: 10) { nodes { name } } subIssuesSummary { total completed } %s } }
      }
    }
    epics: issues(first: 50, states: OPEN, labels: ["Epic"], orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes {
        number title url labels(first: 10) { nodes { name } } parent { number } %s
        subIssues(first: 50) { nodes { number title url state labels(first: 10) { nodes { name } } %s } }
      }
    }
    recent: issues(first: 100, states: OPEN, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number title url labels(first: 10) { nodes { name } } parent { number } %s
        subIssues { totalCount } blockedBy(first: 10) { nodes { number state } }
        comments(last: 20) { nodes { body createdAt } }
      }
    }
    open: pullRequests(first: 50, states: OPEN, orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes {
        number title url body isDraft baseRefName reviewDecision additions deletions changedFiles
        closingIssuesReferences(first: 10) { nodes { number } }
        commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
        comments(last: 20) { nodes { body createdAt } }
      }
    }
    merged: pullRequests(first: 5, states: MERGED, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes { number title url mergedAt baseRefName }
    }
  }
}
'''.replace('%s', status.SIGNALS)
# An Issue whose title starts with this is an exploration: an idea being shaped before any plan.
EXPLORE = 'explore:'
TITLE = re.compile(r'\[([a-z-]+)\] ')
ROLES = {'researcher': 'Researcher', 'planner': 'Planner', 'designer': 'Designer', 'dev-lead': 'Dev lead'}
CHECKS = {'SUCCESS': 'passing', 'FAILURE': 'failing', 'ERROR': 'failing', 'PENDING': 'running', 'EXPECTED': 'running'}
# The order of the Crews tab: what needs a look first.
STATES = ('stuck', 'waiting', 'working', 'background', 'idle', 'free')
# A crew that holds an Issue, runs nothing, and waits for nothing looks stuck after STALL; a background run after
# LONG_RUN.
STALL = timedelta(minutes=30)
LONG_RUN = timedelta(hours=3)
# The board's columns, left to right, and the order in which a container takes the stage of its cards: what needs the
# user first. A container with no open card needs planning.
COLUMNS = {'plan': 'Needs planning', 'backlog': 'Backlog', 'progress': 'In progress', 'ask': 'Questions for you',
           'review': 'Your review', 'done': 'Done'}
ATTENTION = ('ask', 'review', 'progress', 'plan', 'backlog', 'done')
# Where a card with an open question goes: a question or a tool approval asks, a plan, design round, or merge waits
# for the user's review.
ASKS = {'question': 'ask', 'permission': 'ask', 'plan': 'review', 'design': 'review', 'merge': 'review'}
# A question or answer Orchi keeps in an Issue or PR comment: `<!-- orchi:question {"id": "q1", ...} -->`.
MARK = re.compile(r'<!--\s*orchi:(question|answer)\s+(\{.*?\})\s*-->', re.S)
# A sent answer hides its question until Orchi records the answer, for at most SENT.
SENT = timedelta(hours=1)
HISTORY = 20


def role(name: str) -> str | None:
    """The role a crew's name gives (`[dev-lead] pay`), or None for a name without one."""
    match = TITLE.match(name or '')
    return ROLES.get(match[1], match[1]) if match else None


def moment(value) -> datetime | None:
    """An ISO time with its offset (`Z` included), or None when it is missing, unreadable, or has no offset."""
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError, TypeError):
        return None
    return parsed if parsed.tzinfo else None


def collect(repo: str, run: status.Runner = status.gh) -> dict:
    """GitHub state of the repository, shaped for the board."""
    owner, _, name = repo.partition('/')
    if not owner or not name:
        raise ValueError('Repository must be OWNER/NAME: ' + repo)
    data = json.loads(run(['api', 'graphql', '-f', 'query=' + QUERY, '-f', 'owner=' + owner,
                           '-f', 'name=' + name]))['data']['repository']
    # What an Issue waits for: its first open native blocker.
    waits = {node['number']: blocker['number'] for node in data['recent']['nodes']
             for blocker in reversed((node.get('blockedBy') or {}).get('nodes', [])) if blocker['state'] == 'OPEN'}

    def item(number, kind, title, url, state, parent, progress):
        return {'number': number, 'kind': kind, 'title': title, 'url': url, 'status': state, 'parent': parent,
                'progress': progress, 'waits_for': waits.get(number)}

    work = []
    for node in data['initiatives']['nodes']:
        children = node['subIssues']
        work.append(item(node['number'], 'Initiative', node['title'], node['url'], status.stage(node), None,
                         {'done': sum(child['state'] == 'CLOSED' for child in children['nodes']),
                          'total': children['totalCount']}))
    for entry in status.report(status.fetch(repo, run)):
        work.append(item(entry['number'], entry['kind'], entry['title'], entry['url'], entry['status'],
                         entry['parent'], {'done': entry['tasks']['closed'], 'total': entry['tasks']['total']}
                         if entry['tasks'] else None))
    # An Epic's open Tasks, nested under it; status.py lists only Tasks without a parent.
    shown = {entry['number'] for entry in work}
    for node in data['epics']['nodes']:
        if node['number'] not in shown:
            continue
        for child in node['subIssues']['nodes']:
            if child['state'] != 'OPEN' or child['number'] in shown:
                continue
            work.append(item(child['number'], 'Task', child['title'], child['url'],
                             'taken' if status.taken(child) else 'todo', node['number'], None))
    # Issues without a type that nobody holds and nobody planned: explorations and requests that need a plan.
    planning = [item(node['number'], kind_of(node) if kind_of(node) == 'Exploration' else 'needs-planning',
                     node['title'], node['url'], 'planning', None, None)
                for node in sorted(data['recent']['nodes'], key=lambda node: node['number'])
                if kind_of(node) in {'Exploration', 'Issue'} and status.stage(node) == 'unplanned']
    default = (data.get('defaultBranchRef') or {}).get('name')
    pulls, comments = [], []
    for node in data['open']['nodes']:
        commits = node['commits']['nodes']
        rollup = ((commits[0]['commit'].get('statusCheckRollup') or {}) if commits else {}).get('state')
        pulls.append({'number': node['number'], 'title': node['title'], 'url': node['url'], 'draft': node['isDraft'],
                      'base': node['baseRefName'], 'into_default': node['baseRefName'] == default,
                      'checks': CHECKS.get(rollup, 'none'), 'review': node.get('reviewDecision'),
                      'closes': [issue['number'] for issue in node['closingIssuesReferences']['nodes']],
                      'additions': node.get('additions') or 0, 'deletions': node.get('deletions') or 0,
                      'files': node.get('changedFiles') or 0, 'changes': changes(node.get('body'))})
        comments += [{'number': node['number'], 'body': c['body'], 'created': c['createdAt']}
                     for c in (node.get('comments') or {}).get('nodes', [])]
    for node in data['recent']['nodes']:
        comments += [{'number': node['number'], 'body': c['body'], 'created': c['createdAt']}
                     for c in (node.get('comments') or {}).get('nodes', [])]
    merged = [{'number': node['number'], 'title': node['title'], 'url': node['url'], 'merged_at': node['mergedAt'],
               'base': node['baseRefName']} for node in data['merged']['nodes']]
    tree = {'initiatives': data['initiatives']['nodes'], 'epics': data['epics']['nodes'],
            'issues': data['recent']['nodes'], 'comments': comments,
            'waits': waits,
            'standalone': [entry for entry in work if entry['kind'] == 'Task' and entry['parent'] is None]}
    return {'default_branch': default, 'work': work, 'planning': planning, 'pulls': pulls, 'merged': merged,
            'tree': tree}


def changes(body: str | None) -> list[str]:
    """The lines of a PR body's Summary section, without template comments: what changed, for the review card."""
    text = re.sub(r'<!--.*?-->', '', body or '', flags=re.S)
    section = re.search(r'^#+\s*Summary\s*$(.*?)(?=^#+\s|\Z)', text, re.M | re.S)
    lines = [line.strip().lstrip('-*').strip() for line in (section[1] if section else text).splitlines()]
    return [line for line in lines if line][:6]


def lineage(work: list[dict], number: int | None) -> list[int]:
    """The Initiative and Epic an item sits in, outermost first: `[1, 2]` for Task 9 of Epic 2 of Initiative 1."""
    parents = {entry['number']: entry.get('parent') for entry in work}
    chain = []
    while number in parents and parents[number] and parents[number] not in chain:
        number = parents[number]
        chain.insert(0, number)
    return chain


def crews(github: dict, reported: list[dict], now: datetime) -> list[dict]:
    """The crews Orchi reported, joined with the Issue each holds and ordered by what needs a look first.

    A crew's state is Orchi's reading of the app (`working`, `waiting`, `idle`, `stuck`, or `free`); an idle crew with
    a named background run shows as `background`. An idle crew that holds an Issue, waits for no other Issue and no
    merge of its PR, and has been quiet for STALL shows as `stuck`, as does a background run older than LONG_RUN."""
    items = {entry['number']: entry for entry in github['work'] + github['planning']}
    merging = {number for pull in github['pulls'] if not pull['draft'] for number in pull['closes']}
    joined = []
    for crew in reported:
        name = crew.get('name') or ''
        issue = crew.get('issue')
        state = crew.get('state') if crew.get('state') in STATES else 'idle'
        quiet = moment(crew.get('since'))
        reason = crew.get('stuck') or ''
        if state == 'idle' and crew.get('background'):
            state = 'background'
            if quiet and now - quiet > LONG_RUN:
                state, reason = 'stuck', 'background run for hours: ' + crew['background']
        elif (state == 'idle' and issue and quiet and now - quiet > STALL
              and not (items.get(issue) or {}).get('waits_for') and issue not in merging):
            state, reason = 'stuck', 'idle while it holds work'
        entry = items.get(issue) or {}
        joined.append({**crew, 'name': name, 'role': role(name), 'issue': issue, 'state': state, 'stuck': reason,
                       'title': entry.get('title'), 'url': entry.get('url'), 'progress': entry.get('progress'),
                       'path': lineage(github['work'], issue)})
    return sorted(joined, key=lambda crew: STATES.index(crew['state']))


def kept(github: dict, state: dict, joined: list[dict], now: datetime) -> tuple[list[dict], list[dict]]:
    """The user's open questions and the answers of today.

    A question is what Orchi keeps in an Issue or PR comment, joined by id with what it reported through `update_pool`
    (the report wins: it carries the live `request_id`). A waiting crew whose question Orchi did not report yet gets
    one. A question is answered once Orchi's answer comment exists; an answer the board sent hides its question for
    SENT while Orchi picks it up."""
    asked, answers = {}, {}
    for comment in (github.get('tree') or {}).get('comments', []):
        for kind, raw in MARK.findall(comment.get('body') or ''):
            try:
                data = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(data, dict) or not data.get('id'):
                continue
            key = str(data['id'])
            if kind == 'question':
                asked[key] = {'issue': comment['number'], 'asked': comment['created'], **data, 'id': key}
            else:
                answers[key] = {'answer': str(data.get('answer') or ''), 'at': comment['created']}
    for position, question in enumerate(state.get('questions') or []):
        if isinstance(question, dict):
            key = str(question.get('id') or f'orchi-{position + 1}')
            asked[key] = {**asked.get(key, {}), **question, 'id': key}
    for crew in joined:
        if crew['state'] == 'waiting' and crew.get('question') and not any(
                question.get('crew') == crew['name'] and blocking(question) for question in asked.values()):
            key = 'crew:' + crew['name']
            asked.setdefault(key, {'id': key, 'crew': crew['name'], 'issue': crew.get('issue'),
                                   'text': crew['question'], 'asked': crew.get('since'), 'blocking': True})
    sent = {str(entry['id']): entry for entry in state.get('sent') or [] if isinstance(entry, dict) and entry.get('id')}
    open_, answered = [], []
    for key, question in asked.items():
        question = normal(question)
        if key in answers:
            answered.append({**brief(question), **answers[key], 'picked': True})
        elif key in sent and (moment(sent[key].get('at')) or now - SENT) > now - SENT:
            answered.append({**brief(question), 'answer': sent[key].get('answer') or '', 'at': sent[key]['at'],
                             'picked': False})
        else:
            open_.append(question)
    for key, entry in sent.items():
        if key not in asked:
            answered.append({'id': key, 'crew': entry.get('crew') or 'Orchi', 'issue': None,
                             'text': entry.get('question') or '', 'answer': entry.get('answer') or '',
                             'at': entry.get('at'), 'picked': True})
    today = now.date()
    answered = [entry for entry in answered if (moment(entry.get('at')) or now).astimezone(now.tzinfo).date() == today]
    open_.sort(key=lambda question: (not question['blocking'], question.get('asked') or ''))
    return open_, sorted(answered, key=lambda entry: entry.get('at') or '', reverse=True)


def blocking(question: dict) -> bool:
    """A question blocks its crew unless it says otherwise or names what the crew assumes meanwhile."""
    return bool(question['blocking']) if 'blocking' in question else not question.get('assumed')


def normal(question: dict) -> dict:
    """A question in the board's shape, whatever subset of the fields Orchi wrote."""
    def texts(value):
        return [str(item) for item in ([value] if isinstance(value, str) else value or []) if str(item).strip()]

    choices = [{'label': str(choice['label']), 'detail': str(choice.get('detail') or ''),
                'recommended': bool(choice.get('recommended'))}
               for choice in question.get('choices') or [] if isinstance(choice, dict) and choice.get('label')]
    links = [{'label': str(link.get('label') or link.get('url')), 'url': str(link.get('url') or '')}
             for link in question.get('links') or [] if isinstance(link, dict) and (link.get('url') or link.get('label'))]
    issue = question.get('issue')
    return {'id': question['id'], 'crew': question.get('crew') or 'Orchi',
            'issue': issue if isinstance(issue, int) else None,
            'kind': question.get('kind') if question.get('kind') in ASKS else 'question',
            'blocking': blocking(question), 'assumed': question.get('assumed') or '',
            'text': str(question.get('text') or ''), 'context': texts(question.get('context')), 'choices': choices,
            'plan': texts(question.get('plan')), 'request_id': question.get('request_id') or '', 'links': links,
            'asked': question.get('asked') or ''}


def brief(question: dict) -> dict:
    return {key: question[key] for key in ('id', 'crew', 'issue', 'text')}


def build(github: dict, document: dict, previous: dict | None, now: datetime) -> dict:
    """The board's three levels: groups (Initiatives, standalone Epics, and Outside Initiatives), their Epics, and
    the cards inside, each in one column. A container takes the column of its cards in ATTENTION order; one with no
    open card shows itself as its only card."""
    tree = github.get('tree') or {}
    pulls = github['pulls']
    crews_by_issue = {crew['issue']: crew for crew in document['crews'] if crew.get('issue')}
    deferred = set(document.get('deferred') or [])
    merges = set(document.get('merges') or [])
    overrides = {str(key): value for key, value in (document.get('stages') or {}).items() if value in COLUMNS}
    asks = {}
    for question in document['questions']:
        if question['issue']:
            asks.setdefault(question['issue'], []).append(question)
    closing = {}
    for pull in pulls:
        for number in pull['closes']:
            closing.setdefault(number, []).append(pull)
    old = {card['key']: card for card in ((previous or {}).get('board') or {}).get('tasks') or []}
    moves = {}
    for move in document.get('moves') or []:
        if isinstance(move, dict) and isinstance(move.get('number'), int):
            moves.setdefault(move['number'], []).append(move)
    groups, epics, tasks, shown = [], [], [], set()

    def ready(pull):
        return not pull['draft'] and (pull['into_default'] or pull['number'] in merges)

    def card(number, title, url, kind, group, epic, closed=False, signal='ready', pull=None):
        """One card; `signal` is the Issue's GitHub state from status.stage: taken, ready, or unplanned."""
        shown.add(number)
        questions = [question for question in asks.get(number, []) if question['blocking']]
        crew = crews_by_issue.get(number) or {}
        own = [pull] if pull else sorted(closing.get(number, []), key=lambda item: item['draft'])
        if closed:
            stage, detail = 'done', 'done'
        elif number in deferred and not questions:
            stage, detail = 'backlog', 'queued'
        elif questions:
            question = min(questions, key=lambda item: ATTENTION.index(ASKS[item['kind']]))
            stage, detail = ASKS[question['kind']], question['kind']
        elif any(ready(item) for item in own):
            stage, detail = 'review', 'pr'
        elif own or signal == 'taken' or crew:
            stage, detail = 'progress', 'run'
        elif kind in {'Task', 'PR'} and signal != 'unplanned':
            stage, detail = 'backlog', 'queued'
        else:
            stage, detail = 'plan', 'needs-plan'
        if not closed and overrides.get(str(number)):
            stage = overrides[str(number)]
        pull_ = next((item for item in own if ready(item)), own[0] if own else None)
        name = crew.get('name')
        stuck = crew.get('state') == 'stuck'
        entry = {'key': str(number), 'number': number, 'title': title, 'url': url, 'kind': kind, 'group': group,
                 'epic': epic, 'stage': stage, 'detail': detail, 'crew': name, 'session': crew.get('session_id'),
                 'crew_state': crew.get('state'), 'waits_for': (tree.get('waits') or {}).get(number),
                 'deferred': number in deferred, 'questions': [q['id'] for q in asks.get(number, [])],
                 'pull': pull_ and {key: pull_[key] for key in ('number', 'url', 'title', 'draft', 'checks', 'review',
                                                               'additions', 'deletions', 'files', 'changes')}}
        entry['state'], entry['tone'] = describe(entry, questions, crew, stuck)
        entry['history'], entry['back'] = history(entry, old.get(entry['key']), moves.get(number, []), previous, now)
        tasks.append(entry)
        return entry

    def container(cards):
        stages = [item['stage'] for item in cards]
        # Progress counts work items; an Epic's own card only stands in for it while it has no open Task.
        work = [item['stage'] for item in cards if item['kind'] not in ('Epic', 'Initiative')]
        return {'stage': next((stage for stage in ATTENTION if stage in stages), 'plan') if stages else 'plan',
                'done': work.count('done'), 'total': len(work),
                'counts': {stage: stages.count(stage) for stage in COLUMNS}}

    def children(node, group, epic):
        """The cards of an Epic: its Tasks, and itself when it asks something or has no open Task."""
        made = [card(child['number'], child['title'], child['url'], kind_of(child), group, epic,
                     child['state'] == 'CLOSED', status.stage(child)) for child in node['subIssues']['nodes']]
        if not [item for item in made if item['stage'] != 'done'] or any(
                question['blocking'] for question in asks.get(node['number'], [])):
            made.append(card(node['number'], node['title'], node['url'], kind_of(node), group, epic,
                             signal=status.stage(node)))
        return made

    open_epics = {node['number']: node for node in tree.get('epics') or []}
    initiatives = {node['number'] for node in tree.get('initiatives') or []}
    for node in tree.get('initiatives') or []:
        key, inside, start = str(node['number']), [], len(epics)
        shown.add(node['number'])
        for child in node['subIssues']['nodes']:
            number = child['number']
            if child['state'] == 'CLOSED':
                summary_ = child.get('subIssuesSummary') or {}
                made = [card(number, child['title'], child['url'], kind_of(child), key, number, True)]
                totals = {'done': summary_.get('completed') or 1, 'total': summary_.get('total') or 1}
            elif number in open_epics:
                made = children(open_epics[number], key, number)
                totals = {}
            else:
                made = [card(number, child['title'], child['url'], kind_of(child), key, number,
                             signal=status.stage(child))]
                totals = {}
            epics.append({'number': number, 'title': child['title'], 'url': child['url'], 'kind': kind_of(child),
                          'group': key, **container(made), **totals})
            inside += made
        if not node['subIssues']['nodes']:
            made = [card(node['number'], node['title'], node['url'], 'Initiative', key, node['number'],
                         signal=status.stage(node))]
            epics.append({'number': node['number'], 'title': node['title'], 'url': node['url'], 'kind': 'Initiative',
                          'group': key, **container(made)})
            inside += made
        groups.append({'key': key, 'number': node['number'], 'title': node['title'], 'url': node['url'],
                       'kind': 'Initiative', 'epics': len(node['subIssues']['nodes']), **container(inside),
                       'done': sum(item['done'] for item in epics[start:]),
                       'total': sum(item['total'] for item in epics[start:])})
    for node in tree.get('epics') or []:
        if node['number'] in shown or (node.get('parent') or {}).get('number') in initiatives:
            continue
        key = str(node['number'])
        made = children(node, key, node['number'])
        groups.append({'key': key, 'number': node['number'], 'title': node['title'], 'url': node['url'],
                       'kind': 'Epic', 'epics': 0, **container(made)})
    outside = []
    for entry in tree.get('standalone') or []:
        if entry['number'] not in shown:
            outside.append(card(entry['number'], entry['title'], entry['url'], 'Task', 'outside', None,
                                signal=entry['status'] if entry['status'] in {'taken', 'unplanned'} else 'ready'))
    for entry in github['planning']:
        if entry['number'] not in shown:
            outside.append(card(entry['number'], entry['title'], entry['url'], entry['kind'] if entry['kind'] ==
                                'Exploration' else 'Issue', 'outside', None, signal='unplanned'))
    for node in tree.get('issues') or []:
        names = labels(node)
        if node['number'] not in shown and not any(status.labelled(names, kind) for kind in ('Initiative', 'Epic')):
            outside.append(card(node['number'], node['title'], node['url'], kind_of(node), 'outside', None,
                                signal=status.stage(node)))
    for pull in pulls:
        if not pull['closes'] and pull['number'] not in shown:
            outside.append(card(pull['number'], pull['title'], pull['url'], 'PR', 'outside', None, pull=pull))
    if outside:
        groups.append({'key': 'outside', 'number': None, 'title': 'Outside Initiatives', 'url': None,
                       'kind': 'Outside', 'epics': 0, **container(outside)})
    return {'columns': [{'key': key, 'title': title, 'you': key in {'ask', 'review'}} for key, title in COLUMNS.items()],
            'groups': groups, 'epics': epics, 'tasks': tasks}


def labels(node: dict) -> list[str]:
    return status.names(node.get('labels'), 'name')


def kind_of(node: dict) -> str:
    names = labels(node)
    kind = next((kind for kind in ('Initiative', 'Epic', 'Task') if status.labelled(names, kind)), None)
    return kind or ('Exploration' if node.get('title', '').casefold().startswith(EXPLORE) else 'Issue')


def describe(card: dict, questions: list[dict], crew: dict, stuck: bool) -> tuple[str, str]:
    """A card's few words of state, and the tone of its dot."""
    stage, pull = card['stage'], card['pull']
    if stage == 'done':
        return 'done', 'green'
    if stage in {'ask', 'review'}:
        question = next((item for item in questions if ASKS[item['kind']] == stage), None)
        if question:
            return {'permission': 'tool approval', 'plan': 'approve plan', 'design': 'design round',
                    'merge': 'ready to merge'}.get(question['kind'], short(question['text'])), 'orange'
        if pull:
            if card['kind'] == 'PR':
                return 'PR, no Issue', 'orange'
            return ('ready to merge' if pull['checks'] in {'passing', 'none'} else f"checks {pull['checks']}"), 'orange'
        return COLUMNS[stage].lower(), 'orange'
    if stage == 'progress':
        if stuck:
            return short(crew.get('stuck') or 'stuck'), 'red'
        if crew.get('doing'):
            return short(crew['doing']), 'blue'
        if pull and pull['checks'] == 'failing':
            return f"PR #{pull['number']} checks failing", 'blue'
        return (f"draft PR #{pull['number']}" if pull and pull['draft'] else 'in progress'), 'blue'
    if stage == 'backlog':
        if card['waits_for']:
            return f"after #{card['waits_for']}", 'grey'
        return ('deferred' if card['deferred'] else 'queued'), 'grey'
    return 'needs a plan', 'grey'


def short(text: str, width: int = 60) -> str:
    text = ' '.join(str(text).split())
    return text if len(text) <= width else text[:width - 1].rstrip() + '…'


def history(card: dict, old: dict | None, moves: list[dict], previous: dict | None,
            now: datetime) -> tuple[list[dict], bool]:
    """A card's moves: those the board saw between two snapshots, who took it, and the notes Orchi reported. A move
    from Your review back to an earlier column is a back-move; the card shows it until its next move."""
    entries = list((old or {}).get('history') or [])
    at = now.isoformat(timespec='seconds')
    if old and old.get('stage') != card['stage']:
        back = old.get('stage') == 'review' and card['stage'] not in {'review', 'done'}
        entries.append({'at': at, 'from': old.get('stage'), 'to': card['stage'], 'back': back})
    elif not old and previous and card['stage'] != 'done':
        entries.append({'at': at, 'from': None, 'to': card['stage'], 'back': False})
    if card['crew'] and (old or {}).get('crew') != card['crew']:
        entries.append({'at': at, 'text': 'Taken by ' + card['crew']})
    for move in moves:
        entry = {'at': move.get('at') or at, 'to': move.get('to') if move.get('to') in COLUMNS else None,
                 'note': move.get('note') or '', 'back': bool(move.get('back'))}
        if not any(item.get('at') == entry['at'] and item.get('note') == entry['note'] for item in entries):
            entries.append(entry)
    entries.sort(key=lambda item: item.get('at') or '')
    entries = entries[-HISTORY:]
    last = next((item for item in reversed(entries) if item.get('to')), None)
    return entries, bool(last and last.get('back') and last.get('to') == card['stage'])


def waiting(document: dict) -> list[dict]:
    """What waits for the user: the questions that block a crew or Orchi, and PRs waiting for their yes to merge:
    those Orchi asked about, or, when Orchi named none and autonomous mode is off, PRs into the default branch that
    are ready to merge."""
    items = [{'kind': 'question' if question['crew'] != 'Orchi' else 'orchi', 'id': question['id'],
              'crew': question['crew'], 'issue': question['issue'], 'text': question['text']}
             for question in document['questions'] if question['blocking']]
    asked = document.get('merges')
    held = set(document.get('held') or [])
    items += [{'kind': 'merge', 'pull': pull['number'], 'text': pull['title']} for pull in document['pulls']
              if pull['number'] not in held and (pull['number'] in asked if asked is not None else
                                                 document.get('mode') == 'off' and pull['into_default']
                                                 and not pull['draft'] and pull['checks'] in {'passing', 'none'})]
    return items


def snapshot(repo: str, github: dict, state: dict, now: datetime, previous: dict | None = None) -> dict:
    """The document the board renders: GitHub state joined with what Orchi last reported."""
    github = dict(github)
    tree = github.pop('tree', {})
    document = {'repository': repo, 'updated': now.isoformat(timespec='seconds'), 'error': None,
                'mode': state.get('mode'), 'limit': state.get('limit'), 'reported': state.get('reported'),
                'merges': state.get('merges'), 'deferred': state.get('deferred') or [], 'held': state.get('held') or [],
                'stages': state.get('stages') or {}, 'moves': state.get('moves') or [],
                'summary': state.get('summary') or {}, 'queue': state.get('queue') or [], **github}
    document['crews'] = crews(github, state.get('crews') or [], now)
    document['questions'], document['answered'] = kept({'tree': tree}, state, document['crews'], now)
    document['board'] = build({**github, 'tree': tree}, document, previous, now)
    document['waiting'] = waiting(document)
    for name in ('stages', 'moves'):
        document.pop(name)
    return document


def summary(document: dict) -> str:
    """One line: the time of the snapshot and the counts the user scans for."""
    time = (document.get('updated') or '')[11:16]
    if document.get('error'):
        return f'{time} · board refresh failed: {document["error"]}'
    count = {state: sum(crew['state'] == state for crew in document['crews']) for state in STATES}
    line = (f"{time} · {count['working'] + count['waiting'] + count['background']} active · "
            f"{len(document['waiting'])} wait for you · {len(document['pulls'])} PRs")
    return line + (f" · {count['stuck']} stuck" if count['stuck'] else '')


def main(argv: list[str] | None = None, run: status.Runner = status.gh, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', help='OWNER/NAME; defaults to the current repository')
    parser.add_argument('--state', help='JSON file with what Orchi last reported: crews, mode, questions, merges')
    parser.add_argument('--previous', help='JSON file with the previous snapshot, to record the cards\' moves')
    parser.add_argument('--json', action='store_true', help='Print the snapshot instead of its summary line')
    args = parser.parse_args(argv)
    now = now or datetime.now().astimezone()
    repo = args.repo
    try:
        state = {}
        if args.state:
            try:
                with open(args.state, encoding='utf-8') as handle:
                    state = json.load(handle)
            except FileNotFoundError:
                state = {}
            if not isinstance(state, dict):
                raise ValueError('The board state must be a JSON object: ' + args.state)
        previous = None
        if args.previous:
            try:
                with open(args.previous, encoding='utf-8') as handle:
                    previous = json.load(handle)
            except (FileNotFoundError, ValueError):
                previous = None
        repo = repo or json.loads(run(['repo', 'view', '--json', 'nameWithOwner']))['nameWithOwner']
        document = snapshot(repo, collect(repo, run), state, now, previous if isinstance(previous, dict) else None)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        detail = str(getattr(error, 'stderr', '') or error).strip()
        document = {'repository': repo, 'updated': now.isoformat(timespec='seconds'), 'error': detail}
        print(f'Orchi board error: {detail}', file=sys.stderr)
    print(json.dumps(document, ensure_ascii=False, indent=1) if args.json else summary(document))
    return 2 if document['error'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
