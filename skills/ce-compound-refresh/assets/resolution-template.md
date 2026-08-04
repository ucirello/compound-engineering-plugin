# Resolution Document Contract

Select the track from `problem_type` using `references/schema.yaml`. This file
defines semantic content, not fixed Markdown syntax. Preserve any compatible
repository-local heading, ordering, and prose conventions; where none exist,
use the smallest readable structure that covers the applicable requirements.

## Shared Frontmatter

Populate the fields required by `references/schema.yaml` with evidence from the
investigation. Add optional fields only when they improve retrieval or capture
materially useful scope. Apply the array-scalar safety rules in
`references/yaml-schema.md`; do not copy placeholder values or invent enums.

## Bug Track

Use for defect and failure problem types declared in the schema. The body must
let a future maintainer recover:

- the observed problem and user-visible impact
- concrete symptoms or errors
- attempted approaches when they explain a meaningful dead end
- the verified solution, with code only when it materially aids reuse
- the root cause and why the solution addresses it
- prevention through a concrete practice, test, or guardrail
- related durable references when they add context

Choose labels and ordering that fit the repository while keeping the causal
path from symptom through solution easy to follow.

## Knowledge Track

Use for guidance, convention, decision, workflow, and documentation problem
types declared in the schema. The body must let a future maintainer recover:

- the situation, gap, or friction that prompted the guidance
- the evidence-backed practice, pattern, or recommendation
- why following or ignoring it matters
- the conditions under which it applies
- concrete usage or contrast only when it improves understanding
- related durable references when they add context

Choose labels and ordering that fit the repository. Do not force bug-oriented
sections onto knowledge guidance, and do not add empty sections merely to
resemble a template.
