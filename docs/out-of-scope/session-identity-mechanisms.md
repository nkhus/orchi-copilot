# Session identity mechanisms

Orchi does not pin a session's role with an identity line derived from the
session name, a custom instruction file, or a hook that runs when a session
starts.

## Why

The maintainer declined these in favor of re-sending. The claim, Issue, and PR
already record what a crew holds, so one message restores the role, while each
mechanism would add configuration that also runs in sessions that are not
Orchi's crews.

## Instead

When a crew no longer knows its role, Orchi re-sends its assignment. Every
assignment stands alone; the session re-invokes its skill and rebuilds its state
from GitHub.

## Decided in

- 2026-10-12, while designing the worker pool that shipped in
  [nkhus/orchi#34](https://github.com/nkhus/orchi/pull/34).
- Kept in this port ([nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2)).
