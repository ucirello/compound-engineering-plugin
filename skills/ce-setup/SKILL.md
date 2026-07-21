---
name: ce-setup
description: "Check RocketClaw health and workspace-local config."
disable-model-invocation: true
---

# RocketClaw Setup

## Interaction Method

Ask each question below using the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to a numbered list in chat only when no blocking tool exists in the harness or the call errors. Never silently skip or auto-configure.

`ce-setup` is a lightweight health check and workspace-local config helper. It does **not** bulk-install every optional dependency. Missing tools are reported as optional capabilities so the user can install only the workflows they use.

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
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
if [ -f "$SKILL_DIR/scripts/check-health" ]; then
  bash "$SKILL_DIR/scripts/check-health" --version VERSION
else
  echo "Bundled health script not found at $SKILL_DIR/scripts/check-health; run the inline checks from ce-setup instead."
fi
```

Use the same command without `--version VERSION` if Step 1 could not determine a version.

If the script is unavailable, perform the inline equivalent:

1. Check optional tools with `command -v`: `agent-browser`, `gh`, `jq`, `ast-grep`, `ffmpeg`.
2. If inside a JJ workspace, resolve its root with `jj workspace root`.
3. Check for obsolete `rocketclaw.local.md` at the workspace root.
4. Check whether `.rocketclaw/config.local.yaml` exists and, if it does, whether `jj file list .rocketclaw/config.local.yaml` omits it after the working copy is snapshotted, confirming that `.gitignore` prevents automatic tracking.
5. Compare `.rocketclaw/config.local.example.yaml` with `references/config-template.yaml` when the template is readable; otherwise report that the example refresh must be done manually.

Display the diagnostic output to the user. Missing optional tools are not setup failures.

### Step 3: Decide Whether Fixes Are Needed

Proceed to Phase 2 only if one or more workspace-local project issues exist:

- obsolete `rocketclaw.local.md`
- `.rocketclaw/config.local.yaml` exists but is not safely ignored by `.gitignore`
- `.rocketclaw/config.local.example.yaml` is missing or outdated

If no project issues exist, report:

```text
RocketClaw setup complete

Project config: healthy
Optional capabilities: see diagnostic report above

Run /ce-setup anytime to re-check.
```

If optional tools are missing, do not offer a bulk install. The diagnostic already printed the relevant install command or project URL. Say: "Install optional tools only for the workflows you use."

## Phase 2: Fix Workspace-Local Issues

Resolve the workspace root with `jj workspace root`. All paths below are relative to the workspace root, not the current working directory.

### Step 4: Remove Obsolete Local Config

If `rocketclaw.local.md` exists at the workspace root, explain that it is obsolete because review-agent selection is automatic and surviving machine-local settings now live in `.rocketclaw/config.local.yaml`.

Ask whether to delete it now. Delete only if the user approves.

### Step 5: Refresh Example Config

Copy `references/config-template.yaml` to `<workspace-root>/.rocketclaw/config.local.example.yaml`, creating the directory if needed. This file is versioned in the repository and should always reflect the latest available settings.

If the bundled template cannot be located by the current platform, print the source template path that failed and tell the user the example config could not be refreshed automatically.

### Step 6: Create Local Config If Wanted

If `.rocketclaw/config.local.yaml` does not exist, ask:

```text
Set up a local config file for this project?
This saves optional RocketClaw preferences such as output formats, product pulse settings, and Codex delegation defaults.
Everything starts commented out -- you only enable what you need.

1. Yes, create it
2. No thanks
```

If the user approves, copy `references/config-template.yaml` to `<workspace-root>/.rocketclaw/config.local.yaml`.

### Step 7: Ensure Local Config Is Ignored

If `.rocketclaw/config.local.yaml` exists and is not covered by `.gitignore`, offer to add:

```text
.rocketclaw/*.local.yaml
```

Append the entry to the workspace-root `.gitignore` only if the user approves. Do not overwrite unrelated `.gitignore` content.

## Phase 3: Summary

Display a brief summary:

```text
RocketClaw setup complete

Fixed:     <workspace-local fixes applied, or none>
Skipped:   <workspace-local fixes declined, or none>
Optional:  <missing optional tools, or all available>

Run /ce-setup anytime to re-check.
```
