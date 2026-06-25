# `ce-commit`

> Create a single, well-crafted JJ-backed commit from working-copy changes — convention-aware, sensitive-file-safe, with logical splitting when concerns are clearly distinct.

`ce-commit` is the **commit-only** skill — sibling to `/ce-commit-push-pr` for the case where you want commits without pushing or opening a PR. It picks up your repo's existing commit conventions (project instructions first, then recent commit history, then conventional-commits as fallback), groups changed files by naturally distinct concerns (no interactive hunk splitting, file level only), and passes explicit file sets to `jj commit` so sensitive files (`.env`, credentials, build artifacts) don't sneak in.

For the full ship flow (commit + push + PR), use `/ce-commit-push-pr`. For just the commit, this skill.

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Creates one or two well-formed commits from the working copy, following repo conventions, committing explicit file sets |
| When to use it | "Commit this", "save my changes" — when you want commits without push or PR |
| What it produces | One or two commits on the current bookmark/branch (no push, no PR) |
| What's next | `/ce-commit-push-pr` later if you want to open a PR; otherwise `jj git push` manually |

---

## The Problem

Manual commits go wrong in predictable ways:

- **Broad commits** sweep in unintended files — `.env` files, build artifacts, generated files, untracked notes
- **Wrong commit convention** — defaulting to conventional commits when the repo uses ticket-prefix style, or vice versa
- **Mixing distinct concerns** — backend models + frontend components + docs all in one commit because nobody bothered to split
- **Subject lines that describe what changed, not why** — `update foo.rb` tells future readers nothing
- **Unnamed commits** that the user doesn't realize need a bookmark before pushing later
- **Default-branch commits** that surprise the user (no warning before committing to `main`)

## The Solution

`ce-commit` runs commit creation as a structured pass:

- **Convention detection** — repo conventions in context first, then recent 10 commits, then conventional-commits fallback
- **Explicit file sets** — never broad `.` / `all()` commits; pass files by name
- **Logical splitting** at the file level (no `jj commit -i`) when 2-3 distinct concerns are present; single commit when ambiguous
- **No-bookmark handling** — asks whether to create a feature bookmark before committing
- **Default-bookmark warning** — asks before committing to `main`/`master`
- **Heredoc commit messages** — preserves multi-line formatting without shell-escape pain

---

## What Makes It Novel

### 1. Convention detection in priority order

For the commit message format, the skill consults sources in priority:

1. **Repo conventions in context** — project instructions (`AGENTS.md`, `CLAUDE.md`) already loaded at session start; if they specify conventions, follow those
2. **Recent commit history** — examine the last 10 commits; if a clear pattern emerges (conventional commits, ticket prefixes, emoji prefixes), match it
3. **Default to conventional commits** — `type(scope): description` with `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`, `build` as types

When using conventional commits and `fix:` vs `feat:` both seem to fit, the skill defaults to `fix:` (a change that remedies broken or missing behavior is `fix:` even when implemented by adding code). The user can override.

### 2. Explicit file sets — no broad commits

The skill passes files by name in a single command (`jj commit file1 file2 file3 -m ...`). This avoids accidentally including:

- `.env` files with credentials
- Build artifacts (`dist/`, `.next/`, compiled binaries)
- Generated files
- Notes or scratch files in untracked directories

The deliberate avoidance is documented in the skill — broad file sets like `.` and `all()` are explicitly called out as the wrong move.

### 3. Logical splitting at file level

Before committing, the skill scans changed files for naturally distinct concerns. If files clearly group into 2-3 separate logical changes (a refactor in one directory, a new feature in another; or test files for a different change than source files), the skill creates separate commits. Splits happen at the **file level only** — no `jj commit -i`, no hunk-level interactive splitting. When the split is ambiguous, one commit is fine. The sweet spot is 2-3 commits, not many tiny ones.

### 4. No-bookmark handling

If the current change has no bookmark, the skill explains the situation and asks whether to create a feature bookmark first. The user can:

- Create a bookmark (skill derives the name from change content)
- Continue with the unnamed local commit

### 5. Default-branch warning

If the current bookmark is `main`, `master`, or the resolved default branch, the skill warns before committing and offers to create a feature bookmark first. This prevents the case where someone accidentally commits to the default branch in a repo with branch-protection that they'll have to back out.

### 6. Heredoc commit messages — clean multi-line formatting

The skill uses a `cat <<'EOF'` heredoc for the commit message so multi-line bodies preserve their formatting. Example:

```bash
jj commit file1 file2 file3 -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining why this change was made,
not just what changed.
EOF
)"
```

The quoted sentinel (`'EOF'`) prevents `$VAR`, backticks, and embedded `EOF` from being expanded inside the body.

### 7. Subject focused on *why*, not *what*

The skill writes subject lines in imperative mood, focused on motivation rather than mechanical description. "Fix double-submit on checkout" beats "Update checkout.rb." The body explains motivation, trade-offs, or context a future reader would need; it's omitted for obvious single-purpose changes.

---

## Quick Example

You finish a feature touching backend models, controller, and frontend component. You invoke `/ce-commit`.

The skill reads `jj st`: 4 files modified across `app/models/`, `app/controllers/`, and `app/javascript/`. Reads recent commits — the project uses conventional commits with scope (`feat(auth): ...`, `fix(billing): ...`). On feature bookmark `tmchow/notification-mute`, not on the default bookmark.

The skill scans changed files for distinct concerns: model + controller hang together (data layer); the JS component is its own concern (UI). Two logical commits.

Commit 1: commits `app/models/notification_subscription.rb`, `app/controllers/settings_controller.rb`. Composes message:

```text
feat(notifications): add per-subscription mute_until column

Subscriptions can now carry a mute timestamp; nil means not muted.
Controller exposes the toggle endpoint.
```

Commit 2: commits `app/javascript/controllers/notification_toggle_controller.js`. Composes:

```text
feat(notifications): wire toggle UI to mute endpoint
```

Reports both commit hashes and subject lines.

---

## When to Reach For It

Reach for `ce-commit` when:

- You have changes to commit and you want them on the local bookmark/branch only — no push, no PR
- You're committing mid-flow and intend to push later
- You want repo-convention-aware commit messages
- You want broad commits avoided and logical splitting handled

Skip `ce-commit` when:

- You also want to push and open a PR → `/ce-commit-push-pr` does it all
- You need very specific hunk-level splitting -> use `jj commit -i` directly; the skill is file-level
- The change is so trivial that the agent can run `jj commit <files> -m ...` in one breath without the skill — though even tiny changes benefit from the convention detection

---

## Use as Part of the Workflow

`ce-commit` is invoked from skills that explicitly want commit-only flow:

- **`/ce-debug` Phase 4** — when the skill is on a pre-existing branch (not skill-owned) and the user picks "Commit the fix" instead of "Commit and PR", `ce-commit` handles the local commit
- **`/ce-work` Phase 4 (no-PR path)** — when the user prefers to commit without pushing, `ce-commit` is the alternate handoff
- Standalone via `/ce-commit`

The full ship flow (commit + push + PR) is `/ce-commit-push-pr`; this skill is the local-only sibling.

---

## Use Standalone

Direct invocation with no arguments — the skill reads JJ context and proceeds:

- `/ce-commit` — commit current changes following repo conventions
- The user describes what to commit ("commit the auth changes") in conversation; the skill applies that as a hint when grouping or composing the message

There are no arguments. Convention detection, file grouping, and message composition all happen from context.

---

## Reference

| Step | Action |
|------|--------|
| 1 | Gather context (`jj st`, `jj diff --git`, bookmark, recent commits, default branch) |
| 2 | Determine commit message convention (instructions > recent history > conventional-commits) |
| 3 | Consider logical commits (file-level split when concerns are clearly distinct) |
| 4 | Commit explicit file sets (per-group; warn on default bookmark; handle unnamed changes) |
| 5 | Confirm via `jj st`; report commit hashes |

---

## FAQ

**Why not broad file sets?**
Because they sweep in unintended files — `.env` with credentials, build artifacts, generated files. Passing file names keeps commits clean and prevents secret leakage.

**Why no hunk-level splitting?**
Because hunk-level splitting (`jj commit -i`) is interactive and fragile in agent flows. File-level splitting is the right granularity for "logical commits" — distinct concerns naturally separate at the file level. If you genuinely need hunk-level, do it manually.

**What if my repo uses a non-standard convention?**
The skill detects from project instructions first (which is the right place to document conventions), then recent commit history (which is the de facto convention even when not documented). Conventional commits is just the fallback when neither source applies.

**Why ask before committing on the default branch?**
Because most repos with branch protection will reject a default-branch commit, and the user usually didn't intend to commit there. The warning catches the case before anything irreversible happens.

**What if I want to push and PR after?**
Use `/ce-commit-push-pr` for the full flow, or run `jj git push` and `gh pr create` manually after this skill commits.

---

## See Also

- [`/ce-commit-push-pr`](./ce-commit-push-pr.md) — full flow: commit + push + PR
- [`/ce-debug`](./ce-debug.md) — invokes this skill at Phase 4 for the commit-only handoff path
- [`/ce-work`](./ce-work.md) — invokes this skill at Phase 4 when the user picks no-PR
