# Deleting sessions

Orchi does not delete sessions, does not archive a crew that still holds work,
and does not make the user paste a command into a session to start it. It
archives only a crew that has released its work.

## Why

Sessions belong to the user, who may still read or reuse them; deleting one
loses that, and archiving one that holds work loses the work in its worktree. A
pasted command is a manual step that a kickoff prompt replaces.

## Instead

Orchi starts a crew per request with `create_session`, whose kickoff prompt
carries the assignment, so the session invokes its skill itself. When the work
is done, Orchi sends `release`; the crew confirms nothing would be lost and
replies `released`, and Orchi archives it with `archive_session`. Archiving is
reversible: the user may restore the crew.

## Decided in

- [nkhus/orchi#58](https://github.com/nkhus/orchi/pull/58): crews start on
  demand and are archived when done.
- [nkhus/orchi#42](https://github.com/nkhus/orchi/pull/42): Orchi creates its
  sessions; the user no longer creates and titles them.
- Kept in this port, with `create_session` and `archive_session`
  ([nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2)).
