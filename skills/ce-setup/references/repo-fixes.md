# Workspace-local fixes (Phase 2) and the summary (Phase 3)

## Inline health-check equivalent (Step 2 fallback)

When the bundled `scripts/check-health` is unavailable, perform these checks by hand and report the same findings:

1. Check optional tools with `command -v`: `agent-browser`, `gh`, `jq`, `ast-grep`, `ffmpeg`.
2. If inside a Jujutsu workspace, resolve the workspace root with `jj root`.
3. Check for obsolete `rocketclaw.local.md` at the workspace root.
4. Check whether `.rocketclaw/config.yaml` exists.
5. Check whether `.rocketclaw/config.local.yaml` exists and, if it does, whether Jujutsu excludes it from `jj file list` under the workspace's `.gitignore` rules.
6. Compare `.rocketclaw/config.example.yaml` with `references/config-template.yaml` when the template is readable; otherwise report that the example refresh must be done manually.

This file is read at two points: from Step 2 whenever the bundled health script is unavailable, for the inline equivalent above; and before any Phase 2 write, once Step 3 has decided that a writable workspace exists and which reported issues need remediation. Ask with the blocking question tool named in SKILL.md. Maintaining the generated example files is the work this phase does on its own — Step 5's refresh and its removal of the superseded `config.local.example.yaml`. Every change to a user-owned file is offered and applied only if the user approves.

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
