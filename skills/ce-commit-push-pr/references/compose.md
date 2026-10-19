# Compose: evidence and teaching decisions

Read `references/pr-description-writing.md` in full. Pass the explicit PR URL for an existing PR so its body and exact range are fetched; stack PRs use their own immediate parent, never one default-base description.

## Evidence

Use harness capture tools or supplied artifacts; never invent/upload evidence or launch another skill to capture it.

1. Supplied URL, image/embed or path: incorporate under Demo, Screenshots or Evidence as appropriate.
2. Evidence requested but absent: ask for the artifact or explain how to return captured evidence.
3. No material observable claim (internal plumbing, type-only, pure refactor, inert docs): skip. Classify runtime purpose, not extension; runtime instructions/config/policy are not automatically inert docs.
4. Otherwise provide concise factual validation and limits. Missing credentials, services, deployment, hardware or setup must be stated. Missing visuals do not block PR creation; never label test output Demo or Screenshots.

## Teaching gate

Resolve repo root with `jj workspace root`. Read `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml`. Missing files skip. First active non-commented value wins: empty/invalid scalars continue to next layer/default; present lists/maps replace the whole key, even empty. `docs_root` is config.yaml-only.

`pr_teaching_section` defaults on and is off only for exactly `false`. `pr_teaching_archive` defaults off and is on only for exactly `true`; per-run `archive:on|off` overrides it. When teaching is on, follow Step B2 of the description reference. When off, skip novelty judgment, New concepts, concept trailer, ce-explain offer, and archival. When archival is on, Step 5 resolves the artifact root and confirms the applicable apply intent.

Continue through the description reference's pre-apply audit. Do not add attribution badges, generated-by footers or branded creator identities.
