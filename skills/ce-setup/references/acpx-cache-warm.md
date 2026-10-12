# Optional compatibility adapter cache warmup

Active peers use configuration-authoritative OpenCode model discovery and native subagents/shell, not acpx. This optional compatibility support warms the pinned acpx and codex/claude adapter npm cache without launching a dispatcher. It is not a prerequisite or fallback for native reviews. Warming downloads packages over the network; preserve the approval gate below.

Ask once, saying it downloads the pinned acpx and its adapters from the npm registry into the user's npm cache, and that npm runs any install scripts those packages declare, as a legacy adapter run would. Run it only after the user approves; if they decline, fetch nothing. Keep temporary work under the target workspace's `.tmp/`, or cwd-local `.tmp/` outside a JJ repository.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into npx's cache, without starting the package itself, and prints one line per package. Show those lines. A package that could not be fetched leaves peers working; that peer run downloads it instead. Report the warm under Fixed when every package was cached, and under Skipped when the user declined or a fetch failed, naming the package.
