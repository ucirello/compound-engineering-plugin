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

Every RocketClaw skill that writes or reads an artifact directory (`solutions`, `plans`, `ideation`, and the other CE-owned trees) resolves its root through the rule below. `ce-setup` carries the canonical statement and reports the resolved root so an operator can confirm where artifacts land before running other skills.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml`; first non-empty value wins (`<workspace-root>` = `jj workspace root`). Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
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

Run the bundled check script. Set `SKILL_DIR` to the absolute directory you loaded this `ce-setup` SKILL.md from — the Bash tool's CWD is the user's project, not the skill dir, so a bare `scripts/` path will not resolve:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
if [ -f "$SKILL_DIR/scripts/check-health" ]; then bash "$SKILL_DIR/scripts/check-health" --version VERSION; else echo "Bundled health script not found at $SKILL_DIR/scripts/check-health; run the inline checks from ce-setup instead."; fi
```

Use the same command without `--version VERSION` if Step 1 could not determine a version.

If the script is unavailable, perform the inline equivalent:

1. Check optional tools with `command -v`: `agent-browser`, `gh`, `jq`, `ast-grep`, `ffmpeg`.
2. If inside a JJ workspace, resolve the workspace root with `jj workspace root`.
3. Look under workspace-local hidden tool directories for a legacy Markdown config whose YAML frontmatter contains `review_agents` or `plan_review_agents`. Do not assume or print a provider-specific legacy path when none is discovered.
4. Check whether `.rocketclaw/config.local.yaml` exists and, if it does, whether `jj file list .rocketclaw/config.local.yaml` omits it as ignored.
5. Compare `.rocketclaw/config.local.example.yaml` with `references/config-template.yaml` when the template is readable; otherwise report that the example refresh must be done manually.

Display the diagnostic output to the user. Missing optional tools are not setup failures. The health report includes the resolved artifact root and which config layer supplied it (per Artifact Root Resolution above); surface that line so the operator can confirm where artifacts will be written.

### Step 3: Decide Whether Fixes Are Needed

**User-runnable invocation rendering.** In setup summaries, default to `/ce-setup`; use `$ce-setup` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

Proceed to Phase 2 only if one or more workspace-local project issues exist:

- a legacy Markdown config was discovered and has not yet been preserved under `.rocketclaw`
- `.rocketclaw/config.local.yaml` exists but is not safely ignored by JJ
- `.rocketclaw/config.local.example.yaml` is missing or outdated
- the health report marks the `ce-work` skill implementation engine unavailable or invalid, detects retired scalar routing keys, or reports malformed dormant `work_engine_preferences`
- the health report marks `docs_root` invalid (`Invalid docs_root ...`) — artifacts will not be written until it is fixed

If no project issues exist, report:

```text
✅ RocketClaw setup complete

Project config: ✅
Optional capabilities: see diagnostic report above

Run `<rendered invocation>` anytime to re-check.
```

If optional tools are missing, do not offer a bulk install. The diagnostic already printed the relevant install command or project URL. Say: "Install optional tools only for the workflows you use."

## Phase 2: Fix Workspace-Local Issues

Resolve the workspace root with `jj workspace root`. All paths below are relative to the workspace root, not the current working directory.

### Step 4: Preserve Legacy Local Config

If an unpreserved workspace-local Markdown config was discovered by its `review_agents` or `plan_review_agents` frontmatter, explain that review-agent selection is now automatic and current machine-local settings live in `.rocketclaw/config.local.yaml`. Treat an identical existing `.rocketclaw/legacy-config*.local.md` copy as already migrated.

Before creating a blank current config, offer to copy the discovered file byte-for-byte to `<workspace-root>/.rocketclaw/legacy-config.local.md`. Create `.rocketclaw` if needed. Never overwrite either file: if that destination already exists with different content, preserve both by choosing an unused numbered `legacy-config-<n>.local.md` destination. Report both source and destination paths, but do not delete, truncate, or rewrite the source. If the user declines or the copy fails, leave the discovered config untouched and record migration as skipped.

### Step 5: Refresh Example Config

Copy `references/config-template.yaml` to `<workspace-root>/.rocketclaw/config.local.example.yaml`, creating the directory if needed. This file belongs in the working-copy changes and should always reflect the latest available settings.

If the bundled template cannot be located by the current platform, print the source template path that failed and tell the user the example config could not be refreshed automatically.

### Step 6: Create Local Config If Wanted

If `.rocketclaw/config.local.yaml` does not exist, first complete or explicitly skip Step 4 for any discovered legacy config, then ask:

```text
Set up a local config file for this project?
This saves optional RocketClaw preferences such as output formats and product pulse settings.
Everything starts commented out -- you only enable what you need.

1. Yes, create it
2. No thanks
```

If the user approves, copy `references/config-template.yaml` to `<workspace-root>/.rocketclaw/config.local.yaml`.

### Step 6a: Repair Invalid ce-work Preferences

When the health report marks the ce-work implementation engine unavailable or invalid, detects retired scalar routing keys, or reports malformed dormant `work_engine_preferences`, do not guess the intended recipients. Explain the exact reported problem, derive a valid ordered `work_engine_preferences` block from the user's stated harness/model order (or remove malformed dormant preferences and use `work_engine_mode: off` when they want native-by-default), remove any retired scalar routing keys, and show the complete replacement block. Edit only those ce-work keys after the user approves the preview; preserve every unrelated local setting. Re-run the health check and require it to report either native or the intended normalized ordered list before setup is complete.

### Step 6b: Repair Invalid `docs_root`

When the health report marks `docs_root` invalid, explain the exact reason it gave (absolute, escapes the workspace, `..` traversal, workspace root, `.jj/`, or a non-directory component) and the consequence: artifacts will not be written until it is fixed, because `docs_root` fails closed rather than silently falling back to `docs`. `docs_root` may live in the tracked `.rocketclaw/config.yaml` or the local `config.local.yaml`, resolved local-first. Offer to either correct the value to a valid workspace-relative directory the user names, or remove the bad `docs_root` key. Note the fallback precisely: removing it falls back to the **next layer** that sets `docs_root` (deleting a bad value in `config.local.yaml` yields to a `docs_root` still set in the tracked `config.yaml`), reaching the default `docs` only when no layer sets it -- so when both layers carry a value, fix or remove it in each layer that contributes a bad one. Edit only those keys after the user approves; preserve every unrelated setting. Re-run the health check and require it to report a resolved artifact root before setup is complete.

### Step 7: Ensure Local Config Is Ignored by JJ

If `.rocketclaw/config.local.yaml` exists and `jj file list .rocketclaw/config.local.yaml` returns it, offer to add this entry to `<workspace-root>/.rocketclaw/.gitignore`:

```text
*.local.yaml
```

If the user approves, append the entry to `.rocketclaw/.gitignore`, creating that file if needed, then run `jj file untrack .rocketclaw/config.local.yaml`. Do not edit the workspace-root `.gitignore` or overwrite unrelated content.

## Phase 3: Summary

Display a brief summary:

```text
✅ RocketClaw setup complete

Fixed:     <workspace-local fixes applied, or none>
Skipped:   <workspace-local fixes declined, or none>
Optional:  <missing optional tools, or all available>

Run `<rendered invocation>` anytime to re-check.
```
