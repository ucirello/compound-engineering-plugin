# Warm the npm cache for cross-model peers

This optional compatibility-cache maintenance downloads packages within tested version bounds, preserving npm's release-age and date-cutoff policies. It is not native peer dispatch, not a prerequisite for OpenCode models, and does not authorize launching another harness. Resolve models with `opencode.models` and dispatch native subagents under the permission/depth rules in SKILL.md.

Ask once. Explain that this downloads optional compatibility packages into the npm cache, not models, and native OpenCode peer dispatch does not need them. Disclose that npm runs package install scripts. Run only after approval; if declined, fetch nothing. All temporary working directories stay under the absolute JJ workspace's `.tmp/`; without one, skip rather than use global temporary storage.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into npx's cache, without starting the package itself, and prints one line per package. Show those lines. A failed warm does not disable peers; their normal launch still attempts resolution under the same npm policy. In the summary, say whether every package was cached, or that the user declined, or which package failed to fetch.
