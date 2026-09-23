#!/usr/bin/env python3
"""Inspect registered JJ workspaces using only public, read-only commands."""

import argparse
import json
import os
import subprocess
import sys


def inspect(root, main):
    if not os.path.isabs(root):
        raise ValueError("--workspace-root must be absolute")

    def jj(*args):
        return subprocess.run(
            ["jj", "--ignore-working-copy", "--no-pager", *args],
            cwd=root, check=True, text=True, capture_output=True,
        ).stdout.rstrip("\n")

    current = jj("workspace", "root")
    if os.path.normpath(root) != os.path.normpath(current):
        raise ValueError("--workspace-root must be the root printed by jj workspace root")
    names = jj("workspace", "list", "-T", 'name ++ "\\n"').splitlines()
    workspaces = []
    for name in names:
        try:
            workspaces.append({"name": name, "root": jj("workspace", "root", "--name", name)})
        except subprocess.CalledProcessError as error:
            workspaces.append({"name": name, "root": None, "error": error.stderr.strip()})
    matches = [item for item in workspaces if item["root"] == current]
    if len(matches) != 1:
        raise ValueError("current root has no unique registered workspace")
    if main not in names:
        raise ValueError("main workspace is unknown; supply its established name")
    main_workspace = next(item for item in workspaces if item["name"] == main)
    if main_workspace["root"] is None:
        raise ValueError("main workspace root is unavailable: " + main_workspace["error"])
    return {
        "current": matches[0],
        "main": main_workspace,
        "isolated": matches[0]["name"] != main,
        "change_id": jj("log", "-r", "@", "--no-graph", "-T", "change_id"),
        "bookmarks": jj("bookmark", "list", "-r", "@"),
        "workspaces": workspaces,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--main-workspace", default="default")
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.workspace_root, args.main_workspace), indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(detail, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
