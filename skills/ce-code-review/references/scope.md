# Determining the reviewed diff and scope

Read this at Stage 1. Resolve scope and deterministic signals before selecting depth or reviewers. All commands run from the target workspace's absolute root (`workspace_root`), not merely with `-R`. Each repository-scoped `gh` call uses `(cd "$workspace_root" && export GIT_DIR=$(jj git root); gh ...)`. See https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/.

### Stage 1: Determine scope

Minimize permission prompts by combining related read operations. `base:` cannot be combined with a PR or bookmark target: stop with an error explaining that `base:` implies the current workspace is the reviewed tree.

**Explicit `base:` fast path.** Use the supplied revision directly, without base detection, fetch, or ancestry computation. Resolve it to exactly one revision; reject invalid or ambiguous endpoints. Review `jj diff --from "$BASE" --to @ --git` and enumerate `jj diff --from "$BASE" --to @ --name-only`. Accept commit IDs, bookmarks and JJ remote bookmarks such as `main@origin` (resolve Git-style `origin/main` to that remote bookmark explicitly when provided).

**PR number or GitHub URL.** Never check out the PR. First run `gh pr view <number-or-url> --json state,title,body,files` in the context above. Closed or merged PRs stop with `PR is closed/merged; not reviewing.` For a trivial-PR judgment, use `opencode.models` to resolve the cheapest capable model when an explicit override is available, otherwise inherit. Give a lightweight subagent title, body and file paths and ask whether this is an automated/trivial dependency-only bump, release or version increment with no substantive code change. When in doubt answer no: skipped substantive reviews are costlier than unnecessary reviews. A yes stops with `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current bookmark, or pass base:<ref> if review is intended.` Draft PRs are reviewed normally. These skips do not affect standalone, `base:` or branch-remote scope. Emit plain reason in default mode or only `{"status":"skipped","reason":"<reason>"}` in `mode:agent`.

Otherwise read metadata with `gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments`; retain file paths and whether any nonempty/non-approved review or comment exists. `BASE:pr:<number-or-url>` is a logical marker, not a diffable revision.

**Local alignment.** Classify `local-aligned` only when all three checks hold: a bookmark associated with `@` (also inspect `@-` when `@` is an empty tip) matches `headRefName`; `isCrossRepository` is false; and `jj log --no-graph -r '<headRefOid> & ancestors(@)' -T commit_id` resolves to that exact PR head. Matching names alone cannot prove ancestry. If any check fails use `pr-remote`, never workspace file contents for changed paths.

- `local-aligned`: resolve the base remote bookmark from `baseRefName`, using `jj git fetch --remote origin --bookmark <baseRefName>` if needed. Resolve exactly one best common ancestor via `heads(ancestors(@) & ancestors(<resolved-base-ref>))`; an absent or ambiguous result is a scope failure. Diff that revision to `@`, including all in-flight changes. Do not append `gh pr diff` hunks: local unpushed fixes make the workspace canonical. Coverage: `scope: local-aligned (PR; local tree diff)`.
- `pr-remote`: files come from metadata and hunks from `gh pr diff <number-or-url> --color=never`; failure stops with an actionable error, never a checkout fallback. Best-effort fetch the PR head bookmark with `jj git fetch --remote origin --bookmark <headRefName>` without changing the workspace. Set `PR_HEAD_REF` to the concrete commit ID only if its `jj log --no-graph -r '<headRefName>@origin' -T commit_id` equals metadata `headRefOid`. A fork, moved head, fetch failure or mismatch omits this ref and names the limitation in Coverage; reviewers then use only provided hunks. Fetch the base similarly and set `PR_BASE_REF` to the verified concrete base commit ID. Failure omits it and names the gap; never assume `main`. This diffable base is distinct from the logical `BASE` marker. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and verified `<pr-head-ref>`/`<pr-base-ref>` values in reviewer/validator context.

**Bookmark target (branch argument compatibility).** Never switch trees. If the bookmark identifies the current reviewed tree, use standalone scope. Otherwise try `gh pr view <branch> --json baseRefName,url,headRefName` and prefer the PR path if found. Else resolve `<branch>@origin` or the local bookmark, fetching only that remote bookmark when needed. Resolve the default base, then one best common ancestor of base and reviewed head; diff `jj diff --from "$BASE" --to "$BRANCH_HEAD_REF" --git` and enumerate `--name-only`. Missing/ambiguous head or base stops with an actionable error recommending an open PR or explicit `base:` on the intended workspace, never an automatic checkout. Set `branch-remote` and include `<branch-head-ref>` and scope mode in the context.

**Standalone.** Resolve an associated PR from the actual bookmark name, explicitly passing it to `gh pr view <bookmark> --json baseRefName,url` (do not depend on Git's current branch). Otherwise resolve the repository's default remote branch from GitHub metadata and its JJ remote bookmark. An empty `@` may inherit the bookmark from `@-`. If no base resolves, stop rather than reviewing only `@-` and silently missing earlier work. Resolve the unique best common ancestor and diff it to `@`.

For every successful scope record `BASE`, `FILES`, `DIFF`, `UNTRACKED`, `DIFF_A` and `DIFF_B`. Local `DIFF_B` is `@`; remote endpoints are the verified concrete refs. JJ snapshots eligible new files automatically: they belong in the reviewed change. Inspect `jj status` for paths not tracked because of size/ignore policy; list excluded paths in Coverage and continue without prompting. Never silently drop a file actually included by JJ. Local inspection is valid only for standalone/local-aligned; remote reviewers and validators use `jj file show -r <reviewed-head> <path>` and search files exported from that revision under local `.tmp/`, or supplied hunks when a ref is absent. Never use workspace paths for a remote reviewed tree.

### Stage 1b: Compute scope signals (cheap, deterministic)

Use native JJ plus shell to derive facts once and save `<run-dir>/scope.json`; the removed workspace bridge is not invoked. Validate unique endpoints and, for remote scope, both concrete refs and the unique best common ancestor. A missing remote endpoint must fail closed, not compare a base with the unrelated workspace. Derive exact added/deleted line totals from `jj diff --from <a> --to <b> --git`, file inventory from `--name-only`, and executable modes from the patch metadata. Count additions plus deletions, not context lines. Binary, malformed or uncountable paths force `uncounted` and full depth. Failed/ambiguous resolution or diff collection records `status: unavailable`, its reason, and `hard_block_full: true`.

Preserve these fields: `status`, `reason`, `exec_lines`, `exec_nontest_lines`, `unclassified_lines` (counts by extension), `changed_lines`, `uncounted_files`, sorted `changed_files`, `signals`, `hard_block_classes`, `hard_block_full`, `silent_pass_classes`, `size_band`, `test_files_changed`, `agent_surface`, `has_learnings_corpus`, `declared_packs`, and `pack_roots` (0 at this parse-only stage).

Executable means changed executable-mode paths or extensions `.rb .py .js .mjs .cjs .jsx .ts .tsx .go .rs .java .swift .kt .c .cc .cpp .cs .php .ex .exs .scala .sh .bash .zsh .fish .ps1 .pl .pm .lua .dart .vue .svelte`. Test conventions: `test/`, `tests/`, `spec/`, `__tests__/`, `.test.`/`.spec.` suffixes, `test_*.py`/`conftest.py`, or case-sensitive `Test`/`Tests`/`Spec` class suffixes for Java/Kotlin/Scala/Swift/C#. Do not classify `Contest.java` or `Manifest.cs` as tests.

Path signals: migrations/schema (`db/migrate`, `schema.rb/sql`, migration directories, Alembic/Flyway/Liquibase); frontend (TSX/JSX/Vue/Svelte/CSS/SCSS/HTML/ERB/Haml, components, Stimulus/Turbo); API (routes/controllers/api/serializers/graphql, proto/OpenAPI/Swagger); Swift/iOS (Swift/Kotlin/pbxproj/xcconfig/entitlements). Migrations force full. CI paths `.github/workflows`, `.gitlab-ci.yml`/`.gitlab-ci`, Jenkinsfile, `.circleci`, `.buildkite` forbid lite but do not alone force full. `size_band` is `large` at **200 or more executable non-test changed lines**, otherwise `small`; large, any hard-block class or uncounted file forces `hard_block_full`. Neither a small count nor any heuristic awards lite; the depth gate still judges consequence.

Agent surface means skills/agents/prompts/tools/mcp/commands directories, SKILL.md, AGENTS/CLAUDE/GEMINI.md, `.cursor`, `.codex-plugin` or `.claude-plugin`. Determine the learnings corpus at `<root>/solutions/`. In local scope parse `packs:` from project config without resolving/cloning, using the retained `packs-resolve.py --declared-only` when useful; `declared_packs` is true if entries are declared, false if none, null if unreadable (then inspect the key explicitly). In remote scope local config facts are null and no resolver runs. Apply the depth gate before later references; full selection still judges auth, payments, mutation, I/O, concurrency and process execution. These facts are selection inputs, not automatic spawn decisions.

### Stage 1c: Map criteria files to changed paths

Enumerate `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth in the **reviewed tree**, using `jj file list -r <reviewed-head>` for remote scope. Keep files whose directory is an ancestor of a changed path. A remote-only criteria file must be included and a deleted one excluded. Root criteria govern all paths; nested criteria only descendants. Use every governing `CODING_STANDARDS.md`; instruction files supply criteria only for paths with no governing standards file. No path is graded against both kinds. Compound Packs remain a separate learnings source; standards and pack violations are one finding per source. No applicable criteria is a complete result, not a gap; failed or uncertain searches must be recorded, not treated as empty.

Create the run directory for every depth path:

```bash
workspace_root="<absolute target workspace root>"
SCRATCH_ROOT="$workspace_root/.tmp/rocketclaw"
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi
chmod 700 "$SCRATCH_ROOT" || exit 1
RUN_ID=$(date +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' ')
RUN_DIR="$SCRATCH_ROOT/ce-code-review/$RUN_ID"
(umask 077; mkdir -p "$RUN_DIR") || exit 1
chmod 700 "$RUN_DIR" || exit 1
echo "$RUN_DIR"
```

### Stage log

Keep measured cost/profiler support. Only the bundled logger writes `<run-dir>/stages.jsonl`; the receipt writer later folds it into `metadata.json` with `summarize`. Resolve Python by execution in the same shell call (Windows Store stubs can satisfy presence checks):

```bash
SKILL_DIR="<absolute directory containing this SKILL.md>"
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; }
"$PY" "$SKILL_DIR/scripts/run-log.py" event --run-dir "$RUN_DIR" --start scope
```

Later boundaries use the same call with `--end <stage> --start <stage>`, counts in `--reviewers`, `--candidates`, `--tokens` only when provided, and `--fact key=value`. Fold boundaries into existing shell calls, not their own turns. Stage names remain scope/review/receipt on lite/focused, scope/select/dispatch/validate/merge/report on full, with peer overlapping review or dispatch.

## Task Visibility

On the multi-agent path use available task tracking for review outcomes, not individual personas or tool mechanics. Add conditional work only when selected and update meaningful transitions. Without tracking, use normal progress and final report; do not simulate a chat task list.
