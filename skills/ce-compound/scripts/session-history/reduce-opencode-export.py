#!/usr/bin/env python3
"""Reduce a supported OpenCode export/API message response to visible evidence.

Usage: reduce-opencode-export.py < export.json > reduced.txt
No internal session storage is accessed. Tool inputs and reasoning are omitted.
"""
import json
import sys


def reduce_export(payload):
    if isinstance(payload, dict) and "data" in payload:
        payload = payload["data"]
    messages = payload.get("messages") if isinstance(payload, dict) else payload
    if not isinstance(messages, list):
        raise ValueError("expected an export messages array or API message array")
    lines = []
    for entry in messages:
        if not isinstance(entry, dict):
            continue
        info = entry.get("info", entry)
        role = info.get("role")
        if role not in ("user", "assistant"):
            continue
        lines.append(f"[{role} {info.get('id', '')}]")
        for part in entry.get("parts", []):
            if part.get("type") == "text" and isinstance(part.get("text"), str):
                lines.append(part["text"])
            elif part.get("type") == "tool":
                state = part.get("state", {})
                result = state.get("output", state.get("error", ""))
                if not isinstance(result, str):
                    result = json.dumps(result, ensure_ascii=False)
                lines.append(f"tool {part.get('tool', 'unknown')}: {result[:600]}")
    return "\n".join(lines)


if __name__ == "__main__":
    try:
        text = reduce_export(json.load(sys.stdin))
        if not text:
            raise ValueError("no visible user/assistant evidence in supported response")
        print(text)
    except (ValueError, TypeError, KeyError) as error:
        sys.exit(f"OpenCode export reduction failed: {error}")
