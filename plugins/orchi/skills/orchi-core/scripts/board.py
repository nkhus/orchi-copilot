#!/usr/bin/env python3
"""Read-only snapshot of an Orchi pool for its board canvas: the work tree, the planning queue, PRs, recent merges,
and the crews as Orchi last reported them."""
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
    initiatives: issues(first: 50, states: OPEN, labels: ["Initiative"], orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes { number title url labels(first: 20) { nodes { name } } subIssues(first: 100) { totalCount nodes { state } } }
    }
    epics: issues(first: 100, states: OPEN, labels: ["Epic"]) {
      nodes { number subIssues(first: 100) { nodes { number title url state labels(first: 20) { nodes { name } } } } }
    }
    planning: issues(first: 50, states: OPEN, labels: ["needs-planning", "Exploration"],
                     orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes { number title url labels(first: 20) { nodes { name } } }
    }
    claimed: issues(first: 100, states: OPEN, labels: ["in-progress"]) { nodes { number body } }
    open: pullRequests(first: 50, states: OPEN, orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes {
        number title url isDraft baseRefName reviewDecision
        closingIssuesReferences(first: 10) { nodes { number } }
        commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
      }
    }
    merged: pullRequests(first: 5, states: MERGED, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes { number title url mergedAt baseRefName }
    }
  }
}
'''
# The work reference of a claim: `Assigned to [dev-lead] pay (<session id>) by Orchi on <date>`.
CLAIM = re.compile(r'Assigned to (\[[a-z-]+\] [^\n(]+?) \(([^)\s]+)\)')
WAITS = re.compile(r'waits for #(\d+)')
TITLE = re.compile(r'\[([a-z-]+)\] ')
ROLES = {'researcher': 'Researcher', 'planner': 'Planner', 'designer': 'Designer', 'dev-lead': 'Dev lead'}
CHECKS = {'SUCCESS': 'passing', 'FAILURE': 'failing', 'ERROR': 'failing', 'PENDING': 'running', 'EXPECTED': 'running'}
# The order of the Crews tab: what needs a look first.
STATES = ('stuck', 'waiting', 'working', 'background', 'idle', 'free')
# A crew that holds an Issue, runs nothing, and waits for nothing looks stuck after STALL; a background run after
# LONG_RUN.
STALL = timedelta(minutes=30)
LONG_RUN = timedelta(hours=3)


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
    claims, waits = {}, {}
    for node in data['claimed']['nodes']:
        body = node.get('body') or ''
        if match := CLAIM.search(body):
            claims[node['number']] = {'crew': match[1].strip(), 'session': match[2]}
        if match := WAITS.search(body):
            waits[node['number']] = int(match[1])

    def item(number, kind, title, url, state, parent, progress):
        claim = claims.get(number) or {}
        return {'number': number, 'kind': kind, 'title': title, 'url': url, 'status': state, 'parent': parent,
                'crew': claim.get('crew'), 'session': claim.get('session'), 'progress': progress,
                'waits_for': waits.get(number)}

    work = []
    for node in data['initiatives']['nodes']:
        children = node['subIssues']
        work.append(item(node['number'], 'Initiative', node['title'], node['url'],
                         'claimed' if status.claimed(status.names(node['labels'], 'name')) else 'ready', None,
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
                             'claimed' if status.claimed(status.names(child['labels'], 'name')) else 'todo',
                             node['number'], None))
    planning = [item(node['number'], 'Exploration' if status.labelled(status.names(node['labels'], 'name'),
                                                                      'Exploration') else 'needs-planning',
                     node['title'], node['url'], 'planning', None, None) for node in data['planning']['nodes']]
    default = (data.get('defaultBranchRef') or {}).get('name')
    pulls = []
    for node in data['open']['nodes']:
        commits = node['commits']['nodes']
        rollup = ((commits[0]['commit'].get('statusCheckRollup') or {}) if commits else {}).get('state')
        pulls.append({'number': node['number'], 'title': node['title'], 'url': node['url'], 'draft': node['isDraft'],
                      'base': node['baseRefName'], 'into_default': node['baseRefName'] == default,
                      'checks': CHECKS.get(rollup, 'none'), 'review': node.get('reviewDecision'),
                      'closes': [issue['number'] for issue in node['closingIssuesReferences']['nodes']]})
    merged = [{'number': node['number'], 'title': node['title'], 'url': node['url'], 'merged_at': node['mergedAt'],
               'base': node['baseRefName']} for node in data['merged']['nodes']]
    return {'default_branch': default, 'work': work, 'planning': planning, 'pulls': pulls, 'merged': merged}


def lineage(work: list[dict], number: int | None) -> list[int]:
    """The Initiative and Epic an item sits in, outermost first: `[1, 2]` for Task 9 of Epic 2 of Initiative 1."""
    parents = {entry['number']: entry.get('parent') for entry in work}
    chain = []
    while number in parents and parents[number] and parents[number] not in chain:
        number = parents[number]
        chain.insert(0, number)
    return chain


def crews(github: dict, reported: list[dict], now: datetime) -> list[dict]:
    """The crews Orchi reported, joined with their claims and ordered by what needs a look first.

    A crew's state is Orchi's reading of the app (`working`, `waiting`, `idle`, `stuck`, or `free`); an idle crew with
    a named background run shows as `background`. An idle crew that holds an Issue, waits for no other Issue and no
    merge of its PR, and has been quiet for STALL shows as `stuck`, as does a background run older than LONG_RUN."""
    items = {entry['number']: entry for entry in github['work'] + github['planning']}
    held = {}
    for entry in github['work'] + github['planning']:
        for key in (entry.get('session'), entry.get('crew')):
            if key and key not in held:
                held[key] = entry['number']
    merging = {number for pull in github['pulls'] if not pull['draft'] for number in pull['closes']}
    joined = []
    for crew in reported:
        name = crew.get('name') or ''
        issue = crew.get('issue') or held.get(crew.get('session_id')) or held.get(name)
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


def waiting(document: dict) -> list[dict]:
    """What waits for the user: crews that asked them something, Orchi's questions, and PRs waiting for their yes to
    merge: those Orchi asked about, or, when Orchi named none and autonomous mode is off, PRs into the default branch
    that are ready to merge."""
    items = [{'kind': 'question', 'crew': crew['name'], 'issue': crew.get('issue'), 'text': crew.get('question') or ''}
             for crew in document['crews'] if crew['state'] == 'waiting']
    items += [{'kind': 'orchi', 'id': question.get('id'), 'text': question.get('text') or ''}
              for question in document.get('questions') or []]
    asked = document.get('merges')
    held = set(document.get('held') or [])
    items += [{'kind': 'merge', 'pull': pull['number'], 'text': pull['title']} for pull in document['pulls']
              if pull['number'] not in held and (pull['number'] in asked if asked is not None else
                                                 document.get('mode') == 'off' and pull['into_default']
                                                 and not pull['draft'] and pull['checks'] in {'passing', 'none'})]
    return items


def snapshot(repo: str, github: dict, state: dict, now: datetime) -> dict:
    """The document the board renders: GitHub state joined with what Orchi last reported."""
    document = {'repository': repo, 'updated': now.isoformat(timespec='seconds'), 'error': None,
                'mode': state.get('mode'), 'limit': state.get('limit'), 'reported': state.get('reported'),
                'questions': state.get('questions') or [], 'merges': state.get('merges'),
                'deferred': state.get('deferred') or [], 'held': state.get('held') or [], **github}
    document['crews'] = crews(github, state.get('crews') or [], now)
    document['waiting'] = waiting(document)
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
