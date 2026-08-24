---
name: ce-polish
description: "Polish a working feature through user-directed live browser feedback. Use when a functional feature needs focused UX refinement before shipping."
disable-model-invocation: true
argument-hint: "[PR number, bookmark/change/revision, or blank for current change]"
---

# Polish

Put a working feature in front of the user and turn their live observations into focused UX fixes on the running page.

**Done:** the user ends the polish loop, every requested fix is reflected in the live feature or reported as blocked, and the in-scope work is recorded as local described JJ change(s). A server or workspace blocker also ends the run when it is reported with the evidence needed to resume.

**Boundaries:** the user drives what to inspect and change; do not invent an autonomous checklist or expand into general QA. Work only in mutable JJ changes, never rewrite `trunk()` or another immutable revision, and do not use Git's index, stash, branch checkout, or worktree operations. This workflow may edit and locally describe the requested polish, but it never pushes or opens a PR.

## Run

1. **Get the live page ready.** Read `references/run.md` before resolving the requested revision or starting anything. It owns JJ workspace safety, GitHub and Git interoperability, dev-server discovery, the bundled-script calls, reachability, and the browser handoff.
2. **Wait for observations.** Tell the user where the server is running and ask what could be better. Do not start a review pass while they browse.
3. **Iterate.** For each requested change, inspect only as needed, edit the in-scope surface, and let hot reload update the page. When the user asks you to inspect the result, use an available browser capability; if none exists, ask them to describe what they see.
4. **Close locally.** When the user says they are done, invoke `ce-commit` for the polish changes. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local runtime syntax and the project's active instructions always win; apply only compatible Go guidance to quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, layout, template, or example. Then report the recorded change ID(s), any associated bookmark, the still-running server URL, and any residual blocker.
