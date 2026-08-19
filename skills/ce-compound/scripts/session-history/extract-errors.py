#!/usr/bin/env python3
"""Extract failed tool and command results from supported agent JSONL sessions.

Supports Claude Code, Codex, Cursor, Pi, and oh-my-pi (`omp`). With
`--output PATH`, writes the extraction artifact there and prints only status.
"""

import argparse
import json
import os
import sys


parser = argparse.ArgumentParser()
parser.add_argument("--output")
args = parser.parse_args()


def summary(value):
    if isinstance(value, list):
        value = "\n".join(
            block.get("text", "")
            for block in value
            if isinstance(block, dict) and block.get("type") in ("text", "toolError")
        )
    for line in str(value).splitlines():
        if line.strip():
            return line.strip()[:200]
    return ""


def active_pi(objects):
    by_id = {obj.get("id"): obj for obj in objects if obj.get("id") and obj.get("type") != "session"}
    leaf = next((obj.get("id") for obj in reversed(objects) if obj.get("id") and obj.get("type") != "session"), None)
    active = set()
    while leaf and leaf not in active:
        active.add(leaf)
        leaf = by_id.get(leaf, {}).get("parentId")
    selected = [obj for obj in objects if obj.get("type") == "session" or obj.get("id") in active]
    compactions = [obj for obj in selected if obj.get("type") == "compaction"]
    if not compactions or not compactions[-1].get("firstKeptEntryId"):
        return selected
    latest, started, context = compactions[-1], False, [obj for obj in selected if obj.get("type") == "session"] + [compactions[-1]]
    for obj in selected:
        started = started or obj.get("id") == latest.get("firstKeptEntryId")
        if started and obj.get("id") != latest.get("id"):
            context.append(obj)
    return context


def detect(objects):
    title_first = bool(objects and objects[0].get("type") == "title")
    for obj in objects[:12]:
        kind = obj.get("type")
        if kind == "session" and obj.get("cwd"):
            return "omp" if title_first else "pi"
        if kind in ("session_meta", "turn_context", "response_item", "event_msg"):
            return "codex"
        if kind in ("user", "assistant"):
            return "claude"
        if obj.get("role") in ("user", "assistant") and kind is None:
            return "cursor"
    return None


def extract(objects):
    platform = detect(objects)
    if platform in ("pi", "omp"):
        objects = active_pi(objects)
    found = []
    for obj in objects:
        ts = str(obj.get("timestamp", ""))[:19]
        if platform == "claude" and obj.get("type") == "user":
            content = obj.get("message", {}).get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error"):
                        found.append(f"[{ts}] [error] {summary(block.get('content', ''))}\n---")
        elif platform == "codex" and obj.get("type") == "event_msg":
            payload = obj.get("payload", {})
            if payload.get("type") == "exec_command_end":
                output = payload.get("aggregated_output", "")
                stderr = payload.get("stderr", "")
                marker = "Process exited with code "
                exit_code = payload.get("exit_code")
                if marker in output:
                    try:
                        exit_code = int(output.split(marker, 1)[1].splitlines()[0])
                    except (ValueError, IndexError):
                        pass
                if stderr or (exit_code not in (None, 0)):
                    command = payload.get("command", [])
                    command = command[-1] if isinstance(command, list) and command else command
                    found.append(f"[{ts}] [error] exit={exit_code} cmd={str(command)[:120]}: {summary(stderr or output)}\n---")
        elif platform in ("pi", "omp") and obj.get("type") == "message":
            message = obj.get("message", {})
            if message.get("role") == "bashExecution":
                code = message.get("exitCode")
                if code not in (None, 0) or message.get("cancelled"):
                    status = "cancelled" if message.get("cancelled") else f"exit={code}"
                    found.append(f"[{ts}] [error] {status} cmd={str(message.get('command', ''))[:120]}: {summary(message.get('output', ''))}\n---")
            elif message.get("role") == "toolResult":
                content = message.get("content", [])
                is_error = message.get("isError") or (
                    isinstance(content, list)
                    and any(isinstance(block, dict) and block.get("type") == "toolError" for block in content)
                )
                if is_error:
                    found.append(f"[{ts}] [error] tool={message.get('toolName', 'unknown')}: {summary(content)}\n---")
    return platform, found


def main():
    objects, parse_errors = [], 0
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            objects.append(json.loads(line))
        except json.JSONDecodeError:
            parse_errors += 1
    platform, found = extract(objects)
    body = "\n".join(found)
    if body:
        body += "\n"
    stats = {"_meta": True, "platform": platform, "lines": len(objects), "parse_errors": parse_errors, "errors_found": len(found)}
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(body)
        print(json.dumps({**stats, "wrote": args.output, "bytes": os.path.getsize(args.output)}))
    else:
        sys.stdout.write(body)
        print(json.dumps(stats))


if __name__ == "__main__":
    main()
