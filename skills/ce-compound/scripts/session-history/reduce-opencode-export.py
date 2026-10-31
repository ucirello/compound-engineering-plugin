#!/usr/bin/env python3
"""Reduce a supported OpenCode session export/API response before model reads.

Usage: python3 reduce-opencode-export.py <export.json> <reduced.txt>
Both paths must be inside the current workspace's local .tmp directory.
Never reads OpenCode internal storage; unknown envelopes fail visibly.
"""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root = subprocess.run(["jj", "workspace", "root"], cwd=os.path.abspath(os.getcwd()),
                          capture_output=True, text=True, check=True).stdout.strip()
    scratch = (Path(root) / ".tmp").resolve()
    source, destination = (Path(p).resolve() for p in sys.argv[1:])
    if any(not p.is_relative_to(scratch) for p in (source, destination)):
        raise SystemExit("export and reduced evidence must stay under workspace .tmp")
    data = json.loads(source.read_text())
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    messages = data.get("messages") if isinstance(data, dict) else data
    if not isinstance(messages, list):
        raise SystemExit("unsupported export envelope: expected messages array")
    lines = []
    for message in messages:
        info = message.get("info", message)
        role = info.get("role")
        if role not in ("user", "assistant"):
            continue
        lines.append(f"\n[{role}]")
        for part in message.get("parts", []):
            kind = part.get("type")
            if kind == "text":
                lines.append(str(part.get("text", "")))
            elif kind in ("tool", "tool-invocation"):
                state = part.get("state", {})
                if not isinstance(state, dict):
                    state = {}
                output = state.get("output", state.get("error", ""))
                if not isinstance(output, str):
                    output = json.dumps(output, ensure_ascii=False)
                lines.append(f"tool: {part.get('tool', part.get('name', 'unknown'))}; "
                             f"{state.get('status', '')}: {output[:500]}")
    if not lines:
        raise SystemExit("export has no supported user/assistant evidence")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
