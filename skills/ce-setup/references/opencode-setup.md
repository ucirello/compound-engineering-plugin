# OpenCode V2 delegation setup

The skills require an effective depth of at least `3` for deep agentic delegation. Installing RocketClaw through Git or npm does not merge its bundled `opencode.json` into the consuming project's configuration.

Tell the user to merge `"experimental": { "subagent_depth": 3 }` into `~/.config/opencode/opencode.json`. Use `opencode debug paths` or `opencode debug paths config` to find the actual global configuration directory and update its existing `opencode.json` or `opencode.jsonc`. Do not replace the file or create a competing JSON/JSONC file. Preserve unrelated settings, sibling `experimental` fields, and any existing integer depth higher than `3`. Restart OpenCode after a change. No higher-precedence source may lower the effective depth below `3`.

Check the consuming workspace, not the plugin's installation directory. From the absolute workspace root, use the authenticated `opencode api get` interface for `/api/config?location[directory]=<URL-encoded workspace root>` (encode the query key as `location%5Bdirectory%5D`). The endpoint returns source entries, not a merged depth result. Inspect each applicable source's `info.experimental.subagent_depth` and apply [OpenCode V2 configuration precedence](https://opencode.ai/v2/docs/config). Do not infer success from one favorable source. If discovery is unavailable, report that depth could not be verified.

Setup reports the required user-level action and never edits OpenCode configuration. If depth is too low or unverified, continue any independent setup work, but do not report deep delegation ready. A non-interactive run puts the action in its summary without asking or modifying host settings.

## Model routing

Project model settings in `.rocketclaw/config.yaml` and `.rocketclaw/config.local.yaml` express the requested model, provider family, effort, policy, and fallback preferences. Use `opencode.models` to resolve those choices, and use OpenCode's native subagents for delegated execution. Legacy harness labels are model-family preferences, not commands to start another harness. Check whether the route is allowed to delegate, whether it can select a different model, and whether nesting capacity remains. Those are separate conditions. Preserve scope, provider approval, and model independence where a skill requires them. Use only the fallback that skill authorizes, and report any unmet coverage, model, or effort requirement rather than silently substituting.
