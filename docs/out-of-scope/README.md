# Out of scope

Each file here records one proposal that Orchi does not adopt: what it is, why
not, what covers the need instead, and where it was decided. Read the matching
file before proposing a feature in the same area, so a settled question is not
reopened without new evidence. These files serve contributors and are not
installed.

| Proposal | Instead |
| --- | --- |
| [Controller and state database](controller-and-state-database.md) | Git branches and GitHub Issues hold all shared state |
| [Other hosts](other-hosts.md) | The Copilot app, and the Copilot CLI that runs its sessions, only |
| [Session identity mechanisms](session-identity-mechanisms.md) | The owner re-sends the assignment |
| [Deleting sessions](session-lifecycle.md) | A crew that released its work is archived; nothing is deleted |
| [Per-axis sub-reviewers](per-axis-sub-reviewers.md) | One reviewer keeps the axes in separate sections |

## Add a record

Add a file when the maintainer declines a proposal for a reason that should
outlive the conversation, or when Orchi removes a mechanism. Not now is not out
of scope; leave those in an Issue. Use this shape:

```md
# <Proposal>

Orchi does not <do what>.

## Why

<The reason, with the evidence or the maintainer's words.>

## Instead

<What covers the need now.>

## Decided in

- <PR, Issue, or date and context>
```

To reopen a record, bring the evidence its reason lacked: a live run, a
measurement, or a changed upstream capability. When the decision changes,
delete the file in the same PR as the change.
