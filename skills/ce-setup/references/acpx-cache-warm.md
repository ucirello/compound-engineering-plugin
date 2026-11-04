# Optional compatibility transport cache

Native OpenCode peers use model discovery and native subagents/shell, not acpx or another harness dispatcher. This retained cache utility is only for an independent user request to prepare compatibility packages, never a setup prerequisite or an active skill-dispatch route. It preserves npm's release-age and date-cutoff policies. Warming downloads an eligible transport and the adapters associated with the newest validated release.

Only for that explicit compatibility-cache request, ask once. Explain that this downloads compatibility packages into the user's npm cache and npm runs their declared install scripts; it does not start a peer, affect native OpenCode availability, or grant delegation/model-selection permission. Run it only after approval; if declined, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into npx's cache without starting the package itself and prints one line per package. Show those lines. A failed warm does not affect native peers. In the summary, say whether every package was cached, the user declined, or which package failed to fetch.
