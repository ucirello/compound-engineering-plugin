---
name: ce-commit
description: Record local changes with JJ and a clear, repository-appropriate message. Use when the user asks to commit or save selected changes.
---

# Record Local Changes

Create local commits from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow. Use current JJ only; never invoke the Git executable, including for history.

**Done when:** each requested logical change is recorded with an explicit file list and an outcome-oriented message, and those changes no longer appear in the new working-copy change. Unrelated and excluded work must remain intact. **Stop when:** no requested changes remain, or scope, conflicts, or revision identity is ambiguous.

## Context

Resolve and verify the absolute target `workspace_root` from the task. Run every repository command with that directory as its working directory, never `jj -R`. Examples use `(cd "$workspace_root" && ...)`. Gather `jj root`, `jj status`, `jj diff --summary`, `jj diff`, `jj log --no-graph -r '@ | @-'`, and `jj bookmark list --all-remotes`. Check untracked files as well as tracked changes; do not use diff alone as a cleanliness check. Treat errors as errors, not empty history.

Capture the exact working-copy revision and requested file list. Resolve a verified history head from the task's actual target/history and these identities, never a hardcoded default branch. Do not replace an exact reviewed range with the style sample. If GitHub metadata is needed, run repository-scoped calls in this absolute workspace with `GIT_DIR=$(jj git root) gh ...`. Store all scratch/message/error files only under the workspace's ignored `.tmp/`.

## Message standards — required at runtime

Read the **full** https://go.dev/wiki/CommitMessage at runtime before composing. Inspect several recent full subjects **and bodies** from the verified relevant history:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Replace the placeholder with the verified history revision. Compare actual prefixes/package names, casing, tense, subject/body separation, wrapping, and issue placement against the guide. Explicit repository/user instructions and actual local conventions always win; Go supplies only compatible quality and structure. With no history, follow explicit instructions plus compatible Go guidance without inventing precedent. If the guide cannot be read, report the blocker rather than claiming the comparison happened.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

### SOURCE GUIDANCE — verbatim Go excerpts, subordinate to observed repository conventions

This example is source guidance, **not** a mandatory repository syntax or template.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

## Workflow

1. **Gather and bound scope.** Inspect the context above. Stop on conflicts. Honor `exclude:<paths>`: those files stay uncommitted and must be reported as excluded. Recheck revision identity and file scope immediately before recording if anything may have changed.

2. **Preserve ancestry and bookmarks.** JJ does not require a branch or staging area. Keep existing ancestry and bookmarks; do not move default/shared bookmarks, invent a default branch, rewrite pre-existing commits, or create a workspace for this commit-only operation.

3. **Compare standards.** Complete the runtime full-guide read and full-message history comparison above. Do not fall back to fixed type/scope syntax or a prescribed subject grammar.

4. **Group logically.** Split clearly distinct concerns into separate commits at file level only (2–3 maximum). If ambiguous, use one commit. Never sweep unrelated files into a group.

5. **Compose.** Communicate the outcome rather than merely listing files, explaining motivation or trade-offs when needed in the locally appropriate form. Preserve traceability to an already-known, unambiguous plan Implementation Unit ID according to local conventions; do not hunt for a plan or invent a placement rule. Omit it for unclear or multi-unit commits. Preserve human/source credit when carrying someone else's work that will not otherwise land under their name, including credited human collaborators. Copy recorded identities exactly; never guess emails, and use body credit when no email is recorded. Repository/user attribution conventions override the quoted Go-specific guidance. Do not add generated-by, model, or harness attribution.

6. **Record named files only.** JJ snapshots without a Git index. Restrict each group with explicit paths. Pass the complete composed message as one literal tool argument, not interpolated shell source. The neutral placeholder stands for that complete message:

   ```bash
   (cd "$workspace_root" && jj commit -m "<message composed from the standards above>" -- file1 file2 file3)
   ```

   When every change in `@` is authorized, describing it and opening a new working-copy change is also valid:

   ```bash
   (cd "$workspace_root" && jj describe -m "<message composed from the standards above>")
   (cd "$workspace_root" && jj new)
   ```

   Never use the whole-change alternative when exclusions or unrelated work exist. If a message file is needed for literal handling, write it under the absolute workspace's `.tmp/`, not OS temporary storage.

7. **Confirm.** Run `jj status` and inspect the recorded revisions' full descriptions and file summaries using `jj log` and `jj show`. Verify every requested file landed in its intended commit and excluded/unrelated work remains. Report commit/change IDs, subjects, exclusions, and remaining changes. Do not push.

JJ references: https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/ .
