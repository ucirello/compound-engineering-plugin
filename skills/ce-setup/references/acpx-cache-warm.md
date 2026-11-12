# Optional legacy package-cache warming

Apply SKILL.md's mandatory global user OpenCode depth prerequisite first; document it without modifying host configuration. Active review and implementation dispatch uses `opencode.models` and native OpenCode subagents, not acpx or another harness. Retain this consent-gated cache utility only for users explicitly maintaining legacy package consumers; warming is neither a native-dispatch prerequisite nor proof of model availability. Scratch must remain under the target absolute workspace root's `.tmp/rocketclaw/`.

Intentional legacy consumers may resolve acpx within tested version bounds, preserving npm's release-age and date-cutoff policies. This optional support utility downloads an eligible legacy transport and the Codex and Claude adapters associated with the newest validated release. An older policy-selected transport may fetch different adapter packages on its first run. Migrated skills do not use these packages for dispatch.

Offer this utility only when the user explicitly maintains intentional legacy consumers. Ask once. Explain that it downloads now, into the user's npm cache, the transport and adapter packages those legacy consumers would otherwise download on first use. Name acpx only alongside that description. Say that npm runs any install scripts those packages declare, as it would on that first use. State that this does not enable or accelerate migrated skill dispatch, which uses native OpenCode model routes. Run it only after the user approves; if they decline, fetch nothing.

On approval, run the health script with `--warm-acpx` in place of `--version VERSION`, using the same `SKILL_DIR` as Step 2:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-setup SKILL.md>";
bash "$SKILL_DIR/scripts/check-health" --warm-acpx
```

It installs each package into npx's cache, without starting the package itself, and prints one line per package. Show those lines. A failed warm leaves intentional legacy consumers to perform their ordinary package resolution under the same npm policy; native OpenCode dispatch is unaffected. In the summary, say whether every package was cached, or that the user declined, or which package failed to fetch.
