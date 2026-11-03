# Stack manager compatibility

Use context.md's absolute workspace cwd and GIT_DIR wrapper for every gh command. Never run a helper that invokes Git internally, including checkout/commit/fetch/push/rebase/merge. No version upgrade or Git fallback.

Read-only API topology is usable only when compatible implementation is verified. Preserve exact parent PR/head OID, ownership, order and draft state; names alone do not prove identity. Unknown or unsupported topology is a compatibility blocker, not proof of standalone status. Do not substitute link-only API mutations for manager tracking. Follow stack-submit.md.
