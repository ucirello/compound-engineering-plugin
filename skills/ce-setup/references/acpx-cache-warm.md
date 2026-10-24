# Warm the npm cache for cross-model peers

This optional cache-maintenance capability retains pinned acpx and adapter packages for users' intentional compatibility workflows. Current skill peer/model dispatch uses `opencode.models` and OpenCode-native subagents/shell, never acpx or another harness's dispatcher. Warming only fetches these packages into npm's cache; it is not a prerequisite or evidence of native review readiness.

Ask once, saying it downloads the pinned acpx and its adapters from the npm registry into the user's npm cache, and that npm runs any install scripts those packages declare, as a first peer run would. Run it only after the user approves; if they decline, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into npx's cache, without starting the package itself, and prints one line per package. Show those lines. A package that could not be fetched leaves peers working; that peer run downloads it instead. Report the warm under Fixed when every package was cached, and under Skipped when the user declined or a fetch failed, naming the package.
