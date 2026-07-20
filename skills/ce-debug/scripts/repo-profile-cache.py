#!/usr/bin/env python3
"""Deterministic, workspace-local cache for the shared repository profile.

The caller derives a question-agnostic profile on a miss. This helper only
resolves JJ identity, validates cache freshness and profile shape, and performs
atomic cache I/O.

Usage:
    python3 repo-profile-cache.py get
    python3 repo-profile-cache.py put <profile-json-file>

Cache path:
    <workspace-root>/.tmp/rocketclaw/repo-profile/<change-id>/<commit-id>.json

Every unavailable or unverifiable cache state degrades to MISS or NO-CACHE and
exit 0. The cache is an optimization, never a correctness dependency.
"""

import json
import os
import secrets
import subprocess
import sys
from datetime import datetime, timezone


PROFILE_SCHEMA_VERSION = "4"
CACHE_NAMESPACE = os.path.join(".tmp", "rocketclaw", "repo-profile")

# Conservative superset of files used to derive the profile. Over-invalidation
# costs one derivation; under-invalidation could serve stale project context.
_MANIFEST_LOCKFILE = {
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "pnpm-workspace.yaml", "bun.lock", "bun.lockb", "npm-shrinkwrap.json",
    "deno.json", "deno.jsonc", "deno.lock", "nx.json", "lerna.json",
    "turbo.json", "rush.json", "go.mod", "go.sum", "go.work", "go.work.sum",
    "Cargo.toml", "Cargo.lock", "Gemfile", "Gemfile.lock", "gems.rb",
    "gems.locked", "pyproject.toml", "poetry.lock", "Pipfile", "Pipfile.lock",
    "requirements.txt", "setup.py", "setup.cfg", "uv.lock", "pdm.lock",
    "environment.yml", "environment.yaml", "composer.json", "composer.lock",
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
    "settings.gradle.kts", "libs.versions.toml", "build.sbt", "mix.exs",
    "mix.lock", "pubspec.yaml", "pubspec.lock", "Package.swift",
    "Package.resolved", "Podfile", "Podfile.lock", "Cartfile",
    "Cartfile.resolved", "packages.config", "Directory.Packages.props",
    "Directory.Build.props", "paket.dependencies", "paket.lock",
    "CMakeLists.txt", "conanfile.txt", "conanfile.py", "vcpkg.json",
    "stack.yaml", "stack.yaml.lock", "cabal.project",
}
_PROJECT_FILE_SUFFIXES = (
    ".csproj", ".fsproj", ".vbproj", ".sln", ".cabal", ".tf", ".tfvars",
)
_LICENSE = {"LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"}
_TOPOLOGY = {
    "Dockerfile", "Containerfile", "docker-compose.yml", "docker-compose.yaml",
    "vercel.json", "netlify.toml", "fly.toml", "render.yaml", "serverless.yml",
    "serverless.yaml", "app.yaml", "Procfile", "Pulumi.yaml", "Pulumi.yml",
    "Chart.yaml", ".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml",
}
_INPUT_PREFIXES = (
    ".cursor/", ".github/workflows/", ".circleci/", "terraform/", "k8s/",
    "kubernetes/",
)
_ROOT_DOCS = {
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "CONCEPTS.md", "STRATEGY.md",
    "ARCHITECTURE.md", "README.md", "CONTRIBUTING.md", ".cursorrules",
}
_VERSION_SELECTORS = {
    ".nvmrc", ".node-version", ".python-version", ".ruby-version",
    ".java-version", ".go-version", ".terraform-version", ".tool-versions",
    "mise.toml", ".mise.toml", ".sdkmanrc",
}


def is_profile_input(path: str) -> bool:
    base = os.path.basename(path)
    if base in (_MANIFEST_LOCKFILE | _LICENSE | _TOPOLOGY | _VERSION_SELECTORS):
        return True
    if base.endswith(_PROJECT_FILE_SUFFIXES):
        return True
    if "/" not in path and base in _ROOT_DOCS:
        return True
    return path.startswith(_INPUT_PREFIXES)


def jj(*args: str, cwd: "str | None" = None) -> "str | None":
    try:
        result = subprocess.run(
            ["jj", "--no-pager", "--color", "never", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def workspace_root() -> str:
    """Resolve `jj workspace root`, with the physical cwd as the fallback."""
    return jj("workspace", "root") or os.path.realpath(os.getcwd())


def changed_paths(workspace: str) -> "list[str] | None":
    """Return both endpoints from JJ summary entries, including renames."""
    out = jj("diff", "--summary", "-r", "@", cwd=workspace)
    if out is None:
        return None

    def unquote(path: str) -> str:
        path = path.strip()
        if len(path) >= 2 and path[0] == '"' and path[-1] == '"':
            return path[1:-1]
        return path

    def expand(path: str) -> "list[str]":
        if " => " not in path:
            return [unquote(path)]
        if "{" in path and "}" in path:
            prefix, rest = path.split("{", 1)
            middle, suffix = rest.split("}", 1)
            source, destination = middle.split(" => ", 1)
            return [unquote(prefix + source + suffix), unquote(prefix + destination + suffix)]
        return [unquote(item) for item in path.split(" => ", 1)]

    paths: list[str] = []
    for line in out.splitlines():
        if line.strip():
            paths.extend(path for path in expand(line[2:]) if path)
    return paths


def resolve_keys() -> "tuple[str, str, str] | None":
    workspace = workspace_root()
    ids = jj(
        "log", "-r", "@", "--no-graph", "-T",
        'change_id ++ "\\n" ++ commit_id',
        cwd=workspace,
    )
    if not ids:
        return None
    parts = ids.splitlines()
    if len(parts) != 2 or not all(parts):
        return None
    return workspace, parts[0], parts[1]


def cache_path(workspace: str, change_id: str, commit_id: str) -> str:
    return os.path.join(
        workspace, CACHE_NAMESPACE, change_id, f"{commit_id}.json"
    )


def _object_with(value: object, fields: dict[str, object]) -> bool:
    if not isinstance(value, dict):
        return False
    for name, expected in fields.items():
        if name not in value:
            return False
        item = value.get(name)
        if expected == "list" and not isinstance(item, list):
            return False
        if expected == "bool" and not isinstance(item, bool):
            return False
        if expected == "nullable-string" and item is not None and not isinstance(item, str):
            return False
    return True


def is_valid_profile(profile: object) -> bool:
    """Validate the complete shared schema before persisting or serving it."""
    if not isinstance(profile, dict):
        return False
    return (
        _object_with(profile.get("stack"), {
            "languages": "list", "frameworks": "list", "tooling": "list",
        })
        and _object_with(profile.get("dependencies"), {
            "manifests": "list", "lockfiles": "list", "top_level": "list",
            "project_license": "nullable-string", "dependency_licenses": "list",
        })
        and _object_with(profile.get("topology"), {
            "monorepo": "bool", "workspaces": "list",
            "deployment": "nullable-string", "api_styles": "list",
            "data_stores": "list", "module_layout": "nullable-string",
        })
        and _object_with(profile.get("conventions"), {
            "instruction_files": "list", "coding_standards": "nullable-string",
            "testing": "nullable-string", "review_process": "nullable-string",
            "strategy": "nullable-string",
        })
        and _object_with(profile.get("vocabulary"), {
            "concepts_present": "bool", "terms": "list",
        })
    )


def do_get() -> int:
    keys = resolve_keys()
    if keys is None:
        print("NO-CACHE")
        return 0
    workspace, change_id, commit_id = keys
    path = cache_path(workspace, change_id, commit_id)

    def miss() -> int:
        print("MISS")
        print(path)
        return 0

    try:
        with open(path) as cache_file:
            geteuid = getattr(os, "geteuid", None)
            if geteuid is not None and os.fstat(cache_file.fileno()).st_uid != geteuid():
                return miss()
            doc = json.load(cache_file)
    except (OSError, ValueError):
        return miss()

    profile = doc.get("profile") if isinstance(doc, dict) else None
    if (
        not isinstance(doc, dict)
        or doc.get("change_id") != change_id
        or doc.get("commit_id") != commit_id
        or doc.get("profile_schema_version") != PROFILE_SCHEMA_VERSION
        or not is_valid_profile(profile)
    ):
        return miss()

    changed = changed_paths(workspace)
    if changed is None or any(is_profile_input(path) for path in changed):
        return miss()

    print("HIT")
    print(json.dumps(profile))
    return 0


def do_put(profile_file: str) -> int:
    keys = resolve_keys()
    if keys is None:
        print("NO-CACHE")
        return 0
    workspace, change_id, commit_id = keys

    try:
        with open(profile_file) as source:
            profile = json.load(source)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"repo-profile-cache: cannot read profile: {exc}\n")
        print("NO-CACHE")
        return 0

    if not is_valid_profile(profile):
        sys.stderr.write("repo-profile-cache: invalid profile shape; not caching\n")
        print("NO-CACHE")
        return 0

    changed = changed_paths(workspace)
    if changed is None or any(is_profile_input(path) for path in changed):
        sys.stderr.write("repo-profile-cache: profile inputs changed; not caching\n")
        print("NO-CACHE")
        return 0

    doc = {
        "profile_schema_version": PROFILE_SCHEMA_VERSION,
        "change_id": change_id,
        "commit_id": commit_id,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
    }
    path = cache_path(workspace, change_id, commit_id)
    pending: "str | None" = None
    try:
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
        pending = os.path.join(
            directory, f".write-{os.getpid()}-{secrets.token_hex(8)}.json"
        )
        fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "w") as destination:
                json.dump(doc, destination)
            os.replace(pending, path)
            pending = None
        finally:
            if pending is not None:
                try:
                    os.unlink(pending)
                except OSError:
                    pass
    except Exception as exc:
        sys.stderr.write(f"repo-profile-cache: cannot write cache: {exc}\n")
        print("NO-CACHE")
        return 0

    print(path)
    return 0


def usage() -> int:
    sys.stderr.write("usage: repo-profile-cache.py get | put <profile-json-file>\n")
    return 2


def main(argv: "list[str]") -> int:
    if len(argv) == 2 and argv[1] == "get":
        return do_get()
    if len(argv) == 3 and argv[1] == "put":
        return do_put(argv[2])
    return usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
