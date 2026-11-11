# Working on the Orchi for Copilot repository

This file governs contributions to this repository: the Orchi plugin for the
GitHub Copilot app, ported from [nkhus/orchi](https://github.com/nkhus/orchi),
the Claude Code edition. Setup must not copy it into another project's
`AGENTS.md`; there it writes only its own managed section.

## Layout

- `plugins/orchi/`: the plugin. `plugin.json` is its manifest (legacy format,
  no `$schema`); `skills/` holds the skills (`orchi` is the entry, `orchi-core`
  the workflow with its `references/`, `scripts/`, and `assets/`); `agents/`
  holds the six custom agents.
- `.github/plugin/marketplace.json`: the `orchi-copilot` marketplace.
- `tools/validate_package.py`, `tests/`, `.github/workflows/`: validation and CI.
- `docs/`: how Orchi behaves and is built now; `docs/README.md` maps code to
  pages, and `docs/out-of-scope/` records declined proposals.
- `.upstream/`: an optional local read-only clone of nkhus/orchi for porting.
  Keep it ignored and out of commits.

## Rules

- Read `README.md` and the pages that `docs/README.md` assigns to the code
  being changed; update them, and their Decisions sections, in the same branch.
  Every file under `plugins/` must match a row of the ownership map.
- Use English and describe current behavior, without release narratives or
  version markers next to the name Orchi.
- Keep each `SKILL.md` at 100 lines or fewer: it holds the steps, and
  `references/` hold stage guidance with one home per rule.
- Installed files must not link outside `plugins/orchi/skills/`, and must not
  depend on repository-root tools or documentation. Documentation may link into
  `plugins/`.
- Bundled scripts use only the Python standard library.
- Under `plugins/`, the word "claude" appears only in model IDs.
- Preserve the core flow: research and agree scope with the user before
  tracking or changes; proportional Task, Epic, or Initiative scope; Git
  branches and GitHub Issues as the only shared state; documentation updated
  with the code; one full review with targeted follow-up; merge and deployment
  within the user's authority. Do not reintroduce a controller, state database,
  approval receipts, or mandatory command facades.
- A target project's own instructions take precedence over Orchi's defaults;
  keep project-specific paths and tools out of the plugin.
- Before proposing a feature, read `docs/out-of-scope/`; record a proposal the
  maintainer declines for a lasting reason there.
- This repository targets the Copilot app and the Copilot CLI that runs its
  sessions; do not add support for other hosts. Do not change nkhus/orchi from
  here.

## Checks

```bash
python -m pip install -r requirements-dev.txt
python tools/validate_package.py
python -m pytest -q
```

Do not claim that deterministic tests establish live model behavior;
[testing](docs/testing.md#live-behavior) lists what to check by hand.
