# Applying the PR, reporting, and handoff

**Description-only** prints the title and body and stops unless apply was requested.

**New PR** repeats the matching PR query immediately before creation. A matching owner/bookmark switches to the existing path, exit-0 `[]` permits creation, and non-zero blocks until auth or connectivity is resolved. Stack mode submits through `references/stack-submit.md`.

**Existing PR** reports the URL and asks whether to rewrite, except where pipeline defaults say no. Preview any material title/body change; identical content is not edited, and metadata-only cleanup does not create apply intent.

## Explainer Archival

Archive only in full workflow when enabled, a `## New concepts` section exists, and apply is confirmed. Write one file per concept under `<jj-root>/.context/explainers/`. Verify the path is not ignored under workspace ignore rules before writing.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax.

Describe only the explainer files, move the feature bookmark to the described revision, and push it. Build each blob URL for the actual host and bookmark. If write, description, or push fails, warn and continue without the link.

## Concept Trailer

When this run applied a body containing new concepts, report their names after the PR URL. In interactive full workflow, render one user-runnable `ce-explain` invocation per concept according to the active harness. Do not emit a trailer when no body applied.

## Babysit Handoff

After a new PR, stack submit, or new changes on an existing PR, hand off to `ce-babysit-pr` unless a documented skip applies. Stack handoff uses the bottom open non-draft PR and derived posture. Pipeline waits for the downstream stop and propagates typed residuals unchanged.

Never implement watcher mechanics here. `babysit:off` is the per-run skip; `babysit:continuous` and `babysit:checkpoint` force their modes; exact active `auto_babysit: false` under `.rocketclaw` is the standing opt-out. Do not fire for description-only/update, no changed PR, unsupported forge, an unforced draft, or an unpushable head bookmark.

## Applying Via `gh`

Write the body under `<jj-root>/.tmp/rocketclaw/ce-commit-push-pr/` and pass it through `--body-file`; if no workspace can be resolved in description-only mode, use `./.tmp/rocketclaw/ce-commit-push-pr/`. Ensure `.tmp/` is ignored, remove the run file after the call, and never pass the body through stdin or command substitution.

```bash
WORKSPACE_ROOT="$(jj root)";
BODY_DIR="${WORKSPACE_ROOT:-.}/.tmp/rocketclaw/ce-commit-push-pr";
mkdir -p "$BODY_DIR";
BODY_FILE="$BODY_DIR/pr-body.md";
cat > "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

Use `gh pr create --title "<TITLE>" --body-file "$BODY_FILE"` or `gh pr edit <pr-url> --title "<TITLE>" --body-file "$BODY_FILE"`, then remove the file.
