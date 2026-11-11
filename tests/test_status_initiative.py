"""Blockers merged into Initiative branches, where GitHub records no closing PR link.

Ported from nkhus/mirivis-channel-integrity#688.
"""
from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

import status

INITIATIVE = 'initiative/pay-card-payments'
EPIC = 'epic/pay-token-tokenize-cards'


def pr(number: int, head: str, merged: bool = True, base: str = INITIATIVE) -> dict:
    return {'number': number, 'merged': merged, 'baseRefName': base, 'headRefName': head}


def blocker(state: str = 'CLOSED', reason: str | None = 'COMPLETED', body: str = '',
            closing: list[dict] | None = None, references: list[dict] | None = None) -> dict:
    return {
        'number': 617, 'title': '[PAY][TOKEN] Tokenize stored cards', 'state': state, 'stateReason': reason,
        'body': body,
        'closedByPullRequestsReferences': {'nodes': closing or []},
        'timelineItems': {'nodes': [{'source': item} for item in references or []]},
    }


RECORDED = f'## Branch and PR\n`{EPIC}` → `{INITIATIVE}`. Blocked by #615 (CONTRACT).'


class BlockerStateTest(unittest.TestCase):
    def test_closing_link_into_default_branch_is_satisfied(self) -> None:
        node = blocker(closing=[{'number': 9, 'merged': True, 'baseRefName': 'main'}])
        self.assertEqual(status.blocker_state(node), ('satisfied', 'merged into main'))

    def test_merged_pr_from_recorded_branch_satisfies_initiative_epic(self) -> None:
        node = blocker(body=RECORDED, references=[pr(645, EPIC)])
        self.assertEqual(status.blocker_state(node), ('satisfied', f'merged into {INITIATIVE} via #645'))

    def test_unrelated_cross_reference_is_not_proof(self) -> None:
        node = blocker(body=RECORDED, references=[pr(627, 'epic/pay-wallet-wallet-schema'),
                                                  pr(646, 'epic/pay-refund-refund-flow')])
        self.assertEqual(status.blocker_state(node), ('unverified', 'closed without a linked merged PR'))

    def test_unmerged_pr_from_recorded_branch_is_not_proof(self) -> None:
        node = blocker(body=RECORDED, references=[pr(645, EPIC, merged=False)])
        self.assertEqual(status.blocker_state(node)[0], 'unverified')

    def test_branch_named_only_as_a_prefix_does_not_match(self) -> None:
        node = blocker(body=f'`{EPIC}-v2`', references=[pr(645, EPIC)])
        self.assertEqual(status.blocker_state(node)[0], 'unverified')

    def test_cancelled_blocker_blocks_even_with_a_merged_pr(self) -> None:
        node = blocker(reason='NOT_PLANNED', body=RECORDED, references=[pr(645, EPIC)])
        self.assertEqual(status.blocker_state(node), ('blocking', 'cancelled'))

    def test_open_blocker_blocks(self) -> None:
        node = blocker(state='OPEN', reason=None, body=RECORDED, references=[pr(645, EPIC)])
        self.assertEqual(status.blocker_state(node), ('blocking', 'open'))

    def test_connected_pull_request_counts_like_a_cross_reference(self) -> None:
        node = blocker(body=RECORDED)
        node['timelineItems'] = {'nodes': [{'subject': pr(645, EPIC)}, {}, {'source': {}}]}
        self.assertEqual(status.blocker_state(node)[0], 'satisfied')


class ReportTest(unittest.TestCase):
    def test_epic_whose_only_blocker_merged_into_initiative_is_ready(self) -> None:
        epic = {
            'number': 622, 'title': '[PE2E][E2E] Verify the journey', 'url': 'https://example.invalid/622',
            'labels': {'nodes': [{'name': 'Epic'}]}, 'assignees': {'nodes': []},
            'parent': {'number': 614, 'title': '[PE2E] Pricing end-to-end journey'},
            'subIssues': {'totalCount': 0, 'nodes': []},
            'blockedBy': {'nodes': [blocker(body=RECORDED, references=[pr(645, EPIC)])]},
        }
        page = {'data': {'repository': {'issues': {'pageInfo': {'hasNextPage': False, 'endCursor': None},
                                                   'nodes': [epic]}}}}

        def run(args: list[str]) -> str:
            if args[:2] == ['repo', 'view']:
                return json.dumps({'nameWithOwner': 'owner/name'})
            return json.dumps(page)

        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(status.main(['--json'], run=run), 0)
        entry = json.loads(output.getvalue())['entries'][0]
        self.assertEqual(entry['status'], 'ready')
        self.assertEqual(entry['blockers'][0]['detail'], f'merged into {INITIATIVE} via #645')


if __name__ == '__main__':
    unittest.main()
