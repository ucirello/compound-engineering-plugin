# Warm the optional compatibility transport cache

Optional compatibility cache warming resolves acpx within tested version bounds, preserving npm's release-age and date-cutoff policies. It downloads an eligible transport and adapters associated with the newest validated release. This retained cache support is not a dispatch route: all active peer and evaluation work uses native OpenCode model discovery and subagents, without acpx or another harness CLI. An older policy-selected transport can have different adapter packages.

Ask once, saying it downloads a supported acpx version and adapters into the user's npm cache, and npm runs any declared install scripts. This supports legacy compatibility tooling, not native peer dispatch. Run only after approval; if declined, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into npx's cache without starting the package itself, and prints one line per package. Show those lines. A failed warm does not disable native peers. Report Fixed only when every package was cached; otherwise report Skipped, naming any failed package.
