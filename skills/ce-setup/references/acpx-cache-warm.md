# Optional npm cache maintenance

Retain this mechanical cache helper for users who maintain the optional transport packages. It preserves the supported acpx version bounds, adapter specs, and npm release-age/date-cutoff policies. It is not a native OpenCode dispatch route: reviewers and implementation agents use native model discovery and subagents, never these CLIs. Warming downloads an eligible transport and the adapters associated with the newest validated release.

Ask once, saying it downloads a supported acpx version and its adapters from the npm registry into the user's npm cache, and that npm runs any install scripts those packages declare, as a first peer run would. Run it only after the user approves; if they decline, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

Run from the absolute target JJ workspace root. The helper creates temporary working directories only under that workspace's `.tmp/rocketclaw/`, including cleanup on failure. It installs each package into npx's cache, without starting the package itself, and prints one line per package. Show those lines. A failed warm has no effect on native dispatch. Report the warm under Fixed when every package was cached, and under Skipped when the user declined or a fetch failed, naming the package.
