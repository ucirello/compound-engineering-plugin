# `gh stack` Semantics This Skill Relies On

Run `gh stack version` and the applicable `gh stack <command> --help` at runtime. Live help is authoritative because this extension changes independently. This file carries only decision-relevant semantics and does not require another skill.

`gh stack` operates on GitHub PRs and exported Git branch names. Jujutsu remains the owner of local changes, parentage, bookmarks, and Git transport. Stack mode therefore requires a colocated repository whose Jujutsu bookmarks are visible to the extension; stop when that condition is not proven.

## Classifying a Parent

```bash
gh stack checkout "<parent-pr-number>"
```

Resolve a parent by PR number whenever one exists because that can pull manager state from GitHub. A bare name can classify local manager state only. Branch on the exit code rather than parsing status text. Because checkout can move the colocated working copy, record the current Jujutsu change ID first and restore it with `jj edit <change>` after classification.

The installed extension's live help and exit behavior decide success, standalone, invalid-argument, ambiguity, and repository-unavailable states. Any state that does not prove the named parent and topology is a residual, not permission to guess.

```bash
gh stack view --json
```

Use its runtime JSON schema to identify trunk, current exported name, managed names, PR URLs, draft state, and rebase need. Do not infer undocumented ordering or fields. Verify topology against Jujutsu parentage before submission.

## Resolving a PR Head

`gh pr view "<n>" --json headRefName,headRefOid,headRepository,headRepositoryOwner,author` identifies the head. Match an existing Jujutsu Git remote to that repository, or add a distinct remote with `jj git remote add` when the head repository is not represented. Fetch the named head through `jj git fetch --remote <remote> --branch <headRefName>`, verify the fetched commit against `headRefOid`, and create a Jujutsu bookmark there only when no safe bookmark exists. Never move an existing bookmark that targets different work merely to make its name match GitHub.

## Building and Submitting

Inspect live help before using either command:

```bash
gh stack init --base "<trunk>" "<bottom-bookmark>" "<next-bookmark>"
gh stack submit --auto --open
```

Pass the complete exported bookmark chain to `init` bottom-to-top. Existing exported names are adopted. Do not let the extension create missing names: construct and export the Jujutsu bookmark chain first. `--base` keeps an external parent as trunk rather than adopting it as a managed layer.

Use `--auto` only when current help confirms it suppresses title prompts. Use `--open` only when current help confirms it creates ready PRs and the user authorized every affected draft to become ready. Otherwise preserve existing draft state.

Do not use `gh stack add` to construct Jujutsu changes, `gh stack link` as a substitute for local manager state, or `gh pr merge` to land a managed member. Stack landing remains `gh stack merge`, owned by `ce-babysit-pr` under `posture:stack-land` or by the user.
