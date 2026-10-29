# Opt-in JJ stack construction and submission

Load only on explicit stack intent or a standing stack preference. An explicit stack request is required intent, not a single PR with a custom base. Do not proactively suggest stacks. A standing preference alone does not justify artificial slices: one logical change stays single-PR. A residual is an unresolved decision/capability returned without guessing.

Use `context.md` for absolute cwd and scoped `gh`. Never run Git-backed workspace/commit/checkout/push helpers, including `gh stack` commands that launch Git. `gh-stack-cli.md` describes the native boundary. Preserve model/configuration intent, but construction itself uses JJ, not another harness dispatcher.

## Probe and topology — before ordinary Step 3

Probe `gh` availability and the repository's supported stacked-PR API/CLI help. A missing required stack capability is a hard residual on required intent; soft intent may report it and use ordinary single-PR creation. Do not silently convert a managed stack into unrelated PRs or declare a linked-only stack locally managed.

Record original workspace change ID, commit ID, bookmark and complete tracked/untracked/ignored state before classification. Resolve named parent PR by explicit number/URL with `gh pr view <ref> --json headRefName,headRefOid,author,baseRefName,headRepositoryOwner`; match the head repository and exact OID with JJ remote bookmarks. Fetch the exact head bookmark when required and verify OID. A same-name local bookmark at a different commit is a residual, never reset it. A standalone branch may be an untouched trunk; adopt an existing parent PR as an owned bottom layer only with proven ownership/authorization.

Inspect authoritative stack topology using supported read-only service metadata; do not infer order from unordered payloads. Preserve managed membership and explicit parent choice. A non-top named parent, ambiguous/shared membership, unavailable stacks, or unproven classification is a residual, not permission to choose the top or create a second stack. Classification must not move working state. If a supported service operation does move it, restore the verified owned starting state safely before construction; never overwrite unrelated work.

For every new upstack layer choose the exact authoritative parent: its freshly verified remote tip when current, otherwise its verified local unpublished tip. Do not hardcode a remote or use the repo default for an upstack layer. Validate externally supplied bookmark names before shell interpolation, or pass them as argv; reject unsafe names rather than expanding shell text.

## Retrospective construction

Inspect the complete original change set: existing commits plus tracked/untracked working changes, minus `exclude:<paths>`. Plan the smallest linear, independently reviewable whole-file layers, foundation first, each coherent against its immediate parent. No hunk splitting to force a stack.

One clearly safe topology is authorized by explicit stack intent. Multiple materially different review boundaries require a concise bottom-to-top decision; pipeline mode returns that proposal as a residual. Hunk partitioning or published-history rewriting requires explicit confirmation; pipeline mode stops instead. Preserve recovery bookmarks at original tips before authorized rearrangement. Never rewrite away others' authorship or human credit.

For a default-bookmark starting point with no named parent, follow `branch-creation.md`, including the unpublished-local-commit decision. For an existing feature, fetch and verify the selected base directly, not that default-bookmark carry flow. A verified local parent materialized from a PR may have no remote bookmark: use its exact verified commit. Never carry the whole original feature tip into the bottom layer by accident.

Read `commit-message-standards.md` before composing **each layer**: full Go guide and several complete JJ descriptions at the actual layer history anchor, local syntax winning. Include an already-known implementation unit ID semantically when unambiguous; no fixed message suffix or template.

For new working-file groups, snapshot/preserve owned work and recovery IDs before rearrangement. Commit only the planned paths using `jj commit -m "<message composed from the standards above>" -- <layer-owned-paths>` when the current parent is correct. Use native `jj new <verified-parent>` and `jj squash --from <owned-source-change> --into <owned-layer-change> -- <layer-owned-paths>` when constructing layers from a preserved owned source, then `jj describe -r <owned-layer-change> -m "<message composed from the standards above>"`. Verify each transfer by diff and ancestry; never move an entire mixed source or excluded work. Create one non-conflicting bookmark at each exact layer tip using `jj bookmark create <layer-name> -r <layer-tip>`. Existing matching commit boundaries can be adopted without rewriting. Stop safely if isolation of owned work cannot be proved.

Excluded files belong to no layer and remain exactly where found: never save, move, restore or commit them. Inspect ignored/untracked content before working-state transitions; a collision is a residual, never a stash/discard workaround. Store any recovery evidence outside the affected change under workspace-local `.tmp/` and keep it until verification.

Before submission verify every layer against its parent, exact bottom-to-top order, complete original intended top-tree outcome, unchanged exclusions, and retained recovery references. No earlier step submits.

## Submit — Step 5 only

Apply the **Project publishing gate** to each exact outgoing state. Resolve teaching archival first: if requested archival has no safe manager-aware route, stop before submission with a residual; never silently disable it or append an unmanaged post-submit commit.

Re-query open PRs per layer using verified head owner/bookmark. Existing drafts stay drafts unless explicitly authorized ready; no bulk-open action that marks someone's WIP ready. Publish exact layer bookmarks with `jj git push --remote <verified-head-remote> --bookmark <layer-bookmark>` (new bookmarks require authorized `--allow-new`). Verify remote OIDs.

Create missing PRs bottom-to-top with scoped `gh pr create --base <verified-parent-bookmark> --head <layer-bookmark> --title <composed-title> --body-file <local-body-file>`; explicit base repository/head-owner resolution follows Context. Compose each body for its immediate parent and exact head using `pr-description-writing.md`, not one default-base range. Existing PRs retain title/body absent approved rewrite or already-authorized factual babysit maintenance. Update existing base relationships only when the verified topology and request authorize it.

For JJ-managed bookmarks, inspect `gh stack link --help` for the supported service-side external-stack link operation. Supply explicit verified PR URLs/numbers and parent relationships using that help's argument contract; never launch a bare interactive/TUI command or invent flags. Linking is service-side membership, not local manager tracking. If supported help cannot prove the exact registration/membership semantics without Git execution, retain the published state and report incomplete stack registration, never claim a managed submit or begin manager-only landing. Do not substitute another parent or external harness. Re-read service topology and per-PR heads after registration.

Map every created PR to explicit URL, bookmark, parent and head. A draft-only result is a hard residual before babysit when enabled, not successful shipped-stack completion. Optional rewrite refusal keeps descriptions and does not block otherwise authorized monitoring.

Hand off the bottom open non-draft PR only after verified stack submission, with `posture:stack-ready` by default or `posture:stack-land` only on explicit land intent; pipeline submissions pass stack-wide scope. Never `gh pr merge` an individual managed member. `ce-babysit-pr` owns supported stack landing and genuine final-merge decisions. If its manager contract cannot consume the external JJ stack, return that coverage/handoff blocker rather than inventing a merge/watch route.
