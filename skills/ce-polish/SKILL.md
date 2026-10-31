---
name: ce-polish
description: "Polish a working feature through user-directed live browser feedback. Use when a functional feature needs focused UX refinement before shipping."
disable-model-invocation: true
argument-hint: "[PR number, branch name, or blank for current branch]"
---

# Polish

### Quoted Go source guidance (not a mandatory repository template)

The following verbatim excerpts are from https://go.dev/wiki/CommitMessage. Repository-local syntax ALWAYS wins; the Go illustration does not prescribe message syntax here. Keep the runtime full-guide/history comparison below.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,
>
> ```text
> net/http: handle foo when bar
>
> [longer description here in the body]
>
> Fixes #12345
> ```
>
> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

Put a working feature in front of the user and turn their live observations into focused UX fixes on the running page. Two ways to collect those observations: **traditional**, where the user types what could be better; and **live**, where they talk and draw on the page while a voice interviewer turns speech into units and you act on them at checkpoints.

**Done:** the user ends the polish loop, every requested fix is reflected in the live feature or reported as blocked, and the in-scope changes are saved in local commit(s). A live session also ends with a residual list of the units that were not applied and the path of its session log. A server or checkout blocker also ends the run when it is reported with the evidence needed to resume.

**Boundaries:** the user drives what to inspect and change; do not invent an autonomous checklist or expand into general QA. Never work on the repository's default branch. This workflow may edit and locally commit the requested polish, and in live mode the disclosed riffrec setup commit, but it never pushes or opens a PR.

## Run

1. **Ask live or traditional.** Ask once, before any server starts. Include this disclosure with the question: live mode needs an OpenAI key in the environment, runs a voice interviewer in the page that hears the user, is told what they click and draw on, and looks at their screen when they point at something or ask it to, streams the session to a local endpoint this skill runs, and, when riffrec is not yet in the app, adds the riffrec dependency and a provider mount as a setup commit on the current branch that stays after the session. Traditional continues with steps 2–5 unchanged. Live: read `references/live-start.md`; it owns preconditions, install, the endpoint, and the URL handoff, applies the workspace and server rules of `references/run.md` itself, then routes to `references/live-loop.md` for the session and its close. Steps 2–5 do not run for a live session.
2. **Get the live page ready.** Read `references/run.md` before resolving the requested ref or starting anything. It owns existing-worktree safety, dev-server discovery, the bundled-script calls, reachability, and the browser handoff.
3. **Wait for observations.** Tell the user where the server is running and ask what could be better. Do not start a review pass while they browse.
4. **Iterate.** For each requested change, inspect only as needed, edit the in-scope surface, and let hot reload update the page. When the user asks you to inspect the result, use a browser capability available in the active harness; if none exists, ask them to describe what they see.
5. **Close locally.** When the user says they are done, apply the message standards below and invoke `ce-commit` for the polish changes, then report the commit(s), the still-running server URL, and any residual blocker.

## Change message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing any setup or polish message, read the full guide and compare several recent subjects AND bodies from task-verified history: from the absolute target workspace root run `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Repository-local syntax always wins: examine prefixes/packages, casing, tense, subject/body separation, wrapping, and issue references. With no history, follow explicit instructions and compatible Go guidance without inventing precedent. Do not add Markdown, Co-authored-by, or Assisted-by to messages; compatible repository-local rules win. Keep setup messages semantically descriptive (including the installed riffrec version), without imposing a fixed message syntax. If describing directly, use `jj describe -m "<message composed from the standards above>"` from that absolute workspace root. This workflow never pushes.
