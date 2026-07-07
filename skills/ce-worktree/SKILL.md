---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark-oriented workspace for fresh work, or attach a workspace to an existing bookmark/PR/change to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated JJ workspace, without disturbing the user's primary workspace. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to `jj workspace add`.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh workspace from a base bookmark (trunk). This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a change/revision. Attach the workspace to that revision instead of creating an unrelated base. If the target is already being edited in another JJ workspace, do **not** create a conflicting second editing location for the same change — report that it is already active at `<path>` and let the caller act (work there in place; or, only if a clean separate tree is essential, create a new workspace at the same immutable base and make a separate change).

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes what revision the new workspace starts from and what is reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, check whether the current directory is already a JJ workspace and whether the repo already has other workspaces:

```bash
jj workspace root      # root path for the current workspace
jj workspace list      # all known JJ workspaces for this repo
```

If `jj workspace root` fails, this is not a JJ workspace; stop and ask whether to initialize/clone with JJ before continuing. Do not silently fall back to non-JJ VCS commands.

Use `jj workspace list` to decide whether the requested isolation already exists:

- If the current workspace is already the intended isolated location, report the workspace root (`jj workspace root`) and current state (`jj st`). Do not create another workspace — a workspace-from-workspace can land in a place the harness does not track. Then **work in place**.
- If another listed workspace is clearly the intended one (matching PR, bookmark, or task name), report its path and ask before switching there or creating another workspace.
- If no existing workspace matches the request, continue to Step 1.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native workspace primitive — for example an `EnterWorkspace` / `WorkspaceCreate` tool, a `/workspace` command, or a `--workspace` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` can create state the harness cannot see, navigate to, or clean up.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the workspace root.** The `.workspaces/` and ignore paths below are root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj workspace root)"`. Without this, `.workspaces/<bookmark>` and the ignore edit would land in the subdirectory (e.g. `src/.workspaces/...`, `src/.gitignore` in a colocated repo) instead of at the workspace root.
2. Choose a meaningful bookmark/workspace name from the work description (e.g. `feat-login`, `fix-email-validation`) — avoid opaque auto-generated names. Pick a base bookmark (default: the repo's default bookmark such as `main`, preferring the tracked remote form when available).
3. **Ensure `.workspaces/` is ignored before creating anything**, so workspace contents are not accidentally tracked from the parent workspace. Use the project's existing ignore convention; in colocated repos this is usually a `.workspaces/` line in `.gitignore`.
4. Best-effort refresh remote bookmarks without disturbing the current workspace: `jj git fetch --remote origin`. This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or local-only work), do not abort; continue to the next step and use the local bookmark/revision.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add --name <workspace-name> .workspaces/<workspace-name> --revision <base-bookmark>` (use the local `<base-bookmark>` if the remote-tracking bookmark does not exist). After the first real described change, create or move the outgoing bookmark with `jj bookmark create <bookmark-name> -r @-` or `jj bookmark set <bookmark-name> -r @-`, then publish with `jj git push --bookmark <bookmark-name>`.
   - **Isolate an existing ref:** attach to the target revision instead of starting from the base — for an existing bookmark, tag, change ID, or revision, `jj workspace add --name <workspace-name> .workspaces/<workspace-name> --revision <target-rev>`. For a **GitHub PR**, inspect the PR with `gh pr view <n>` and fetch the PR head into JJ-visible refs/bookmarks with `jj git fetch` as needed, then create the workspace at that PR head revision. Keep fixes on a bookmark that can be pushed back with `jj git push --bookmark <bookmark-name>`.
6. Enter it: `cd .workspaces/<workspace-name>`.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace — do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the workspace option). Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current workspace" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current workspace on explicit confirmation, and do not retry alternative paths automatically.

## Other workspace operations

Use JJ directly — no wrapper is needed:

```bash
jj workspace list                          # list workspaces
jj workspace root                          # print the current workspace root
jj workspace add .workspaces/<name>        # add a workspace
cd .workspaces/<name>                      # enter a workspace by path
cd "$(jj workspace root)"                  # return to the current workspace root
jj st                                      # inspect workspace state
jj diff                                    # inspect workspace changes
```

## When to create a workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on a bookmark/change in the current workspace — and never when Step 0 shows you are already in the intended one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "workspace" or the legacy "worktree" label in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark/workspace name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path or workspace name is in use. Enter it (`cd .workspaces/<name>`) or choose a different workspace name/path before recreating. If the workspace should be retired, use `jj workspace list` to confirm it, then forget the workspace with `jj workspace forget <name>` and remove the directory only after confirming it has no needed changes.

**"Cannot forget workspace: it is the current workspace"**: `cd` to another workspace first, then run `jj workspace forget <name>`.
