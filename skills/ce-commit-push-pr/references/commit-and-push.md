# Committing and pushing

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Use `context.md`'s absolute workspace cwd and scoped GitHub environment. If `stack-submit.md` already committed layers, skip ordinary single-bookmark publication; Step 5 submits them. On the default bookmark follow `branch-creation.md` first.

Scan for naturally distinct concerns: at most 2–3 logical changes, whole-file groups only; ambiguity permits one change. Inspect tracked/untracked changes, track only intended new paths with `jj file track <paths>`, and commit only explicitly reviewed owned paths. Honor `exclude:<paths>`: never move or commit them; preserve and report them. Do not broadly track or commit the workspace. Stop on conflicts.

Before composing each message, read and follow `commit-message-standards.md` in full. Include a known plan Implementation Unit ID as semantic context in the observed repository style; do not impose suffix syntax or hunt for plans. Omit unclear/multi-unit IDs.

Add changes above others' commits without rewriting away authors or existing human trailers. For carried work that will not otherwise land under its author's name, preserve exact human credit in the body or required project convention; never invent emails. Do not add model/harness attribution or new Co-authored-by/Assisted-by message trailers. Preserve existing human trailers on commits you did not author.

```bash
jj commit -m "<message composed from the standards above>" -- <owned-paths>
```

Read back the full description and diff; verify excluded/unrelated work remains. Resolve the actual resulting head, not the new empty `@`. Set/create only the intended feature bookmark there with `jj bookmark set <head-bookmark> -r <verified-head>`.

Apply the **Project publishing gate** to the exact outgoing state. Immediately before push verify target, repository, remote, tracking state, PR and authority:

```bash
jj git push --remote <verified-head-remote> --bookmark <head-bookmark>
```

For new remote bookmarks use `--allow-new` only when creation is authorized. Re-read remote bookmark and PR head and verify exact commit agreement after push. Clean state with all intended commits already published is a no-op. Never force a guessed target or discard unrelated work.
