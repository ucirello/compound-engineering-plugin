# Grounding the interview in the workspace

Required read at the start of Phase 0, before the workspace model is built.

Read `<workspace-root>/STRATEGY.md` with the native file-read tool.

Then build a **workspace model** - your working understanding of what this product is - from two inputs with different jobs:

- **What the product is.** Stated intent (`README.md`, `CONCEPTS.md`, durable artifacts under `<root>`, an existing `STRATEGY.md`, and sibling docs such as `PRODUCT.md` or `VISION.md`) and structure (what the code is organized around, what is public, what is tested) - the authority for the problem, approach, and persona questions. Bound the read to "what is this and who is it for"; do not profile the whole workspace.
- **What is getting attention now.** Recent Jujutsu changes and provider review records, informing only the Tracks question and staleness in an update run. Use explicit `jj log` revsets because plain `jj log` defaults to mutable revisions plus context rather than complete history; use `-r ::` when the question requires all visible history, and narrow by path, date, bookmark, author, or another semantic revset when the question is bounded. Inspect a candidate revision with `jj show` or `jj diff`, not a Git working-tree mutation. Resolve remotes with `jj git remote list` rather than assuming `origin`. For GitHub, inspect PRs through `gh`; in a non-colocated JJ workspace, point Git-dependent provider tools at the directory returned by `jj git root`. In a colocated workspace, read-only Git and provider tooling may interoperate through the shared `.git` directory, but repository mutations stay in JJ. These commands and revsets have the same semantics in Git Bash; quote revsets and paths so the shell does not reinterpret them. A burst of recent work is a fact about the last few weeks, not about what the product is; where it disagrees with stated intent, that is a question for the user using neutral placeholders for the observed area and candidate interpretation, never a conclusion.

If the workspace has no substantive content, say so in one line and run the interview ungrounded - a normal path, not a blocker.

## Artifact paths

Read `docs_root` only from `<workspace-root>/.rocketclaw/config.yaml`. Unset means `<root>` is `<workspace-root>/docs`. A configured value must be a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`; otherwise stop and name the invalid key and value. Use `<root>` as the sole durable artifact location. Do not also read `docs` when `<root>` differs. Temporary work belongs under `<workspace-root>/.tmp/rocketclaw/ce-strategy/`, or `./.tmp/rocketclaw/ce-strategy/` relative to the physical current project directory when `jj workspace root` is unavailable.

## A legacy sibling doc and no `STRATEGY.md`

`STRATEGY.md` is the shared project doc; `VISION.md` and `PRODUCT.md` are legacy names used before converging on it. When one exists at the workspace root and `STRATEGY.md` does not, it has already seeded the workspace model; before the interview, offer the user the choice of folding it in or linking to it. Folding: this skill creates `STRATEGY.md` in the template's order and carries the legacy doc in - every meaning this run writes merges with legacy content carrying the same meaning into one section in the user's language, with contradictions put to the user; every meaning outside this skill's contribution is carried under its own heading with content unchanged. The legacy file then becomes redundant: say so and leave removal to the user. Downstream `ce-*` readers take `STRATEGY.md` first and consult a legacy sibling only for meanings it lacks, so a folded sibling is not re-read for meanings it carried. Linking: leave the legacy file where it is and point to it from the template's sibling line. Never edit the legacy file either way.

Show the workspace model in chat before the first question: three to five lines on what you take the product to be, who it seems to serve, and where attention has gone, each with its source named. Invite correction. On a first run the interview then runs in full; an update run still revisits only the section Phase 2 settles on. If it could not supply the product's name, ask for that here - the template's frontmatter and title need it.

## Focus hint

(Also stated in the always-loaded body, which is where it has to fire.) Any argument this skill was invoked with — present in the current prompt or conversation, from the user or a calling skill — is a focus hint: a section to revisit (`metrics`, `positioning`, `tracks`; older names such as `approach` or `who it's for` map to the current section) or a scope hint. With none, proceed open-ended and let the file state decide the path.
