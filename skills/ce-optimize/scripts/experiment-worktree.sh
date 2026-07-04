#!/bin/bash

# Deprecated experiment isolation helper.
# The old implementation used JJ workspace isolation commands. ce-optimize now
# requires JJ workspace semantics, so this script fails clearly instead of
# creating JJ workspaces behind the user's back.

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

command_name="${1:-help}"

case "$command_name" in
  count)
    echo "0"
    ;;
  help|--help|-h)
    cat <<'EOF'
ce-optimize experiment isolation now uses JJ workspaces.

Create an experiment workspace with JJ commands from the optimization root, for example:
  jj workspace add ../optimize-<spec>-exp-<NNN> -r optimize/<spec>
  jj bookmark create optimize-exp/<spec>/exp-<NNN>

Remove completed experiment workspaces with the matching JJ workspace cleanup command for your JJ version.
EOF
    ;;
  create|cleanup|cleanup-all)
    echo -e "${RED}Error: experiment-worktree.sh no longer manages experiment isolation.${NC}" >&2
    echo -e "${YELLOW}Use JJ workspace commands instead:${NC}" >&2
    echo "  jj workspace add ../optimize-<spec>-exp-<NNN> -r optimize/<spec>" >&2
    echo "  jj bookmark create optimize-exp/<spec>/exp-<NNN>" >&2
    echo "  jj st" >&2
    echo "  jj diff" >&2
    exit 2
    ;;
  *)
    echo -e "${RED}Unknown command: $command_name${NC}" >&2
    exit 1
    ;;
esac
