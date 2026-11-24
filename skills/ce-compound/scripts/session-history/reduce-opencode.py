#!/usr/bin/env python3
"""Reduce a supported OpenCode session export or message response to JSONL."""

import json
import sys


def emit(row):
    print(json.dumps(row, ensure_ascii=False))


def reduce_messages(messages):
    usable_text = False
    for message in messages:
        if not isinstance(message, dict):
            continue
        info = message.get("info", message)
        role = info.get("role") if isinstance(info, dict) else None
        if role not in ("user", "assistant"):
            continue
        for part in message.get("parts", []):
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text":
                text = part.get("text")
                if isinstance(text, str) and text.strip() and not part.get("synthetic"):
                    emit({"role": role, "text": text})
                    usable_text = True
            elif role == "assistant" and part.get("type") == "tool":
                state = part.get("state")
                tool = part.get("tool")
                if not isinstance(tool, str) or not isinstance(state, dict):
                    continue
                row = {"tool": tool}
                status = state.get("status")
                if isinstance(status, str):
                    row["status"] = status
                result = state.get("output", state.get("error"))
                if isinstance(result, str):
                    row["result"] = result[:500] + ("…" if len(result) > 500 else "")
                emit(row)
    return usable_text


def main():
    try:
        with open(sys.argv[1], encoding="utf-8") as handle:
            document = json.load(handle)
        messages = document.get("messages") if isinstance(document, dict) else document
        if not isinstance(messages, list) or not reduce_messages(messages):
            raise ValueError("no usable user or assistant text in OpenCode response")
    except (IndexError, OSError, ValueError, TypeError) as exc:
        print(f"reduce-opencode: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
