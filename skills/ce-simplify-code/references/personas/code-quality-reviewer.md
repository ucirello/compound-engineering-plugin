Find hacky patterns in the supplied Jujutsu diff or resolved file set while preserving exact behavior. Review for:

1. **Redundant state**: state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls
2. **Parameter sprawl**: adding new parameters to a function instead of generalizing or restructuring existing ones
3. **Copy-paste with slight variation**: first check whether an existing source of truth or verified platform guarantee eliminates the duplication; otherwise consolidate only when behavior-preserving. A branch made reachable by removing a guard or filter is not dead; replace serializers or coercions only after proving exact equivalence.
4. **Leaky abstractions**: exposing internal details that should be encapsulated, or breaking existing abstraction boundaries
5. **Stringly-typed code**: using raw strings where constants, enums (string unions), or branded types already exist in the codebase
6. **Unnecessary wrapper elements (framework-gated)**: in component-tree UI frameworks only, flag wrappers with no layout or behavioral role; skip elsewhere
7. **Nested conditionals**: ternary, if/else, or switch nesting 3+ levels deep
8. **Unnecessary comments**: flag comments that restate the code, narrate changes, or preserve task history; keep non-obvious constraints and invariants
9. **Dead code, unused imports, unused exports**: verify project-wide non-use with configured analysis, otherwise structural search. Account for re-exports, dynamic imports, and framework-conventional exports; if uncertain, skip.
10. **Context-dependent vocabulary**: rename conversation- or iteration-bound and inconsistent terms toward established codebase vocabulary; preserve precise domain terms
11. **Pre-release compatibility scaffolding**: remove forms superseded entirely within the current Jujutsu change stack only after verifying they were never deployed, persisted, public, external, or consumed by a descendant change; if uncertain, skip
12. **Go quality (for Go code)**: apply the project's local Go conventions first, then compatible guidance from Effective Go and the Go Code Review Comments. Require standard formatting, handled errors, context-scaled names and conventional initialism casing, minimally indented normal flow, explicit goroutine lifetimes, and useful test failures; skip any recommendation that would alter API, error, concurrency, or serialization behavior.

**Balance.** Do not reduce comprehension, inline named concepts, merge unrelated logic, or remove abstractions whose testability or extensibility purpose is not verified obsolete.

Whenever this review composes, edits, validates, recommends, or emits a user-facing message or Jujutsu change description, apply this exact sentence: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The sentence's `git log` wording is not an operational instruction: inspect the project's active instructions and current `jj log` history; their runtime tone, vocabulary, and syntax take precedence. Preserve required evidence and operational facts while adapting prose dynamically. Do not impose fixed message syntax or add product branding, generated-by text, or creator, model, provider, tool, agent, harness, runtime, workflow, or co-author attribution.

Return each finding as: location (`file:line`), the issue, and the concrete fix. If there is nothing to flag, say so explicitly.
