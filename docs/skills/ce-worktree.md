# `ce-worktree`

> Ensure work happens in an isolated workspace without disturbing the current checkout — by detecting existing isolation, deferring to the harness's native worktree/workspace tool, and falling back to `jj workspace add` only when needed.

`ce-worktree` is the **isolation guardrail** skill. Its value is judgment, not mechanics: most coding harnesses now create a worktree/workspace by default at session start, so the common case is that you are *already* isolated. The skill encodes the discipline to recognize that, defer to the harness's own workspace tooling, and only create a JJ workspace as a last resort — so you never nest workspaces or create state the harness can't manage.

It is pure prose + inline VCS commands, with **no bundled script**, so it works verbatim on every supported target (Claude Code, Codex, Gemini, OpenCode, Pi).

---

## TL;DR

| Question | Answer |
|----------|--------|
| What does it do? | Ensures isolation exists. Detects an existing workspace first, prefers the harness's native worktree/workspace tool, falls back to `jj workspace add` under `.worktrees/<workspace-name>` when needed |
| When to use it | Starting work that should stay isolated; when `ce-work` or `ce-code-review` offers a worktree option |
| What it produces | Either "you're already isolated, work in place" or a new isolated workspace |
| Skip when | Single-task work that fits on a bookmark in the current checkout |

---

## The Problem

Asking an agent to "make a worktree" is increasingly the *wrong* default, because the agent is usually already in one:

- **Workspace-from-workspace** — creating another isolated tree when the harness already gave you one lands work in a place the harness may not manage.
- **Phantom state** — a behind-the-back workspace can be invisible to the harness (Orca, Cursor, etc.) that owns workspace lifecycle: it can't list, navigate to, or clean it up.
- **Cryptic names** — auto-generated names like `worktree-jolly-beaming-raven` obscure what the workspace is for.

## The Solution

`ce-worktree` runs isolation as an ordered decision, not a creation script:

1. **Detect existing isolation** with `jj workspace list` and `jj workspace root`. Already isolated -> report and work in place.
2. **Prefer the harness's native worktree/workspace tool** (e.g. an `EnterWorktree` tool, a `/worktree` command, a `--worktree` flag) so the workspace stays managed.
3. **JJ workspace fallback** only when neither applies: create `.worktrees/<workspace-name>` with a meaningful workspace/bookmark name.

---

## What Makes It Novel

### 1. Detection before creation

The single most important behavior: before creating anything, determine whether the current directory is already an isolated JJ workspace. When already isolated, the skill works in place rather than nesting.

### 2. Native-tool deference

If the harness provides a worktree/workspace primitive, the skill uses it instead of shelling out. This avoids creating phantom workspaces the harness can't see or clean up — the "don't fight the harness" rule.

### 3. Portable by construction

There is no bundled script and no `${CLAUDE_SKILL_DIR}` dependence — only inline VCS commands the agent runs from the project directory. That is why the skill resolves identically on every target, and why it carries no `ce_platforms` gate.

### 4. Naming guidance for upstream callers

When `ce-work` or `ce-code-review` invoke the skill, they derive meaningful workspace/bookmark names from the work (`feat-crowd-sniff`, `fix-email-validation`) — never an opaque auto-generated name.

---

## Quick Example

You're in an Orca-managed worktree (the harness created it at session start) and ask `ce-work` to isolate the work. The skill runs Step 0, sees the current workspace is already isolated, reports the workspace root and current bookmark, and proceeds in place — no second workspace, no phantom state.

In a plain terminal checkout with no native worktree tool, the same invocation falls through to Step 2: it fetches the base bookmark, runs `jj workspace add --name feat-login -r main@origin .worktrees/feat-login`, enters that workspace, and creates a meaningful bookmark if needed.

---

## When to Reach For It

Reach for `ce-worktree` when:

- You're starting work that should stay isolated from the current checkout
- A skill (`ce-work`, `ce-code-review`) offered worktree as an option

Skip it when:

- The work is single-task and fits on a bookmark in the current checkout
- You are already isolated and have no need for a *second*, parallel workspace (the skill detects this for you)

---

## Use as Part of the Workflow

`ce-worktree` is invoked from chain skills as their isolation step:

- **`/ce-work`** — when starting work, the user can choose workspace isolation over using the current checkout
- **`/ce-code-review`** — for reviewing PRs concurrently without disturbing in-progress work

Upstream callers pass meaningful workspace/bookmark names; the skill expects names derived from the work — not auto-generated random names.

---

## Other worktree operations

List, forget, and switch use JJ workspace commands directly — the skill provides no wrapper:

```bash
jj workspace list                          # list JJ workspaces
jj workspace forget <workspace-name>       # stop tracking a removed workspace
cd .worktrees/<workspace-name>             # switch when shell navigation is available
cd "$(jj workspace root)"                  # return to the current workspace root
```

---

## FAQ

**Why a skill instead of just `jj workspace add`?**
The value isn't the `jj workspace add` command — the agent knows that. It's the *judgment*: detect that you're probably already isolated, defer to the harness's workspace tooling, and don't nest or create phantom state. That discipline is shared by `ce-work` and `ce-code-review`, so it lives in one named skill rather than being duplicated and drifting.

**I'm already in a worktree — will it make another?**
No. Step 0 detects existing isolation and works in place. Workspace-from-workspace is exactly the failure mode the skill prevents.

**How do I clean up a workspace?**
Leave the workspace directory, remove it, then run `jj workspace forget <workspace-name>`. Delete the bookmark separately only after confirming it is no longer needed.

---

## See Also

- [`/ce-work`](./ce-work.md) — offers this skill as its isolation option
- [`/ce-code-review`](./ce-code-review.md) — offers worktree isolation for concurrent review
