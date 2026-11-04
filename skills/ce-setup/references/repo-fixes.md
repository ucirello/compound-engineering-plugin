# Repo-local fixes (Phase 2)

## Inline health-check equivalent (Step 2 fallback)

Also carry out SKILL.md's OpenCode V2 installation prerequisite: discover the global directory with `opencode debug paths` / `opencode debug paths config`, then offer to merge `"experimental": { "subagent_depth": 3 }` into its existing `opencode.json(c)` (normally `~/.config/opencode/opencode.json`). Preserve higher integer depths, sibling experimental fields, and unrelated settings; never replace the whole file or create competing JSON/JSONC files. Installing a plugin or its bundled package config alone does not enable deep delegation. Verify higher-precedence configuration does not lower the effective value below `3`, and disclose unverified effective depth rather than assuming capacity. Only mutate user configuration with approval during an actual setup run, never during migration.

When the bundled `scripts/check-health` is unavailable, perform these checks by hand and report the same findings:

1. Check optional tools with `command -v`: `agent-browser`, `gh`, `jq`, `ast-grep`, `ffmpeg`.
2. If inside a JJ workspace, resolve its absolute root with `jj workspace root` and run subsequent JJ commands with that root as cwd. See https://docs.jj-vcs.dev/latest/cli-reference/ . Scope repository GitHub commands there with `GIT_DIR=$(jj git root)`.
3. Check for obsolete `rocketclaw.local.md` at the repo root.
4. Check whether `.rocketclaw/config.yaml` exists.
5. Check whether `.rocketclaw/config.local.yaml` exists and, if it does, check local ignore coverage with the retained `scripts/ignore-status.py <absolute-root> .rocketclaw/config.local.yaml`. If that helper is also unavailable, inspect applicable `.gitignore` rules including negations; report uncertain coverage as unverified, never as safely ignored.
6. Compare `.rocketclaw/config.example.yaml` with `references/config-template.yaml` when the template is readable; otherwise report that the example refresh must be done manually.
7. Report a legacy Compound Codex tool map when `${CODEX_HOME:-$HOME/.codex}/AGENTS.md` contains a standalone `<!-- BEGIN COMPOUND CODEX TOOL MAP -->` line followed by a standalone `<!-- END COMPOUND CODEX TOOL MAP -->` line.
8. Report the optional compatibility-cache `node` row as available when `node -p 'process.versions.node'` is 22.13 or newer and `command -v npx` succeeds; otherwise name which is missing or too old. This is not a native OpenCode peer availability check. Resolve configured model intent through `opencode.models` and permitted native subagents/shell, respecting delegation permission, model-override permission, and effective nesting depth separately.

This file is read at two points: from Step 2 whenever the bundled health script is unavailable, for the inline equivalent above; and before any Phase 2 write, once Step 3 has decided that a writable checkout exists and which reported issues need remediation. Ask with the blocking question tool named in SKILL.md. Maintaining the generated example files is the work this phase does on its own — Step 5's refresh and its removal of the superseded `config.local.example.yaml`. Every change to a user-owned file is offered and applied only if the user approves.

## Phase 2: Fix Repo-Local Issues

Resolve the repository root (`jj workspace root`). All paths below are relative to the repo root, not the current working directory.

### Step 4: Remove Obsolete Local Config

If `rocketclaw.local.md` exists at the repo root, explain that it is obsolete because review-agent selection is automatic and surviving machine-local settings now live in `.rocketclaw/config.local.yaml` (the optional override). Team defaults live in `config.yaml`.

Ask whether to delete it now. Delete only if the user approves.

### Step 5: Refresh Example Config

Copy `references/config-template.yaml` to `<repo-root>/.rocketclaw/config.example.yaml`, creating the directory if needed. This file is committed to the repo and should always reflect the latest available settings.

If leftover `<repo-root>/.rocketclaw/config.local.example.yaml` remains after the new example exists, treat it as stale generated example (not user config) and remove it with `trash` (never `rm`).

If the bundled template cannot be located by the current platform, print the source template path that failed and tell the user the example config could not be refreshed automatically.

### Step 6: Create Repo Config If Missing

If `.rocketclaw/config.yaml` does not exist, offer to create it, even when health is otherwise green. The user should learn that it is a shared file where the team can turn on RocketClaw settings, that every setting starts commented out so nothing changes until someone enables one, and that declining keeps the defaults.

If the user approves, copy `references/config-template.yaml` to `<repo-root>/.rocketclaw/config.yaml`. Never overwrite an existing `config.yaml` or `config.local.yaml`.

If `config.local.yaml` already exists, leave it. After creating (or if both files already exist), name ordinary local keys that would shadow the new team file. If local still has `docs_root`, say it is ignored and offer to move it into `config.yaml`.

Do not create `config.local.yaml`.

### Step 6a: Repair Invalid Work Preferences

When the health report marks the Work implementation engine unavailable or invalid, detects retired scalar routing keys, or reports malformed dormant `work_engine_preferences`, do not guess the intended recipients. Explain the exact reported problem, derive a valid ordered `work_engine_preferences` block from the user's stated harness/model order (or remove malformed dormant preferences and use `work_engine_mode: off` when they want native-by-default), remove any retired scalar routing keys, and show the complete replacement block. Edit the layer that supplied the failing value. If the bad ordinary key is only in `config.yaml`, edit that file after preview. Do not hide a broken team value behind a new local override. Preserve every unrelated setting. Re-run the health check and require it to report either native or the intended normalized ordered list before setup is complete.

When the health report warns about `work_engine_effort`, the health status of the engine does not change, and the warning says what `ce-work` does with the value. A value that is not a map, or an entry for an unknown harness, requests nothing. A `cursor` entry is different: no Cursor route can run at an effort, so `ce-work` treats Cursor entries in the preference list as unavailable until the entry is removed. The key is a map from harness to one of that harness's own effort levels. Ask what effort the user wants for each harness rather than guessing, show the replacement map, and edit the layer the warning names. Re-run the health check and require the warning to be gone.

### Step 6b: Repair Invalid `docs_root`

When the health report marks `docs_root` invalid, explain the exact reason it gave (absolute, escapes the repo, `..` traversal, repo root, `.git/`, or a non-directory component) and the consequence: artifacts will not be written until it is fixed, because `docs_root` fails closed rather than silently falling back to `docs`. `docs_root` is read only from `.rocketclaw/config.yaml`. A `docs_root` in `config.local.yaml` is ignored — if local still has one, say so and offer to move it into `config.yaml`. Offer to either correct the tracked value to a valid repo-relative directory the user names, or remove the bad `docs_root` key from `config.yaml`. Removing it reaches the default `docs`. Edit only those keys after the user approves; preserve every unrelated setting. Re-run the health check and require it to report a resolved artifact root before setup is complete.

### Step 7: Ensure Local Config Is Gitignored

If `.rocketclaw/config.local.yaml` exists and is not covered by `.gitignore`, offer to add:

```text
.rocketclaw/*.local.yaml
```

Append the entry to the repo-root `.gitignore` only if the user approves. Do not overwrite unrelated `.gitignore` content.

### Step 8: Offer To Ignore Scratch Space

Skills keep durable scratch under `.context/` and temporary data under `.tmp/`. Probe local coverage with `scripts/ignore-status.py <absolute-root> .context/` and separately `.tmp/`, including directory-only rules before a directory exists. Uncertain coverage is unverified, not proven safe. When either is not covered, offer the corresponding entries:

```text
.context/
.tmp/
```

Append the entry to the repo-root `.gitignore` only if the user approves. Do not overwrite unrelated `.gitignore` content.

Unlike Step 7 this does not wait for the path to exist. The skill about to write there offers the same entry at its first write, so a repository that never uses one of those skills never needs the line — adding it here only means that prompt never has to fire.

### Step 9: Point Agents At The Knowledge Store, And Offer The Standing Directives

Runs whenever the repository has a root agent-instructions file (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or the equivalent this project uses). When one file only `@`-includes another, the substantive file is the target. No such file: skip this step and say so in the summary; setup never creates one.

**Outcome:** an agent that reads the file learns that the knowledge store exists at the resolved `<root>/solutions/` and when it is relevant, and the file carries a standing instruction for capturing learnings and one for the agent's own chat replies if the user wants them. Each addition is offered separately, previewed with its exact placement, and applied only on approval.

**Store mention.** Read the file and judge semantically, not by string match, whether a reader would learn three things: a store of documented solutions exists at the concrete path, enough of its shape to search it (categories, YAML frontmatter fields such as `module`, `tags`, `problem_type`), and that it is relevant when implementing or debugging in a documented area. When the spirit is met, offer nothing. Otherwise draft the smallest addition in the file's own style: one line in the closest existing section (a directory listing, architecture tree, conventions block) beats a new heading, and a new heading is the last resort. Keep the tone informational, not imperative, because an imperative causes redundant reads when a workflow already searches. Write the concrete resolved path, never the `<root>` placeholder, since people and plugin-less agents read this file. Calibration for a directory listing:

```text
<root>/solutions/  # documented solutions to past problems (bugs, best practices, workflow patterns), organized by category with YAML frontmatter (module, tags, problem_type)
```

**Compounding directive.** Offer it only when the repository treats the store as tracked, committed knowledge: `jj file list <root>/solutions/` from the absolute workspace root lists at least one tracked file (an untracked or ignored directory is not evidence), or the user just accepted the store mention. Skip the offer when the file already carries a standing instruction to invoke `ce-compound` at a completion checkpoint, in any wording. Otherwise offer it. The user should learn that agents would then record a lesson after fixing a problem whose reasoning the code alone does not show, so the next agent does not repeat the mistake. The choices are that agents ask first, that they do it without asking, or no instruction.

Insert the chosen variant verbatim from `assets/compounding-directive.md` in this skill's directory; the wording is pinned by a test, so do not paraphrase it. Place it beside the store mention when that landed in a conventions or working-agreement block, otherwise in the block where the file states how agents should work. Match the surrounding form (a bullet in a bullet list, a paragraph in prose). Say where the text would go and what it asks agents to do, and show the exact text if the user asks. Append only on approval and leave the rest of the file untouched.

**Chat-register directive.** Offer it whenever this step runs. Skip the offer only when the file already carries an instruction that covers all three parts of the bundled one: the report boundary (a user-facing report, summary, or handoff about to be written), the invocation (use the `ce-noslop` skill for that writing), and the exclusions (code, config, verbatim quotes, text the user asked to post as written). A partial instruction, such as one naming only the boundary or a generic "write plainly", or an unrelated writing rule still gets the offer. The user should learn that agents' reports and summaries would then be written plainly, without AI writing habits, and that code and text they asked to post as written are untouched.

Insert the text verbatim from `assets/noslop-directive.md` in this skill's directory; do not paraphrase it. Place it beside the compounding directive when that landed or already exists, otherwise where the compounding directive would go. Match the surrounding form. Say where the text would go and what it asks agents to do, and show the exact text if the user asks. Append only on approval and leave the rest of the file untouched.

Report all three outcomes in the Phase 3 summary.

### Step 10: Offer Starting Drafts Of The Project's Review Docs

Read `references/project-docs.md` from this skill's directory and follow it. It makes one offer to draft or update `CODING_STANDARDS.md`, `REVIEW.md`, and the agent-instructions lines and AI reviewer files that point to them, built from the repository's own review history, and writes nothing until the user approves the drafts.
