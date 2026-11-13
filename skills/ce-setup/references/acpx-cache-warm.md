# Warm the optional compatibility-package npm cache

This optional compatibility-cache operation is not an active OpenCode peer dispatch path. Native peer execution uses `opencode.models` and native subagents/shell with the configured model intent. Retain this cache maintenance only for users who explicitly want the compatibility packages. The version bounds preserve npm's release-age and date-cutoff policies.

Ask once. Explain that this downloads optional compatibility packages into the user's npm cache and runs any declared install scripts. It does not enable native model coverage or authorize another harness dispatcher. Run it only after the user approves; if they decline, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into npx's cache, without starting the package itself, and prints one line per package. Show those lines. This compatibility-only cache operation never participates in native peer availability, review coverage, or active dispatch: neither a successful warm nor a failure changes those judgments, and native peer launch does not attempt npm resolution of these packages. Optional compatibility-package retrieval retains the same npm policy and approval requirement. In the summary, say whether every package was cached, or that the user declined, or which package failed to fetch.
