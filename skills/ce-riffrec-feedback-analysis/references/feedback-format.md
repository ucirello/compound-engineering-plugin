# Feedback Format

Use this shape when converting Riffrec evidence into a durable brainstorm or planning input.

## Finding

```markdown
### <finding-id>. <problem-title>

- **Severity:** <severity>
- **Observed:** <grounded-observation>
- **Expected:** <expected-behavior>
- **Evidence:** <evidence-references>
- **Confidence:** <confidence-and-reason>
- **Requirement candidates:** <requirement-ids>
```

## Requirements Kickoff

```markdown
---
date: <date>
topic: <topic>
---

# <Topic Title>

## Problem Frame

<Who is affected, what is changing, and why it matters.>

---

## Actors

- <actor-id>. <actor-name>: <role-in-recorded-workflow>

---

## Key Flows

- <flow-id>. <flow-name>
  - **Trigger:** <trigger>
  - **Actors:** <actor-ids>
  - **Steps:** <observed-product-steps>
  - **Outcome:** <required-outcome>
  - **Covered by:** <requirement-ids>

---

## Requirements

**Observed product behavior**
- <requirement-id>. <product-behavior-requirement>

**Feedback evidence and reviewability**
- <requirement-id>. <evidence-or-reviewability-requirement>

---

## Acceptance Examples

- <example-id>. **Covers <requirement-ids>.** Given <state>, when <action>, <outcome>.

---

## Success Criteria

- <Human outcome>
- <Downstream agent handoff quality>

---

## Scope Boundaries

- <Deliberate non-goal>

---

## Key Decisions

- <Decision>: <Rationale>

---

## Dependencies / Assumptions

- <Material dependency or assumption>

---

## Outstanding Questions

### Resolve Before Planning

- <Only product questions that block planning>

### Deferred to Planning

- [Technical] <Questions better answered during codebase exploration>

---

## Next Steps

-> Invoke `ce-brainstorm` to confirm, correct, and regroup the captured requirements before any planning.
```

## Evidence Rules

- Prefer moment IDs and screenshot links over prose-only claims.
- Mark visual interpretation as an inference when the screenshot does not prove intent.
- Requirements should describe product behavior, not implementation details.
- Do not include absolute local paths in shared documents; use workspace-relative paths when possible.
