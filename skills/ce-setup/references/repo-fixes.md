# Repo-local fixes (Phase 2)

## Inline health-check equivalent (Step 2 fallback)

When the bundled `scripts/check-health` is unavailable, perform these checks by hand and report the same findings:

1. Check optional tools with `command -v`: `agent-browser`, `gh`, `jq`, `ast-grep`, `ffmpeg`, `opencode`.
2. Resolve the root with [`jj workspace root`](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace-root). Run repository commands from that absolute root. If none is resolved, skip repo checks.
3. Check for the obsolete root local settings file by the filename constructed in Step 4 below.
4. Check whether `.rocketclaw/config.yaml` exists.
5. Check whether `.rocketclaw/config.local.yaml` exists. Run `python3 "$SKILL_DIR/scripts/check-ignore.py" "$repo_root"` from the absolute root to list safely ignored targets; a missing helper or an error is unverified, not unignored. Report `.context/` and `.tmp/` coverage too.
6. Compare `.rocketclaw/config.example.yaml` with `references/config-template.yaml` when the template is readable; otherwise report that the example refresh must be done manually.
7. Report a legacy Compound Codex tool map when `${CODEX_HOME:-$HOME/.codex}/AGENTS.md` contains a standalone `<!-- BEGIN COMPOUND CODEX TOOL MAP -->` line followed by a standalone `<!-- END COMPOUND CODEX TOOL MAP -->` line.
8. Check effective OpenCode V2 depth and configured model availability as described in `references/native-models.md`. Tell users to merge `"experimental": { "subagent_depth": 3 }` into `~/.config/opencode/opencode.json` or the existing JSON/JSONC in the directory shown by `opencode debug paths` / `opencode debug paths config`. Preserve unrelated and sibling settings and higher depths, do not create a competing file, and verify that no higher-precedence file lowers the value below `3`. Installing the package alone does not enable deep delegation in a consuming project. Do not make this user-level edit yourself.

This file is read at two points: from Step 2 whenever the bundled health script is unavailable, for the inline equivalent above; and before any Phase 2 write, once Step 3 has decided that a writable checkout exists and which reported issues need remediation. Ask with the blocking question tool `references/communication.md` names. Maintaining the generated example files is the work this phase does on its own — Step 5's refresh and its removal of the superseded `config.local.example.yaml`. Every change to a user-owned file is offered and applied only if the user approves.

## Phase 2: Fix Repo-Local Issues

Resolve the absolute root with `jj workspace root`. All paths below are relative to that root.

### Step 4: Remove Obsolete Local Config

The obsolete file came from older installs: set `legacy_prefix=compound` and check `${legacy_prefix}-engineering.local.md` at the repo root. If present, explain that review-agent selection is now automatic and surviving machine-local settings live in `.rocketclaw/config.local.yaml` (the optional override). Team defaults live in `config.yaml`.

Ask whether to delete it now. Delete only if the user approves.

### Step 5: Refresh Example Config

Copy `references/config-template.yaml` to `<repo-root>/.rocketclaw/config.example.yaml`, creating the directory if needed. This file is committed to the repo and should always reflect the latest available settings. When the health report says the example was written by a newer plugin, leave it alone, so an older plugin never rolls it back.

If leftover `<repo-root>/.rocketclaw/config.local.example.yaml` remains after the new example exists, treat it as stale generated example (not user config) and remove it with `trash` (never `rm`).

If the bundled template cannot be located by the current platform, print the source template path that failed and tell the user the example config could not be refreshed automatically.

### Step 5a: Refresh Repo Config Files

When the health report says `config.yaml` was written from an older template, names a retired config key in either file, or calls `config.local.yaml` a full copy of the old local template, read `references/config-refresh.md` and follow it. A file the report says was written by a newer plugin, or cannot be refreshed, stays untouched.

### Step 6: Create Repo Config If Missing

If `.rocketclaw/config.yaml` does not exist, offer to create it, even when health is otherwise green. The user should learn that it is a shared file where the team can turn on RocketClaw settings, that every setting starts commented out so nothing changes until someone enables one, and that declining keeps the defaults.

If the user approves, copy `references/config-template.yaml` to `<repo-root>/.rocketclaw/config.yaml`. Change an existing `config.yaml` or `config.local.yaml` only through Step 5a's verified refresh or the repairs below.

If `config.local.yaml` already exists, leave it. After creating (or if both files already exist), name ordinary local keys that would shadow the new team file. If local still has `docs_root`, say it is ignored and offer to move it into `config.yaml`.

Do not create `config.local.yaml`.

### Step 6a: Repair Invalid Work Preferences

When health marks the implementation engine unavailable or invalid, or reports malformed dormant `work_engine_preferences`, do not guess the intended recipients. Retired routing keys such as `work_engine_target` are Step 5a's to remove, not this step's. Explain the exact problem, derive a valid ordered `work_engine_preferences` block from the user's stated route/model order (or remove malformed dormant preferences and use `work_engine_mode: off` when they want the session model by default), and show the complete replacement block. Edit the layer that supplied the failing value; never conceal a bad shared value behind a new local override. Preserve every unrelated setting. Re-run health and require it to report the intended normalized list or session default. Check model availability through `references/native-models.md`; a well-formed but unavailable or unauthorized route is not a config syntax error or permission to rewrite it.

When health warns about `work_engine_effort`, the engine's config status does not change. A value that is not a map, or an entry for an unknown route label, requests nothing. A `cursor` or `pi` entry makes that route unavailable because the route accepts no effort. The key is a map from legacy route labels to their supported effort levels; execution matches the chosen OpenCode model's advertised variants, never invoking that harness. Ask what effort the user wants rather than guessing, show the replacement map, and edit the layer the warning names. Re-run health and require the warning to be gone.

### Step 6b: Repair Invalid `docs_root`

When the health report marks `docs_root` invalid, explain the exact reason and the consequence: artifacts will not be written until it is fixed, because `docs_root` fails closed rather than silently falling back to `docs`. `docs_root` is read only from `.rocketclaw/config.yaml`. A `docs_root` in `config.local.yaml` is ignored — if local still has one, say so and offer to move it into `config.yaml`. Offer to either correct the tracked value to a valid repo-relative directory the user names, or remove the bad `docs_root` key from `config.yaml`. Removing it reaches the default `docs`. Edit only those keys after the user approves; preserve every unrelated setting. Re-run the health check and require it to report a resolved artifact root before setup is complete.

### Step 7: Ensure Local Config Is Gitignored

If `.rocketclaw/config.local.yaml` exists and is not covered by `.gitignore`, offer to add:

```text
.rocketclaw/*.local.yaml
```

Append the entry to the repo-root `.gitignore` only if the user approves. Do not overwrite unrelated `.gitignore` content.

### Step 8: Offer To Ignore Local Scratch Space

Skills use `.context/` for context artifacts and `.tmp/` for temporary files, including failure output. Use Step 2's JJ ignore probe to check directory coverage even when these paths do not exist. If coverage is unverified, report that, not a definitive result. When coverage is missing, offer only the missing entries:

```text
.context/
.tmp/
```

Append the entry to the repo-root `.gitignore` only if the user approves. Do not overwrite unrelated `.gitignore` content.

Unlike Step 7 this does not wait for the path to exist. A skill writing `.context/` still offers its entry at first use. Tell the user to ignore `.tmp/` before running workflows that need it. Outside JJ use local `.tmp/`, never global temporary storage.

### Step 9: Point Agents At The Knowledge Store, And Offer The Standing Directives

Runs whenever the repository has a root agent-instructions file (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or the equivalent this project uses). When one file only `@`-includes another, the substantive file is the target. No such file: skip this step and say so in the summary; setup never creates one.

**Outcome:** an agent that reads the file learns that the knowledge store exists at the resolved `<root>/solutions/` and when it is relevant, and the file carries a standing instruction for capturing learnings and one for the agent's own chat replies if the user wants them. Each addition is offered separately, previewed with its exact placement, and applied only on approval.

**Store mention.** Read the file and judge semantically, not by string match, whether a reader would learn three things: a store of documented solutions exists at the concrete path, enough of its shape to search it (categories, YAML frontmatter fields such as `module`, `tags`, `problem_type`), and that it is relevant when implementing or debugging in a documented area. When the spirit is met, offer nothing. Otherwise draft the smallest addition in the file's own style: one line in the closest existing section (a directory listing, architecture tree, conventions block) beats a new heading, and a new heading is the last resort. Keep the tone informational, not imperative, because an imperative causes redundant reads when a workflow already searches. Write the concrete resolved path, never the `<root>` placeholder, since people and plugin-less agents read this file. Calibration for a directory listing:

```text
<root>/solutions/  # documented solutions to past problems (bugs, best practices, workflow patterns), organized by category with YAML frontmatter (module, tags, problem_type)
```

**Compounding directive.** Offer it only when the repository treats the store as tracked, committed knowledge: from the absolute workspace root, `jj --ignore-working-copy file list -r <verified-history-head> -- "<root>/solutions"` lists at least one file in the relevant committed history (an untracked or ignored directory is not evidence), or the user just accepted the store mention. Skip the offer when the file already carries a standing instruction to invoke `ce-compound`, in any wording, that runs at a completion checkpoint and lets the skill decide whether a lesson qualifies. When the existing instruction has the agent first decide whether the lesson deserves a document, offer to replace it with the bundled variant of the same kind (ask first or automatic). That pre-judgment skips lessons the skill would hold in a test or a coding standard. Otherwise offer it. The user should learn that agents would then record a lesson as a test, a coding standard, or a learning after work that corrected a wrong belief about how something behaves, so the next agent does not repeat the mistake. The choices are that agents ask first, that they do it without asking, or no instruction.

Insert the chosen variant verbatim from `assets/compounding-directive.md` in this skill's directory; the wording is pinned by a test, so do not paraphrase it. Place it beside the store mention when that landed in a conventions or working-agreement block, otherwise in the block where the file states how agents should work. Match the surrounding form (a bullet in a bullet list, a paragraph in prose). Say where the text would go and what it asks agents to do, and show the exact text if the user asks. Append only on approval and leave the rest of the file untouched.

**Chat-register directive.** Offer it whenever this step runs. Skip the offer only when the file already carries an instruction that covers all three parts of the bundled one: the report boundary (a user-facing report, summary, or handoff about to be written), the invocation (use the `ce-noslop` skill for that writing), and the exclusions (code, config, verbatim quotes, text the user asked to post as written). A partial instruction, such as one naming only the boundary or a generic "write plainly", or an unrelated writing rule still gets the offer. The user should learn that agents' reports and summaries would then be written plainly, without AI writing habits, and that code and text they asked to post as written are untouched.

Insert the text verbatim from `assets/noslop-directive.md` in this skill's directory; do not paraphrase it. Place it beside the compounding directive when that landed or already exists, otherwise where the compounding directive would go. Match the surrounding form. Say where the text would go and what it asks agents to do, and show the exact text if the user asks. Append only on approval and leave the rest of the file untouched.

Report all three outcomes in the Phase 3 summary.

### Step 10: Offer Starting Drafts Of The Project's Review Docs

Read `references/project-docs.md` from this skill's directory and follow it. It makes one offer to draft or update `CODING_STANDARDS.md`, `REVIEW.md`, and the agent-instructions lines and AI reviewer files that point to them, built from the repository's own review history, and writes nothing until the user approves the drafts.
