# Committing and pushing

If stack construction already committed its layers, continue to Step 4; Step 5 pushes and submits them. For work based on the default bookmark, first follow `references/branch-creation.md` so stale base and unpushed local work are resolved safely.

Scan changed files for naturally distinct concerns. When clearly separate, use two or three file-level groups; otherwise one commit is fine. Do not force a hunk split. Honor `exclude:<paths>`: excluded and unrelated files stay in the working-copy change and out of every published ancestor. Report what was left out. JJ automatically snapshots files, so selection means explicit commit filesets, not staging.

Read https://go.dev/wiki/CommitMessage before composing or validating each message.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Here `git log` means history inspected using `jj log`; never execute Git. Runtime project instructions and visible history syntax override Go guidance. Preserve relevant issue/PR references. When a plan Implementation Unit ID is already in hand for this group, include it in the message using project conventions; omit it when unclear, spanning units, or unavailable. Do not hunt for a plan.

From the absolute workspace root, commit each group with literal, verified filesets. Use `file:"<literal-path>"` for each selected file, retaining the inner fileset quotes and escaping their contents according to JJ string-literal syntax; argv or shell quoting alone does not escape fileset operators or wildcards.

```bash
jj commit -m "<message composed from the standards above>" -- <selected-files>
```

Inspect `jj show -r @-` and `jj diff` after each group: selected content must be in the completed change, remaining content in `@`. Never omit the path list while unrelated files remain. Resolve conflicts before publishing. Verify the entire outgoing range, not just the last change, excludes user work.

Apply the **Project publishing gate** to the exact outgoing state. Re-resolve the feature bookmark and its head: after commit the publishable change is normally `@-`, even when `@` contains excluded work. Create a missing bookmark or move the existing intended bookmark to that verified revision; never move the default or an unrelated bookmark. Do not silently rewrite published history or use a backwards move to bypass a mismatch.

```bash
jj bookmark create <branch> -r <publishable-head>
```

For an existing intended bookmark use `jj bookmark set <branch> -r <publishable-head>`. Then push only that bookmark to the confirmed head remote:

```bash
jj git push --remote <head-remote> --bookmark <branch>
```

Use `--allow-new` only when creating the verified remote bookmark for the first time and the installed help requires it. If all selected work is already committed and pushed, this step is a no-op.
