# Warm the npm cache for cross-model peers

This optional compatibility operation fetches pinned acpx and its codex and claude adapters into the user's npm cache. Active peer and implementation routes resolve configured model choices with `opencode.models` and execute through permitted OpenCode-native subagents/shell; they never dispatch through these adapters. Keep this cache support only for users who intentionally use the compatibility packages outside those active routes. Temporary working directories belong under the absolute workspace root's `.tmp/`, or local `.tmp/` outside a JJ repository, with no OS-global fallback.

Ask once, saying it downloads the pinned acpx and its adapters from the npm registry into the user's npm cache, and that npm runs any install scripts those packages declare. Run it only after the user approves; if they decline, fetch nothing. Warming does not launch a peer or validate an active native route.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into npx's cache, without starting the package itself, and prints one line per package. Show those lines. A package that could not be fetched leaves peers working; that peer run downloads it instead. Report the warm under Fixed when every package was cached, and under Skipped when the user declined or a fetch failed, naming the package.
