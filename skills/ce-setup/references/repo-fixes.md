# Repo-local fixes (Phase 2) and the summary (Phase 3)

## Inline health-check equivalent (Step 2 fallback)

When the bundled `scripts/check-health` is unavailable, perform these checks by hand and report the same findings:

1. Check optional tools with `command -v`: `agent-browser`, `gh`, `jq`, `ast-grep`, `ffmpeg`.
2. Resolve the JJ workspace root with `jj workspace root`; run subsequent JJ commands with that absolute root as cwd.
3. Check for obsolete `rocketclaw.local.md` at the repo root.
4. Check whether `.rocketclaw/config.yaml` exists.
5. Check whether `.rocketclaw/config.local.yaml` exists and, if it does, verify a covering `.gitignore` rule and that `jj file list --ignore-working-copy` does not list it. If coverage cannot be established, report it as unverified rather than safe.
6. Compare `.rocketclaw/config.example.yaml` with `references/config-template.yaml` when the template is readable; otherwise report that the example refresh must be done manually.
7. Report a legacy Compound Codex tool map when `${CODEX_HOME:-$HOME/.codex}/AGENTS.md` contains a standalone `<!-- BEGIN COMPOUND CODEX TOOL MAP -->` line followed by a standalone `<!-- END COMPOUND CODEX TOOL MAP -->` line.

This file is read at two points: from Step 2 whenever the bundled health script is unavailable, for the inline equivalent above; and before any Phase 2 write, once Step 3 has decided that a writable checkout exists and which reported issues need remediation. Ask with the blocking question tool named in SKILL.md. Maintaining the generated example files is the work this phase does on its own — Step 5's refresh and its removal of the superseded `config.local.example.yaml`. Every change to a user-owned file is offered and applied only if the user approves.

## Phase 2: Fix Repo-Local Issues

Resolve the workspace root (`jj workspace root`). All paths below are relative to that root, not the current working directory; set JJ subprocess cwd to the absolute root.

### Step 4: Remove Obsolete Local Config

If `rocketclaw.local.md` exists at the repo root, explain that it is obsolete because review-agent selection is automatic and surviving machine-local settings now live in `.rocketclaw/config.local.yaml` (the optional override). Team defaults live in `config.yaml`.

Ask whether to delete it now. Delete only if the user approves.

### Step 5: Refresh Example Config

Copy `references/config-template.yaml` to `<repo-root>/.rocketclaw/config.example.yaml`, creating the directory if needed. This file is committed to the repo and should always reflect the latest available settings.

If leftover `<repo-root>/.rocketclaw/config.local.example.yaml` remains after the new example exists, treat it as stale generated example (not user config) and remove it with `trash` (never `rm`).

If the bundled template cannot be located by the current platform, print the source template path that failed and tell the user the example config could not be refreshed automatically.

### Step 6: Create Repo Config If Missing

If `.rocketclaw/config.yaml` does not exist, ask — even when health is otherwise green:

```text
Set up a repo config file for this project?
This creates .rocketclaw/config.yaml with optional RocketClaw team defaults.
Everything starts commented out -- you only enable what you need.
It does not create config.local.yaml.

1. Yes, create it
2. No thanks
```

If the user approves, copy `references/config-template.yaml` to `<repo-root>/.rocketclaw/config.yaml`. Never overwrite an existing `config.yaml` or `config.local.yaml`.

If `config.local.yaml` already exists, leave it. After creating (or if both files already exist), name ordinary local keys that would shadow the new team file. If local still has `docs_root`, say it is ignored and offer to move it into `config.yaml`.

Do not create `config.local.yaml`.

### Step 6a: Repair Invalid RocketClaw Work Preferences

When the health report marks the RocketClaw Work implementation engine unavailable or invalid, detects retired scalar routing keys, or reports malformed dormant `work_engine_preferences`, do not guess the intended recipients. Explain the exact reported problem, derive a valid ordered `work_engine_preferences` block from the user's stated harness/model order (or remove malformed dormant preferences and use `work_engine_mode: off` when they want native-by-default), remove any retired scalar routing keys, and show the complete replacement block. Edit the layer that supplied the failing value. If the bad ordinary key is only in `config.yaml`, edit that file after preview. Do not hide a broken team value behind a new local override. Preserve every unrelated setting. Re-run the health check and require it to report either native or the intended normalized ordered list before setup is complete.

For OpenCode V2, accept `harness: opencode` with an exact discovered `provider/modelname#variant`; preserve explicit effective subagent/harness settings. The template also supports `cross_model_peer: opencode`, and `plan_harness: opencode` or `brainstorm_harness: opencode` paired with their model keys. Native OpenCode delegation applies only when no explicit subagent or alternative-harness route wins and model discovery plus native subagent model selection are available. Preserve cross-model intent and tiers without guessing or silently reusing the session model.

When the health report names an invalid OpenCode model in any of those scalar routes, repair the model key in the reported config layer using an exact discovered ID and optional variant. Preserve the intended harness and unrelated settings, preview the replacement for approval, and require the diagnostic to disappear after rerunning the check. OpenCode effort requests must match the selected model's discovered `#variant` rather than a separate CLI effort flag.

When the health report warns about `work_engine_effort`, the health status of the engine does not change, and the warning says what `ce-work` does with the value. A value that is not a map, or an entry for an unknown harness, requests nothing. A `cursor` entry is different: no Cursor route can run at an effort, so `ce-work` treats Cursor entries in the preference list as unavailable until the entry is removed. The key is a map from harness to one of that harness's own effort levels. Ask what effort the user wants for each harness rather than guessing, show the replacement map, and edit the layer the warning names. Re-run the health check and require the warning to be gone.

### Step 6b: Repair Invalid `docs_root`

When the health report marks `docs_root` invalid, explain the exact reason it gave (absolute, escapes the repo, `..` traversal, repo root, `.jj/` or `.git/`, or a non-directory component) and the consequence: RocketClaw artifacts will not be written until it is fixed, because `docs_root` fails closed rather than silently falling back to `docs`. `docs_root` is read only from `.rocketclaw/config.yaml`. A `docs_root` in `config.local.yaml` is ignored — if local still has one, say so and offer to move it into `config.yaml`. Offer to either correct the tracked value to a valid repo-relative directory the user names, or remove the bad `docs_root` key from `config.yaml`. Removing it reaches the default `docs`. Edit only those keys after the user approves; preserve every unrelated setting. Re-run the health check and require it to report a resolved artifact root before setup is complete.

### Step 7: Ensure Local Config Is Gitignored

If `.rocketclaw/config.local.yaml` exists and is not covered by `.gitignore`, offer to add:

```text
.rocketclaw/*.local.yaml
```

Append the entry to the repo-root `.gitignore` only if the user approves. Do not overwrite unrelated `.gitignore` content.

### Step 8: Offer To Ignore RocketClaw Scratch Space

Skills keep runtime scratch under the absolute workspace root's `.tmp/` (local `.tmp/` outside JJ). Verify a covering repo-root `.gitignore` rule and no tracked scratch files using `jj file list --ignore-working-copy`. When coverage is missing or cannot be verified, offer to add:

```text
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

**Compounding directive.** Offer it only when the repository treats the store as tracked, committed knowledge: `jj file list --ignore-working-copy '<root>/solutions/'` is non-empty (an untracked or ignored directory is not evidence), or the user just accepted the store mention. Skip the offer when the file already carries a standing instruction to invoke `ce-compound` at a completion checkpoint, in any wording. Otherwise ask:

```text
Add a standing instruction so agents capture qualifying learnings with ce-compound?
1. Offer first -- the agent asks before capturing
2. Run automatically -- the agent captures without asking
3. No thanks
```

Insert the chosen variant verbatim from `assets/compounding-directive.md` in this skill's directory; the wording is pinned by a test, so do not paraphrase it. Place it beside the store mention when that landed in a conventions or working-agreement block, otherwise in the block where the file states how agents should work. Match the surrounding form (a bullet in a bullet list, a paragraph in prose). Preview the exact text and location, then append only on approval and leave the rest of the file untouched.

**Chat-register directive.** Offer it whenever this step runs. Skip the offer only when the file already carries an instruction that covers all three parts of the bundled one: the report boundary (a user-facing report, summary, or handoff about to be written), the invocation (use the `ce-noslop` skill for that writing), and the exclusions (code, config, verbatim quotes, text the user asked to post as written). A partial instruction, such as one naming only the boundary or a generic "write plainly", or an unrelated writing rule still gets the offer. Ask:

```text
Add a standing instruction so agents write reports and summaries to you with ce-noslop?
1. Yes, add it
2. No thanks
```

Insert the text verbatim from `assets/noslop-directive.md` in this skill's directory; do not paraphrase it. Place it beside the compounding directive when that landed or already exists, otherwise where the compounding directive would go. Match the surrounding form. Preview the exact text and location, then append only on approval and leave the rest of the file untouched.

Report all three outcomes in the Phase 3 summary under Fixed or Skipped.
