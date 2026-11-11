# Installation

Orchi is a plugin, `orchi`, in the `orchi-copilot` marketplace of this
repository; its ID is `orchi@orchi-copilot`. The plugin holds the skills and
custom agents, and every workflow instruction lives there. The first time Orchi
starts in a repository, it prepares that repository with `setup.py`, which
writes tool-neutral development rules, documentation and standards checks, and
the type labels. Nothing it writes names Orchi or requires it: a developer
working with another assistant, or none, follows the same rules without knowing
Orchi is in use.

## Requirements

- The [GitHub Copilot app](https://docs.github.com/en/copilot/how-tos/github-copilot-app),
  or the [Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli)
  for installing from the command line.
- In each repository Orchi works on: Git, a GitHub remote, the
  [GitHub CLI](https://cli.github.com/) (`gh`) signed in, and Python 3 for the bundled
  scripts.

## Install

In the Copilot app:

1. Click **Customize** in the sidebar, select the marketplace settings control
   next to the marketplace dropdown, and add the GitHub repository
   `nkhus/orchi-copilot`.
2. On **Customize**, search Browse for `orchi` and click **Install**.

With the Copilot CLI:

```bash
copilot plugin marketplace add nkhus/orchi-copilot
copilot plugin install orchi@orchi-copilot
```

In an interactive CLI session, the same commands run as `/plugin marketplace
add nkhus/orchi-copilot` and `/plugin install orchi@orchi-copilot`. The plugin
is installed under `~/.copilot/installed-plugins/orchi-copilot/orchi/`.

Then create a Copilot Project for the repository (in the sidebar, **+** next to
Projects) and type `/orchi` in its conversation; the entry skill runs only when
typed, and the conversation stays Orchi from then on. Orchi prepares the repository in
that turn ([pool](pool.md#orchi)).

## Update, turn off, and remove

In the app, **Customize** → **Installed** has a toggle that turns the plugin on
or off. With the Copilot CLI:

```bash
copilot plugin update orchi
copilot plugin disable orchi
copilot plugin enable orchi
copilot plugin uninstall orchi
copilot plugin marketplace remove orchi-copilot
```

`marketplace remove` refuses while a plugin from the marketplace is installed;
`--force` uninstalls it too. Removing the plugin leaves each repository's setup
in place. What setup wrote is neutral and stays useful without Orchi; delete the
files and sections listed below by hand if the team does not want them.

The plugin is personal: setup does not enable it for the repository, so other
members are not offered Orchi and need nothing to work on the repository.

## Repository setup

`setup.py`, in the orchi-core skill's `scripts/` folder, prepares a repository.
Orchi runs it through a setup subagent and proposes the result as a pull request
([pool](pool.md#orchi)); it can also be run by hand from the repository root:

```bash
python3 <orchi-core>/scripts/setup.py [options]
```

where `<orchi-core>` is the orchi-core skill's base directory, for example
`~/.copilot/installed-plugins/orchi-copilot/orchi/skills/orchi-core`.

| Option | Effect |
| --- | --- |
| `--project PATH` | The repository to prepare; by default the Git top level of the current directory |
| `--dry-run` | Prints each change as `Would …` and writes nothing |
| `--check` | Like `--dry-run`, but exits 1 when a committed file or a label would change; Orchi runs it on every start |
| `--replace` | Overwrites managed files and sections someone edited, and files setup did not create |
| `--no-labels` | Neither checks nor changes labels |
| `--paths` | Prints every path setup writes or removes, the earlier setup's included, and exits |
| `--exclude` | Only adds `.orchi-tmp/` to this clone's Git exclude file, and exits |
| `--docs-workflow`, `--no-docs-workflow` | Writes (the default) or removes the documentation check and its script |
| `--standards-workflow`, `--no-standards-workflow` | Writes (the default) or removes the standards check and its script |

It writes:

| Path | Kind | Content |
| --- | --- | --- |
| `AGENTS.md` | Managed section | `## Development rules`: agree scope first, track work in Issues and PRs, leave taken Issues to their owner, follow `ENGINEERING.md`, update the documentation with the code, and never infer merge or deploy permission |
| The PR template | Managed section | The Summary, Verification, and Documentation impact sections, added to the template GitHub reads first (`.github/pull_request_template.md` when there is none) |
| `.github/workflows/docs-check.yml`, `.github/scripts/knowledge.py` | Managed files | New broken documentation links and the Documentation impact section, checked on pull requests, and the script they run |
| `.github/workflows/standards-check.yml`, `.github/scripts/standards.py` | Managed files | The `ENGINEERING.md` checks on pull requests, and the script they run |

Sections sit between `<!-- managed:begin -->` and `<!-- managed:end -->`.
None of these files name Orchi. A workflow turned off stays off: without a flag,
a later run keeps it only while its file is present.

Outside the commit, setup adds `.orchi-tmp/`, the temporary files of Orchi's
sessions and subagents, to the clone's own exclude file
(`git rev-parse --git-path info/exclude`); `--check` does not count it. A
session in another clone, a Cloud crew's included, runs `setup.py --exclude`
before it writes there.

It creates the type labels `Initiative`, `Epic`, and `Task` with `gh` when they
are missing, with neutral descriptions. When `gh` cannot reach GitHub, it notes
that labels were not checked and goes on.

A second run prints `Nothing to change.`

### Migrating an earlier setup

A repository prepared by an earlier setup is migrated on the next run. Setup
recognises what it wrote then by the digests of those versions, or by the old
manifest's record:

- the Issue forms in `.github/ISSUE_TEMPLATE/orchi-*.yml`, the manifest
  `.github/orchi/manifest.json`, and the `.gitignore` section between
  `# orchi:begin` and `# orchi:end` are removed;
- `.github/workflows/orchi-docs.yml` and `orchi-standards.yml`, with their
  scripts in `.github/orchi/scripts/`, are replaced by the new pair, each kept
  off when the manifest recorded it off;
- the `<!-- orchi:begin -->` sections of `AGENTS.md` and the PR template are
  replaced in place by the new sections;
- `.github/github-app.yml` loses the instructions setup wrote, and is removed
  when nothing else is left;
- `.github/copilot/settings.json` loses `orchi@orchi-copilot`, and the
  marketplace entry setup wrote when no other plugin of it remains; it is
  removed when it ends up empty. An explicit `false` is kept, with a note;
- the process labels (`in-progress`, `Exploration`, `needs-planning`,
  `delivery-ready`, `retro`, `design`) are deleted when their description is
  still the one setup wrote, after their meaning moves to the Issues: an open
  `in-progress` Issue without an assignee is assigned to whoever runs setup, an
  open `Exploration` Issue's title gains `Explore: `, and a `retro` Issue's
  `Lesson: `; a `design` Issue gets a note to start its UI design field with
  `Design Epic:`. A label whose description someone changed is kept, with a
  note. The type labels' old descriptions are replaced.

Directories left empty are removed. An old file someone edited is left in place
with a note, except a workflow and its script, which are replaced only as a
pair; an edited old section is a conflict like any other.

### Refusals

Setup never overwrites what someone else wrote. A managed file or section that
was edited after setup wrote it, or a file at a managed path that setup did not
create, stops the whole run before anything is written: it prints
`Refused, nothing written` with the list and exits 1. `--replace` overwrites
them. Malformed markers, a file that is not UTF-8, and a path through a symlink
are refused even with `--replace`. A workflow turned off after someone edited it
is left in place, no longer managed, with a note to remove it by hand.

## Decisions

### Plugin format

The plugin uses the legacy Copilot plugin format: `plugins/orchi/plugin.json`
without `$schema`, with its components in the default `agents/` and `skills/`
directories. Agent Plugins 1.0 defines a closed manifest whose `extensions`
field is namespaced client data (Copilot's components live under
`com.github.copilot/`) and documents no location for canvas extensions. The
legacy manifest's `extensions` field is a path to extension directories:
`"extensions": "extensions/"` ships `extensions/orchi-canvases/`, which the
Copilot CLI loads in each session once the plugin is installed
([canvases](canvases.md#how-they-load)). The CLI plugin reference lists the
field, and a test plugin's extension loaded through it.

### What each surface supports

Copilot app plugins can package skills, hooks, custom agents, MCP servers, and
canvas extensions. Copilot CLI plugins can package custom agents, skills,
commands, hooks, MCP servers, and LSP servers. Orchi ships skills, custom
agents, and one extension with two canvases. The board's snapshot runs
`board.py` with Python 3 and reads GitHub with `gh`, signed in through its
keyring: the extension's environment does not pass `GITHUB_TOKEN`.

### Distribution

The marketplace is `.github/plugin/marketplace.json` in this repository, and
its one plugin's source is `./plugins/orchi`. Copilot installs it under
`~/.copilot/installed-plugins/orchi-copilot/orchi/`. Project and personal skills
and custom agents take precedence over a plugin's with the same name (the first
one found wins; skills are matched by their `name`, agents by file name), so a
repository with its own `orchi-*` skill or agent shadows Orchi's.

### Neutral repository footprint

All of Orchi's workflow instructions live in the plugin; a repository holds only
tool-neutral development and documentation rules, so developers with other
assistants work on it without knowing Orchi is in use, and nothing there tells
an assistant to use Orchi or to refuse work
([#7](https://github.com/nkhus/orchi-copilot/issues/7)). Orchi reads process
state from standard GitHub signals instead of labels and markers
([workflow](workflow.md#github-signals)). This reverses earlier decisions:

| Earlier decision | Now |
| --- | --- |
| Setup wrote `.github/copilot/settings.json` so that every member was offered Orchi | The plugin is personal; setup writes no plugin settings and migration removes them |
| Setup created `.github/github-app.yml` with instructions pointing to Orchi | Orchi's instructions come from the plugin; migration removes the ones setup wrote |
| `AGENTS.md` held `## Orchi workflow`, routing work to Orchi | `## Development rules`, which any developer or assistant follows |
| Setup recorded digests in `.github/orchi/manifest.json` | No record in the repository; setup recognises its versions by digest |
| Setup wrote Issue forms `.github/ISSUE_TEMPLATE/orchi-*.yml` | The forms live in the plugin, `assets/issues/`, and Orchi builds Issue bodies from them |
| Setup created nine labels, six of them for the process | Only the type labels `Initiative`, `Epic`, and `Task` |
| A `.gitignore` section ignored `.orchi-tmp/` | The clone's own Git exclude file does |
| Workflows `orchi-docs.yml` and `orchi-standards.yml`, with a weekly drift run and a `docs/work/` check | `docs-check.yml` and `standards-check.yml` on pull requests; Orchi runs the drift and `docs/work/` checks itself |

### Vendored scripts

A target repository does not contain the plugin, so its CI cannot run scripts
from it. Setup copies `knowledge.py` and `standards.py` into `.github/scripts/`,
and the workflows run them there.

### Managed files and sections

Setup keeps no record in the repository. It treats a managed file or section as
its own when it equals the version setup ships or one whose sha256 is in
`PREVIOUS`; anything else was edited or is someone else's, and refuses the whole
run, with nothing written, unless `--replace` is given. Whoever changes a
managed asset or section body adds the old version's digest to `PREVIOUS`, so
repositories prepared with it still update. The earlier setup's files are
recognised by the digests in `LEGACY_DIGESTS` or by its manifest.

### Labels

Setup creates only the type labels. In progress, ready, and needs a plan are read
from assignees, linked pull requests and branches, sub-issues, and the plan in
an Issue body, which every developer already sets without knowing Orchi.

### Models

Each agent pins its model: `claude-haiku-5.5` for `orchi-scout`,
`claude-sonnet-5.5` for `orchi-fixer`, and `claude-opus-5.5` for the others.
A user whose plan or policy lacks a pinned model may not be able to run that
agent as pinned; this has not been checked live.

### Worktrees

The Copilot app keeps session worktrees outside the repository, so the clone's
exclude file ignores only `.orchi-tmp/`.

### Design skills

The design skills Hallmark and prototype are neither bundled nor vendored. On
the user's yes, the session that runs the first design round installs them with
`gh skill install`, pinned, at user scope ([design](design.md#design-skills));
removing the plugin leaves them installed, and `gh skill list` shows where.
