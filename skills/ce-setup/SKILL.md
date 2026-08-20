---
name: ce-setup
description: "Check RocketClaw health and workspace-local config."
disable-model-invocation: true
---

# RocketClaw Setup

## Interaction Method

Ask each question below using the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to a numbered list on the host's user-visible chat surface only when no blocking tool exists in the harness or the call errors. Never silently skip or auto-configure.

`ce-setup` is a lightweight health check and workspace-local config helper. It does **not** bulk-install every optional dependency. Missing tools are reported as optional capabilities so the user can install only the workflows they use.

## Artifact Root Resolution

Every RocketClaw skill that writes or reads an artifact directory (`solutions`, `plans`, `ideation`, and the other RocketClaw-owned trees) resolves its root through the rule below. `ce-setup` carries the canonical statement and reports the resolved root so an operator can confirm where artifacts land before running other skills.

<!-- rocketclaw-docs-root:start -->
**Resolve the RocketClaw artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only (`<workspace-root>` = `jj root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- rocketclaw-docs-root:end -->

## Phase 1: Diagnose

### Step 1: Determine Plugin Version

Detect the installed RocketClaw plugin version by reading the plugin metadata or manifest when the platform exposes it. If the version cannot be determined, skip this step.

If a version is found, pass it to the check script via `--version`. Otherwise omit the flag.

### Step 2: Run the Health Check

Before running the script, display:

```text
RocketClaw -- checking your environment...
```

Run the bundled check script. Set `SKILL_DIR` to the absolute directory you loaded this `ce-setup` SKILL.md from — the Bash tool's CWD is the user's project, not the skill dir, so a bare `scripts/` path will not resolve:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
if [ -f "$SKILL_DIR/scripts/check-health" ]; then bash "$SKILL_DIR/scripts/check-health" --version VERSION; else echo "Bundled health script not found at $SKILL_DIR/scripts/check-health; run the inline checks from ce-setup instead."; fi
```

Use the same command without `--version VERSION` if Step 1 could not determine a version.

If the script is unavailable, perform the inline equivalent:

1. Check optional tools with `command -v`: `agent-browser`, `gh`, `jq`, `ast-grep`, `ffmpeg`.
2. If inside a Jujutsu workspace, resolve the workspace root with `jj root`.
3. Check for obsolete `rocketclaw.local.md` at the workspace root.
4. Check whether `.rocketclaw/config.yaml` exists.
5. Check whether `.rocketclaw/config.local.yaml` exists and, if it does, whether Jujutsu excludes it from `jj file list` under the workspace's `.gitignore` rules.
6. Compare `.rocketclaw/config.example.yaml` with `references/config-template.yaml` when the template is readable; otherwise report that the example refresh must be done manually.

Display the diagnostic output to the user. Missing optional tools are not setup failures. The health report includes the resolved artifact root and which config layer supplied it (per Artifact Root Resolution above); surface that line so the operator can confirm where RocketClaw artifacts will be written. Missing `config.yaml` is a reported absence, not a project issue.

### Step 3: Decide Whether Fixes Are Needed

**User-runnable invocation rendering.** In setup summaries, default to `/ce-setup`; use `$ce-setup` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. On oh-my-pi (`omp`), use `/skill:ce-setup`. Render only the invocation as inline code and output one form only.

Report-gated workspace-local remediations apply only to the workspace the health report diagnosed; if Phase 2 will write a different writable workspace, diagnose that workspace first, while session-level findings such as plugin version and optional tools remain from this session's Phase 1.

After the health report, decide Phase 2 from writable-workspace availability:

- If this session has a writable Jujutsu workspace, run Phase 2 locally, including when `project_issues` is 0. Phase 2 always refreshes the example and always offers to create `config.yaml` when that file is missing.
- If this session has no writable workspace, but the user named a repository and the harness exposes a remote repository surface with a writable Jujutsu workspace, run Phase 2 on that surface instead and report the remote workspace-local fixes in Phase 3.
- Otherwise skip Phase 2 and go to Phase 3, saying workspace-local writes were skipped because no writable Jujutsu workspace is available.

Also remediate these project issues when the report names them:

- obsolete `rocketclaw.local.md`
- `.rocketclaw/config.local.yaml` exists but is not safely ignored
- `.rocketclaw/config.example.yaml` is missing or outdated
- the health report marks the `ce-work` skill implementation engine unavailable or invalid, detects retired scalar routing keys, or reports malformed dormant `work_engine_preferences`
- the health report marks `docs_root` invalid (`Invalid docs_root ...`) — RocketClaw artifacts will not be written until it is fixed

If optional tools are missing, do not offer a bulk install. The diagnostic already printed the relevant install command or project URL. Say: "Install optional tools only for the workflows you use."

## Phase 2: Fix Workspace-Local Issues

Resolve the workspace root with `jj root`. All paths below are relative to the workspace root, not the current working directory. If Jujutsu is unavailable or the current directory is not in a workspace, stop before making workspace-local changes.

### Step 4: Remove Obsolete Local Config

If `rocketclaw.local.md` exists at the workspace root, explain that it is obsolete because review-agent selection is automatic and surviving machine-local settings now live in `.rocketclaw/config.local.yaml` (the optional override). Team defaults live in `config.yaml`.

Ask whether to delete it now. Delete only if the user approves.

### Step 5: Refresh Example Config

Copy `references/config-template.yaml` to `<workspace-root>/.rocketclaw/config.example.yaml`, creating the directory if needed. This file belongs in workspace history and should always reflect the latest available settings.

If leftover `<workspace-root>/.rocketclaw/config.local.example.yaml` remains after the new example exists, treat it as stale generated example (not user config) and remove it with `trash` (never `rm`).

If the bundled template cannot be located by the current platform, print the source template path that failed and tell the user the example config could not be refreshed automatically.

### Step 6: Create Workspace Config If Missing

If `.rocketclaw/config.yaml` does not exist, ask — even when health is otherwise green:

```text
Set up a workspace config file for this project?
This creates .rocketclaw/config.yaml with optional RocketClaw team defaults.
Everything starts commented out -- you only enable what you need.
It does not create config.local.yaml.

1. Yes, create it
2. No thanks
```

If the user approves, copy `references/config-template.yaml` to `<workspace-root>/.rocketclaw/config.yaml`. Never overwrite an existing `config.yaml` or `config.local.yaml`.

If `config.local.yaml` already exists, leave it. After creating (or if both files already exist), name ordinary local keys that would shadow the new team file. If local still has `docs_root`, say it is ignored and offer to move it into `config.yaml`.

Do not create `config.local.yaml`.

### Step 6a: Repair Invalid Work Preferences

When the health report marks the `ce-work` implementation engine unavailable or invalid, detects retired scalar routing keys, or reports malformed dormant `work_engine_preferences`, do not guess the intended recipients. Explain the exact reported problem, derive a valid ordered `work_engine_preferences` block from the user's stated harness/model order (or remove malformed dormant preferences and use `work_engine_mode: off` when they want native-by-default), remove any retired scalar routing keys, and show the complete replacement block. Edit the layer that supplied the failing value. If the bad ordinary key is only in `config.yaml`, edit that file after preview. Do not hide a broken team value behind a new local override. Preserve every unrelated setting. Re-run the health check and require it to report either native or the intended normalized ordered list before setup is complete.

### Step 6b: Repair Invalid `docs_root`

When the health report marks `docs_root` invalid, explain the exact reason it gave (absolute, escapes the workspace, `..` traversal, workspace root, `.jj/`, or a non-directory component) and the consequence: RocketClaw artifacts will not be written until it is fixed, because `docs_root` fails closed rather than silently falling back to `docs`. `docs_root` is read only from `.rocketclaw/config.yaml`. A `docs_root` in `config.local.yaml` is ignored — if local still has one, say so and offer to move it into `config.yaml`. Offer to either correct the tracked value to a valid workspace-relative directory the user names, or remove the bad `docs_root` key from `config.yaml`. Removing it reaches the default `docs`. Edit only those keys after the user approves; preserve every unrelated setting. Re-run the health check and require it to report a resolved artifact root before setup is complete.

### Step 7: Ensure Local Config Is Ignored

If `.rocketclaw/config.local.yaml` exists and is not covered by `.gitignore`, offer to add:

```text
.rocketclaw/*.local.yaml
```

Append the entry to the workspace-root `.gitignore` only if the user approves. Do not overwrite unrelated `.gitignore` content.

### Step 8: Offer To Ignore RocketClaw Scratch Space

Skills that keep local scratch write it under `<workspace-root>/.tmp/rocketclaw/`; outside a Jujutsu workspace they fall back to `<current-directory>/.tmp/rocketclaw/`. Check whether the workspace-root `.gitignore` covers `.tmp/rocketclaw/`, including before the directory exists, and when it is not covered, offer to add:

```text
.tmp/rocketclaw/
```

Append the entry to the workspace-root `.gitignore` only if the user approves. Do not overwrite unrelated `.gitignore` content.

Unlike Step 7 this does not wait for the path to exist. The skill about to write there offers the same entry at its first write, so a workspace that never uses one of those skills never needs the line — adding it here only means that prompt never has to fire.

## Phase 3: Summary

Display a brief summary:

```text
✅ RocketClaw setup complete

Fixed:     <workspace-local fixes applied, or none>
Skipped:   <workspace-local fixes declined, or none>
Optional:  <missing optional tools, or all available>

Run `<rendered invocation>` anytime to re-check.
```
