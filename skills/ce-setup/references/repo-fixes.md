# Repo-local fixes (Phase 2)

## Inline health-check equivalent (Step 2 fallback)

When the bundled `scripts/check-health` is unavailable, perform these checks by hand and report the same findings:

1. Check optional tools with `command -v`: `agent-browser`, `gh`, `jq`, `ast-grep`, `ffmpeg`.
2. Resolve the absolute root with `jj workspace root`. If no JJ workspace is present, report that repo-local checks did not run.
3. Check for obsolete `rocketclaw.local.md` at the workspace root.
4. Check whether `.rocketclaw/config.yaml` exists.
5. Check whether `.rocketclaw/config.local.yaml` exists. If so, inspect workspace-root and nested `.gitignore` rules (including negations) and whether `(cd "$workspace_root" && jj --ignore-working-copy file list -r @ -- .rocketclaw/config.local.yaml)` reports it as tracked. Check `.tmp/` and `.context/` ignore coverage even when absent. Report an uncertain result instead of assuming the path is ignored.
6. Compare `.rocketclaw/config.example.yaml` with `references/config-template.yaml` when the template is readable; otherwise report that the example refresh must be done manually.
7. Report a legacy Compound Codex tool map when `${CODEX_HOME:-$HOME/.codex}/AGENTS.md` contains a standalone `<!-- BEGIN COMPOUND CODEX TOOL MAP -->` line followed by a standalone `<!-- END COMPOUND CODEX TOOL MAP -->` line.
8. Report the `node` row as available for optional legacy npm cache warming when `node -p 'process.versions.node'` is 22.13 or newer and `command -v npx` succeeds; otherwise name which of the two is missing or too old. This does not check native delegation; `references/opencode-setup.md` owns that prerequisite.

This file is read at two points: from Step 2 whenever the bundled health script is unavailable, for the inline equivalent above; and before any Phase 2 write, once Step 3 has decided that a writable checkout exists and which reported issues need remediation. Ask with the blocking question tool `references/communication.md` names. Maintaining the generated example files is the work this phase does on its own — Step 5's refresh and its removal of the superseded `config.local.example.yaml`. Every change to a user-owned file is offered and applied only if the user approves.

## Phase 2: Fix Repo-Local Issues

Resolve the absolute workspace root (`jj workspace root`) and use it as the CWD for all repo-scoped commands. All paths below are relative to that root.

### Step 4: Remove Obsolete Local Config

If `rocketclaw.local.md` exists at the workspace root, explain that it is obsolete because review-agent selection is automatic and surviving machine-local settings now live in `.rocketclaw/config.local.yaml` (the optional override). Team defaults live in `config.yaml`.

Ask whether to delete it now. Delete only if the user approves.

### Step 5: Refresh Example Config

Copy `references/config-template.yaml` to `<repo-root>/.rocketclaw/config.example.yaml`, creating the directory if needed. This file is committed to the repo and should always reflect the latest available settings. When the health report says the example was written by a newer plugin, leave it alone, so an older plugin never rolls it back.

If leftover `<repo-root>/.rocketclaw/config.local.example.yaml` remains after the new example exists, treat it as stale generated example (not user config) and remove it with `trash` (never `rm`).

If the bundled template cannot be located by the current platform, print the source template path that failed and tell the user the example config could not be refreshed automatically.

### Step 5a: Refresh Repo Config Files

When the health report says `config.yaml` was written from an older template, names a retired config key in either file, or calls `config.local.yaml` a full copy of the old local template, read `references/config-refresh.md` and follow it. A file the report says was written by a newer plugin, or cannot be refreshed, stays untouched.

### Step 6: Create Repo Config If Missing

If `.rocketclaw/config.yaml` does not exist, offer to create it, even when health is otherwise green. It is the shared place to turn on RocketClaw settings; everything starts commented out, and declining keeps the defaults. This is not the user-level OpenCode configuration required in `references/opencode-setup.md`.

If the user approves, copy `references/config-template.yaml` to `<repo-root>/.rocketclaw/config.yaml`. Change an existing `config.yaml` or `config.local.yaml` only through Step 5a's verified refresh or the repairs below.

If `config.local.yaml` already exists, leave it. After creating (or if both files already exist), name ordinary local keys that would shadow the new team file. If local still has `docs_root`, say it is ignored and offer to move it into `config.yaml`.

Do not create `config.local.yaml`.

### Step 6a: Repair Invalid `ce-work` Preferences

When the health report marks the `ce-work` implementation preferences unavailable or invalid, or reports malformed dormant `work_engine_preferences`, do not guess the intended recipients. Retired routing keys such as `work_engine_target` are Step 5a's to remove. Derive the ordered list from the user's model preferences, or remove malformed dormant preferences and use `work_engine_mode: off` when they want the skill default. Show the exact problem and complete replacement. Repair the layer that supplied the failing value, never a new override, and preserve unrelated settings. Re-run health to verify the normalized list or default. Health validates shape; `ce-work` resolves availability through `opencode.models` before native delegation.

When the health report warns about `work_engine_effort`, show the warning, ask what effort the user intended, and preview the replacement map. The key is a map from the configured family label to a requested effort. Existing label-specific input restrictions still apply; the exact resolved OpenCode model must be able to honor the requested effort at dispatch. Edit the layer the warning names and re-run the health check.

### Step 6b: Repair Invalid `docs_root`

When the health report marks `docs_root` invalid, explain the exact reason and consequence: artifacts will not be written until it is fixed. `docs_root` is read only from `.rocketclaw/config.yaml`. If local supplies one, say that it is ignored and offer to move it into the tracked config. Offer to correct the value to a valid repo-relative directory the user names or remove it to restore the `docs` default. Edit only the approved keys, preserve unrelated settings, and re-run health to verify the resolved root.

### Step 7: Ensure Local Config Is Gitignored

If `.rocketclaw/config.local.yaml` exists and is not covered by `.gitignore`, offer to add:

```text
.rocketclaw/*.local.yaml
```

Append the entry to the repo-root `.gitignore` only if the user approves. Do not overwrite unrelated rules or claim that an ignore rule untracks an already-tracked config. If the file is already tracked, flag it separately and avoid sharing its contents.

### Step 8: Offer to Ignore Local Run Storage

Run temporary files belong under the workspace's `.tmp/`, or under local `.tmp/` outside JJ. When health reports it uncovered, offer the repo-root entry:

```text
/.tmp/
```

Append the entry to the repo-root `.gitignore` only if the user approves. Do not overwrite unrelated `.gitignore` content.

Verify the ignore rule even before the directory exists. If the project uses `.context/` for repo-bound local artifacts and that directory is uncovered, also offer `/.context/`; it is not a fallback for temporary files.

### Step 9: Point Agents At The Knowledge Store, And Offer The Standing Directives

Runs whenever the repository has a root agent-instructions file (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or the equivalent this project uses). When one file only `@`-includes another, the substantive file is the target. No such file: skip this step and say so in the summary; setup never creates one.

**Outcome:** an agent that reads the file learns that the knowledge store exists at the resolved `<root>/solutions/` and when it is relevant, and the file carries a standing instruction for capturing learnings and one for the agent's own chat replies if the user wants them. Each addition is offered separately, previewed with its exact placement, and applied only on approval.

**Store mention.** Read the file and judge semantically, not by string match, whether a reader would learn three things: a store of documented solutions exists at the concrete path, enough of its shape to search it (categories, YAML frontmatter fields such as `module`, `tags`, `problem_type`), and that it is relevant when implementing or debugging in a documented area. When the spirit is met, offer nothing. Otherwise draft the smallest addition in the file's own style: one line in the closest existing section (a directory listing, architecture tree, conventions block) beats a new heading, and a new heading is the last resort. Keep the tone informational, not imperative, because an imperative causes redundant reads when a workflow already searches. Write the concrete resolved path, never the `<root>` placeholder, since people and plugin-less agents read this file. Calibration for a directory listing:

```text
<root>/solutions/  # documented solutions to past problems (bugs, best practices, workflow patterns), organized by category with YAML frontmatter (module, tags, problem_type)
```

**Compounding directive.** Offer it only when the repository treats the store as committed knowledge: `(cd "$workspace_root" && jj --ignore-working-copy file list -r "$verified_history_head" -- "$artifact_root/solutions")` lists at least one file at the verified committed history head, or the user just accepted the store mention. An untracked or ignored directory is not evidence. Skip the offer when the file already has an equivalent instruction letting `ce-compound` decide at a completion checkpoint. If an existing directive instead makes the agent decide whether a lesson deserves a document, offer the corresponding bundled variant. Explain that a lesson can be captured as a test, coding standard, or learning, and offer ask-first, automatic, or no instruction.

Insert the chosen variant verbatim from `assets/compounding-directive.md` in this skill's directory; the wording is pinned by a test, so do not paraphrase it. Place it beside the store mention when that landed in a conventions or working-agreement block, otherwise in the block where the file states how agents should work. Match the surrounding form (a bullet in a bullet list, a paragraph in prose). Say where the text would go and what it asks agents to do, and show the exact text if the user asks. Append only on approval and leave the rest of the file untouched.

**Chat-register directive.** Offer it whenever this step runs. Skip the offer only when the file already carries an instruction that covers all three parts of the bundled one: the report boundary (a user-facing report, summary, or handoff about to be written), the invocation (use the `ce-noslop` skill for that writing), and the exclusions (code, config, verbatim quotes, text the user asked to post as written). A partial instruction, such as one naming only the boundary or a generic "write plainly", or an unrelated writing rule still gets the offer. The user should learn that agents' reports and summaries would then be written plainly, without AI writing habits, and that code and text they asked to post as written are untouched.

Insert the text verbatim from `assets/noslop-directive.md` in this skill's directory; do not paraphrase it. Place it beside the compounding directive when that landed or already exists, otherwise where the compounding directive would go. Match the surrounding form. Say where the text would go and what it asks agents to do, and show the exact text if the user asks. Append only on approval and leave the rest of the file untouched.

Report all three outcomes in the Phase 3 summary.

### Step 10: Offer Starting Drafts Of The Project's Review Docs

Read `references/project-docs.md` from this skill's directory and follow it. It makes one offer to draft or update `CODING_STANDARDS.md`, `REVIEW.md`, and the agent-instructions lines and AI reviewer files that point to them, built from the repository's own review history, and writes nothing until the user approves the drafts.
