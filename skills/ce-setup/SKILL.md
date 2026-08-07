---
name: ce-setup
description: "Check RocketClaw health and workspace-local config."
disable-model-invocation: true
---

# RocketClaw Setup

## Interaction Method

Ask each question below using the platform's blocking question capability. Fall back to a numbered list in chat only when no blocking capability exists in the harness or the call errors. Never silently skip or auto-configure.

`ce-setup` is a lightweight health check and workspace-local config helper. It does **not** bulk-install every optional dependency. Missing tools are reported as optional capabilities so the user can install only the workflows they use.

## Artifact Root Resolution

Every RocketClaw skill that writes or reads an artifact directory (`solutions`, `plans`, `ideation`, and the other workflow-owned trees) resolves its root through the rule below. `ce-setup` carries the canonical statement and reports the resolved root so an operator can confirm where artifacts land before running other skills.

<!-- ce-docs-root:start -->
**Resolve the RocketClaw artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` only from `<workspace-root>/.rocketclaw/config.yaml` (`<workspace-root>` = `jj workspace root`, with `pwd -P` fallback). A value in `config.local.yaml` is ignored. Unset -> `<root>` is `docs`.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/` or `.git/`. Otherwise stop with an error naming `docs_root` and the value; never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Phase 1: Diagnose

### Step 1: Determine Plugin Version

Detect the installed RocketClaw plugin version by reading the plugin metadata or manifest when the platform exposes it. If the version cannot be determined, skip this step.

If a version is found, pass it to the check script via `--version`. Otherwise omit the flag.

### Step 2: Run the Health Check

Before running the script, display:

```text
RocketClaw -- checking your environment...
```

Run the bundled check script. Set `SKILL_DIR` to the absolute directory you loaded this `ce-setup` SKILL.md from; the Bash tool's CWD is the user's project, not the skill dir:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
if [ -f "$SKILL_DIR/scripts/check-health" ]; then bash "$SKILL_DIR/scripts/check-health" --version VERSION; else echo "Bundled health script not found at $SKILL_DIR/scripts/check-health; run the inline checks from ce-setup instead."; fi
```

Use the same command without `--version VERSION` if Step 1 could not determine a version.

If the script is unavailable, perform the inline equivalent:

1. Check optional tools with `command -v`: `agent-browser`, `gh`, `jq`, `ast-grep`, `ffmpeg`.
2. Resolve the workspace root with `jj workspace root`; if it fails or returns empty, use `pwd -P`.
3. Check for obsolete `rocketclaw.local.md` at the workspace root.
4. Check for `.rocketclaw/config.yaml` and `.rocketclaw/config.local.yaml`; when local config exists, verify that `jj file list .rocketclaw/config.local.yaml` omits it. If JJ is unavailable, report that ignore safety could not be verified.
5. Compare `.rocketclaw/config.example.yaml` with `references/config-template.yaml` when the template is readable; otherwise report that the example refresh must be done manually.
6. Verify that `.tmp/` is ignored by JJ before treating setup as healthy.

Display the diagnostic output to the user. Missing optional tools are not setup failures. Surface the resolved artifact root and its config source so the operator can confirm where RocketClaw artifacts will be written. Missing `config.yaml` is a reported absence, not a project issue.

### Step 3: Decide Whether Fixes Are Needed

**User-runnable invocation rendering.** In setup summaries, default to `/ce-setup`; use `$ce-setup` only when the active host explicitly documents dollar-prefixed skill invocation. On oh-my-pi (`omp`), use `/skill:ce-setup`. Render only the invocation as inline code and output one form only.

Continue to Phase 2 whenever a workspace root is available. Phase 2 refreshes the example, offers to create missing team config, and remediates any reported workspace issue:

- obsolete `rocketclaw.local.md`
- `.rocketclaw/config.local.yaml` is not safely ignored by JJ
- `.rocketclaw/config.example.yaml` is missing or outdated
- `.tmp/` is not ignored by JJ
- the health report marks the `ce-work` implementation engine unavailable or invalid, detects retired scalar routing keys, or reports malformed dormant `work_engine_preferences`
- the health report marks `docs_root` invalid

If no workspace root can be resolved, skip Phase 2. Workspace-local files cannot be created or refreshed without it.

If optional tools are missing, do not offer a bulk install. The diagnostic already printed the relevant install command or project URL. Say: "Install optional tools only for the workflows you use."

## Phase 2: Fix Workspace-Local Issues

Resolve the workspace root with `jj workspace root`; if it fails or returns empty, use `pwd -P`. All paths below are relative to that root, not the current working directory. Any temporary storage used while applying fixes must stay under `<workspace-root>/.tmp`; do not use OS-global temporary storage.

### Step 4: Remove Obsolete Local Config

If `rocketclaw.local.md` exists at the workspace root, explain that it is obsolete because review-agent selection is automatic and surviving machine-local settings now live in `.rocketclaw/config.local.yaml`. Team defaults live in `.rocketclaw/config.yaml`.

Ask whether to delete it now. Delete only if the user approves.

### Step 5: Refresh Example Config

Copy `references/config-template.yaml` to `<workspace-root>/.rocketclaw/config.example.yaml`, creating the directory if needed. This support asset belongs in the working-copy change and must reflect the latest available settings.

If leftover `<workspace-root>/.rocketclaw/config.local.example.yaml` remains after the new example exists, treat it as a stale example rather than user config and ask before deleting it.

If the bundled template cannot be located by the current platform, print the source template path that failed and tell the user the example config could not be refreshed automatically.

### Step 6: Create Team Config If Missing

If `.rocketclaw/config.yaml` does not exist, ask even when health is otherwise green:

```text
Set up a team config file for this project?
This creates .rocketclaw/config.yaml with optional RocketClaw team defaults.
Everything starts commented out -- you only enable what you need.
It does not create config.local.yaml.

1. Yes, create it
2. No thanks
```

If the user approves, copy `references/config-template.yaml` to `<workspace-root>/.rocketclaw/config.yaml`. Never overwrite existing `config.yaml` or `config.local.yaml`.

If `config.local.yaml` already exists, leave it. Name ordinary local keys that shadow team defaults. If local config contains `docs_root`, explain that it is ignored and offer to move the value into `config.yaml`. Do not create `config.local.yaml`.

### Step 6a: Repair Invalid `ce-work` Preferences

When health reports invalid `ce-work` routing, explain the reported problem and derive a valid ordered `work_engine_preferences` block from the user's stated harness/model order. Use `work_engine_mode: off` when they want native-by-default, and remove retired scalar routing keys. Show the complete replacement, edit the layer that supplies the failure only after approval, preserve unrelated settings, and re-run health until it reports native or the intended normalized list. Do not hide a broken team value behind a local override.

### Step 6b: Repair Invalid `docs_root`

When health marks `docs_root` invalid, explain the reported boundary failure and that artifact writes fail closed. `docs_root` is read only from `.rocketclaw/config.yaml`; offer to correct it to a valid workspace-relative directory or remove it to restore the `docs` default. If local config also contains `docs_root`, offer to remove or move that ignored value. Edit only approved keys, preserve unrelated settings, and require a resolved artifact root from the next health check.

### Step 7: Ensure Local Config Is Ignored by JJ

If `.rocketclaw/config.local.yaml` exists and `jj file list .rocketclaw/config.local.yaml` returns it, offer to add this entry to `<workspace-root>/.rocketclaw/.gitignore`:

```text
*.local.yaml
```

If the user approves, append the entry without overwriting unrelated content, then run `jj file untrack .rocketclaw/config.local.yaml`. The `.gitignore` filename is part of Git/JJ interoperability; do not replace it with a platform-specific ignore file.

### Step 8: Ensure Workspace Scratch Is Ignored by JJ

RocketClaw temporary storage belongs under `<workspace-root>/.tmp/`. When that path is not ignored, offer to append this entry to the workspace-root `.gitignore`:

```text
.tmp/
```

Append it only if the user approves, and preserve unrelated `.gitignore` content. This check does not wait for `.tmp/` to exist.

## Phase 3: Summary

Display a brief summary:

```text
RocketClaw setup complete

Fixed:     <workspace-local fixes applied, or none>
Skipped:   <workspace-local fixes declined, or none>
Optional:  <missing optional tools, or all available>

Run `<rendered invocation>` anytime to re-check.
```
