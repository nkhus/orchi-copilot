#!/usr/bin/env python3
"""Snapshot of an Orchi pool for its board canvas, built from GitHub alone: the work tree, the planning queue, PRs,
recent merges, and a column and history for every card, read from standard GitHub signals (assignees, linked branches
and PRs, sub-issues, native blocked-by relationships). With the live overlay Orchi reports on its owner's board, it
adds the crews, the open questions, the Summary, the autonomous mode, and the pool size; without it, the board shows
only the work and is read-only."""
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
        comments(last: 20) { nodes { body createdAt authorAssociation } }
        timelineItems(last: 20, itemTypes: [ASSIGNED_EVENT, CLOSED_EVENT, REOPENED_EVENT]) {
          nodes {
            __typename
            ... on AssignedEvent { createdAt assignee { ... on User { login } } }
            ... on ClosedEvent { createdAt }
            ... on ReopenedEvent { createdAt }
          }
        }
      }
    }
    open: pullRequests(first: 50, states: OPEN, orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes {
        number title url body isDraft baseRefName reviewDecision additions deletions changedFiles createdAt updatedAt
        closingIssuesReferences(first: 10) { nodes { number } }
        commits(last: 1) { nodes { commit { committedDate statusCheckRollup { state } } } }
        comments(last: 20) { nodes { body createdAt authorAssociation } }
        timelineItems(last: 30, itemTypes: [READY_FOR_REVIEW_EVENT, CONVERT_TO_DRAFT_EVENT, PULL_REQUEST_REVIEW]) {
          nodes {
            __typename
            ... on ReadyForReviewEvent { createdAt }
            ... on ConvertToDraftEvent { createdAt }
            ... on PullRequestReview { state submittedAt }
          }
        }
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
# The comments Orchi writes for the user's defer, resume, and hold requests. Only comments by the repository's owner,
# members, and collaborators count.
DEFER = re.compile(r"^(Deferred|Resumed) at the user's request", re.M)
HOLD = re.compile(r"^(Held|Released) at the user's request", re.M)
TRUSTED = {'OWNER', 'MEMBER', 'COLLABORATOR'}
# The order of the Crews tab: what needs a look first.
STATES = ('stuck', 'waiting', 'working', 'background', 'idle', 'free')
# A crew Orchi reports idle that holds an Issue, runs nothing, and waits for nothing looks stuck after STALL; a
# background run after LONG_RUN.
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
# A sent answer hides its question until Orchi stops reporting it, for at most SENT.
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


def latest(*values) -> str | None:
    """The latest of some ISO times, ignoring the unreadable ones."""
    times = [value for value in values if moment(value)]
    return max(times, key=moment) if times else None


def collect(repo: str, run: status.Runner = status.gh) -> dict:
    """GitHub state of the repository, shaped for the board."""
    owner, _, name = repo.partition('/')
    if not owner or not name:
        raise ValueError('Repository must be OWNER/NAME: ' + repo)
    data = json.loads(run(['api', 'graphql', '-f', 'query=' + QUERY, '-f', 'owner=' + owner,
                           '-f', 'name=' + name]))['data']['repository']
    # What an Issue waits for: its first open native blocker.
    waits = {}
    for node in data['recent']['nodes']:
        blockers = [blocker['number'] for blocker in (node.get('blockedBy') or {}).get('nodes', [])
                    if blocker.get('state') == 'OPEN']
        if blockers:
            waits[node['number']] = blockers[0]

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
    planning = [item(node['number'], 'Exploration' if kind_of(node) == 'Exploration' else 'needs-planning',
                     node['title'], node['url'], 'planning', None, None)
                for node in sorted(data['recent']['nodes'], key=lambda node: node['number'])
                if kind_of(node) in {'Exploration', 'Issue'} and status.stage(node) == 'unplanned']
    default = (data.get('defaultBranchRef') or {}).get('name')
    pulls = []
    for node in data['open']['nodes']:
        commits = node['commits']['nodes']
        commit = commits[0]['commit'] if commits else {}
        rollup = (commit.get('statusCheckRollup') or {}).get('state')
        events = pull_events(node)
        asked = [event['at'] for event in events if event['kind'] == 'changes']
        pulls.append({'number': node['number'], 'title': node['title'], 'url': node['url'], 'draft': node['isDraft'],
                      'base': node['baseRefName'], 'into_default': node['baseRefName'] == default,
                      'checks': CHECKS.get(rollup, 'none'), 'review': node.get('reviewDecision'),
                      'closes': [issue['number'] for issue in node['closingIssuesReferences']['nodes']],
                      'additions': node.get('additions') or 0, 'deletions': node.get('deletions') or 0,
                      'files': node.get('changedFiles') or 0, 'changes': changes(node.get('body')),
                      'created': node.get('createdAt'), 'committed': commit.get('committedDate'),
                      'updated': latest(node.get('updatedAt'), commit.get('committedDate')), 'events': events,
                      # Sent back: its latest review asks for changes and nothing was pushed since.
                      'sent_back': node.get('reviewDecision') == 'CHANGES_REQUESTED' and not (
                          asked and moment(commit.get('committedDate'))
                          and moment(commit['committedDate']) > moment(max(asked, key=moment)))})
    timeline = {node['number']: issue_events(node) for node in data['recent']['nodes']}
    merged = [{'number': node['number'], 'title': node['title'], 'url': node['url'], 'merged_at': node['mergedAt'],
               'base': node['baseRefName']} for node in data['merged']['nodes']]
    tree = {'initiatives': data['initiatives']['nodes'], 'epics': data['epics']['nodes'],
            'issues': data['recent']['nodes'], 'timeline': timeline, 'waits': waits,
            'standalone': [entry for entry in work if entry['kind'] == 'Task' and entry['parent'] is None]}
    return {'default_branch': default, 'work': work, 'planning': planning, 'pulls': pulls, 'merged': merged,
            'deferred': flagged(data['recent']['nodes'], DEFER, 'Deferred'),
            'held': flagged(data['open']['nodes'], HOLD, 'Held'), 'tree': tree}


def flagged(nodes: list[dict], pattern: re.Pattern, on: str) -> list[int]:
    """The Issues or PRs whose latest trusted comment matching the pattern says `on`: `Deferred` or `Held`."""
    numbers = []
    for node in nodes:
        said = [(moment(comment.get('createdAt')), match[1])
                for comment in (node.get('comments') or {}).get('nodes', [])
                if comment.get('authorAssociation') in TRUSTED and moment(comment.get('createdAt'))
                for match in pattern.finditer(comment.get('body') or '')]
        if said and max(said, key=lambda pair: pair[0])[1] == on:
            numbers.append(node['number'])
    return sorted(numbers)


def issue_events(node: dict) -> list[dict]:
    """An Issue's history: assignments that took it, closing and reopening, and the user's defer and resume."""
    events = []
    for event in (node.get('timelineItems') or {}).get('nodes', []):
        kind, at = event.get('__typename'), event.get('createdAt')
        if kind == 'AssignedEvent':
            login = (event.get('assignee') or {}).get('login')
            events.append({'at': at, 'to': 'progress', 'note': f'assigned to @{login}' if login else 'assigned',
                           'back': False})
        elif kind == 'ClosedEvent':
            events.append({'at': at, 'to': 'done', 'note': '', 'back': False})
        elif kind == 'ReopenedEvent':
            events.append({'at': at, 'text': 'Reopened'})
    for comment in (node.get('comments') or {}).get('nodes', []):
        if comment.get('authorAssociation') in TRUSTED:
            for match in DEFER.finditer(comment.get('body') or ''):
                events.append({'at': comment.get('createdAt'), 'text': match[1] + ' at your request'})
    return events


def pull_events(node: dict) -> list[dict]:
    """A PR's moves: marked ready for review, converted to draft, and reviews that approve or ask for changes."""
    kinds = {'ReadyForReviewEvent': 'ready', 'ConvertToDraftEvent': 'draft'}
    events = []
    for event in (node.get('timelineItems') or {}).get('nodes', []):
        kind = event.get('__typename')
        if kind in kinds:
            events.append({'at': event.get('createdAt'), 'kind': kinds[kind]})
        elif kind == 'PullRequestReview' and event.get('state') in {'CHANGES_REQUESTED', 'APPROVED'}:
            events.append({'at': event.get('submittedAt'),
                           'kind': 'changes' if event['state'] == 'CHANGES_REQUESTED' else 'approved'})
    return sorted((event for event in events if moment(event['at'])), key=lambda event: moment(event['at']))


def changes(body: str | None) -> list[str]:
    """The lines of a PR body's Summary section, without template comments: what changed, for the review card."""
    text = re.sub(r'<!--.*?-->', '', body or '', flags=re.S)
    section_ = re.search(r'^#+\s*Summary\s*$(.*?)(?=^#+\s|\Z)', text, re.M | re.S)
    lines = [line.strip().lstrip('-*').strip() for line in (section_[1] if section_ else text).splitlines()]
    return [line for line in lines if line][:6]


def lineage(work: list[dict], number: int | None) -> list[int]:
    """The Initiative and Epic an item sits in, outermost first: `[1, 2]` for Task 9 of Epic 2 of Initiative 1."""
    parents = {entry['number']: entry.get('parent') for entry in work}
    chain = []
    while number in parents and parents[number] and parents[number] not in chain:
        number = parents[number]
        chain.insert(0, number)
    return chain


def merging(github: dict) -> set[int]:
    return {number for pull in github['pulls'] if not pull['draft'] for number in pull['closes']}


def crews(github: dict, reported: list[dict], now: datetime) -> list[dict]:
    """The crews Orchi reported, joined with the Issue each holds and ordered by what needs a look first.

    A crew's state is Orchi's reading of the app (`working`, `waiting`, `idle`, `stuck`, or `free`); an idle crew with
    a named background run shows as `background`. An idle crew that holds an Issue, waits for no other Issue and no
    merge of its PR, and has been quiet for STALL shows as `stuck`, as does a background run older than LONG_RUN."""
    # A taken Issue without a type is no work item; its title and link come from the recent Issues.
    items = {node['number']: {'title': node['title'], 'url': node['url']} for node in github['tree']['issues']}
    items.update({entry['number']: entry for entry in github['work'] + github['planning']})
    waits = github['tree'].get('waits') or {}
    pending = merging(github)
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
              and not waits.get(issue) and issue not in pending):
            state, reason = 'stuck', 'idle while it holds work'
        entry = items.get(issue) or {}
        joined.append({**crew, 'name': name, 'role': role(name), 'issue': issue, 'state': state, 'stuck': reason,
                       'title': entry.get('title'), 'url': entry.get('url'), 'progress': entry.get('progress'),
                       'path': lineage(github['work'], issue)})
    return sorted(joined, key=lambda crew: STATES.index(crew['state']))


def kept(state: dict, joined: list[dict], now: datetime) -> tuple[list[dict], list[dict]]:
    """The user's open questions and the answers of today, from Orchi's live overlay.

    A question is what Orchi reported through `update_pool`; a waiting crew whose question Orchi did not report yet
    gets one. An answer the board sent hides its question for SENT while Orchi picks it up, and counts as picked up
    once Orchi no longer reports the question."""
    asked = {}
    for position, question in enumerate(state.get('questions') or []):
        if isinstance(question, dict):
            key = str(question.get('id') or f'orchi-{position + 1}')
            asked[key] = {**question, 'id': key}
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
        if key in sent and (moment(sent[key].get('at')) or now - SENT) > now - SENT:
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


def ready(pull: dict) -> bool:
    """A PR waits for the user's review: into the default branch, not a draft, and not sent back."""
    return not pull['draft'] and pull['into_default'] and not pull.get('sent_back')


def mergeable(pull: dict) -> bool:
    return ready(pull) and pull['checks'] in {'passing', 'none'}


def build(github: dict, document: dict, now: datetime) -> dict:
    """The board's three levels: groups (Initiatives, standalone Epics, and Outside Initiatives), their Epics, and
    the cards inside, each in one column. A container takes the column of its cards in ATTENTION order; one with no
    open card shows itself as its only card."""
    tree = github.get('tree') or {}
    pulls = github['pulls']
    crews_by_issue = {crew['issue']: crew for crew in document['crews'] if crew.get('issue')}
    queued_after = {item['issue']: item.get('after') for item in document.get('queue') or [] if item.get('after')}
    deferred = set(github.get('deferred') or [])
    held = set(github.get('held') or [])
    asks = {}
    for question in document['questions']:
        if question['issue']:
            asks.setdefault(question['issue'], []).append(question)
    closing = {}
    for pull in pulls:
        for number in pull['closes']:
            closing.setdefault(number, []).append(pull)
    timeline = tree.get('timeline') or {}
    groups, epics, tasks, shown = [], [], [], set()

    def card(number, title, url, kind, group, epic, closed=False, signal='ready', pull=None):
        """One card; `signal` is the Issue's GitHub state from status.stage: taken, ready, or unplanned."""
        shown.add(number)
        questions = [question for question in asks.get(number, []) if question['blocking']]
        crew = crews_by_issue.get(number) or {}
        own = [pull] if pull else sorted(closing.get(number, []), key=lambda item: item['draft'])
        queued = queued_after.get(number)
        if closed:
            stage, detail = 'done', 'done'
        elif number in deferred and not questions:
            stage, detail = 'backlog', 'queued'
        elif questions:
            question = min(questions, key=lambda item: ATTENTION.index(ASKS[item['kind']]))
            stage, detail = ASKS[question['kind']], question['kind']
        elif any(ready(item) for item in own):
            stage, detail = 'review', 'pr'
        elif queued:
            stage, detail = 'backlog', 'queued'
        elif own or signal == 'taken' or crew:
            stage, detail = 'progress', 'run'
        elif signal == 'ready':
            stage, detail = 'backlog', 'queued'
        else:
            stage, detail = 'plan', 'needs-plan'
        pull_ = next((item for item in own if ready(item)), own[0] if own else None)
        name = crew.get('name')
        stuck = crew.get('state') == 'stuck'
        entry = {'key': str(number), 'number': number, 'title': title, 'url': url, 'kind': kind, 'group': group,
                 'epic': epic, 'stage': stage, 'detail': detail, 'crew': name, 'session': crew.get('session_id'),
                 'crew_state': crew.get('state'), 'waits_for': (tree.get('waits') or {}).get(number),
                 'queued_after': queued, 'deferred': number in deferred,
                 'held': bool(pull_ and pull_['number'] in held),
                 'questions': [q['id'] for q in asks.get(number, [])],
                 'pull': pull_ and {key: pull_[key] for key in ('number', 'url', 'title', 'draft', 'checks', 'review',
                                                               'additions', 'deletions', 'files', 'changes')}}
        entry['state'], entry['tone'] = describe(entry, questions, crew, stuck)
        entry['history'], entry['back'] = history(entry, timeline.get(number, []), own)
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
        if node['number'] not in shown and kind_of(node) not in {'Initiative', 'Epic'}:
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
    return kind or ('Exploration' if (node.get('title') or '').casefold().startswith(EXPLORE) else 'Issue')


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
            if card['held']:
                return 'on hold', 'orange'
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
        if pull and pull['review'] == 'CHANGES_REQUESTED':
            return f"PR #{pull['number']} changes requested", 'blue'
        return (f"draft PR #{pull['number']}" if pull and pull['draft'] else 'in progress'), 'blue'
    if stage == 'backlog':
        if card['deferred']:
            return 'deferred', 'grey'
        if card['waits_for']:
            return f"after #{card['waits_for']}", 'grey'
        if card['queued_after']:
            return f"queued after #{card['queued_after']}", 'grey'
        return 'queued', 'grey'
    return 'needs a plan', 'grey'


def short(text: str, width: int = 60) -> str:
    text = ' '.join(str(text).split())
    return text if len(text) <= width else text[:width - 1].rstrip() + '…'


def history(card: dict, events: list[dict], pulls: list[dict]) -> tuple[list[dict], bool]:
    """A card's moves from GitHub's timelines: its assignments, closing, the user's defer and resume, and its PRs opened,
    ready for review, approved, sent back by a review or a return to draft, and updated after that. A move from Your
    review back to In progress is a back-move; the card shows it until its next move."""
    entries = list(events)
    for pull in pulls:
        number, into = pull['number'], pull.get('into_default')
        if pull.get('created'):
            entries.append({'at': pull['created'], 'text': f'PR #{number} opened'})
        toggles = [event['kind'] for event in pull.get('events') or [] if event['kind'] in {'ready', 'draft'}]
        reviewable = toggles[0] == 'draft' if toggles else not pull['draft']
        if reviewable and into and pull.get('created'):
            entries.append({'at': pull['created'], 'to': 'review', 'note': f'PR #{number}', 'back': False})
        asked = None
        for event in pull.get('events') or []:
            if event['kind'] == 'ready':
                reviewable = True
                if into:
                    entries.append({'at': event['at'], 'to': 'review', 'note': f'PR #{number} ready', 'back': False})
            elif event['kind'] == 'draft':
                if reviewable and into:
                    entries.append({'at': event['at'], 'to': 'progress', 'note': f'PR #{number} back to draft',
                                    'back': True})
                reviewable = False
            elif event['kind'] == 'changes':
                asked = event['at']
                entries.append({'at': asked, 'to': 'progress', 'note': f'changes requested on PR #{number}',
                                'back': True})
            else:
                entries.append({'at': event['at'], 'text': f'PR #{number} approved'})
        if asked and reviewable and into and not pull.get('sent_back') and moment(pull.get('committed')) \
                and moment(pull['committed']) > moment(asked):
            entries.append({'at': pull['committed'], 'to': 'review', 'note': f'PR #{number} updated', 'back': False})
    entries = sorted((entry for entry in entries if moment(entry.get('at'))), key=lambda entry: moment(entry['at']))
    entries = entries[-HISTORY:]
    last = next((entry for entry in reversed(entries) if entry.get('to')), None)
    return entries, bool(last and last.get('back') and last.get('to') == card['stage'])


def queue(github: dict, document: dict) -> list[dict]:
    """Work that starts when a crew is free: the Issues Orchi reports a planner keeps queued, then planned Epics and
    standalone Tasks nobody holds, that wait for nothing and that the user did not defer."""
    deferred = set(github.get('deferred') or [])
    items = [{'issue': item['issue'], 'action': item.get('action') or 'take', 'title': item.get('title') or '',
              **({'after': item['after']} if item.get('after') else {})}
             for item in document.get('queue') or [] if isinstance(item, dict) and isinstance(item.get('issue'), int)]
    listed = {item['issue'] for item in items}
    for entry in github['work']:
        if (entry['kind'] in {'Epic', 'Task'} and entry['status'] == 'ready' and not entry['waits_for']
                and entry['number'] not in deferred | listed):
            items.append({'issue': entry['number'], 'action': 'take', 'title': entry['title']})
    return items


def waiting(document: dict) -> list[dict]:
    """What waits for the user: the questions that block a crew or Orchi, and, unless autonomous mode is on, PRs
    into the default branch that are ready to merge (not a draft, not sent back, checks green) and not held."""
    items = [{'kind': 'question' if question['crew'] != 'Orchi' else 'orchi', 'id': question['id'],
              'crew': question['crew'], 'issue': question['issue'], 'text': question['text']}
             for question in document['questions'] if question['blocking']]
    if document.get('mode') != 'on':
        held = set(document.get('held') or [])
        items += [{'kind': 'merge', 'pull': pull['number'], 'text': pull['title']} for pull in document['pulls']
                  if mergeable(pull) and pull['number'] not in held]
    return items


def snapshot(repo: str, github: dict, state: dict, now: datetime) -> dict:
    """The document the board renders. Its owner, whose Orchi reports the live overlay, gets the crews, questions,
    Summary, autonomous mode, and pool size from it; anyone else gets the work as GitHub shows it, read-only."""
    owner = bool(state.get('reported'))
    overlay = state if owner else {}
    limit = overlay.get('limit')
    document = {'repository': repo, 'updated': now.isoformat(timespec='seconds'), 'error': None, 'owner': owner,
                'reported': state.get('reported'),
                'mode': overlay.get('mode') if overlay.get('mode') in {'on', 'off'} else None,
                'limit': limit if isinstance(limit, int) and not isinstance(limit, bool) and limit > 0 else None,
                'summary': overlay.get('summary') if isinstance(overlay.get('summary'), dict) else {},
                **{key: value for key, value in github.items() if key != 'tree'}}
    document['crews'] = crews(github, overlay.get('crews') or [], now)
    document['questions'], document['answered'] = kept(overlay, document['crews'], now) if owner else ([], [])
    document['queue'] = queue(github, overlay)
    document['board'] = build(github, document, now)
    document['waiting'] = waiting(document)
    document['pulls'] = [{key: value for key, value in pull.items() if key != 'events'} for pull in github['pulls']]
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
    parser.add_argument('--state', help="JSON file with Orchi's live overlay: crews, questions, sent answers")
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
        repo = repo or json.loads(run(['repo', 'view', '--json', 'nameWithOwner']))['nameWithOwner']
        document = snapshot(repo, collect(repo, run), state, now)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        detail = str(getattr(error, 'stderr', '') or error).strip()
        document = {'repository': repo, 'updated': now.isoformat(timespec='seconds'), 'error': detail}
        print(f'Orchi board error: {detail}', file=sys.stderr)
    print(json.dumps(document, ensure_ascii=False, indent=1) if args.json else summary(document))
    return 2 if document['error'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
