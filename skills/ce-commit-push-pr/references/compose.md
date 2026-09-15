# Composing the title and body: evidence and teaching gates

**You MUST read `references/pr-description-writing.md`** in full. It defines value-first framing, sizing, program altitude (where this PR sits in a multi-PR series), related-work references (preserve existing `Related:` / `Fixes` on rewrite), and the pre-apply audit. The only input it needs from this skill is the PR ref, if the mode selection identified one (description-only with a pasted URL, description update, or a confirmed existing-PR rewrite in the full workflow). If Step 1 (resolve bookmark and PR state) found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body. In Stack mode, Step 5 (apply and report) follows the post-submit description steps in `references/stack-submit.md` instead of composing one default-base body here.

Change descriptions for this skill are composed in Step 3 (`references/commit-and-push.md`), not here. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repo-local syntax. Do not choose commit-message syntax here, and do not re-template a change description already composed from those sources.

**Evidence decision** before composition. RocketClaw has no capture workflow of its own. Use the harness's capture tools or artifacts the user supplied; never invent or upload evidence, and never launch another skill to capture it.

1. **User supplied** (URL, markdown image/embed, local path) — incorporate as `## Demo`, `## Screenshots`, or `## Evidence`.
2. **User asked for evidence but supplied none** — ask for the artifact or tell them to capture with the harness and return.
3. **No material observable claim** (internal plumbing, type-only, pure refactor, inert docs) — skip without asking. Classify by runtime purpose, not extension (runtime agent instructions / config / product content / policy YAML is not auto-skippable as "docs").
4. **Otherwise** (UI, CLI, API, workflow, ranking, deploy/config behavior) — write a concise validation note of what was exercised. If a real run was impossible (credentials, paid services, deploy-only, hardware, missing setup), say so. Do not block PR creation for missing visuals; test or manual-check notes are fine. Never label test output "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the repo root gathered in Context, resolving it with `jj workspace root` if you don't already have it (description-only and description-update modes can skip the Context snapshot). Then apply the ordinary-key rule below.

<!-- ce-config-layers:start -->
**Resolve ordinary RocketClaw yaml keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<repo-root>` = `jj workspace root`). Missing files are skipped. Ignore files do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

Only an **active (non-commented)** `pr_teaching_section:` key counts. Lines starting with `#` are YAML comments, and matching a commented template key would silently flip the decision. Teaching is off only when the winning active value is exactly `false`; a missing key or any other value → default **on**. The same layer order resolves `pr_teaching_archive:`: on only when the winning active value is exactly `true`, else **off**. A per-run `archive:on|off` token overrides it for this invocation.

- Gate **on** — judge novelty and compose per **Step B2** of the reference.
- Gate **off** — compose without concept handling: skip the novelty judgment, the `## New concepts` section, the Step 5 concept trailer and `ce-explain` offer, and archival entirely.

Then continue with the reference (Steps A–E, including Step B2 when the teaching gate is on). Step E must run before the body is returned.
