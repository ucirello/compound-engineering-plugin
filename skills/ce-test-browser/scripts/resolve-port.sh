#!/usr/bin/env bash
# Resolve the dev-server port for ce-test-browser and print it alone on stdout, so a
# caller can capture it with $(...) instead of transcribing it out of prose.
#
# Usage: resolve-port.sh [--free | --check] [EXPLICIT_PORT]
#   --free         after resolving, scan upward to the first port with no listener
#   --check        exit 0 when the resolved port has a listener, 1 when it does not
#   EXPLICIT_PORT  a port the caller already knows (the user's --port, or an in-context
#                  project instruction that states the dev-server port)
#
# Resolution order: EXPLICIT_PORT, a --port flag in package.json, PORT= in .env /
# .env.local / .env.development, then 3000.
set -u

free=0
check=0
explicit=""
for arg in "$@"; do
  case "$arg" in
    --free) free=1 ;;
    --check) check=1 ;;
    "") ;;
    *[!0-9]*) ;;
    *) explicit="$arg" ;;
  esac
done

port="$explicit"
if [ -z "$port" ]; then
  port=$(grep -Eo -- '--port[= ]+[0-9]{2,5}' package.json 2>/dev/null | grep -Eo '[0-9]{2,5}' | head -1)
fi
if [ -z "$port" ]; then
  # take the first digit run after PORT=, so quotes and a trailing "# comment" drop out
  port=$(grep -h '^PORT=' .env .env.local .env.development 2>/dev/null | tail -1 | grep -Eo '[0-9]+' | head -1)
fi
port="${port:-3000}"

port_is_listening() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -i ":$1" -sTCP:LISTEN -t >/dev/null 2>&1
  elif command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | grep -Eq "[.:]$1[[:space:]]"
  elif command -v netstat >/dev/null 2>&1; then
    netstat -an 2>/dev/null | grep -Eq "[.:]$1[[:space:]].*(LISTEN|LISTENING)"
  else
    return 2
  fi
}

if [ "$check" = 1 ]; then
  port_is_listening "$port"
  status=$?
  if [ "$status" = 2 ]; then
    echo "Cannot inspect port listeners: lsof, ss, and netstat are unavailable" >&2
  fi
  exit "$status"
fi

if [ "$free" = 1 ]; then
  while :; do
    port_is_listening "$port"
    status=$?
    case "$status" in
      0) port=$((port + 1)) ;;
      1) break ;;
      *) echo "Cannot inspect port listeners: lsof, ss, and netstat are unavailable" >&2; exit 1 ;;
    esac
  done
fi

echo "$port"
