#!/usr/bin/env python3
"""Shared repo-grounding project-profile cache: deterministic get/put.

This helper owns the *deterministic* cache I/O for the question-agnostic
project profile that repo-grounding skills reuse. The non-deterministic
derivation (reading manifests, summarizing conventions) is done by the
`repo-profiler` persona only on a miss — never here.

Usage:
    python3 repo-profile-cache.py get
    python3 repo-profile-cache.py put <profile-json-file>

`get` prints exactly one of:
    HIT\\n<profile-json>     a valid entry exists for the current repo state;
                            the profile JSON follows on subsequent lines
    MISS\\n<write-path>      JJ repo, no valid entry — caller derives the
                            profile and calls `put <write-path-or-any-file>`
    NO-CACHE                no writable workspace-local cache — caller derives
                            the profile fresh and skips `put`

`put <file>` reads the profile JSON from <file>, wraps it with a validity
stamp, and writes it atomically to the computed cache path. Prints the path
on success, `NO-CACHE` when the repo/cache is unavailable.

Cache path:
    $(jj workspace root)/.tmp/rocketclaw/repo-profile/<root-id>/<current-id>.json
    (falling back to ./.tmp/rocketclaw when no JJ workspace root is available)
  root-id = the commit ID selected by `jj log -r 'root()'` — the repository
            identity.
  current-id = the commit ID selected by `jj log -r @` — the working state.

Validity (HIT) requires ALL of:
  - the cache file exists and parses as JSON,
  - stored `current_commit_id` == the current working-copy commit ID,
  - stored `profile_schema_version` == PROFILE_SCHEMA_VERSION,
  - the cache key matches the exact JJ working-copy snapshot. JJ snapshots
    tracked and newly added files before commands, so profile-input edits change
    the current commit ID and select a different cache entry.

Cardinal rule: this cache is an optimization, never a correctness dependency.
Every failure mode (not a JJ repo, unreadable/malformed cache, no writable
workspace-local `.tmp`, JJ errors) degrades to NO-CACHE/MISS and exits 0 — it never raises and
never serves a profile it cannot prove fresh.

Pure stdlib. No third-party dependencies.
"""
import json
import os
import secrets
import subprocess
import sys
from datetime import datetime, timezone

# Bump when the profile schema changes so a newer reader never reuses an
# entry written under an older (narrower) schema.
PROFILE_SCHEMA_VERSION = "2"

# --- Profile-input set (the schema-derived superset, per the plan's R3) -------
# This documents the files from which the profiler derives its result. JJ's
# exact working-copy commit ID now provides cache invalidation for all edits.

# Dependency manifests + lockfiles. Matched by basename at ANY depth so a
# monorepo workspace's manifest also invalidates. The profiler derives
# stack/deps for ANY language, so this list must span ecosystems, not just JS;
# an omitted manifest would make the derived profile incomplete.
_MANIFEST_LOCKFILE = {
    # JavaScript / TypeScript / Deno
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "pnpm-workspace.yaml", "bun.lock", "bun.lockb", "npm-shrinkwrap.json",
    "deno.json", "deno.jsonc", "deno.lock",
    # Monorepo / workspace orchestrators
    "nx.json", "lerna.json", "turbo.json", "rush.json",
    # Go (incl. workspaces)
    "go.mod", "go.sum", "go.work", "go.work.sum",
    # Rust
    "Cargo.toml", "Cargo.lock",
    # Ruby
    "Gemfile", "Gemfile.lock", "gems.rb", "gems.locked",
    # Python
    "pyproject.toml", "poetry.lock", "Pipfile", "Pipfile.lock",
    "requirements.txt", "setup.py", "setup.cfg",
    "uv.lock", "pdm.lock", "environment.yml", "environment.yaml",
    # PHP
    "composer.json", "composer.lock",
    # JVM (Maven / Gradle incl. version catalogs)
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
    "settings.gradle.kts", "libs.versions.toml", "build.sbt",
    # Elixir / Dart
    "mix.exs", "mix.lock", "pubspec.yaml", "pubspec.lock",
    # Swift / iOS (a live target for this project)
    "Package.swift", "Package.resolved", "Podfile", "Podfile.lock",
    "Cartfile", "Cartfile.resolved",
    # .NET
    "packages.config", "Directory.Packages.props", "Directory.Build.props",
    "paket.dependencies", "paket.lock",
    # C / C++
    "CMakeLists.txt", "conanfile.txt", "conanfile.py", "vcpkg.json",
    # Haskell
    "stack.yaml", "stack.yaml.lock", "cabal.project",
}

# Project-file extensions whose presence or version edit changes the stack
# profile. Suffix-matched at any depth (e.g. Foo.csproj, App.sln).
_PROJECT_FILE_SUFFIXES = (
    ".csproj", ".fsproj", ".vbproj", ".sln", ".cabal", ".tf", ".tfvars",
)

_LICENSE = {"LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"}

# Topology / deployment sources. Basename match at any depth — these determine
# the derived deployment model (monolith / multi-service / serverless).
_TOPOLOGY = {
    "Dockerfile", "Containerfile",
    "docker-compose.yml", "docker-compose.yaml",
    "vercel.json", "netlify.toml", "fly.toml", "render.yaml",
    "serverless.yml", "serverless.yaml", "app.yaml", "Procfile",
    # IaC descriptors that define the deployment topology.
    "Pulumi.yaml", "Pulumi.yml", "Chart.yaml",
    # CI descriptors outside .github/workflows/ (that prefix is handled below).
    ".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml",
}

# Path prefixes whose contents shape the profile (conventions / CI / deploy).
_INPUT_PREFIXES = (
    ".github/workflows/", ".circleci/",
    "terraform/", "k8s/", "kubernetes/",
)

# Root-level instruction/doc files cached in the profile. Matched ONLY at the
# repo root — subdirectory-scoped instruction files are NOT cached; consumers
# re-glob those fresh, so a subdir change
# must not invalidate the root profile.
_ROOT_DOCS = {
    "AGENTS.md",
    "CONCEPTS.md", "STRATEGY.md",
    "ARCHITECTURE.md", "README.md", "CONTRIBUTING.md",
}

# Runtime / tool version selectors that pin a language or tool version OUTSIDE
# the manifests (the profiler reads these for stack versions). Basename match.
_VERSION_SELECTORS = {
    ".nvmrc", ".node-version", ".python-version", ".ruby-version",
    ".java-version", ".go-version", ".terraform-version",
    ".tool-versions", "mise.toml", ".mise.toml", ".sdkmanrc",
}


def is_profile_input(path: str) -> bool:
    """True when a path is one the cached profile derives from.

    Deliberately a conservative superset of inputs feeding the
    stack/deps/topology/conventions profile.
    """
    base = os.path.basename(path)
    if (
        base in _MANIFEST_LOCKFILE
        or base in _LICENSE
        or base in _TOPOLOGY
        or base in _VERSION_SELECTORS
    ):
        return True
    if base.endswith(_PROJECT_FILE_SUFFIXES):
        return True
    if "/" not in path and base in _ROOT_DOCS:
        return True
    if path.startswith(_INPUT_PREFIXES):
        return True
    return False


def jj(*args: str) -> "str | None":
    """Run a JJ command; return stripped stdout, or None on any failure."""
    try:
        result = subprocess.run(
            ["jj", *args], capture_output=True, text=True, check=False
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def workspace_root() -> str:
    """Use the JJ workspace root, falling back to the local directory."""
    return jj("workspace", "root") or os.getcwd()


def cache_path(root: str, current: str) -> str:
    cache_root = os.path.join(
        workspace_root(), ".tmp", "rocketclaw", "repo-profile"
    )
    return os.path.join(cache_root, root, f"{current}.json")


def resolve_keys() -> "tuple[str, str] | None":
    """The (root commit ID, current commit ID) key for a usable JJ repo."""
    template = 'commit_id ++ "\\n"'
    root = jj("log", "-r", "root()", "--no-graph", "-T", template)
    current = jj("log", "-r", "@", "--no-graph", "-T", template)
    if not root or not current:
        return None
    return root, current


_PROFILE_KEYS = ("stack", "dependencies", "topology", "conventions", "vocabulary")


def is_valid_profile(profile: object) -> bool:
    """A profile must be an object carrying every expected top-level key. This
    rejects a profiler failure that still returned JSON — a wrapper/error object
    or a partial result — which would otherwise be cached and served as a HIT,
    leaving consumers to skip fresh derivation and read missing fields from a
    broken object."""
    return isinstance(profile, dict) and all(k in profile for k in _PROFILE_KEYS)


def do_get() -> int:
    keys = resolve_keys()
    if keys is None:
        print("NO-CACHE")
        return 0
    root, current = keys
    path = cache_path(root, current)

    def miss() -> int:
        print("MISS")
        print(path)
        return 0

    # A missing file raises FileNotFoundError (an OSError) and degrades to the
    # same MISS, so no separate existence check is needed.
    try:
        with open(path) as f:
            # Reject a cache file not owned by us so a planted workspace file
            # cannot feed attacker-controlled text into the agent as the
            # "profile" (indirect prompt injection). Skip where geteuid is
            # unavailable (non-POSIX).
            geteuid = getattr(os, "geteuid", None)
            if geteuid is not None and os.fstat(f.fileno()).st_uid != geteuid():
                return miss()
            doc = json.load(f)
    except (OSError, ValueError):
        return miss()

    profile = doc.get("profile") if isinstance(doc, dict) else None
    if (
        not isinstance(doc, dict)
        or doc.get("current_commit_id") != current
        or doc.get("profile_schema_version") != PROFILE_SCHEMA_VERSION
        or not is_valid_profile(profile)
    ):
        return miss()

    print("HIT")
    print(json.dumps(profile))
    return 0


def do_put(profile_file: str) -> int:
    keys = resolve_keys()
    if keys is None:
        print("NO-CACHE")
        return 0
    root, current = keys

    try:
        with open(profile_file) as f:
            profile = json.load(f)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"repo-profile-cache: cannot read profile: {exc}\n")
        print("NO-CACHE")  # nothing persisted; keep the stdout contract
        return 0  # degrade — never block the caller

    # Shape guard: the profile must be an object carrying the expected top-level
    # keys. A misbehaving profiler that returns garbage JSON (`{}`, `"oops"`,
    # `[]`, `42`) or a partial/error object must not be cached and then served
    # to every skill as the agnostic profile. Reject it (the caller already has
    # its own derived profile for this run; the next run re-derives).
    if not is_valid_profile(profile):
        sys.stderr.write(
            "repo-profile-cache: profile is not a valid profile object; not caching\n"
        )
        print("NO-CACHE")
        return 0

    doc = {
        "profile_schema_version": PROFILE_SCHEMA_VERSION,
        "root_commit_id": root,
        "current_commit_id": current,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
    }

    path = cache_path(root, current)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Atomic write: temp file in the same dir + os.replace (atomic on
        # POSIX) so a concurrent reader never sees a torn JSON.
        tmp = os.path.join(
            os.path.dirname(path), f".tmp-{secrets.token_hex(12)}.json"
        )
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(doc, f)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except Exception as exc:  # never block the caller, whatever the failure
        sys.stderr.write(f"repo-profile-cache: cannot write cache: {exc}\n")
        print("NO-CACHE")
        return 0

    print(path)
    return 0


def usage() -> int:
    sys.stderr.write(
        "usage: repo-profile-cache.py get | put <profile-json-file>\n"
    )
    return 2


def main(argv: "list[str]") -> int:
    if len(argv) < 2:
        return usage()
    cmd = argv[1]
    if cmd == "get":
        return do_get()
    if cmd == "put":
        if len(argv) != 3:
            return usage()
        return do_put(argv[2])
    return usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
