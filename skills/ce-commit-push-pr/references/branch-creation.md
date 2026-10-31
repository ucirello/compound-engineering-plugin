# Feature bookmark creation from default bookmark

Use the absolute target workspace root as cwd for every JJ command. Fetch with `(cd "$workspace_root" && jj git fetch --remote <verified-remote> --branch <base>)`, then verify the exact remote bookmark tip. Inspect full descriptions in `jj log -r '<base>@<remote>..<verified-local-head>'` from that same root.

- No local-only default-bookmark commits: choose the verified remote tip.
- Local-only commits present: show the list and ask whether to carry them or leave them on the local default bookmark. Pipeline mode stops with that decision as a residual. Never silently carry foreign commits. Preserve the original bookmark and recovery references.

Create a nonconflicting feature bookmark at the chosen base with `(cd "$workspace_root" && jj bookmark create <feature-bookmark> -r <verified-base>)`. Carry only intended owned working changes onto that base after inspecting tracked changes, conflicts, ignored and untracked content. If safe movement cannot be proved, stop with the colliding paths; never reset, discard, stash or remove them. Feature bookmark creation itself needs no extra approval in an authorized full workflow.

On fetch failure, current verified local head may be used only if that fallback is authorized; disclose unverified base freshness and skip the unreliable local-only-commit decision. Unknown or ambiguous targets stop rather than being guessed.
