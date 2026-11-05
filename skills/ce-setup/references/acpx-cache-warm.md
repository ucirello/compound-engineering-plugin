# Warm the npm cache for cross-model peers

This is optional legacy transport cache maintenance for an explicit user request, not a native peer route or installation prerequisite. Native peers use `opencode.models` and permitted subagents under SKILL.md's permission, model, depth and coverage rules. Never dispatch through acpx or another harness. Preserve version bounds and npm's release-age/date-cutoff policies: warming downloads an eligible transport and its adapters without starting their CLIs.

For an explicit legacy-cache request, confirm once. Explain that this downloads legacy transport and adapter packages into the user's npm cache; it does not enable or verify native model routes. Say too that npm runs any install scripts those packages declare. Name a package such as acpx only alongside that description. Run it only after the user approves; if they decline, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into npx's cache, without starting the package itself, and prints one line per package. Show those lines. A failed warm does not disable peers; their normal launch still attempts resolution under the same npm policy. In the summary, say whether every package was cached, or that the user declined, or which package failed to fetch.
