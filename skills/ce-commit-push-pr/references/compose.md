# Composing the title and body: evidence and teaching gates

**You MUST read `references/pr-description-writing.md`** in full. It defines value-first framing, sizing, program altitude, related references, and the pre-apply audit. Pass the verified PR URL when one exists so PR mode fetches the existing body. Stack mode composes each layer against its immediate parent. Before composing any message or title that recommends commit syntax, read and follow the full runtime standards and labeled source excerpts in `references/commit-and-push.md`; repository-local syntax is authoritative.

**Evidence decision** before composition. Use artifacts the user or caller supplied, and take screenshots yourself only as `references/visual-evidence.md` describes. Never invent evidence, and never launch another skill to capture it.

1. **User or caller supplied** (URL, markdown image/embed, local path) — incorporate as `## Demo`, `## Screenshots`, or `## Evidence`, and take no screenshots of what it already shows. A supplied screenshot of the UI without this change is different: it is the before image for item 4, not finished evidence.
2. **User asked for evidence but supplied none** — for screenshots of UI, go to item 4. For anything else (a recording, a demo), ask for the artifact or tell them to capture it with the harness and return.
3. **No material observable claim** (internal plumbing, type-only, pure refactor, inert docs) — skip without asking. Classify by runtime purpose, not extension (runtime agent instructions / config / product content / policy YAML is not auto-skippable as "docs").
4. **Material visual claim** (rendered UI a reviewer would judge faster or more correctly by seeing it), or the user asked for screenshots — read `references/visual-evidence.md` now and follow it. When it cannot capture, it falls back to item 5's note.
5. **Otherwise** (CLI, API, workflow, ranking, deploy/config behavior) — write a concise validation note of what was exercised. If a real run was impossible (credentials, paid services, deploy-only, hardware, missing setup), say so. Do not block PR creation for missing visuals; test or manual-check notes are fine. Never label test output "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the absolute root from `jj workspace root`, including in description-only/update modes. Apply the ordinary-key rule below.

<!-- ce-config-layers:start -->
**Resolve ordinary yaml keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<repo-root>` = `jj workspace root`). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

Only an **active (non-commented)** `pr_teaching_section:` key counts. Lines starting with `#` are YAML comments, and matching a commented template key would silently flip the decision. Teaching is off only when the winning active value is exactly `false`; a missing key or any other value → default **on**. The same layer order resolves `pr_teaching_archive:`: on only when the winning active value is exactly `true`, else **off**. A per-run `archive:on|off` token overrides it for this invocation.

- Gate **on** — judge novelty and compose per **Step B2** of the reference.
- Gate **off** — compose without concept handling: skip the novelty judgment, the `## New concepts` section, the Step 5 concept trailer and `ce-explain` offer, and archival entirely.

Do not add creator, skill, model, or harness branding or attribution.

## Message composition source guidance

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing a message or recommending message syntax, read the full Go guide at runtime and compare several full recent subjects and bodies with `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'` from the absolute target root. Resolve that head from the actual task, not a fixed default or a replacement for the reviewed range. Compare prefix/package, casing, tense, separation, wrapping and issue placement. Local project instructions and observed syntax always win; apply only compatible Go quality guidance. Without history use explicit instructions and Go guidance without inventing precedent.

Verbatim Go source example and guidance — illustrative, **not** a mandatory repository template:

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

Then continue with the reference (Steps A–E, including Step B2 when the teaching gate is on). Step E must run before the body is returned.
