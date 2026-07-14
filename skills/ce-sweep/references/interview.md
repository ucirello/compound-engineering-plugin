# Sweep First-Run Interview

Loaded by `SKILL.md` when `/ce-sweep` runs with no `feedback_sources` configured. Captures the setup that will be merged into `<repo-root>/.rocketclaw/config.local.yaml` (the unified RocketClaw local config, ignored and machine-local) and re-read on every subsequent run.

This interview is **interactive only**. The caller refuses first-run setup in headless mode — a scheduled or piped run with no config aborts and tells the user to run `/ce-sweep` interactively once. Do not attempt to infer sources, actions, or approvals without asking.

## Interaction Method

Ask **one question at a time** using the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to numbered options in chat only when no blocking tool exists in the harness or the call errors — never silently skip a question or assume a default without surfacing it.

## Overall Rules

1. **One source at a time, fully.** Sections 1-3 form a per-source loop: for each source, capture its identity, its acknowledgment actions plus standing approval, and its sensitivity flag before moving to the next source. Do not batch these across sources — a user answering "approve writes" needs to know *which* source they are approving.
2. **Standing approval is consent, captured verbatim.** Section 2's approval question authorizes source-side writes (Slack reactions, GitHub labels) on every future run with no per-run confirmation. Record the literal yes/no. A "no" is not a failure — it leaves that source read-only.
3. **Defaults are shown, not silently applied.** Every question with a default states the default in the question. The user accepts or overrides; you never pick for them.
4. **Capture in the user's own terms.** Config ids, emoji names, and label names are read by the whole team and used verbatim by the connectors — record exactly what the user gives.

---

## 1. Sources (repeatable loop)

**Opening framing:** "Let's wire up the feedback sources this sweep will watch. We'll add them one at a time — you can add as many as you want."

For each source, ask two things:

1. **Source type** — one of:
   - `slack` — a Slack channel
   - `github-issues` — a GitHub repository's issues
   - `email-experimental` — an email account/folder (experimental; stored in config as `type: email`)
2. **Identity** — depends on the type:
   - Slack: the **channel ID** (e.g. `C0XXXXXXX`, not the `#name`). Stored as `target`.
   - GitHub: the repo as `owner/repo`. Stored as `target`.
   - Email: the account plus a folder/label hint (e.g. `feedback@acme.com / Inbox`). Stored as `target`.

Then assign the source a **short config id** — a stable, lowercase, hyphenated handle the state file and reports use to name this source (e.g. `slack-alpha`, `gh-issues`). Suggest one derived from the type, let the user override. Ids must be unique within `feedback_sources`.

After each source's actions and sensitivity are captured (sections 2-3), ask: **"Add another source?"** Loop until the user is done. At least one source is required to proceed.

**Capture per source:** `type` (`slack` | `github-issues` | `email`), `id` (short handle), `target` (channel ID / `owner/repo` / mailbox hint).

---

## 2. Acknowledgment actions + standing approval (per source)

Every source carries two source-side actions the sweep can perform, plus a standing approval that governs whether it may perform them unattended.

**Ask the acknowledgment action** — what the sweep does to mark an item *seen* on its source:

- Slack: an **emoji reaction** name. Default `eyes`.
- GitHub: a **label** to apply. Default `feedback:ack`.
- Email: none. Email items are tracked only in state; there is no source-side ack. Skip this question for email sources and note that.

**Ask the close-out action** — what the sweep does to mark an item *resolved* on its source:

- Slack: an emoji reaction. Default `white_check_mark`.
- GitHub: a label. Default `feedback:resolved`.
- Email: none — email items stay state-tracked only; explain there is no source-side close-out.

**Then ask the standing-approval question, verbatim:**

> "Do you approve the sweep performing these actions — applying the acknowledgment and close-out `{{action names}}` on `{{source id}}` — on **every future run, without asking you again each time**? Yes authorizes source-side writes for this source going forward. No keeps this source read-only: the sweep ingests and triages items but never touches the source, and items land as `ack_deferred` for you to action manually."

Record the literal answer:

- **Yes** -> `approved: true`. The sweep may apply the ack and close-out actions on this source unattended.
- **No** -> `approved: false`. The source is read-only; its items are tracked as `ack_deferred` and no reaction/label is ever written.

For email sources there are no source-side actions, so approval is moot — record `approved: false` and note the source is inherently read-only.

**Capture per source:** `ack_action` (emoji/label name, or omit for email), `closeout_action` (emoji/label name, or omit for email), `approved` (`true` | `false`).

---

## 3. Sensitive flag (per source)

**Ask:** "Should item content from `{{source id}}` be withheld from tracked state and from plan text? Say yes when the source can carry screen recordings, PII, customer data, or anything you don't want written to a file that may be included in a JJ change or shared. When yes, the sweep drops item body and quote before writing state — only titles, urls, ids, and status persist. Default is no."

- **No** (default) -> `sensitive: false`. Full item content is retained in state and available to plans.
- **Yes** -> `sensitive: true`. The state engine drops `body` and `quote` at write time for this source's items, and plans reference items by id/title/url only.

**Capture per source:** `sensitive` (`true` | `false`).

---

## 4. State location

Ask where the sweep's state file lives:

- **Tracked in the repo** (recommended when multiple agents or machines share bookmarks — one source of truth everyone reads and writes). Sets `sweep_state_path` to the tracked default `docs/feedback-sweep/state.yml`.
- **Machine-local under the workspace scratch directory** (solo setups; keeps sweep bookkeeping out of JJ changes). Sets `sweep_state_path` to `<repo-root>/.tmp/rocketclaw/ce-sweep/<repo-slug>/state.yml`, or `./.tmp/rocketclaw/ce-sweep/<repo-slug>/state.yml` when `jj workspace root` fails. Create the parent directory before the first state-engine call.

Let the user override the path if they want a different location. If they pick machine-local, note that a fresh workspace or a teammate's machine will not see this state — it is per-machine by design.

**Capture:** `sweep_state_path` (string).

---

## 5. Acknowledgment cap

**Ask:** "What's the most acknowledgments the sweep may perform on a single source in one run before it pauses? This is a circuit breaker against a runaway sweep spamming a channel or issue tracker. When the cap is hit, an interactive run pauses and asks you; a headless run stops acknowledging and defers the rest. Default is 25."

**Capture:** `sweep_ack_cap` (integer, default 25).

---

## 6. Shared bookmark (only if tracked state)

**Skip this section entirely if the user chose machine-local state in section 4** — the shared-bookmark topology only applies to tracked state.

**Ask:** "Is this a multi-agent setup where several workspaces push the sweep state to a shared docs bookmark? Answer yes only if more than one machine or AI Assistant describes changes and pushes the same bookmark. Default is no — a single workspace recording changes locally."

- **No** (default) -> `sweep_shared_bookmark: false`. The single-writer lease serializes overlapping sweeps within one workspace.
- **Yes** -> `sweep_shared_bookmark: true`. Explain: the lease becomes **push-gated** — before any source-side write, the sweep isolates and describes the lease-acquisition change, moves the shared bookmark, pushes it with `jj git push`, and confirms its writer won, making the lease a repo-wide mutex across machines. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local instructions and `git log` syntax always win; apply compatible Go quality guidance, and derive the message dynamically from the change's purpose and content rather than imposing any fixed prefix, type, scope, subject, template, or example.

**Capture:** `sweep_shared_bookmark` (`true` | `false`).

---

## 7. Legacy import (optional)

Offer to seed state from an existing legacy feedback-tracking file so prior work is not re-ingested and already-acknowledged items are not acknowledged again.

**Ask:** "Do you have an existing feedback state file to import — for example a prior dogfood tracker like `docs/dogfood-reports/cora-v2-alpha-feedback-state.yml`? Importing carries over its cursors and items so the first sweep skips what's already been processed. Skip if this is a clean start."

- **No / skip** -> proceed to section 8.
- **Yes** -> ask for the file path. Then build a `--source-map`: for each legacy channel/source id in the file, pair it with the configured source id from section 1 (the short name the live connector reads by), as a JSON object like `{"C0AQLMQBGBD":"slack-alpha"}`. This is load-bearing — without it, an imported `C0AQLMQBGBD` cursor lands under `C0AQLMQBGBD` while the connector reads under `slack-alpha`, orphaning the cursor and re-ingesting everything on the first sweep. Run the import from **this skill's directory**; set `SKILL_DIR` inline to the absolute path of the directory containing the `SKILL.md` you loaded:

  ```bash
  SKILL_DIR="<absolute path of this skill's directory>"
  python3 "$SKILL_DIR/scripts/sweep-state.py" import-legacy --state <sweep_state_path> --file <legacy-path> --source-map '{"<legacy-id>":"<config-source-id>"}'
  ```

  where `<sweep_state_path>` is the value captured in section 4 and `<legacy-path>` is the file the user named. Omit `--source-map` only when the legacy ids already equal the configured source ids. Report the `cursors_imported` and `items_imported` counts the command returns. The import is additive and best-effort: it maps what matches known shapes and skips the rest. It does **not** re-ingest source content and does **not** re-acknowledge imported items — mapped cursors carry forward so already-processed items stay processed.

---

## 8. Write config

Merge the captured settings into `<repo-root>/.rocketclaw/config.local.yaml`. Resolve the repo root with `jj workspace root`; if it fails because the current directory is not a JJ workspace, use the current directory.

- If the directory or file does not exist, create `.rocketclaw/` and write the file.
- If the file exists, merge the sweep keys into the existing YAML, **preserving every unrelated key untouched** (e.g. `work_delegate_*`, `pulse_*`, `plan_*`). Only add or update the sweep keys.
- Do not edit `.gitignore`; the orchestrator owns ignore configuration. If `.rocketclaw/config.local.yaml` is not ignored, report that condition before writing.

Write these keys (see "Config File Shape" below for the exact form):

- `feedback_sources` — the list of source maps assembled across sections 1-3.
- `sweep_state_path` — from section 4.
- `sweep_ack_cap` — from section 5.
- `sweep_shared_bookmark` — from section 6 (default `false`; only meaningful with tracked state).

Then surface the resulting Sweep section to the user in chat and offer **one round of edits**.

---

## 9. Schedule offer

**Ask:** "Want the sweep to run on a recurring schedule so feedback gets triaged automatically, or run it on demand? On-demand works fully without a schedule."

- **On demand** -> nothing to register. Note that `/ce-sweep` is ready to run any time.
- **Recurring** -> hand off to whichever scheduling primitive the harness exposes — the in-plugin `schedule` skill if it is installed, otherwise name the platform-native mechanism (cron, GitHub Actions, the host's own automation) and emit a brief hint of what would need to run. **The registered invocation must include `mode:headless`** — e.g. `/ce-sweep mode:headless` — so the scheduled run knows it is unattended and defers instead of prompting. Never schedule inline; always hand off to the scheduling primitive.

Declining a schedule leaves on-demand use fully working.

**End the interview:** tell the user setup is complete and the first sweep can run now with `/ce-sweep`.

---

## Config File Shape

After the interview completes, merge these flat keys into `<repo-root>/.rocketclaw/config.local.yaml`, preserving any unrelated keys already present.

~~~yaml
# --- Sweep (ce-sweep) ---

feedback_sources:
  - { type: slack, id: slack-alpha, target: C0XXXXXXX, ack_action: eyes, closeout_action: white_check_mark, sensitive: false, approved: true }
  - { type: github-issues, id: gh-issues, target: owner/repo, ack_action: "feedback:ack", closeout_action: "feedback:resolved", sensitive: false, approved: true }

sweep_state_path: docs/feedback-sweep/state.yml   # tracked (multi-agent) or workspace .tmp path (solo)
sweep_ack_cap: 25                                 # max acks per source per run before the circuit breaker
sweep_lease_ttl_minutes: 60                       # single-writer lease staleness threshold; not asked interactively, tunable here
sweep_shared_bookmark: false                      # true: push-gated lease for shared-docs bookmark topology
~~~

Notes:

- Each `feedback_sources` entry carries: `type` (`slack` | `github-issues` | `email`), `id` (short handle), `target` (channel ID / `owner/repo` / mailbox hint), `ack_action` and `closeout_action` (emoji/label names; omit both for email), `sensitive` (`true` withholds body/quote from tracked state and plan text), and `approved` (standing approval for source-side writes; `false` keeps the source read-only with `ack_deferred` items).
- `feedback_sources` is a generic key — other skills may read this list.
- `sweep_lease_ttl_minutes` is not asked in the interview; it is written with its default of `60` and left as a tunable the user can edit.
- Email sources are read-only: omit `ack_action`/`closeout_action`, and record `approved: false`.
