# Orchi knowledge tools

`scripts/knowledge.py` searches project Markdown, reads exact files, and checks
local links. It needs only Git and the Python standard library, reads only, and
creates no index, state database, or controller. Run it from the repository root
with the orchi-core skill's base directory (`<orchi-core>`, shown when the skill
loads), for example:

```sh
python3 <orchi-core>/scripts/knowledge.py search 'account session'
python3 <orchi-core>/scripts/knowledge.py --ref main search 'account session'
python3 <orchi-core>/scripts/knowledge.py --ref main get docs/accounts/README.md
python3 <orchi-core>/scripts/knowledge.py --path docs lint --since main
```

Select `--ref` explicitly for main, an initiative, or an Epic snapshot. It resolves
to a commit before reading. Without it, the working tree includes uncommitted and
untracked non-ignored documents and may contain unverified drafts. Search reports
that distinction, path, line, heading, snippet, and full-content SHA256. Use the
reported commit with `get --sha256 HASH PATH` to reject stale reads. `get` returns
the complete file; snippets are discovery aids, not authoritative source reads.
Invalid refs, missing files, or mismatched hashes fail instead of falling back.

Search is case-insensitive lexical matching of all query words against a line,
its heading, and its path; it is not semantic or cross-language search. Results
are deterministic in path/line order, limited by `--limit` (1–100, default 20).
The corpus is every Markdown file in the snapshot except installed skill bundles
(`.agents/skills/`, `.github/skills/`), custom agent definitions
(`.github/agents/`), and vendored
directories such as `node_modules/`. Narrow it with one or more `--path PREFIX` options. Use
`rg` when looking for code or other files; `get` can read any selected text file.

`lint` checks local Markdown inline links, defined reference links, and ATX
heading/HTML anchors in that corpus, ignoring fenced examples and inline code. It
does not fetch external links, validate arbitrary embedded HTML or all Markdown
extensions, or prove that current-state claims are true. Review indexes,
requirements, implementation evidence, and semantic consistency as described in
[knowledge guidance](knowledge.md).

`lint --since REF` reports only errors not already present in `REF`, matched by
file and message rather than line number, so existing debt does not hide a new
break. The documentation workflow (`docs-check.yml`) runs it against the PR base branch. `impact` checks
that a PR body (`--body-file`, or the `PR_BODY` variable) has a filled
`Documentation impact` section.
