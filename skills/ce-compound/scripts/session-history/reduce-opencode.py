#!/usr/bin/env python3
"""Reduce a supported OpenCode export/API response without internal-storage access."""
import json
from pathlib import Path
import sys


def reduce_export(value):
    if isinstance(value, dict):
        value = value.get("messages", value.get("data"))
    if not isinstance(value, list):
        raise ValueError("unsupported export: expected messages array")
    lines = []
    for message in value:
        if not isinstance(message, dict):
            continue
        info = message.get("info", message)
        role = info.get("role")
        if role not in ("user", "assistant"):
            continue
        for part in message.get("parts", []):
            kind = part.get("type")
            if kind == "text" and isinstance(part.get("text"), str):
                lines.append(f"[{role}] {part['text']}")
            elif kind == "tool":
                state = part.get("state", {})
                result = state.get("output", state.get("error", state.get("status", "")))
                lines.append(f"[tool {part.get('tool', 'unknown')}] {str(result)[:400]}")
    if not any(line.startswith(("[user]", "[assistant]")) for line in lines):
        raise ValueError("export contains no user/assistant text")
    return "\n\n".join(lines) + "\n"


if __name__ == "__main__":
    source, destination = map(Path, sys.argv[1:])
    destination.write_text(reduce_export(json.loads(source.read_text(encoding="utf-8"))), encoding="utf-8")
    print(destination)
