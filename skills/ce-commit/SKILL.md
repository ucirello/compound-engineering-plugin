---
name: ce-commit
description: Use when the user asks to save current work by describing a Jujutsu change or to improve the description of the working-copy change.
---

# Jujutsu Change Description

Describe the current working-copy change accurately and leave its contents and topology unchanged.

## Context

Run each command as its own shell tool call. Do not join commands with shell operators, pipes, substitutions, or redirects. Interpret a non-zero exit directly.

| Command | Purpose | Non-zero exit / empty result |
| --- | --- | --- |
| `jj root` | Confirm the workspace and obtain its root | Not a Jujutsu workspace; report and stop |
| `jj status` | Inspect `@`, its parent, conflicts, and changed paths | Context unavailable; report and stop |
| `jj diff -r @` | Read the complete content change being described | Context unavailable; report and stop |
| `jj log -r '::@' -n 10` | Observe recent description syntax and wording | No useful history; rely on active repo-local instructions and compatible clarity guidance |
| `jj log -r @ --no-graph` | Read the current change ID and description | Current change unavailable; report and stop |

These commands may snapshot the working copy. They do not create a separate staging selection. Treat their output as one context snapshot, then rerun `jj status` and `jj diff -r @` immediately before changing the description.

## Workflow

### 1. Inspect the change

Gather the context above. Include every path and hunk in `@` when determining its intent. Do not infer a partial selection or silently exclude unrelated-looking files.

If `@` has no content change, report that there is nothing to describe and stop. If conflicts prevent an accurate description, report the conflicts and stop. If the content has no truthful unifying intent, ask the user to separate the concerns; do not split, squash, create, abandon, rebase, or otherwise alter changes in this workflow.

Do not create or move bookmarks. Work in the normal Jujutsu state without assumptions about a current bookmark.

### 2. Compose, apply, and validate the description

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repo-local active instructions and the syntax observed in history always win. Apply only compatible Go clarity and structure guidance: make the first line concise and action-oriented, avoid a trailing period, and add a separated body when future readers need the motivation, constraints, trade-offs, or issue context. Do not impose a prefix, category, scope, or other format that the repository does not already use. Do not add branding, generated-by text, authorship, co-authorship, or sign-off attribution.

Describe only the content currently in `@`. Preserve issue references and semantic details required by the active instructions or history. Use this neutral command form:

```bash
jj describe -m "<message composed from the standards above>"
```

Pass the complete multiline value as the single `-m` argument. Do not use a global temporary directory. If the harness cannot safely pass that argument directly, use only the workspace-local `.tmp/rocketclaw/ce-commit/` fallback after confirming `.tmp` is ignored; otherwise stop rather than create tracked scratch content.

After `jj describe` succeeds, run `jj status`, `jj diff -r @`, and `jj log -r @ --no-graph` as separate calls. Confirm that the content and topology are unchanged and that the displayed description exactly matches the composed value. If concurrent edits changed `@`, stop and report that the description must be reconsidered against the new content.

### 3. Report

Report the change ID and final first line. State that only the description changed. If any required confirmation failed, report the blocker instead of claiming success.
