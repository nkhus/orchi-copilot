#!/usr/bin/env python3
"""Read-only overview of tracked work: open Epics and standalone Tasks, who holds them, and readiness.

State comes from standard GitHub signals, so work anyone tracks counts the same: an Issue with an assignee, an open
linked pull request, or a linked branch is taken; one with sub-issues or a plan (a Requirements section with R1) is
planned; anything else needs a plan."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Callable

# The fields `taken` and `planned` read, for any Issue node in a query.
SIGNALS = ('body assignees(first: 10) { nodes { login } } linkedBranches(first: 5) { nodes { ref { name } } } '
           'closedByPullRequestsReferences(first: 10) { nodes { number state } }')
QUERY = '''
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 50, after: $cursor, states: OPEN, labels: ["Epic", "Task"],
           orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url
        labels(first: 20) { nodes { name } }
        %s
        parent { number title }
        subIssues(first: 100) { totalCount nodes { number title state } }
        blockedBy(first: 50) { nodes {
          number title state stateReason body
          closedByPullRequestsReferences(first: 10, includeClosedPrs: true) {
            nodes { number merged baseRefName } }
          timelineItems(last: 50, itemTypes: [CROSS_REFERENCED_EVENT, CONNECTED_EVENT]) { nodes {
            ... on CrossReferencedEvent { source { ... on PullRequest { number merged baseRefName headRefName } } }
            ... on ConnectedEvent { subject { ... on PullRequest { number merged baseRefName headRefName } } }
          } }
        } }
      }
    }
  }
}
'''.replace('%s', SIGNALS)
TAGS = re.compile(r'\[([A-Z][A-Z0-9]{1,7})\]')
# Branch names an Issue body records for its work, such as `epic/pay-token-tokenize-cards`.
BRANCH = re.compile(r'(?<![\w/.-])((?:epic|fix|initiative)/[A-Za-z0-9._/-]*[A-Za-z0-9])')
# A plan in an Issue body: a Requirements heading whose section names R1.
PLAN = re.compile(r'^#{1,6}\s*Requirements\s*$(?:(?!^#{1,6}\s).)*?\bR1\b', re.M | re.S | re.I)
ORDER = {'ready': 0, 'check': 1, 'blocked': 2, 'unplanned': 3, 'taken': 4}

Runner = Callable[[list[str]], str]


def gh(args: list[str]) -> str:
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True).stdout


def names(connection: dict | None, key: str) -> list[str]:
    return [node[key] for node in (connection or {}).get('nodes', [])]


def labelled(labels: list[str], name: str) -> bool:
    # GitHub label names are unique regardless of case, and Orchi's setup reuses an existing `epic` label.
    return any(label.casefold() == name.casefold() for label in labels)


def taken(node: dict) -> bool:
    """Someone holds the Issue: an assignee, an open linked pull request, or a linked branch. Nodes queried without
    SIGNALS count as not taken."""
    if names(node.get('assignees'), 'login') or (node.get('linkedBranches') or {}).get('nodes'):
        return True
    return any(pr.get('state', 'OPEN') == 'OPEN'
               for pr in (node.get('closedByPullRequestsReferences') or {}).get('nodes', []))


def planned(node: dict) -> bool:
    """The Issue has native sub-issues or a plan in its body."""
    children = node.get('subIssues') or {}
    total = children.get('totalCount', len(children.get('nodes') or []))
    summary = (node.get('subIssuesSummary') or {}).get('total') or 0
    return bool(total or summary or PLAN.search(node.get('body') or ''))


def stage(node: dict) -> str:
    """`taken`, `ready` when planned, or `unplanned`."""
    return 'taken' if taken(node) else 'ready' if planned(node) else 'unplanned'


def tags(title: str) -> list[str]:
    """Leading [TAG] groups of a title."""
    found, position = [], 0
    while match := TAGS.match(title, position):
        found.append(match[1])
        position = match.end()
    return found


def shown(path: list[str]) -> str:
    return ''.join(f'[{tag}]' for tag in path) or 'no tags'


def naming(issue: dict, kind: str) -> list[str]:
    """Titles start with the Initiative tag and the Epic tag; Tasks repeat their Epic's tags."""
    own = tags(issue['title'])
    warnings = []
    if kind == 'Epic':
        parent = tags(issue['parent']['title']) if issue.get('parent') else []
        if own[:-1] != parent or len(own) != len(parent) + 1:
            expected = ''.join(f'[{tag}]' for tag in parent) + '[<EPIC TAG>]'
            warnings.append(f'title should start with {expected}, not {shown(own)}')
        for child in (issue.get('subIssues') or {}).get('nodes', []):
            if child.get('state') == 'OPEN' and 'title' in child and tags(child['title']) != own:
                warnings.append(f"Task #{child['number']} title should start with {shown(own)}, not {shown(tags(child['title']))}")
    elif own:
        warnings.append(f'a standalone Task title has no tags, not {shown(own)}')
    return warnings


def referencing_prs(node: dict) -> list[dict]:
    """Pull requests that cross-reference or were connected to an Issue."""
    prs = []
    for item in (node.get('timelineItems') or {}).get('nodes', []):
        pr = (item or {}).get('source') or (item or {}).get('subject')
        if pr and 'number' in pr:
            prs.append(pr)
    return prs


def blocker_state(node: dict) -> tuple[str, str]:
    """Classify one native blocker as satisfied, unverified, or blocking."""
    if node['state'] == 'OPEN':
        return 'blocking', 'open'
    if node.get('stateReason') != 'COMPLETED':
        return 'blocking', 'cancelled'
    merged = [pr for pr in (node.get('closedByPullRequestsReferences') or {}).get('nodes', []) if pr['merged']]
    if merged:
        return 'satisfied', 'merged into ' + ', '.join(sorted({pr['baseRefName'] for pr in merged}))
    # GitHub links closing PRs only for the default branch, so an Epic merged into its Initiative branch has no
    # closing link. Accept a merged PR that references the blocker from the branch its Issue records; an unrelated
    # cross-reference is not proof.
    recorded = set(BRANCH.findall(node.get('body') or ''))
    from_branch = {pr['number']: pr for pr in referencing_prs(node) if pr.get('merged') and pr.get('headRefName') in recorded}
    if from_branch:
        prs = [from_branch[number] for number in sorted(from_branch)]
        return 'satisfied', ('merged into ' + ', '.join(sorted({pr['baseRefName'] for pr in prs}))
                             + ' via ' + ', '.join(f"#{pr['number']}" for pr in prs))
    return 'unverified', 'closed without a linked merged PR'


def classify(issue: dict) -> dict | None:
    """Return an entry-point summary, or None for Tasks that belong to a parent."""
    labels = names(issue.get('labels'), 'name')
    kind = 'Epic' if labelled(labels, 'Epic') else 'Task'
    if kind == 'Task' and issue.get('parent'):
        return None
    blockers = []
    for node in (issue.get('blockedBy') or {}).get('nodes', []):
        state, detail = blocker_state(node)
        blockers.append({'number': node['number'], 'title': node['title'], 'state': state, 'detail': detail})
    states = {blocker['state'] for blocker in blockers}
    if taken(issue):
        status = 'taken'
    elif not planned(issue):
        status = 'unplanned'
    elif 'blocking' in states:
        status = 'blocked'
    elif 'unverified' in states:
        status = 'check'
    else:
        status = 'ready'
    children = issue.get('subIssues') or {'totalCount': 0, 'nodes': []}
    done = sum(1 for node in children['nodes'] if node['state'] == 'CLOSED')
    parent = issue.get('parent')
    return {'number': issue['number'], 'kind': kind, 'title': issue['title'], 'url': issue['url'],
            'status': status, 'owners': names(issue.get('assignees'), 'login'),
            'parent': parent['number'] if parent else None,
            'tasks': {'closed': done, 'total': children['totalCount']} if kind == 'Epic' else None,
            'blockers': blockers, 'naming': naming(issue, kind)}


def fetch(repo: str, run: Runner = gh) -> list[dict]:
    owner, _, name = repo.partition('/')
    if not owner or not name:
        raise ValueError('Repository must be OWNER/NAME: ' + repo)
    issues, cursor = [], None
    while True:
        # -f keeps variables strings; -F would turn a repository named 2048 or true into a number or boolean.
        args = ['api', 'graphql', '-f', 'query=' + QUERY, '-f', 'owner=' + owner, '-f', 'name=' + name]
        if cursor:
            args += ['-f', 'cursor=' + cursor]
        page = json.loads(run(args))['data']['repository']['issues']
        issues += page['nodes']
        if not page['pageInfo']['hasNextPage']:
            return issues
        cursor = page['pageInfo']['endCursor']


def report(issues: list[dict]) -> list[dict]:
    entries = [entry for entry in map(classify, issues) if entry]
    return sorted(entries, key=lambda entry: (ORDER[entry['status']], entry['number']))


def render(entries: list[dict]) -> str:
    if not entries:
        return 'No open Epics or standalone Tasks.'
    lines = []
    for entry in entries:
        extra = []
        if entry['parent']:
            extra.append(f"in #{entry['parent']}")
        if entry['tasks'] is not None:
            extra.append(f"tasks {entry['tasks']['closed']}/{entry['tasks']['total']}")
        if entry['owners']:
            extra.append('owner ' + ', '.join(entry['owners']))
        lines.append(f"{entry['status']:<9} {entry['kind']:<4} #{entry['number']} {entry['title']}"
                     + (f"  ({'; '.join(extra)})" if extra else ''))
        for blocker in entry['blockers']:
            lines.append(f"            blocked by #{blocker['number']}: {blocker['detail']}")
        for warning in entry['naming']:
            lines.append(f'            naming: {warning}')
    lines.append('Snapshot only: confirm predecessor results are on the intended integration branch before taking work.')
    return '\n'.join(lines)


def main(argv: list[str] | None = None, run: Runner = gh) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', help='OWNER/NAME; defaults to the current repository')
    parser.add_argument('--json', action='store_true', help='Print machine-readable output')
    args = parser.parse_args(argv)
    try:
        repo = args.repo or json.loads(run(['repo', 'view', '--json', 'nameWithOwner']))['nameWithOwner']
        entries = report(fetch(repo, run))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, 'stderr', '') or error
        print(f'Status error: {detail}'.rstrip(), file=sys.stderr)
        return 2
    print(json.dumps({'repository': repo, 'entries': entries}, indent=2) if args.json else render(entries))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
