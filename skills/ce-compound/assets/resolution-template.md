# Resolution Structure

Choose the structure matching the `problem_type` track in `references/schema.yaml`. Frontmatter uses the canonical fields and quoting rules from `references/yaml-schema.md`; use corpus vocabulary rather than fixed sample values.

## Bug Track

After valid frontmatter and a descriptive title, preserve this semantic order:

1. **Problem**: the issue and user-visible impact.
2. **Symptoms**: observable evidence.
3. **What Didn't Work**: attempted approaches and why they failed, when known.
4. **Solution**: the verified fix, using project-native evidence or neutral placeholders only where useful.
5. **Why This Works**: the root cause and the mechanism that addresses it.
6. **Prevention**: a concrete practice, test, or guardrail.
7. **Related Issues**: related durable learnings, issues, or pull requests when present.

## Knowledge Track

After valid frontmatter and a descriptive title, preserve this semantic order:

1. **Context**: the situation, gap, or friction that prompted the guidance.
2. **Guidance**: the practice or recommendation, using project-native evidence or neutral placeholders only where useful.
3. **Why This Matters**: the consequence of following or ignoring the guidance.
4. **When to Apply**: the conditions under which the guidance is relevant.
5. **Evidence**: concrete project-native evidence when it changes understanding; omit when none is needed.
6. **Related**: related durable learnings, issues, or pull requests when present.
