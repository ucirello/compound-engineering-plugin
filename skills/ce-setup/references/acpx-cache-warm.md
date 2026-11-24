# Optional npm cache warming for legacy acpx workflows

This maintenance is only for users who also run legacy acpx workflows. Native OpenCode subagents do not need it; their user-level prerequisite is in `references/opencode-setup.md`. Warming downloads an eligible acpx transport and associated adapters while preserving npm's release-age and date-cutoff policies. An older policy-selected transport may fetch different adapters.

Ask once. Explain that this downloads packages into the user's npm cache now so their legacy acpx workflows usually avoid a first-use download. npm can run the packages' install scripts, just as on first use. Run it only after approval; on decline, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same absolute `working_root` and `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
(cd "$working_root" && bash "$SKILL_DIR/scripts/check-health" --warm-acpx)
```

It stages temporary files under the workspace's `.tmp/`, or local `.tmp/` outside JJ, and downloads each package into npx's cache without starting its CLI. Show the line for each package. A failed warm does not affect native delegation; report what cached, what failed, or that the user declined.
