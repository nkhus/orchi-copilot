# Installation

Orchi is a plugin, `orchi`, in the `orchi-copilot` marketplace of this
repository; its ID is `orchi@orchi-copilot`. The plugin holds the skills and
custom agents. The first time Orchi starts in a repository, it prepares that
repository with `setup.py`, which writes the labels, GitHub files, and
instructions the workflow relies on.

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
in place; delete the files and sections listed below by hand if a repository
stops using Orchi.

## Repository defaults

Setup writes `.github/copilot/settings.json`, so that everyone who works on the
repository is offered Orchi:

```json
{
  "extraKnownMarketplaces": {
    "orchi-copilot": {"source": {"source": "github", "repo": "nkhus/orchi-copilot"}}
  },
  "enabledPlugins": {"orchi@orchi-copilot": true}
}
```

Copilot merges these with each member's own settings, the repository's taking
precedence. A member turns the default off for themselves with
`"enabledPlugins": {"orchi@orchi-copilot": false}` in
`.github/copilot/settings.local.json`, which is not committed, and a new
session. Enterprise managed settings always win.

## Repository setup

`setup.py`, in the orchi-core skill's `scripts/` folder, prepares a repository.
Orchi runs it through a setup subagent and commits the result
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
| `--check` | Like `--dry-run`, but exits 1 when anything would change; Orchi runs it on every start |
| `--replace` | Overwrites managed files and sections someone edited, and files Orchi did not create |
| `--no-labels` | Neither checks nor creates labels |
| `--docs-workflow`, `--no-docs-workflow` | Writes (the default) or removes the documentation workflow and its script; the choice is kept for later runs |
| `--standards-workflow`, `--no-standards-workflow` | Writes (the default) or removes the standards workflow and its script; the choice is kept for later runs |

It writes:

| Path | Kind | Content |
| --- | --- | --- |
| `.github/ISSUE_TEMPLATE/orchi-{initiative,epic,task,exploration}.yml` | Managed file | The Issue forms |
| `.github/workflows/orchi-docs.yml`, `.github/orchi/scripts/knowledge.py` | Managed files | Documentation checks on pull requests, and the script they run |
| `.github/workflows/orchi-standards.yml`, `.github/orchi/scripts/standards.py` | Managed files | Standards checks on pull requests and the weekly drift run, and the script they run |
| `.github/orchi/manifest.json` | Record | The digests of managed files and sections, and the workflow choices |
| `AGENTS.md` | Managed section | `## Orchi workflow`: who runs the work, and the core rules every session follows |
| The PR template | Managed section | Orchi's PR sections, added to the template GitHub reads first (`.github/pull_request_template.md` when there is none) |
| `.gitignore` | Managed section | `.orchi-tmp/`, the temporary files of Orchi's sessions and subagents |
| `.github/copilot/settings.json` | Merged | The marketplace and the enabled plugin, as above; every other value is kept |
| `.github/github-app.yml` | Created when missing | `instructions:` that point the app's sessions to the Orchi section of `AGENTS.md` and the orchi-core skill |

It creates the nine labels the workflow uses (`Initiative`, `Epic`, `Task`,
`in-progress`, `Exploration`, `needs-planning`, `delivery-ready`, `retro`,
`design`) with `gh` when they are missing and leaves existing labels as they
are. When `gh` cannot reach GitHub, it notes that labels were not checked and
goes on.

A second run prints `Nothing to change.`

### Refusals

Setup never overwrites what someone else wrote. A managed file or section that
was edited after Orchi wrote it, a file at a managed path that Orchi did not
create, or a `.github/copilot/settings.json` that is not valid JSON or not a JSON
object stops the
whole run before anything is written: it prints `Refused, nothing written` with
the list and exits 1. `--replace` overwrites them. Malformed markers, a file that
is not UTF-8, an unreadable manifest, and a path through a symlink are refused
even with `--replace`. A workflow turned off after someone edited it is left in
place, no longer managed, with a note to remove it by hand. An existing
`.github/github-app.yml` that Orchi did not create is left as it is, with a note.

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

### Repository defaults

Setup writes `.github/copilot/settings.json` with the marketplace and the
enabled plugin, merged into what is there, and keeps an explicit `false`: a team
that turned Orchi off stays off. Members can still turn repository defaults off
for themselves.

### Vendored scripts

A target repository does not contain the plugin, so its CI cannot run scripts
from it. Setup copies `knowledge.py` and `standards.py` into
`.github/orchi/scripts/`, and the workflows run them there.

### Managed files and sections

Setup records the sha256 digest of every whole file and section it manages in
`.github/orchi/manifest.json`. Sections sit between `<!-- orchi:begin -->` and
`<!-- orchi:end -->` (`# orchi:begin` and `# orchi:end` in `.gitignore`). An
edited file or section refuses the whole run, with nothing written, unless
`--replace` is given.

### `.github/github-app.yml`

Setup creates `.github/github-app.yml` only when it is missing, and without
markers: the app rewrites the file from its settings UI, and applies a change
made outside the app only after the user reviews and accepts it. An existing
file is left as it is.

### Labels

Setup creates all nine labels the workflow uses, not only the four the pool
needs, so planning and delivery never stop on a missing label.

### Models

Each agent pins its model: `claude-haiku-5.5` for `orchi-scout`,
`claude-sonnet-5.5` for `orchi-fixer`, and `claude-opus-5.5` for the others.
A user whose plan or policy lacks a pinned model may not be able to run that
agent as pinned; this has not been checked live.

### Worktrees

The Copilot app keeps session worktrees outside the repository, so the managed
`.gitignore` section ignores only `.orchi-tmp/`.

### Design skills

The design skills Hallmark and prototype are neither bundled nor vendored. On
the user's yes, the session that runs the first design round installs them with
`gh skill install`, pinned, at user scope ([design](design.md#design-skills));
removing the plugin leaves them installed, and `gh skill list` shows where.
