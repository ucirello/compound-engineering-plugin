# Composing the title and body: evidence and teaching gates

**You MUST read `references/pr-description-writing.md`** in full. It defines value-first framing, sizing, program altitude, related-work preservation and the pre-apply audit. Pass the resolved PR ref so PR mode fetches its exact range and existing body. Stack mode uses Step 5's per-layer post-submit descriptions in `references/stack-submit.md`, not one default-base body. Before message-derived title recommendations follow `commit-message-standards.md`; the repository determines syntax at runtime.

**Evidence decision** before composition. This skill has no capture workflow of its own. Use the harness's capture tools or artifacts the user supplied; never invent or upload evidence, and never launch another skill to capture it.

1. **User supplied** (URL, markdown image/embed, local path) — incorporate as `## Demo`, `## Screenshots`, or `## Evidence`.
2. **User asked for evidence but supplied none** — ask for the artifact or tell them to capture with the harness and return.
3. **No material observable claim** (internal plumbing, type-only, pure refactor, inert docs) — skip without asking. Classify by runtime purpose, not extension (runtime agent instructions / config / product content / policy YAML is not auto-skippable as "docs").
4. **Otherwise** (UI, CLI, API, workflow, ranking, deploy/config behavior) — write a concise validation note of what was exercised. If a real run was impossible (credentials, paid services, deploy-only, hardware, missing setup), say so. Do not block PR creation for missing visuals; test or manual-check notes are fine. Never label test output "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the absolute root gathered in Context, resolving it with `jj workspace root` if absent (description-only/update can skip the Context snapshot). All JJ and scoped GitHub commands still follow Context's cwd/environment rules. Then apply the ordinary-key rule below.

<!-- ce-config-layers:start -->
**Resolve ordinary yaml keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<repo-root>` = absolute `jj workspace root`). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

Only an **active (non-commented)** `pr_teaching_section:` key counts. Lines starting with `#` are YAML comments, and matching a commented template key would silently flip the decision. Teaching is off only when the winning active value is exactly `false`; a missing key or any other value → default **on**. The same layer order resolves `pr_teaching_archive:`: on only when the winning active value is exactly `true`, else **off**. A per-run `archive:on|off` token overrides it for this invocation.

- Gate **on** — judge novelty and compose per **Step B2** of the reference.
- Gate **off** — compose without concept handling: skip the novelty judgment, the `## New concepts` section, the Step 5 concept trailer and `ce-explain` offer, and archival entirely.

Then continue with the reference (Steps A–E, including Step B2 when the teaching gate is on). Step E must run before the body is returned.
