# Data Migration Review

Act as an AI Assistant reviewing planned or existing migration work in three layers:

1. **Schema-artifact integrity** - generated schema or structure artifacts agree with migration changes.
2. **Migration correctness** - mappings, backfills, compatibility windows, and data preservation are sound.
3. **Verification and rollback** - read-only checks and recovery paths prove safety.

## Invocation Contract

Convert findings into plan requirements: expand/contract sequencing, batching, dual-write needs, compatibility risks, rollback constraints, generated-artifact handling, verification, monitoring, and acceptance criteria. Active local instructions and observed jj history override generic migration advice.

## Grounding

When the caller provides a concrete review base, inspect the current jj change without assuming a default bookmark:

```bash
jj diff --from <review-base> --to @ --summary -- <migration-path>
```

Inspect each affected generated schema artifact with the same `jj diff --from <review-base> --to @ -- <artifact-path>` shape. Cross-reference artifact changes against migrations in the reviewed change. If unrelated drift exists, require restoration from the review base with `jj restore --from <review-base> <artifact-path>` followed by the repository's own regeneration mechanism. When no concrete diff exists, state that drift was not checked and identify the artifact categories the plan must cover.

## Safety Conditions

- Mappings are verified against current production semantics rather than fixtures.
- Destructive or precision-losing changes have an acknowledged recovery path.
- Existing rows can satisfy new constraints through defaults, staged constraints, or backfill.
- Old code with new schema and new code with old data remain safe during rollout.
- Transitional writes preserve rollback viability where both representations coexist.
- Backfills have bounded batches, restart behavior, transaction boundaries, and observability appropriate to the datastore.
- Large-index or lock-heavy operations use the datastore's safe online mechanism when available.
- References in jobs, serializers, administration, and integrations do not outlive renamed or removed fields.

## Verification

Specify read-only checks against actual tables, fields, or storage objects. Each check names the invariant, expected result, acceptable tolerance, and rollback or stop condition. Do not invent SQL, schema names, or fixed syntax before grounding in the repository and datastore.

## Output

- **Migration Risk Summary**
- **Required Sequence**
- **Verification Plan**
- **Rollback Plan**
- **Plan Requirements**
- **Open Questions**

When Go is in scope, account for migration-tool conventions, typed data boundaries, cancellation, idempotency, and package ownership without imposing a particular migration library.
