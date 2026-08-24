---
name: ce-test-xcode
description: "Test iOS apps in a simulator with XcodeBuildMCP. Use when iOS changes need simulator evidence before handoff."
argument-hint: "[scheme name or 'current' to use default]"
disable-model-invocation: true
---

# Xcode Simulator Test

Build and exercise an iOS app on a simulator, preserving screenshots, logs, human-verification results, and failures as evidence for the user.

Use Jujutsu for local version-control state. Resolve the workspace with `jj workspace root`, treat `@` as the working-copy change, and inspect it with `jj status` and `jj diff`; Jujutsu snapshots non-ignored working-copy files and has no staged/unstaged split. Derive the changed iOS surface from that state when the user does not name a narrower scope. Keep GitHub and other provider operations on their provider interfaces.

**Runtime prose conventions.** If this skill or a delegated skill composes, edits, recommends, or validates a Jujutsu change description or commit message, use the syntax reported by the installed command's live `--help`, because Jujutsu command syntax can vary by version. Use `jj describe` to name the current working-copy change and `jj commit` only when the requested operation should also create a new change. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The sentence's `git log` wording is not an operational instruction: inspect the project's active instructions and current `jj log` history; their runtime tone, vocabulary, and syntax take precedence. Do not impose a fixed prefix, heading, subject, body, layout, template, or example. Do not add product branding, generated-by text, or creator, model, provider, tool, agent, harness, runtime, workflow, or co-author attribution; operational provider names required to run or explain the test remain facts, not attribution.

**Done:**

- A completed run reports overall `PASS`, `FAIL`, or `PARTIAL` plus project, scheme, simulator, build result, per-surface `PASS` / `FAIL` / `SKIP`, console errors, human checks, and residual failures.
- Per-surface status is derived from evidence, not the user's routing choice. `PASS` requires completed passing evidence. `FAIL` records observed failing evidence until a completed retest replaces it. `SKIP` means the check has no completed outcome.
- The overall result is `FAIL` while any failure remains, `PARTIAL` when no failure remains but a scoped check is skipped, and otherwise `PASS`.
- Any failure before the launched-with-log-capture handoff stops later stages and reports an actionable setup blocker with its evidence.

**Boundaries:** this skill tests and reports. Diagnosis and any user-approved product fix belong to `ce-debug`, invoked with authority narrowed to return here without describing or committing a Jujutsu change, moving or pushing a bookmark, or opening a PR. Preserve all pre-existing working-copy content. Keep simulator interaction within the app and flows the user placed in scope.

## Run

1. **Prepare and launch.** Read `references/setup-and-build.md`. It owns the XcodeBuildMCP availability gate, project and scheme discovery, simulator choice, build, install, launch, and log-capture start.
2. **Exercise and report.** After launch, read `references/test-and-report.md`. It owns per-screen evidence, human-only flows, the SwiftUI inline-link automation limitation, failure routing, cleanup, and the fixed summary fields.

Do not replace either required read with remembered tool names. XcodeBuildMCP adapters differ by host, while their observable success conditions do not.
