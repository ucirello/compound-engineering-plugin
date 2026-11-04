# Native execution and change descriptions

Use OpenCode-native subagents and shell tools, not another harness's dispatcher. Configuration and the spec remain authoritative for routes, capability tiers, concurrency, costs and security intent. Discover concrete models with `opencode.models` only when model selection is permitted. Delegation permission, optional model overrides and remaining nesting depth are distinct: this skill explicitly requests its research, experiment and independent judge subagents where the host allows user-or-skill-requested delegation. An unconditional prohibition still wins. If model overrides require an explicit user request, omit the model argument and use an adequate inherited model; disclose unmet fixed routes or different-model requirements. Separate same-model contexts provide reviewer independence, not cross-model coverage. Classify actual permission, missing-tool, model-argument, depth and transient active-capacity errors separately. Never evade a denial or depth limit through another harness; queue only transient capacity failures. Judges cannot fall back to inline self-scoring. Preserve result receipts, pending waits, bounded recovery and all measurement gates.

Run every JJ command with its cwd set to the target workspace's absolute root; shell examples use `(cd "$workspace_root" && jj ...)`. Obtain roots through `jj workspace root`. Repository-scoped GitHub calls run there with `GIT_DIR=$(jj git root)`. Do not execute Git directly. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-command-table/ .

## Experiment isolation (replaces the workspace bridge)

Throughout the existing measurement/ledger vocabulary, “branch” means a JJ bookmark, “worktree” means an isolated JJ workspace, and a commit/SHA is an immutable JJ commit ID. Create, archive and move bookmarks with `jj bookmark create/set`; resume only at the verified recorded head in an owned clean workspace. Fetch exact remote refs through `jj git fetch`, read files with `jj file show -r <verified-id> <path>`, and verify remote parent IDs and mutable-only ranges with `jj log` and `jj diff --from <base_sha> --to <head_sha>`. Do not substitute a per-commit diff or a style-history sample for that captured range. Push only the explicitly authorized result bookmark through `jj git push --bookmark <result_ref>` to the verified remote.

For winning integration, freeze/describe the candidate and record its commit ID; create a JJ merge change with the verified optimization head and candidate as parents (`jj new <optimization-head> <candidate-id>`), resolve conflicts without expanding scope, describe it under the standards below, and move the optimization bookmark only after success. For a file-disjoint runner-up, duplicate the candidate with `jj duplicate <candidate-id>`, identify the new owned change, and rebase only that duplicate with `jj rebase -r <duplicate-id> -d <new-baseline>`. Measure that combined state afresh before keeping it. Rejection abandons only this run-owned integration change and leaves the optimization bookmark at the previous verified head; preserve the original candidate and recovery references until evidence is secured. Every cleanup mention in the loop is subject to the removal safeguards below.

Detect existing harness isolation first and respect its ownership/lifecycle. Reuse verified existing isolation without renaming, recreating or altering it merely to impose new naming or colocation. For fresh work use the harness's supported colocated JJ capability when available, requesting the required name; unsupported naming/colocation is a compatibility blocker, not permission to bypass ownership.

Resolve the exact optimization bookmark to one commit ID and record it as `base_sha` before dispatch. Capture local `YYYYMMDD` once. Derive a meaningful kebab-case slug from the spec and experiment index; normalize caller names without double-prefixing. Persist one identity such as `20261104-optimize-parser-exp-001` for both the workspace name and destination basename under the source workspace's absolute `.tmp/optimize/` directory. Check both `jj workspace list` registrations and destination existence; select `-2`, `-3`, etc. on collision without overwriting. Persist the selected identity, absolute root and base in the ledger before creation, preserving them across retries, resumes and midnight. Existing registered state is reused only after verifying ownership, path, revision and pending work; never reset or clean it.

From the source workspace's absolute root create with `(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$base_sha" "$absolute_destination")`. From the new absolute root verify `jj git colocation status`, registration and the intended base (an empty `@` above the base is expected). Adopt that directory through the harness session/workspace mechanism before executing there. Copy configured shared resources only after validating source/destination containment and symlinks; retain relative paths, never overwrite unknown files. Preserve configured port parameterization. Count registered experiment workspaces for the existing budget and approval evidence instead of calling a bridge script.

Before retiring any experiment, stop its workers, preserve required result markers and receipts outside its directory and read them back, retain recovery/best/archive bookmarks, and prove integration for kept candidates. Inspect tracked changes, conflicts and ignored/untracked files; snapshots do not protect ignored or untracked content. Verify exact registration, absolute path, run ownership and cleanup authorization. Completion alone does not authorize removal. Leave the target and migrate any active harness session to a surviving workspace. From that surviving absolute root run `jj workspace remove <verified-workspace-name>` only for authorized disposable run-owned state. Verify deregistration AND directory disappearance; warnings or partial deletion are blockers. Never force-delete or fall back to Git cleanup. Bookmark deletion is separate and must preserve needed recovery references. Use `jj workspace forget` only for explicitly unregistering while retaining files. Still-referenced or ambiguously owned workspaces remain intact.

## Description composition (all candidate, marker and report changes)

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full guide and resolve the relevant history head from the actual task. From the target workspace's absolute root examine several recent subjects AND bodies, for example `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Compare package/prefix syntax, casing, tense, subject/body separation, wrapping and issue placement. Project/user instructions and repository-local syntax always win; apply compatible Go guidance for clarity and structure. With no history, use explicit instructions and Go guidance without inventing precedent. Describe the hypothesis, experiment and scope, or marker/report purpose as applicable, without a fixed prefix or template. Use `jj describe -m "<message composed from the standards above>"` on the intended owned change; freeze candidates before integration and move the optimization bookmark only after validated integration. Use JJ rebase/cherry-pick equivalents on separate owned candidate changes; abandon only the run-owned rejected integration change, never unrelated work.

Go source guidance, illustrative rather than a mandatory repository template:

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
