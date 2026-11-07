#!/usr/bin/env python3
"""Reduce supported OpenCode export/API JSON, never internal session storage."""
import json
import sys


def reduce_messages(data):
    if isinstance(data, dict):
        data = data.get("messages", data.get("data", []))
    if not isinstance(data, list):
        raise ValueError("expected export messages or API message array")
    for message in data:
        info = message.get("info", message)
        role = info.get("role")
        if role not in ("user", "assistant"):
            continue
        print(f"\n[{role}]")
        for part in message.get("parts", []):
            kind = part.get("type")
            if kind == "text":
                print(part.get("text", ""))
            elif kind == "tool":
                state = part.get("state", {})
                result = state.get("output", state.get("error", ""))
                if not isinstance(result, str):
                    result = json.dumps(result, ensure_ascii=False)
                print(f"tool: {part.get('tool', 'unknown')} [{state.get('status', 'unknown')}]")
                print(result[:1200])


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as source:
        reduce_messages(json.load(source))
