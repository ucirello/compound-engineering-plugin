#!/usr/bin/env python3
"""Extract a compact conversation skeleton from supported agent JSONL sessions.

Supports Claude Code, Codex, Cursor, Pi, and oh-my-pi (`omp`). Thinking and
reasoning are excluded. Use `--output PATH` to write the result atomically.
"""

import json
import os
import re
import sys
import tempfile


STRIP_BLOCK = re.compile(r"<(system-reminder|system_instruction|environment_context|permissions instructions)>.*?</\1>", re.DOTALL | re.IGNORECASE)
STRIP_TAG = re.compile(r"</?(system-reminder|system_instruction|environment_context|permissions instructions)[^>]*>", re.IGNORECASE)


def clean(text):
    text = STRIP_BLOCK.sub("", str(text))
    return STRIP_TAG.sub("", text).strip()


def text_blocks(content):
    if isinstance(content, str):
        value = clean(content)
        return [value] if value else []
    values = []
    if not isinstance(content, list):
        return values
    for block in content:
        if isinstance(block, str):
            value = clean(block)
        elif isinstance(block, dict) and block.get("type") not in ("thinking", "reasoning", "tool_result", "function_call_output"):
            value = clean(block.get("text") or block.get("input_text") or block.get("output_text") or "")
        else:
            value = ""
        if value:
            values.append(value)
    return values


def tool_summary(name, data):
    if not isinstance(data, dict):
        return name
    target = next((data.get(key) for key in ("file_path", "path", "command", "pattern", "query", "prompt", "url") if data.get(key)), "")
    target = clean(target)[:240]
    return f"{name}: {target}" if target else name


def result_status(content, is_error=False):
    text = "\n".join(text_blocks(content)) if not isinstance(content, str) else clean(content)
    lowered = text.lower()
    exit_codes = [int(value) for value in re.findall(r"process exited with code (-?\d+)", lowered)]
    failed = is_error or any(code != 0 for code in exit_codes) or any(marker in lowered for marker in ("error:", "exception", "traceback"))
    return ("error" if failed else "ok") + (f": {text[:240]}" if text else "")


def active_pi(objects):
    by_id = {obj.get("id"): obj for obj in objects if obj.get("id")}
    entries = [obj for obj in objects if obj.get("type") != "session"]
    if not entries or not entries[-1].get("id"):
        return objects
    chain, current = [], entries[-1]
    while current:
        chain.append(current)
        current = by_id.get(current.get("parentId"))
    chain.reverse()
    compactions = [obj for obj in chain if obj.get("type") == "compaction"]
    if not compactions:
        return chain
    latest = compactions[-1]
    first_kept = latest.get("firstKeptEntryId")
    kept = [latest]
    include = first_kept is None
    for obj in chain:
        include = include or obj.get("id") == first_kept
        if include and obj.get("id") != latest.get("id"):
            kept.append(obj)
    return kept


def detect(objects):
    title_first = bool(objects and objects[0].get("type") == "title")
    for obj in objects:
        kind = obj.get("type")
        if kind == "session" and obj.get("cwd"):
            return "omp" if title_first else "pi"
        if kind in ("session_meta", "response_item", "event_msg", "turn_context"):
            return "codex"
        if kind in ("user", "assistant"):
            return "claude"
        if "role" in obj and kind is None:
            return "cursor"
    return "codex"


def render(objects):
    platform = detect(objects)
    if platform in ("pi", "omp"):
        objects = active_pi(objects)
    output = []
    for obj in objects:
        kind = obj.get("type")
        ts = str(obj.get("timestamp", ""))[:19]
        payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}

        if platform == "codex":
            ptype = payload.get("type")
            if kind == "event_msg" and ptype in ("user_message", "agent_message"):
                role = "USER" if ptype == "user_message" else "ASSISTANT"
                for text in text_blocks(payload.get("message", "")):
                    output.append(f"[{ts}] {role}: {text}".strip())
            elif kind == "response_item" and ptype == "message":
                role = str(payload.get("role", "assistant")).upper()
                for text in text_blocks(payload.get("content", [])):
                    output.append(f"[{ts}] {role}: {text}".strip())
            elif kind == "response_item" and ptype in ("function_call", "custom_tool_call"):
                output.append(f"[{ts}] TOOL: {tool_summary(payload.get('name', 'tool'), payload.get('arguments', {}))}".strip())
            elif kind == "response_item" and ptype in ("function_call_output", "custom_tool_call_output"):
                output.append(f"[{ts}] RESULT: {result_status(payload.get('output', ''))}".strip())
            elif kind == "event_msg" and ptype == "exec_command_end":
                exit_code = payload.get("exit_code")
                output.append(f"[{ts}] RESULT: {result_status(payload.get('stderr') or payload.get('aggregated_output', ''), exit_code not in (None, 0))}".strip())
            continue

        message = obj.get("message") if isinstance(obj.get("message"), dict) else obj
        role = message.get("role") or (kind if kind in ("user", "assistant") else None)
        if role in ("user", "assistant"):
            for text in text_blocks(message.get("content", "")):
                output.append(f"[{ts}] {role.upper()}: {text}".strip())
            content = message.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") in ("tool_use", "toolCall"):
                        output.append(f"[{ts}] TOOL: {tool_summary(block.get('name', 'tool'), block.get('input', block.get('arguments', block)))}".strip())
                    elif isinstance(block, dict) and block.get("type") == "tool_result":
                        output.append(f"[{ts}] RESULT: {result_status(block.get('content', ''), block.get('is_error', False))}".strip())
        elif platform in ("pi", "omp") and message.get("role") in ("toolResult", "bashExecution"):
            if message.get("role") == "bashExecution":
                output.append(f"[{ts}] TOOL: {tool_summary('bash', {'command': message.get('command', '')})}".strip())
            content = message.get("content") or message.get("output", "")
            failed = message.get("isError", False) or message.get("cancelled", False) or message.get("exitCode") not in (None, 0)
            output.append(f"[{ts}] RESULT: {result_status(content, failed)}".strip())
        elif platform in ("pi", "omp") and message.get("role") == "custom":
            for text in text_blocks(message.get("content", "")):
                output.append(f"[{ts}] SUMMARY: {text}".strip())
        elif kind in ("compaction", "branch_summary") and obj.get("summary"):
            output.append(f"[{ts}] COMPACTION: {clean(obj['summary'])}".strip())
        elif kind == "custom_message":
            for text in text_blocks(obj.get("content", "")):
                output.append(f"[{ts}] SUMMARY: {text}".strip())
    return "\n\n".join(output) + ("\n" if output else "")


def main():
    output_path = None
    args = sys.argv[1:]
    if "--output" in args:
        index = args.index("--output")
        if index + 1 >= len(args):
            raise SystemExit("--output requires a path")
        output_path = args[index + 1]
    objects = []
    for line in sys.stdin:
        try:
            if line.strip():
                objects.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    result = render(objects)
    status = {"_meta": True, "lines": len(objects), "bytes": len(result.encode("utf-8"))}
    if output_path:
        parent = os.path.dirname(os.path.abspath(output_path))
        fd, temporary = tempfile.mkstemp(prefix=".session-skeleton-", dir=parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(result)
            os.replace(temporary, output_path)
        except BaseException:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise
        print(json.dumps({**status, "wrote": output_path}))
    else:
        sys.stdout.write(result)
        print(json.dumps(status))


if __name__ == "__main__":
    main()
