---
name: ce-polish
description: "Polish a working feature through user-directed live browser feedback. Use when a functional feature needs focused UX refinement before shipping."
disable-model-invocation: true
argument-hint: "[PR number, bookmark name, or blank for current working copy]"
---

# Polish

Put a working feature in front of the user and turn their live observations into focused UX fixes on the running page.

**Done:** the user ends the polish loop, every requested fix is reflected in the live feature or reported as blocked, and the in-scope changes are saved in local Jujutsu commit(s). A server or workspace blocker also ends the run when it is reported with the evidence needed to resume.

**Boundaries:** the user drives what to inspect and change; do not invent an autonomous checklist or expand into general QA. Never work in the revision targeted by the repository's default bookmark. This workflow may edit and locally commit the requested polish, but it never pushes or opens a PR.

## Run

1. **Get the live page ready.** Read `references/run.md` before resolving the requested revision or starting anything. It owns existing-workspace safety, dev-server discovery, the bundled-script calls, reachability, and the browser handoff.
2. **Wait for observations.** Tell the user exactly `Go to <verified-actual-url> and tell me what could be better.` Do not start a review pass while they browse.
3. **Iterate.** For each requested change, inspect only as needed, edit the in-scope surface, and let hot reload update the page. When the user asks you to inspect the result, use a browser capability available in the active harness; if none exists, ask them to describe what they see.
4. **Close locally.** When the user says they are done, invoke `ce-commit` for the polish changes. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed in `git log` always win over Go guidance. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose a fixed message syntax. Do not add generated-by text, authorship, co-authorship, sign-off, or other attribution. Then report the commit(s), the still-running server URL, and any residual blocker.
