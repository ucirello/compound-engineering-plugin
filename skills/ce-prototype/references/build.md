# Building the prototype

Required read before you write any prototype code, alongside `references/preview.md`.

## Fidelity

Fidelity is a different axis from size (`references/scoping.md` owns sizing, which the go-ahead depends on). Throwaway means unmaintained and unshipped, not thin — do not test, abstract, or harden past runnable, but take finish as far as the dimension under test needs. A flow or state model gets rich enough to drive; a visual direction gets finished enough to judge; a placement question stays thin. Fidelity may differ per avenue within one wide run. Do not stay low-fidelity on principle, and persist state only when persistence is the question.

## The artifact on the web path

On the web path the artifact is whatever a browser can display and you can author — HTML, SVG, CSS renderings, images — shown inside the page the preview helper already serves. Where the host offers image generation, use it. Where it does not, author the candidates as markup when markup can carry the dimension honestly, and say so; when it cannot — a photographic or painterly direction — report the missing capability instead, because substituting markup there fakes the very thing being judged. Do not introduce a second display mechanism alongside that page; a yielded run displays however its own medium does.

## Which run root

Resolve the root with `jj workspace root`. Prefer `<workspace-root>/.context/ce-prototype/<date>-<slug>/` so the prototype survives alongside the decisions capsule. Use `<workspace-root>/.tmp/ce-prototype/<date>-<slug>/` when the user asks for a transient run, declines the `.context/` ignore rule, or the persistent path fails its safety checks. When `jj workspace root` fails, use `<current-directory>/.tmp/ce-prototype/<date>-<slug>/`. Never use an OS-global temporary facility.

Before writing under a JJ workspace, prove every top-level directory the run may use is covered by the applicable `.gitignore` rules. Official JJ documentation states that ordinary commands snapshot the working copy, new files are tracked by default, and `.gitignore` is the supported ignore mechanism: https://jj-vcs.github.io/jj/latest/working-copy/#ignored-files. Offer to append only the needed `.context/` or `.tmp/` rule before creating files. A kept run preflights `.tmp/` too because path-safety failure can send it there. If the user declines `.context/`, try the already-ignored or user-approved `.tmp/` path; if `.tmp/` cannot be safely excluded, stop. A local fallback outside JJ still uses `.tmp` beneath the current directory. Calling the prototype throwaway is not a request to leave the workspace, and a kept prototype is never deleted.

## Recreate, do not rebuild the app

Recreate what this question needs from the current product. Do not stand up the full app unless the question is the whole-product feel.

Scale into the existing app only as a throwaway overlay when the user asks or the question is density or chrome on an existing page — an isolated page will hide that. An overlay requires a JJ workspace; outside JJ, report that this mode is unavailable rather than editing product files without an isolated change.

Create the overlay in a dedicated workspace under `<workspace-root>/.tmp/ce-prototype/workspaces/<run-slug>/`, based on the revision that represents the product state being judged. Inspect `jj status`, `jj log -r '@|@-'`, `jj workspace list`, and the installed `jj workspace add --help` before mutation. The new workspace must have a distinct name and a distinct working-copy change; do not reuse, edit, or rewrite the invoking workspace's `@`. Installed help determines the supported workspace-name, revision-selection, and description options. When composing that change description, use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed in `git log` always win over Go guidance. Preserve the requirement that the description identify a transient prototype overlay. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose a fixed message syntax, prefix, type, scope, subject, body, layout, template, or example.

Jujutsu has no active or current bookmark. Do not create, move, track, or publish one for a prototype. Keep all overlay edits in the dedicated workspace's anonymous working-copy change and confirm their scope with `jj status` and `jj diff` from that workspace.

When the try ends, stop its preview server, verify the dedicated change contains only overlay work, and use the installed `jj abandon --help` syntax to abandon only that change. Then use the installed `jj workspace forget --help` syntax to forget only the dedicated workspace. Official JJ documentation states that forgetting unregisters a workspace but does not delete its files: https://jj-vcs.github.io/jj/latest/working-copy/#workspaces. Remove only the exact transient workspace directory after confirming it contains no unrelated data. An overlay run therefore leaves no prototype artifact. If any ownership, change identity, or cleanup check is ambiguous, do not abandon or remove anything; report the workspace name, path, change ID, and residual files.

## Showing it

When the question is which option wins, put the options on one surface so they can be judged together — unless that surface would distort what is being judged: a scroll or transition gets a full-size run of its own rather than being nested in a small framed panel, and the comparison surface stays static.

After each user-facing action or variant change, show the relevant state so they can see what changed.

Give each question in a multi-question run its own child directory under the run directory. Never delete a kept prototype — the directory is theirs to prune. Calling the prototype throwaway is not a request to delete it; throwaway describes the code.

The run capsule at `decisions.md` carries the question, what was built, the run and question directories each screen sits in, what won and why, what was rejected, stated adjustments that were not in the prototype, and what is still open. SKILL.md owns when it is written and what it must not become.

A run's output is a set of decisions. Converging on one direction that resolves the ambiguity is the best outcome, not a precondition for the run being complete.
