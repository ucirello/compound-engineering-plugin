#!/usr/bin/env python3
"""Extract session metadata from Claude Code, Codex, Cursor, Pi, and omp JSONL.

Accepts file paths for batch mode and emits one JSON object per recognized
session followed by a `_meta` record. With no paths, reads one JSONL session
from stdin for backward compatibility.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


def objects_from(path=None):
    objects, parse_errors = [], 0
    try:
        stream = open(path, encoding="utf-8", errors="replace") if path else sys.stdin
        with stream if path else _nullcontext(stream):
            for line in stream:
                if not line.strip():
                    continue
                try:
                    objects.append(json.loads(line))
                except json.JSONDecodeError:
                    parse_errors += 1
    except OSError:
        parse_errors += 1
    return objects, parse_errors


class _nullcontext:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, *_):
        return False


def detect(objects):
    title_first = bool(objects and objects[0].get("type") == "title")
    for obj in objects:
        kind = obj.get("type")
        if kind == "session" and obj.get("cwd"):
            return "omp" if title_first else "pi"
        if kind == "session_meta":
            return "codex"
        if kind in ("user", "assistant"):
            return "claude"
        if "role" in obj and kind is None:
            return "cursor"
    return None


def timestamp(obj):
    payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
    message = obj.get("message") if isinstance(obj.get("message"), dict) else {}
    return obj.get("timestamp") or payload.get("timestamp") or message.get("timestamp") or ""


def metadata(objects, path=None):
    platform = detect(objects)
    if not platform:
        return None
    result = {"platform": platform}
    for obj in objects:
        payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
        if not result.get("cwd"):
            result["cwd"] = obj.get("cwd") or payload.get("cwd") or ""
        if not result.get("branch"):
            result["branch"] = obj.get("gitBranch") or payload.get("git_branch") or ""
        if not result.get("session"):
            result["session"] = (
                obj.get("sessionId")
                or (obj.get("id") if obj.get("type") == "session" else "")
                or payload.get("id")
                or payload.get("session_id")
                or ""
            )
        ts = timestamp(obj)
        if ts:
            result.setdefault("ts", ts)
            result["last_ts"] = ts
    if path:
        result["file"] = path
        try:
            result["size"] = os.path.getsize(path)
        except OSError:
            result["size"] = 0
        if platform == "cursor":
            mtime = os.path.getmtime(path)
            result.setdefault("ts", datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat())
            result.setdefault("last_ts", result["ts"])
            result.setdefault("session", os.path.basename(os.path.dirname(path)))
    return {key: value for key, value in result.items() if value not in (None, "")}


def normalize_path(path):
    value = path.replace("\\", "/").rstrip("/")
    if len(value) >= 2 and value[1] == ":":
        value = value[0].upper() + ":" + value[2:].casefold()
    return value


def paths_related(left, right):
    left, right = normalize_path(left), normalize_path(right)
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


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


def searchable_text(objects, platform):
    if platform in ("pi", "omp"):
        objects = active_pi(objects)
    chunks = []
    for obj in objects:
        kind = obj.get("type")
        if kind in ("thinking", "reasoning"):
            continue
        payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
        payload_kind = payload.get("type")
        if payload_kind in ("reasoning", "function_call_output") or kind == "tool_result":
            continue
        candidate = payload if platform == "codex" else obj.get("message", obj)
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content", "")
        if platform == "codex" and isinstance(payload.get("message"), str):
            chunks.append(payload["message"])
        if platform in ("pi", "omp") and kind == "message":
            role = candidate.get("role")
            if role == "bashExecution" and isinstance(candidate.get("command"), str):
                chunks.append(candidate["command"])
            if role == "assistant" and isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "toolCall":
                        continue
                    arguments = block.get("arguments", {})
                    if isinstance(arguments, dict):
                        chunks.extend(str(arguments[key]) for key in ("path", "file_path", "command", "pattern", "query", "prompt") if arguments.get(key))
        if platform in ("pi", "omp") and kind in ("compaction", "branch_summary") and isinstance(obj.get("summary"), str):
            chunks.append(obj["summary"])
        if platform in ("pi", "omp") and kind == "custom_message":
            content = obj.get("content", content)
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, list):
            for block in content:
                if not isinstance(block, dict) or block.get("type") in ("thinking", "reasoning", "tool_result"):
                    continue
                text = block.get("text") or block.get("input_text") or block.get("output_text")
                if text:
                    chunks.append(str(text))
                if block.get("type") in ("tool_use", "toolCall"):
                    data = block.get("input") if isinstance(block.get("input"), dict) else block
                    for key in ("path", "file_path", "command", "pattern", "query", "prompt"):
                        if data.get(key):
                            chunks.append(str(data[key]))
    return "\n".join(chunks)


def parse_args(args):
    paths, cwd_filter, keywords = [], None, []
    index = 0
    while index < len(args):
        if args[index] == "--cwd-filter" and index + 1 < len(args):
            cwd_filter = args[index + 1]
            index += 2
        elif args[index] == "--keyword" and index + 1 < len(args):
            keywords.extend(item for item in args[index + 1].split(",") if item)
            index += 2
        else:
            paths.append(args[index])
            index += 1
    return paths, cwd_filter, keywords


def main():
    paths, cwd_filter, keywords = parse_args(sys.argv[1:])
    if not paths:
        objects, parse_errors = objects_from()
        result = metadata(objects)
        if result:
            print(json.dumps(result, ensure_ascii=False))
        print(json.dumps({"_meta": True, "files_processed": 1 if objects or parse_errors else 0, "parse_errors": parse_errors + (1 if objects and not result else 0)}))
        return

    processed = parse_errors = filtered_by_cwd = files_matched = 0
    patterns = [re.compile(re.escape(word), re.IGNORECASE) for word in keywords]
    for path in paths:
        processed += 1
        objects, line_errors = objects_from(path)
        parse_errors += line_errors
        result = metadata(objects, path)
        if not result:
            parse_errors += 1
            continue
        session_cwd = result.get("cwd")
        if cwd_filter and result["platform"] in ("claude", "codex", "pi", "omp"):
            if not session_cwd or not paths_related(session_cwd, cwd_filter):
                filtered_by_cwd += 1
                continue
        if patterns:
            text = searchable_text(objects, result["platform"])
            matches = {keyword: len(pattern.findall(text)) for keyword, pattern in zip(keywords, patterns)}
            result["keyword_matches"] = matches
            result["match_count"] = sum(matches.values())
            if not result["match_count"]:
                continue
            files_matched += 1
        print(json.dumps(result, ensure_ascii=False))
    meta = {"_meta": True, "files_processed": processed, "parse_errors": parse_errors}
    if filtered_by_cwd:
        meta["filtered_by_cwd"] = filtered_by_cwd
    if keywords:
        meta["files_matched"] = files_matched
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
