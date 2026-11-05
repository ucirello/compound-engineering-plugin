---
name: ce-setup
description: "Check RocketClaw health and repo-local config, scaffold a Compound Pack with `pack:<id>`, or draft or refresh coding standards and review docs with `standards`."
argument-hint: "[pack:<id> | standards]"
disable-model-invocation: true
---

# RocketClaw Setup

## Interaction Method

Ask each question below using the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to a numbered list on the host's user-visible chat surface only when no such tool is in the list or a real question call errors. Never silently skip or auto-configure.

Read `references/communication.md` from this skill's directory before your first offer. It says what each offer, question, and preview must tell the user.

## Pack Scaffold

When the invocation names a Compound Pack to add, create, or scaffold (the `pack:<id>` argument, or the same request in words), read `references/pack-scaffold.md` from this skill's directory and follow it in place of Phases 1-2: it writes the pack and its config entry only after the user approves, runs the health check itself, and reports into Phase 3 (Summary).

## Review Docs

When the invocation asks to draft, refresh, or update coding standards or review docs (the `standards` argument, or the same request in words), read `references/project-docs.md` and follow it in place of Phases 1-2, drafting the whole set of files even when the request names one. Report into Phase 3.

## Artifact Root Resolution

Every RocketClaw skill that reads or writes an artifact tree (`solutions`, `plans`, and others) resolves its root by this rule. Step 2 reports the resolved root.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/` or `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Required OpenCode installation prerequisite

Before declaring setup complete, tell the user to merge `"experimental": { "subagent_depth": 3 }` into `~/.config/opencode/opencode.json`. Use `opencode debug paths` or `opencode debug paths config` to locate the actual global configuration directory and update its existing `opencode.json` or `opencode.jsonc` instead when applicable. Preserve JSONC comments, unrelated settings, sibling experimental fields, and any existing integer depth higher than 3. Never replace the whole file or create a competing JSON/JSONC file. Obtain approval before applying a user-owned configuration edit.

Depth at least 3 is required for deep agentic delegation. Installing the plugin or shipping package-local `opencode.json` alone does not enable it in the consuming project. Inspect effective configuration precedence: no higher-precedence configuration may lower depth below 3. Report a missing or overridden prerequisite rather than declaring setup complete.

## Native model routing

For repository-scoped GitHub operations, run from the target workspace's absolute root and obtain `GIT_DIR=$(jj git root)` there, exporting it or prefixing `gh` with it. This is not permission to invoke Git directly. Keep all run scratch, including fallback/error paths, under that workspace's `.tmp/`; ensure `.tmp/` is covered by its `.gitignore` through the existing approval flow. JJ command reference: https://docs.jj-vcs.dev/latest/cli-reference/.

Configuration remains authoritative for desired models, tiers, effort and provider routes. Resolve these with `opencode.models`, then execute permitted work through native subagents and shell, never another harness's dispatcher. Delegation permission, model-override permission, and remaining nesting capacity are separate checks. Under a user-or-loaded-skill permission rule, an explicit skill reviewer request suffices; unconditional prohibitions still apply. If model overrides require an explicit user request, omit the optional model argument and use suitable inherited-model reviewers, disclosing unmet configured intent. Same-model reviewers do not establish cross-model independence. Classify actual dispatch errors as permission, unavailable tool, model rejection, or depth/capacity; never evade them through another harness. Preserve receipts and report required unsatisfied independent coverage as incomplete.

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

If the script is unavailable, run the inline equivalent listed in `references/repo-fixes.md`.

Display the diagnostic output to the user. The health report includes the resolved artifact root and which config layer supplied it (per Artifact Root Resolution above); show that line so the operator can confirm where artifacts will be written. Missing `config.yaml` is a reported absence, not a project issue.

### Step 3: Decide Whether Fixes Are Needed

Repo-local fixes the health report names apply only to the checkout that report diagnosed. If Phase 2 will write to a different writable checkout, diagnose that checkout first. Session-level findings such as plugin version and optional tools still come from this session's Phase 1.

After the health report, decide Phase 2 from writable-checkout availability:

- If this session has a writable JJ workspace, run Phase 2 locally, including when `project_issues` is 0. Phase 2 always refreshes the example and always offers to create `config.yaml` when that file is missing.
- If this session has no writable checkout, but the user named a repository and the harness exposes a remote repo-work surface with a writable checkout, run Phase 2 on that surface instead and report the remote repo-local fixes in Phase 3.
- Otherwise skip Phase 2 and go to Phase 3, saying repo-local writes were skipped because no writable checkout is available.

One offer concerns this machine rather than the checkout, so it stands whether or not Phase 2 runs: if the report names a legacy Compound Codex tool map, offer to remove it following `references/legacy-codex-tool-map.md` from this skill's directory. Preserve the optional cache-maintenance procedure in `references/acpx-cache-warm.md` for users explicitly requesting legacy transport cache warming; it is not a native model route or installation prerequisite. Never dispatch peers through that transport.

Phase 2 remediates every project issue the report names, each in its own step of `references/repo-fixes.md`. That includes a `ce-work` implementation engine the report marks unavailable or invalid, retired scalar routing keys, and malformed dormant `work_engine_preferences` or `work_engine_effort`.

If optional tools are missing, do not offer a bulk install. The diagnostic already printed the relevant install command or project URL. Say: "Install optional tools only for the workflows you use."

## Phase 2: Fix Repo-Local Issues

Read `references/repo-fixes.md` from this skill's directory before making any repo-local change. It carries Steps 4-10: removing the obsolete `rocketclaw.local.md`, refreshing the example config, offering to create `config.yaml`, repairing invalid `work_engine_preferences` and `docs_root`, the two `.gitignore` offers, and the agent-instructions offers (a knowledge-store mention, the compounding directive, and the chat-register directive for `ce-noslop`), and the offer to draft the project's review docs.

Every change to a user-owned file is offered and applied only if the user approves.

## Phase 3: Summary

**User-runnable invocation rendering.** In setup summaries, default to `/ce-setup` and `/ce-help`; use `$ce-setup` and `$ce-help` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. On oh-my-pi (`omp`), use `/skill:ce-setup` and `/skill:ce-help`. Render only the invocation as inline code and output one form only.

Write the summary that `references/summary.md` describes. End it with these two lines, with the rendered invocations filled in:

```text
Run `<rendered invocation>` anytime to re-check.
Run `<rendered ce-help invocation>` to ask which skill fits or what comes next.
```

When setup left changes uncommitted, close with a question after those lines: commit them and open a pull request, commit only, or leave them for the user to review first. Run `ce-commit-push-pr` or `ce-commit` for the user's choice.
