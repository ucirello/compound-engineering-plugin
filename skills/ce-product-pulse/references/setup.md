# First-run setup

Required read on a first run or a `setup`/`reconfigure`/`edit config` run. Key definitions and defaults are in `references/config.md`.

**OpenCode V2 installation prerequisite.** For RocketClaw workflows that use deep delegation, merge `"experimental": { "subagent_depth": 3 }` into the user-level `~/.config/opencode/opencode.json`. Use `opencode debug paths` or `opencode debug paths config` to locate the actual global configuration directory and edit its existing `opencode.json` or `opencode.jsonc`. Preserve unrelated settings, other `experimental` keys, and any integer depth above 3; do not create a competing config file. The bundled package config alone does not enable deep delegation in consuming projects, and higher-precedence config must not lower the effective depth below 3. This interview does not change OpenCode settings.

## Seed from strategy (if available)

Before asking any questions, read the strategy doc with the native file-read tool - `STRATEGY.md`, or when it is absent the first of `VISION.md`, `PRODUCT.md` (in that order) that exists; readers accept the legacy names while other tools converge on `STRATEGY.md`. Every setup and every report resolves the doc this way from current files, so the source never depends on a prior run. If a doc exists, extract:

- The product name from the `name` key in the YAML frontmatter, falling back to the H1 title (stripping the trailing ` Strategy` suffix, e.g., `# Spiral Strategy` -> `Spiral`) if frontmatter is missing. `STRATEGY.md` is the agreed shared project doc and may carry neither, in which case take the name from the README or repository and confirm it in the interview.
- The list of key metrics, one per line, from the section that carries them: `## Key metrics` when `ce-strategy` wrote it, otherwise whichever section of a shared or hand-written file lists the success measures (go by meaning, since headings vary by writer). When `STRATEGY.md` carries no metrics but points to a legacy sibling doc (`VISION.md`, `PRODUCT.md`) for content it defers, read the metrics from there. When no section anywhere carries them, treat them as not yet on file and say so.

Open the interview by surfacing what was extracted: name the doc that was read, show the seeded product name and the list of key metrics that will be carried into event/data setup, and invite the user to correct any of it before continuing.

If none of those docs exists, note that explicitly in chat: no strategy doc on file, running setup from scratch, and mention that `ce-strategy` can seed pulse later if run first.

## Interview

Read `references/interview.md`. This load is non-optional - the pushback rules, anti-pattern examples, and metric-to-source mapping logic live there.

Run the interview in this order:

1. Product name (confirm or edit the seeded value)
2. Primary engagement event
3. Value-realization event
4. Completions or conversions (0-3)
5. Quality scoring (opt-in, AI products only)
6. Data sources - wire up connections for each agreed metric and event. Nudge toward MCP. Reject read-write database access. DB entirely optional.
7. System performance - a short recommended setup for top errors and latency. Users rarely have strong opinions here; present defaults and accept.
8. Default lookback window

Apply the pushback rules in `references/interview.md` for each section. Treat every metric, event, and signal the user proposes against the **SMART bar** (specific, measurable, actionable, relevant, timely) spelled out in `references/interview.md` under "Overall Rules" - push back on anything vague, vanity, or unactionable.

If the user offers read-write database access, refuse and offer the alternatives documented in `references/interview.md` section 6.

## Writing the config

Write the captured config to `<repo-root>/.rocketclaw/config.local.yaml` as flat `pulse_*` keys, using the schema in `references/interview.md` under "Config file shape". Use the absolute workspace root verified with `jj workspace root` in Phase 0. If root discovery failed, complete the interview but ask for the intended JJ workspace before saving settings or a report; do not guess a destination. Before writing, inspect the workspace's applicable `.gitignore` rules for `.rocketclaw/config.local.yaml` without launching Git. If the file is not already covered, offer to add `/.rocketclaw/config.local.yaml` to the root `.gitignore`. If the file or directory does not exist, create `.rocketclaw/` and write the YAML file; otherwise merge new keys into the existing YAML, preserving any non-pulse keys (e.g., `plan_*`) untouched. Show the resulting pulse block to the user in chat and offer one round of edits.

## Scheduling

After the config is written, run the **scheduling recommendation** from `references/interview.md` section 9: offer to set up a recurring run so the user gets the pulse on a cadence instead of having to remember to run it. Accept yes/no/later. Use the OpenCode automation handoff described there; do not schedule inline.

The later-runs re-surface rule lives in `SKILL.md` Phase 3; do not repeat it here.
