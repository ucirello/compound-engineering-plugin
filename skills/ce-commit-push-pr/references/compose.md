# Composing the title and body

Read `references/pr-description-writing.md` in full. It owns value-first framing, sizing, program altitude, related references, project-required metadata, and pre-apply audit. Pass any resolved PR URL so rewrite mode can preserve its body. Stack mode uses `references/stack-submit.md` after submission.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win for change descriptions. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe any fixed syntax or example. Project PR conventions remain authoritative for PR titles and bodies.

## Evidence

Use user-supplied artifacts or available capture interfaces; never invent or upload evidence.

1. Incorporate supplied evidence under an appropriate heading.
2. If evidence was requested but omitted, ask for it or ask the user to capture it.
3. Skip when there is no observable claim, judged by runtime purpose rather than extension.
4. Otherwise state concise validation and any reason a real run was impossible. Tests are not screenshots or demos.

## Teaching

Use the workspace root from `jj root`. Resolve ordinary workflow keys from `<jj-root>/.rocketclaw/config.local.yaml`, then `config.yaml`; first active valid value wins, and a present list or map replaces the whole value. `docs_root` does not use this cascade.

Only active `pr_teaching_section:` and `pr_teaching_archive:` keys count. Teaching defaults on; archive defaults off; `archive:on|off` overrides this run. When teaching is on, use Step B2 of the writing reference.

## Metadata

Include only metadata required by the project's PR contract. Do not add generated provenance, promotional marks, product identity, or tool attribution. Remove such generated material on rewrite unless the project contract requires the exact field.

Continue through Steps A-E of the writing reference. Step E runs before returning the body.
