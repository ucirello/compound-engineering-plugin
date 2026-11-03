# Native execution contract

## Repository and descriptions

Resolve the absolute target workspace root with `jj root`. Every JJ operation runs with that absolute target as shell cwd, not merely `-R`. Use only JJ, including transport (`jj git fetch`, `jj git push --bookmark <verified-name>`), history, patch data (`jj diff --git`), and local cache operations; never execute Git. Scope repository GitHub calls as `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Scratch and prompt files live in the target workspace's absolute `.tmp/`, never OS temporary directories. Retain measurement, decision, profiling, and cache helpers.

At EVERY description composition site (candidate, receipt-only result commit, integration, exported report, and wrap-up fixes): Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards. Read the FULL Go guide before composing. Resolve the actual verified history head for the task, then inspect several full subjects and bodies with `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. This history sample is not a replacement for the exact baseline-to-candidate review range. Infer prefix, package, case, tense, body separation, wrapping, and issue conventions from several messages; repository instructions and history syntax win, with compatible Go quality guidance. Without history use project/user instructions plus Go guidance, never invented precedent. Use `jj describe -m "<message composed from the standards above>"`; no fixed optimize prefix is prescribed. Preserve experiment identity and scope in the composed message where appropriate; omit assistant attribution.

The following verbatim Go source guidance and example are illustrative source material, NOT a mandatory repository template. Repository instructions and syntax inferred from verified runtime history take precedence; apply only compatible Go quality guidance. This excerpt does not replace reading the full guide.

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

Create the optimization bookmark at the verified starting revision with `jj bookmark create`; resume only at the recorded verified run head. The empty working-copy revision above a bookmark is not itself the measured base. Record immutable commit IDs for every baseline and candidate. Check clean scope using `jj diff --summary` against the recorded baseline and inspect conflicts with `jj status`; preserve dirty or unrelated work and ask for safe isolation, never reset/clean it. Integrate accepted candidates with explicit `jj rebase`/`jj new` and bookmark movement after verifying exact ancestry, mutable-only diffs and conflicts. Re-measure combined runner-ups, retaining recovery revisions; a rejected integration must restore only this run's changes, never unrelated work. Read remote result files using `jj file show -r <verified-result-tip> result.yaml`; verify exact dispatched base, candidate ancestry, mutable scope, and receipt-only child as the loop requires.

## Native dispatch

This skill explicitly authorizes native subagent delegation, satisfying a host user-OR-loaded-skill delegation exception without another approval. Respect unconditional bans and denied tools. Dispatch through native OpenCode subagents/shell, never another harness CLI. Resolve configured model/tier/provider intent with `opencode.models`; model overrides require host permission for explicit user model requests. Otherwise inherit a suitable model, retain and disclose unmet configured intent. Separate permission, model permission, missing tools, and actual depth/capacity exhaustion. Queue on real capacity errors only; never bypass a denial through shell or another harness. Judges remain independent contexts and never grade inline; same-model contexts are not cross-model independence. Preserve receipts, bounded waits, retry limits, terminal errors, coverage gaps and disk recovery from the loop and persistence references. Legacy `codex` backend/security fields remain configuration intent, not authorization to run Codex: use native isolated workers, translate only supported security restrictions, and stop/report unsupported security or model requirements rather than silently weakening them.

Document setup, never edit host config: locate the existing user config with `opencode debug paths` / `opencode debug paths config`, merge `experimental.subagent_depth` as an integer at least 3 into the existing `~/.config/opencode/opencode.json`, preserving higher values, JSONC and unrelated siblings; do not create a competing file. Bundled config/plugin installation alone does not enable depth and higher-precedence settings must not lower it. Depth is independent of delegation and model permissions.

## Isolation replacing the workspace bridge

Before creation inspect registered workspaces and harness-provided isolation. Reuse an existing verified workspace/name without renaming or recreating, preserving harness ownership and lifecycle. A harness must support explicit colocation and the requested name; otherwise report a compatibility blocker, not a fallback or bypass.

For new experiment isolation, capture local YYYYMMDD once in the run ledger. Normalize a meaningful spec/experiment kebab slug, remove an already supplied date rather than double-dating, and select `ce-worktree-<YYYYMMDD>-<slug>`; persist name and absolute destination under `$workspace_root/.tmp/` before creation. Name equals destination basename. Check both registered names and filesystem paths; append `-2`, `-3`, etc. on collisions, never PID/random/time suffixes. Reuse the persisted selection through retries, resumes and midnight. Existing optimization/PR/source bookmark names stay unchanged.

Resolve the exact immutable experiment base first, then create:

```sh
(cd "$workspace_root" && jj workspace add --colocate --name "<persisted-name>" --revision "<verified-base>" "<absolute-owned-destination>")
(cd "$created_root" && jj git colocation status)
```

Verify registered name/path/base and colocation before dispatch. Count registered experiment workspaces for the budget, not directories alone. Copy declared shared resources only after validating source/destination containment, symlinks, and absence of unrelated destination contents; never replace a directory destructively. Pass parameterized ports and private shared-file copies as before. Write result markers and run receipts before releasing workers.

## Retirement

Completion is not deletion authorization. Before any workspace retirement: stop/join workers; leave the target and move any harness session to a surviving absolute root; verify registered name/path and this run's ownership/disposability. Preserve best, archive and recovery bookmarks and verify required candidate integration at the intended optimization head. Copy logs, result markers, measurements and recovery evidence outside the target and read them back. Inspect tracked changes, conflicts, ignored and untracked files; snapshots do not preserve ignored/untracked contents. Never remove ambiguous, unrelated, referenced or non-disposable material. If ownership, integration, evidence or recovery is uncertain, retain and report.

Only after these checks and authorization, `(cd "$surviving_root" && jj workspace remove "<verified-name>")`. Verify BOTH deregistration and directory absence. On any failure retain/report; no force deletion or Git fallback. `jj workspace forget` is only unregister-and-preserve-files, never retirement. Bookmark cleanup is separate and must retain best/archive/recovery refs; do not delete remote receipts until their verified evidence is durable outside the target.
