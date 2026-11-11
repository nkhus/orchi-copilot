# Other hosts

Orchi for the Copilot app does not support hosts other than the GitHub Copilot
app and the Copilot CLI that runs its sessions. Claude Code, VS Code, and other
assistants are not supported targets of this repository.

## Why

The pool relies on the app's primitives: a Copilot Project as Orchi's
conversation, child sessions started with `create_session`, messages with
`send_session_message`, and archiving with `archive_session`. Other hosts lack
some of them or provide them differently, and supporting several hosts would
split every skill and reference into host-specific branches.

## Instead

[nkhus/orchi](https://github.com/nkhus/orchi) is the Claude Code edition. This
repository ports it to the Copilot app and keeps the workflow the same where
the hosts allow ([upstream](../upstream.md)). The plugin's skills and agents may
load in other Copilot surfaces, but nothing here is built or checked for them.

## Decided in

- [nkhus/orchi-copilot#1](https://github.com/nkhus/orchi-copilot/issues/1) and
  [nkhus/orchi-copilot#2](https://github.com/nkhus/orchi-copilot/issues/2).
