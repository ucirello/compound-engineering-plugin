---
name: ce-commit-push-pr
description: Describe changes, push a bookmark, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# Jujutsu Change, Push, and PR

**Asking the user:** use the available blocking question interface. Fall back to chat only when no blocking interface exists or the call errors. Never silently skip a question.

## Mode

- **Description-only** - compose and print a description. Apply only when asked.
- **Description update** - update an existing PR without change or push intent. An exit-0 `[]` means no PR; non-zero means unknown and must be resolved before continuing.
- **Full workflow** - otherwise, run Steps 1-5. Enter Stack mode only from stack intent or standing preference.

**`mode:pipeline`** suppresses every blocking ask. Use conservative defaults: no existing-PR rewrite, keep the current bookmark, stop on an unresolved base, and apply a description-update preview directly because the invocation supplies apply intent. Stack mode uses only supplied intent and scope and passes posture to handoff.

## Stack Mode

Opt in only from explicit intent or standing preference. Never suggest or manufacture a stack from one logical change.

Read `references/stack-submit.md` before Step 3 and follow only probe, topology, and retrospective construction there. Its layer-by-layer Jujutsu flow replaces ordinary Step 3. Step 5 owns submission and handoff. Use `posture:stack-ready` by default and `posture:stack-land` only for explicit land intent, handing off the bottom open non-draft PR.

## Context

**Read `references/context.md` before Step 1.** It owns Jujutsu probes, exit meanings, fork handling, bookmark routing, and PR resolution.

Every probe is its own argv-form call, and output is a snapshot. Re-verify bookmark, remote, and PR state before push or create. Only an exit-0 `[]` against the base repository means no open PR.

## Artifact Root

When archival is enabled, use `<jj-root>/.context/explainers/`, with `<jj-root>` from `jj root`. Configuration is read from `<jj-root>/.rocketclaw/config.yaml`; ordinary layered keys may also use `config.local.yaml` as the composing reference specifies.

## Step 1: Resolve Bookmark And PR State

Follow `references/context.md`. Never push the default bookmark directly. Resolve ambiguous bookmark ancestry or PR ownership by stopping rather than guessing.

## Step 2: Determine Conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax. Derive PR titles independently from project PR conventions and the change outcome.

## Step 3: Describe Changes And Push

**Read `references/commit-and-push.md`.** It owns feature-bookmark creation, file-granularity grouping, exact filesets, Jujutsu descriptions, bookmark movement, and push. Honor `exclude:<paths>` exactly.

## Step 4: Compose The PR Title And Body

**Read `references/pr-description-writing.md` in full**, then `references/compose.md`. They own title/body quality, evidence, teaching, project metadata, preservation, and pre-apply audit. Pass an existing PR URL when rewriting it.

## Step 5: Apply And Report

**Read `references/apply-and-handoff.md`.** It owns routes, preview, archival, workspace-local body files, and babysit handoff.

Immediately before `gh pr create`, repeat the existing-PR check. A match takes the existing path, exit-0 `[]` permits creation, and non-zero blocks.

In interactive full workflow, or pipeline stack submission, the run is not done until `ce-babysit-pr` owns follow-on unless a documented skip applies. No ad-hoc watcher substitutes.
