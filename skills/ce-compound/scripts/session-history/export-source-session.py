#!/usr/bin/env python3
"""Export an explicit OpenCode source session using its supported public CLI.

Keep the full JSON in private workspace-local scratch and emit a compact
chronological text transcript. Unknown export layouts fail visibly rather than
turning inaccessible evidence into an apparently empty conversation.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def reduce_messages(export):
    if isinstance(export, dict):
        messages = export.get("messages")
        if messages is None and isinstance(export.get("data"), dict):
            messages = export["data"].get("messages")
    else:
        messages = export if isinstance(export, list) else None
    if not isinstance(messages, list):
        raise ValueError("unsupported export layout: no messages array; inspect supported API output")
    lines = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        info = message.get("info", message)
        role = info.get("role") if isinstance(info, dict) else None
        if role not in ("user", "assistant"):
            continue
        parts = message.get("parts", [])
        if isinstance(message.get("content"), str):
            parts = [*parts, {"type": "text", "text": message["content"]}]
        for part in parts:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text" and isinstance(part.get("text"), str):
                lines.append(f"{role}: {part['text']}")
            elif part.get("type") in ("tool", "tool-invocation"):
                state = part.get("state", {})
                if not isinstance(state, dict):
                    state = {}
                result = state.get("error") or state.get("output") or state.get("status") or "result unavailable"
                short = " ".join(str(result).split())
                if len(short) > 600:
                    short = short[:600] + "… [truncated; full result in export]"
                lines.append(f"{role} tool {part.get('tool', part.get('name', 'unknown'))}: {short}")
    if not lines:
        raise ValueError("export contains no reducible user/assistant evidence")
    return "\n\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_id", help="explicit source ID read from parent's OPENCODE_SESSION_ID")
    parser.add_argument("--workspace", required=True, help="verified absolute JJ workspace root")
    parser.add_argument("--output-dir", required=True, help="private run directory under workspace/.tmp")
    args = parser.parse_args()
    if not args.session_id.startswith("ses_") or any(c.isspace() for c in args.session_id):
        parser.error("an explicit OpenCode source session ID is required")
    workspace = Path(args.workspace)
    if not workspace.is_absolute():
        parser.error("workspace must be absolute")
    workspace = workspace.resolve()
    local = (workspace / ".tmp").resolve()
    destination = Path(args.output_dir).resolve()
    if not local.is_relative_to(workspace) or not destination.is_relative_to(local):
        parser.error("output must remain under the workspace-local .tmp tree")
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt" and destination.stat().st_uid != os.geteuid():
        parser.error("output directory is not owned by this user")
    os.chmod(destination, 0o700)
    # A unique run directory avoids overwriting another run's evidence.
    raw_path = destination / "source-session.json"
    text_path = destination / "source-session.txt"
    if raw_path.exists() or raw_path.is_symlink() or text_path.exists() or text_path.is_symlink():
        parser.error("source evidence already exists; reuse it or choose a fresh local run directory")
    result = subprocess.run(["opencode", "session", "export", args.session_id],
                            cwd=str(workspace), capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f"supported session export failed: {result.stderr.strip()}")
    export = json.loads(result.stdout)
    transcript = reduce_messages(export)
    for path, content in ((raw_path, result.stdout), (text_path, transcript)):
        with path.open("x", encoding="utf-8") as stream:
            os.chmod(path, 0o600)
            stream.write(content)
    print(json.dumps({"source_session_id": args.session_id,
                      "export": str(raw_path), "transcript": str(text_path)}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"source-session export blocked: {exc}", file=sys.stderr)
        sys.exit(1)
