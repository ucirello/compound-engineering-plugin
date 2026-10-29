# Warm the optional compatibility npm cache

Native peers use `opencode.models` and `subagents`, not acpx or another harness dispatcher. This retained optional compatibility-cache operation downloads acpx within tested version bounds, preserving npm's release-age and date-cutoff policies, and the adapters associated with the newest validated release. It does not dispatch peers or prove native model availability.

Ask once, saying it downloads a supported acpx version and its adapters from the npm registry into the user's npm cache, and that npm runs any install scripts those packages declare, as a first peer run would. Run it only after the user approves; if they decline, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into a workspace-local `.tmp/` npm cache, without starting the package itself, and prints one line per package. Show those lines. A failed warm does not disable native peers. Report the warm under Fixed when every package was cached, and under Skipped when the user declined or a fetch failed, naming the package. Do not run a compatibility dispatcher as recovery.
