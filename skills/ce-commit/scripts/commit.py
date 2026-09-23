#!/usr/bin/env python3
"""Pass a file-backed message and exact file selections to JJ without a shell."""

import json
from pathlib import Path
import subprocess
import sys


def main():
    if len(sys.argv) < 4:
        raise SystemExit("usage: commit.py ABSOLUTE_WORKSPACE MESSAGE_FILE FILE [FILE ...]")
    workspace = Path(sys.argv[1])
    if not workspace.is_absolute():
        raise SystemExit("workspace must be absolute")
    root = subprocess.run(
        ["jj", "workspace", "root"], cwd=workspace, check=True,
        text=True, capture_output=True,
    ).stdout.removesuffix("\n")
    if not Path(root).is_absolute():
        raise SystemExit("JJ returned a non-absolute workspace root")
    if workspace.resolve() != Path(root).resolve():
        raise SystemExit("workspace must be the JJ workspace root")
    message_file = Path(sys.argv[2])
    if not message_file.is_absolute():
        raise SystemExit("message file must be absolute")
    message = message_file.read_text(encoding="utf-8")
    if not message.strip():
        raise SystemExit("commit message must not be empty")
    paths = sys.argv[3:]
    for name in paths:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise SystemExit("files must be named workspace-relative paths")
        if path.parts[0] == ".tmp":
            raise SystemExit("scratch files cannot be committed")
    filesets = ["file:" + json.dumps(name, ensure_ascii=False) for name in paths]
    result = subprocess.run(
        ["jj", "commit", "--message", message, "--", *filesets], cwd=root,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
