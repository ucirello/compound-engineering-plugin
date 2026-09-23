#!/usr/bin/env bash

# Call from the target workspace's absolute root. Explicit OWNER/REPO calls also
# work outside JJ; their scratch stays under the local directory's .tmp.
workspace_root=$(jj workspace root 2>/dev/null) || workspace_root=
if [ -n "$workspace_root" ]; then
    cd "$workspace_root"
    GIT_DIR=$(jj git root)
    export GIT_DIR
else
    workspace_root="$PWD"
fi
scratch_root="$workspace_root/.tmp"
