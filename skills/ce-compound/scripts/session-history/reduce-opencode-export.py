#!/usr/bin/env python3
"""Reduce a supported OpenCode session export to human text and short tool results."""

import argparse
import json
import sys


def reduce_export(data, session_id):
    if data.get("info", {}).get("id") != session_id:
        raise ValueError("export does not identify the requested source session")
    messages = data.get("messages")
    if not isinstance(messages, list):
        raise ValueError("OpenCode export has no message array")
    lines = []
    for message in messages:
        kind = message.get("type")
        if kind == "user":
            text = message.get("text")
            if isinstance(text, str) and text.strip():
                lines.append(f"user:\n{text}")
        elif kind == "assistant":
            for part in message.get("content", []):
                if part.get("type") == "tool":
                    name = " ".join(part["name"].split())[:80]
                    state = part.get("state", {})
                    status = state.get("status")
                    result = []
                    if status == "error":
                        result.append(state.get("error", {}).get("message", ""))
                    if status in ("completed", "error"):
                        result.extend(
                            item["text"] for item in state.get("content", [])
                            if item.get("type") == "text"
                        )
                    short = " ".join(" ".join(result).split())
                    if short:
                        lines.append(f"tool {name}: {short[:500]}{' …' if len(short) > 500 else ''}")
                    else:
                        lines.append(f"tool {name}")
                elif part.get("type") == "text":
                    text = part.get("text")
                    if isinstance(text, str) and text.strip():
                        lines.append(f"assistant:\n{text}")
    if not any(line.startswith(("user:\n", "assistant:\n")) for line in lines):
        raise ValueError("export contains no user or assistant text")
    return "\n\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_id")
    parser.add_argument("export")
    args = parser.parse_args()
    try:
        with open(args.export, encoding="utf-8") as handle:
            print(reduce_export(json.load(handle), args.session_id))
    except (OSError, ValueError, AttributeError, TypeError, KeyError) as exc:
        print(f"reduce OpenCode export: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
