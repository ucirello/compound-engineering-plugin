---
name: ce-setup
description: "Check RocketClaw health and repo-local config, scaffold a Compound Pack with `pack:<id>`, or draft or refresh coding standards and review docs with `standards`."
argument-hint: "[pack:<id> | standards]"
disable-model-invocation: true
---

# RocketClaw Setup

## Required user-global delegation setup (documentation only)

Before deep delegation, the user must merge `experimental.subagent_depth` of at least `3` into their existing user-global OpenCode configuration, normally `~/.config/opencode/opencode.json`. Discover the actual config directory with `opencode debug paths` / `opencode debug paths config`; use its existing `opencode.json` or `opencode.jsonc`, never create a competing file. Preserve comments, unrelated fields, experimental siblings, and any higher integer. Merge this field, not a replacement document:

```json
{"experimental": {"subagent_depth": 3}}
```

Plugin installation and package-local shipped config alone do not enable this prerequisite. Check effective configuration through supported discovery and ensure higher-precedence configuration does not lower it. Document the required user action; never modify the host configuration during setup.

## Native model routing

`config.yaml`, `config.local.yaml`, and the example remain authoritative for model routes, tiers, pins, ordering, and effort intent. Discover exact available models with `opencode.models`, then use native subagents and shell, not other-harness dispatchers. Provider/harness names in compatibility examples express intent, not permission to launch those harnesses. Explicit reviewer dispatch in an applicable skill authorizes delegation under user-OR-skill policy; merely loading another skill does not. Respect unconditional prohibitions and tool denial. If optional model overrides are forbidden absent a user model request, omit the model argument, use an inherited suitable model, and disclose the unmet tier. Same-model review is not cross-model independence; unavailable required cross-model coverage remains incomplete. Inspect effective nesting configuration separately from permission; classify actual failures as depth/capacity, permission, model rejection, or missing tool. Inline/parent fallback is allowed only by the review contract, never to evade denial or claim missing independent coverage.

All JJ commands run with cwd set to the verified absolute target workspace root (shell: `(cd "$workspace_root" && jj ...)`). Discover that root by walking ancestors for `.jj` before calling `jj root` there. Repository `gh` operations must run there with `GIT_DIR=$(jj git root)`. Read history with `jj log` including full descriptions and task-verified anchors. No direct Git executable or Git fallback.

## Interaction Method

Ask each question below using the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to a numbered list on the host's user-visible chat surface only when no such tool is in the list or a real question call errors. Never silently skip or auto-configure.

`ce-setup` is a lightweight health check and repo-local config helper. It does **not** bulk-install every optional dependency. Missing tools are reported as optional capabilities so the user can install only the workflows they use.

## Pack Scaffold

When the invocation names a Compound Pack to add, create, or scaffold (the `pack:<id>` argument, or the same request in words), read `references/pack-scaffold.md` from this skill's directory and follow it in place of Phases 1-2 (Diagnose and Fix Repo-Local Issues): it writes the pack and its config entry only after the user approves, runs the health check itself, and reports into Phase 3 (Summary).

## Review Docs

When the invocation asks to draft, refresh, or update coding standards or review docs (the `standards` argument, or the same request in words), read `references/project-docs.md` and follow it in place of Phases 1-2, drafting the whole set of files even when the request names one. Report into Phase 3.

## Artifact Root Resolution

Every RocketClaw skill that writes or reads an artifact directory (`solutions`, `plans`, `ideation`, and the other RocketClaw-owned trees) resolves its root through the rule below. `ce-setup` carries the canonical statement and reports the resolved root so an operator can confirm where artifacts land before running other skills.

<!-- ce-docs-root:start -->
**Resolve the RocketClaw artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` = `jj root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Phase 1: Diagnose

### Step 1: Determine Plugin Version

Detect the installed rocketclaw plugin version by reading the plugin metadata or manifest when the platform exposes it. If the version cannot be determined, skip this step.

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

If the script is unavailable, run the inline equivalent listed in `references/repo-fixes.md`.

Display the diagnostic output to the user. Missing optional tools are not setup failures. The health report includes the resolved artifact root and which config layer supplied it (per Artifact Root Resolution above); show that line so the operator can confirm where RocketClaw artifacts will be written. Missing `config.yaml` is a reported absence, not a project issue.

### Step 3: Decide Whether Fixes Are Needed

Repo-local fixes the health report names apply only to the checkout that report diagnosed. If Phase 2 will write to a different writable checkout, diagnose that checkout first. Session-level findings such as plugin version and optional tools still come from this session's Phase 1.

After the health report, decide Phase 2 from writable-checkout availability:

- If this session has a writable JJ workspace, run Phase 2 locally, including when `project_issues` is 0. Phase 2 always refreshes the example and always offers to create `config.yaml` when that file is missing.
- If this session has no writable checkout, but the user named a repository and the harness exposes a remote repo-work surface with a writable checkout, run Phase 2 on that surface instead and report the remote repo-local fixes in Phase 3.
- Otherwise skip Phase 2 and go to Phase 3, saying repo-local writes were skipped because no writable checkout is available.

Two offers concern this machine rather than the checkout, so they stand whether or not Phase 2 runs. If the report names a legacy Compound Codex tool map, offer to remove it following `references/legacy-codex-tool-map.md` from this skill's directory. If the bundled health script reported the `node` row available, offer to warm the optional legacy adapter cache (not native model dispatch) following `references/acpx-cache-warm.md`.

Phase 2 remediates every project issue the report names, each in its own step of `references/repo-fixes.md`. That includes a `ce-work` implementation engine the report marks unavailable or invalid, retired scalar routing keys, and malformed dormant `work_engine_preferences` or `work_engine_effort`.

If optional tools are missing, do not offer a bulk install. The diagnostic already printed the relevant install command or project URL. Say: "Install optional tools only for the workflows you use."

## Phase 2: Fix Repo-Local Issues

Read `references/repo-fixes.md` from this skill's directory before making any repo-local change. It carries Steps 4-10: removing the obsolete `rocketclaw.local.md`, refreshing the example config, offering to create `config.yaml`, repairing invalid `work_engine_preferences` and `docs_root`, the two `.gitignore` offers, and the agent-instructions offers (a knowledge-store mention, the compounding directive, and the chat-register directive for `ce-noslop`), and the offer to draft the project's review docs.

Every change to a user-owned file is offered and applied only if the user approves.

## Phase 3: Summary

**User-runnable invocation rendering.** In setup summaries, default to `/ce-setup`; use `$ce-setup` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. On oh-my-pi (`omp`), use `/skill:ce-setup`. Render only the invocation as inline code and output one form only.

Display a brief summary:

```text
✅ RocketClaw setup complete

Fixed:     <fixes applied, or none>
Skipped:   <fixes declined, or none>
Optional:  <missing optional tools, or all available>

Run `<rendered invocation>` anytime to re-check.
```
