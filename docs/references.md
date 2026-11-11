# External references

The sources below describe the hosts, standards, and tools Orchi relies on.
Orchi's own behavior is defined by its skills, references, and custom agents.

| Source | Relevance |
| --- | --- |
| [Agent Skills specification](https://agentskills.io/specification) | `SKILL.md` metadata, directory structure, scripts, references, and assets |
| [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts) | Self-contained bundled scripts |
| [Copilot: agent skills](https://docs.github.com/en/copilot/concepts/customizations/agent-skills) | Skill locations and discovery |
| [Copilot: custom agents](https://docs.github.com/en/copilot/concepts/customizations/custom-agents) and [their configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration) | Agent profiles: `name`, `description`, `tools`, `model`, and invocation |
| [Copilot: plugins](https://docs.github.com/en/copilot/concepts/customizations/plugins) | What a plugin packages, plugin IDs, and the surfaces that load plugins |
| [Copilot CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference) | The legacy and Agent Plugins manifests, `copilot plugin` commands, install location, and precedence |
| [Plugin and marketplace reference](https://docs.github.com/en/copilot/reference/plugin-and-marketplace-reference) | `marketplace.json` and plugin sources |
| [Creating and sharing a plugin marketplace](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/create-and-share-plugin-marketplaces) | Hosting the marketplace in `.github/plugin/` |
| [Copilot CLI configuration directory](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) | Repository settings in `.github/copilot/settings.json`: `extraKnownMarketplaces` and `enabledPlugins` |
| [Customizing the Copilot app](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app) | Installing plugins and adding a marketplace in the app |
| [Working with projects](https://docs.github.com/en/copilot/how-tos/github-copilot-app/working-with-projects) | Copilot Projects, the home of Orchi's conversation and its child sessions |
| [Copilot app repository configuration](https://docs.github.com/en/copilot/reference/github-copilot-app-reference/repository-configuration) | `.github/github-app.yml` and its review before changes apply |
| [Hallmark](https://github.com/Nutlope/hallmark) | One of the two design engines; the user installs it; strongest on pages that are read |
| [prototype](https://github.com/emilkowalski/skills) (Emil Kowalski) | The other design engine; the user installs it; builds divergent variants, strongest on screens that are worked in |
| [SmoothUI](https://smoothui.dev/) | Animated React components a project's stack may name; added through the shadcn CLI or MCP server |
| [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/) | An agent-first codebase: rules enforced by structural tests and lint rules, the repository as the agents' memory, recurring cleanup of drift |
| [GitHub rulesets](https://docs.github.com/en/rest/repos/rules) | The ruleset `standards.py ruleset` prints for required checks |
| [GitHub sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues) | Native Initiative/Epic/Task hierarchy |
| [GitHub issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies) | Native `blocked by` relationships between Epics |

Bundled scripts use only the Python standard library. Review these sources
periodically: plugin formats, skill and agent discovery, and the app's features
can change independently of this repository.
