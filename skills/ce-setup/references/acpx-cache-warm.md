# Optional legacy adapter cache compatibility

This is a cache helper only, not a reviewer or model dispatcher. Native OpenCode model discovery and subagents are the active routes; this optional warm does not enable independent coverage. All downloads remain in workspace-local `.tmp`, never the global npm cache.

# Warm the npm cache for cross-model peers

Cross-model peers resolve acpx within tested version bounds, preserving npm's release-age and date-cutoff policies. Warming downloads an eligible transport and the adapters associated with the newest validated release. An older policy-selected transport may fetch different adapter packages on its first run.

Ask once, saying it downloads a supported acpx version and its adapters from the npm registry into the workspace-local npm cache, and that npm runs any install scripts those packages declare, as a first peer run would. Run it only after the user approves; if they decline, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into workspace-local npx cache, without starting the package itself, and prints one line per package. Show those lines. A failed warm does not disable peers; their normal launch still attempts resolution under the same npm policy. Report the warm under Fixed when every package was cached, and under Skipped when the user declined or a fetch failed, naming the package.
