#!/usr/bin/env python3
"""Deterministic JJ-revision cache for the shared project profile."""
import json, os, subprocess, sys, time
from datetime import datetime, timezone

VERSION = "2"
KEYS = ("stack", "dependencies", "topology", "conventions", "vocabulary")

def jj(*args, cwd=None):
    try:
        result = subprocess.run(["jj", *args], cwd=cwd, capture_output=True, text=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except OSError:
        return None

def resolve():
    workspace = jj("workspace", "root")
    if not workspace or not os.path.isabs(workspace):
        return None
    workspace = os.path.abspath(workspace)
    roots = jj("log", "-r", "roots(::@ ~ root())", "--no-graph", "--color=never", "-T", 'commit_id ++ "\\n"', cwd=workspace)
    revision = jj("log", "-r", "@", "--no-graph", "--color=never", "-T", "commit_id", cwd=workspace)
    if not roots or not revision:
        return None
    root = sorted(roots.splitlines())[0]
    path = os.path.join(workspace, ".tmp", "rocketclaw", "repo-profile", root, revision + ".json")
    return root, revision, path

def no_cache(message=None):
    if message:
        sys.stderr.write("repo-profile-cache: " + message + "\n")
    print("NO-CACHE")
    return 0

def valid(profile):
    return isinstance(profile, dict) and all(key in profile for key in KEYS)

def get():
    state = resolve()
    if state is None:
        return no_cache()
    root, revision, path = state
    try:
        with open(path) as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        try:
            os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
        except OSError:
            return no_cache()
        print("MISS\n" + path)
        return 0
    profile = document.get("profile") if isinstance(document, dict) else None
    if document.get("profile_schema_version") != VERSION or document.get("root_id") != root or document.get("revision_id") != revision or not valid(profile):
        print("MISS\n" + path)
        return 0
    print("HIT\n" + json.dumps(profile))
    return 0

def put(source):
    state = resolve()
    if state is None:
        return no_cache()
    root, revision, path = state
    if os.path.abspath(source) != os.path.abspath(path):
        return no_cache("JJ revision changed before put; not caching")
    try:
        with open(source) as handle:
            profile = json.load(handle)
    except (OSError, ValueError) as error:
        return no_cache("cannot read profile: " + str(error))
    if not valid(profile):
        return no_cache("profile is not a valid profile object; not caching")
    document = {"profile_schema_version": VERSION, "root_id": root, "revision_id": revision, "built_at": datetime.now(timezone.utc).isoformat(), "profile": profile}
    staging = os.path.join(os.path.dirname(path), f".write-{os.getpid()}-{time.time_ns()}.json")
    try:
        descriptor = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as handle:
            json.dump(document, handle)
        os.replace(staging, path)
    except Exception as error:
        try:
            os.unlink(staging)
        except OSError:
            pass
        return no_cache("cannot write cache: " + str(error))
    print(path)
    return 0

def main(argv):
    if len(argv) == 2 and argv[1] == "get":
        return get()
    if len(argv) == 3 and argv[1] == "put":
        return put(argv[2])
    sys.stderr.write("usage: repo-profile-cache.py get | put <profile-json-file>\n")
    return 2

if __name__ == "__main__":
    sys.exit(main(sys.argv))
