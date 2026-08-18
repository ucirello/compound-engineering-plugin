# Spiral CLI reference

Spiral (`@every-env/spiral-cli`) drafts copy in a user's brand voice. `ce-promote` uses it as an **optional enhancement** — every call must be wrapped so a missing, unauthed, or erroring CLI never blocks the skill.

## Detection — three states

```bash
which spiral
spiral auth status --json 2>/dev/null
```

- **Absent** — `which spiral` finds nothing. → Path 0 (offer to install + connect).
- Otherwise parse `spiral auth status --json`:
  - **Ready** — `"authenticated": true` (equivalently `"status": "authenticated"`, any `source`). Use Path A.
  - **Unauthed** — `"authenticated": false`. → Path 0 (offer to sign in).
  - **Older CLI** that ignores `--json` (output isn't JSON): fall back to the human-readable signal in that same output — ready iff it contains `spiral_sk_`, else unauthed.

Prefer the JSON `authenticated` flag over substring-matching `spiral_sk_` — the flag is the designed contract, and the substring is only the backward-compat fallback. Any error or timeout → treat as not-ready and continue; never block.

## Path 0 — Offer setup (first run, declinable)

When Spiral is unauthed or absent, offer setup once. First check the opt-out so this never nags.

### Check the opt-out

<!-- ce-config-layers:start -->
**Resolve ordinary YAML keys from the two workspace files.**

- **Read** `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml`. Resolve `<workspace-root>` with `jj workspace root`; if that fails, use the current directory. Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

Resolve the workspace root with `jj workspace root`, using the current directory if resolution fails, then apply the ordinary-key rule above for `ce_promote_spiral_optout`. If the winning **uncommented** top-level value is exactly `true`, **skip Path 0** and go straight to Path B. **Ignore commented lines** — `ce-setup`'s template includes a commented example, and a commented line is documentation, not an opt-out (a naive substring match would wrongly suppress the offer for any project that accepted the default template). Otherwise, offer setup.

### Ask

Use the platform's blocking-question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`) / Pi. If no blocking tool exists or the call errors, present the same options as a numbered list in chat and wait for a reply — never silently skip.

For the **unauthed** state, the **agent itself** runs `spiral login --json` (CLI >= 1.8.0): it's non-blocking and the API key never passes through the agent — the agent shares the returned `auth_url`, the user approves in a browser, and the credential is delivered server->CLI. The blocking question is mainly the escape hatch.

Phrase the question dynamically from the detected state. Explain that Spiral personalizes the copy, offer setup or direct drafting, and disclose that choosing direct drafting records a project-local opt-out that can be reversed later.

Offer exactly **two** options (labels must be self-contained):

- **Unauthed** state: `Sign in to Spiral` · `Draft directly without Spiral`
- **Absent** state: `Install Spiral` · `Draft directly without Spiral`

There is deliberately no separate "don't ask again" option: **dismissing is itself the opt-out.** A single first-run decline records the flag and the offer never recurs in this workspace. This is what keeps a per-ship skill from nagging — never make the user choose a special variant to stop being asked.

### Act on the choice

- **Sign in to Spiral** (installed, unauthed) — the agent runs `spiral login --json` itself. It's non-blocking, and the **API key never touches the agent** (the token is exchanged server->CLI via a device-code flow). Parse the JSON `status`:
  - `already_authenticated` — `{ "authenticated": true, "status": "already_authenticated", "prefix": "..." }`: a credential already exists; nothing to approve. Go to Path A. (To switch accounts the user runs `spiral logout` first.)
  - `pending` — `{ "status": "pending", "auth_url": "...", "user_code": "ABCD-2345", "expires_in": 900 }`: surface the `auth_url` for the user to open and approve in their browser (the `user_code` is embedded in the URL — show it too so they can confirm it matches), then wait. Once the user says they've approved, confirm by running `spiral auth status --json`: it returns `"authenticated": true` when claimed, or `"status": "pending"` if not yet (re-check, don't busy-loop with sleeps — let the user's confirmation drive the re-check). If it stays unclaimed or the code expires (~`expires_in`s), offer to retry or fall to Path B. On success -> Path A.
  - **Never have the user paste an API key into chat** — with agent login the agent never handles the key at all.
  - **Older CLI (< 1.8.0, no agent login):** if `spiral login --json` returns the legacy `API key required ... --token` text instead of JSON, suggest `npm i -g @every-env/spiral-cli@latest`, or have the user run `spiral login` themselves in their terminal (browser sign-in) and re-check `spiral auth status`. If they would rather not, go to Path B.
- **Install Spiral** (absent) — the pairing-code command installs and connects in one step. Direct the user to Settings → Connect an Agent at https://app.writewithspiral.com to copy their command, which looks like:
  ```bash
  npx @every-env/spiral-cli@latest setup --pairing-code <code>
  ```
  The pairing code is single-use and expires in ~15 minutes, so the user must fetch a fresh one from the web app — do not hardcode it. Once installed, if still unauthed, follow the **Sign in to Spiral** flow above (`spiral login --json`). If the user can't or won't install, go to Path B.
- **Draft directly without Spiral** — record the opt-out (below) so the offer never re-prompts in this workspace, then go to Path B. (A failed/abandoned **sign-in or install** attempt does NOT record the opt-out — only an explicit "draft directly" dismissal does — so a user whose auth didn't complete still gets one clean re-offer next run.)

### Record the opt-out (best-effort)

Resolve the workspace root with `jj workspace root`, using the current directory if resolution fails, then add `ce_promote_spiral_optout: true` as a top-level key to `<workspace-root>/.rocketclaw/config.local.yaml`, using the native file-write/edit tool:

- **File already exists:** ensure an **uncommented** `ce_promote_spiral_optout: true` line is present — add one (or uncomment the example) unless an uncommented one already exists. A commented `# ce_promote_spiral_optout: true` (from `ce-setup`'s template) does **not** count as present; leaving only the comment would let the comment-ignoring read path re-prompt next run.
- **File absent:** before creating it, ensure `.rocketclaw/*.local.yaml` is active in the backing Git repository's local exclude file, resolving the backing Git directory with `jj git root` and using its `info/exclude` file. This interoperability is required because Jujutsu honors `$GIT_DIR/info/exclude`; do **not** hardcode a `.git` path, which is incorrect for non-colocated repositories and linked workspaces. Use the local exclude, **not** `.gitignore`: it keeps the rule local and avoids changing a tracked file on what was a drafts-only action. `ce-setup` is the canonical place that adds the shared `.gitignore` entry for teammates. Only after the ignore is active, create the file (and its `.rocketclaw/` directory) with the key. Without an ignore rule, a user who runs `/ce-promote` before `/ce-setup` could accidentally include machine-local opt-out state in a change.

If resolving or updating the backing Git exclude fails, do not create a new config file. If that or any other write fails, proceed to Path B anyway; the opt-out is a convenience, never a blocker.

After recording, confirm it in one dynamically worded line so the write isn't silent and the user knows how to undo it. Name `.rocketclaw/config.local.yaml`, state that it is excluded from revision history, and explain that removing `ce_promote_spiral_optout` restores the offer.

## Generate

```bash
spiral write "<prompt>" --instant --num-drafts <1-5> --json
```

- `--instant` — skip clarifying questions. **Always use it**; this is a headless context with no human mid-call.
- `--json` — machine-readable output. Always use it.
- `--num-drafts <1-5>` — number of drafts (single-channel mode only; see gotcha).
- `--workspace <uuid>` — scope to a brand-voice workspace. List with `spiral workspaces`. Use only if the user names one.
- `--style <uuid>` — pin a specific voice/style. Use only if the user names one.

### Output shape

JSON with (fields verified against the Spiral CLI `write` output):

```json
{
  "session_id": "uuid",
  "status": "complete | needs_input",
  "drafts": [
    { "id": "uuid", "title": "...", "content": "markdown", "channel": "x",
      "url": "https://app.writewithspiral.com/chat/<session>?draft=<id>", "display_hint": "inline | expandable" }
  ],
  "text": "pipeline commentary — DO NOT show the user unless drafts is empty",
  "style_used": null,
  "quota_remaining": 42
}
```

- `channel` (lowercase) is one of `x`, `linkedin`, `email`, `newsletter`, `blog`, `instagram_tiktok`, `research`, or `null`.
- `url` opens that draft in the Spiral web app for editing. Drafts persist to the user's account — surface `session_id` + each `url` in your output (Phase 4).
- **Do not surface the `text` field** to the user — it's internal pipeline commentary. Only fall back to it if `drafts` is empty.
- With `--instant`, `status` should be `complete`. If it comes back `needs_input` (rare with `--instant`), don't relay Spiral's questions to the user — either answer from the context you already have via a `--session` follow-up, or fall back to Path B for that channel.

If parsing fails or `drafts` is empty, fall back to direct drafting for the affected channels.

## The multi-channel / cue-word gotcha (important)

Multi-channel output is **phrasing-driven, not a flag.** Spiral enters "campaign mode" when the prompt contains **≥2 channel keywords** (tweet/X, LinkedIn, email, blog, …) **OR** any cue word: `campaign`, `across`, `multi-channel`, `everywhere`, `cross-post`.

Two consequences to encode:

### (a) To get N variations of ONE channel

Ask for `"<count> <single-channel> options for <shipped capability>"` and:

- **Avoid** the cue words above. Ironically, a prompt literally containing `campaign` or `multi-channel` trips campaign mode — so describe the task **without** those words.
- Pass `--num-drafts <count>`.

If you accidentally include a cue word, Spiral decides it's a single campaign piece and returns **1 draft**, ignoring `--num-drafts`.

Working shape: `spiral write "<count> <single-channel> options for <shipped capability>" --instant --num-drafts <count> --json`
Avoid a prompt shape that adds campaign cue words to a single-channel request, because it collapses to one draft.

### (b) To get a real multi-channel set

Phrase the prompt with the multiple channels named. Spiral returns **one set of drafts per channel**, each draft carrying its `channel`. In this mode **`--num-drafts` is ignored** — per-channel counts apply.

Working shape: `spiral write "<announcement context naming each requested channel and the shipped capability>" --instant --json`

This one-call cross-channel set is the ideal fit for `ce-promote` when the user wants to announce across surfaces.

**Spiral picks per-channel counts itself.** In campaign mode the count per channel is Spiral's call, not yours; a request naming multiple channels can return several drafts for each, all tagged with their `channel`. Group the returned `drafts` by `channel` for Phase 4; don't assume one per channel.

## Failure handling

Detection that comes back not-ready routes through Path 0 above. Once on Path A, any of these → fall back to direct drafting (SKILL.md Path B), silently, for the affected channels:

- `spiral write` exits non-zero, hangs, or emits non-JSON
- `drafts` is empty or missing expected fields

Never surface raw Spiral errors to the user as a blocker. The skill always produces drafts.
