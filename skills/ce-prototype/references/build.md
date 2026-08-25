# Building the prototype

Required read before you write any prototype code, alongside `references/preview.md`.

## Fidelity

Fidelity is a different axis from size (`references/scoping.md` owns sizing, which the go-ahead depends on). Throwaway means unmaintained and unshipped, not thin — do not test, abstract, or harden past runnable, but take finish as far as the dimension under test needs. A flow or state model gets rich enough to drive; a visual direction gets finished enough to judge; a placement question stays thin. Fidelity may differ per avenue within one wide run. Do not stay low-fidelity on principle, and persist state only when persistence is the question. Follow the product's current runtime, syntax, and conventions instead of imposing a fixed scaffold. When the required medium is Go, use only quality practices compatible with its current module, toolchain, and local conventions.

## The artifact on the web path

On the web path the artifact is whatever a browser can display and you can author — HTML, SVG, CSS renderings, images — shown inside the page the preview helper already serves. Where the host offers image generation, use it. Where it does not, author the candidates as markup when markup can carry the dimension honestly, and say so; when it cannot — a photographic or painterly direction — report the missing capability instead, because substituting markup there fakes the very thing being judged. Do not introduce a second display mechanism alongside that page; a yielded run displays however its own medium does.

## Which run root

Inside JJ, prefer `<workspace-root>/.rocketclaw/ce-prototype/<date>-<slug>/` so the prototype survives with the workspace. Use `<workspace-root>/.tmp/rocketclaw/ce-prototype/<date>-<slug>/` when the user declines the durable root, asks that the run not be retained there, or the durable root fails its safety checks. These paths remain outside `@` only when `.tmp/` and any selected `.rocketclaw/` root are ignored before creation. If those ignores cannot be established safely, stop before writing. Outside JJ, use `<current-directory>/.tmp/rocketclaw/ce-prototype/<date>-<slug>/`; its survival is best-effort. Calling the prototype throwaway is not a request to delete a kept prototype.

## JJ workspace model

Use `jj workspace root` to discover the workspace. Treat `@` as the current working-copy change, not as a named checkout. JJ has no staging area: ordinary file writes are automatically snapshotted into `@`. Use `jj status` or `jj diff -r <revset>` with the narrowest workspace-relative `root:` fileset needed for inspection. Use change IDs and revsets to identify work; use bookmarks only when a provider or remote needs a named pointer.

Use JJ for every repository read and mutation. Use `jj git import` or `jj git export` when a non-colocated provider interoperability step needs synchronization. When `gh` needs the underlying repository, resolve it with `jj git root` and provide that path as `GIT_DIR` for the invocation. Run shell adapters in the active local shell; POSIX blocks must also remain valid in Git Bash.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local syntax and active instructions win; apply compatible Go guidance to message quality, clarity, and structure without imposing a fixed message shape.

## Recreate, do not rebuild the app

Recreate what this question needs from the current product. Do not stand up the full app unless the question is the whole-product feel.

Scale into the existing app only as a throwaway overlay when the user asks or the question is density or chrome on an existing page — an isolated page will hide that. That overlay is not the shipped feature. Before editing, let JJ snapshot current files into the existing `@`, create a new child working-copy change, and record the exact `root:` filesets the overlay will touch. At cleanup, inspect the whole child change. If it contains only the recorded overlay filesets, abandon it. If unrelated work appeared, restore only the overlay filesets from the child's parent and leave the remaining change intact; if that separation is ambiguous, preserve everything and report the affected filesets. An overlay leaves no prototype artifact. Outside a JJ workspace, use an isolated prototype instead of an overlay.

## Showing it

When the question is which option wins, put the options on one surface so they can be judged together — unless that surface would distort what is being judged: a scroll or transition gets a full-size run of its own rather than being nested in a small framed panel, and the comparison surface stays static.

After each user-facing action or variant change, show the relevant state so they can see what changed.

Give each question in a multi-question run its own child directory under the run directory. Never delete a kept prototype — the directory is theirs to prune. Calling the prototype throwaway is not a request to delete it; throwaway describes the code.

The run capsule at `decisions.md` carries the question, what was built, the run and question directories each screen sits in, what won and why, what was rejected, stated adjustments that were not in the prototype, and what is still open. SKILL.md owns when it is written and what it must not become.

A run's output is a set of decisions. Converging on one direction that resolves the ambiguity is the best outcome, not a precondition for the run being complete.
