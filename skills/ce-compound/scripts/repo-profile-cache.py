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
    NO-CACHE                no JJ repo or no writable cache — caller derives
                            the profile fresh and skips `put`

`put <file>` reads the profile JSON from <file>, wraps it with a validity
stamp, and writes it atomically to the computed cache path. Prints the path
on success, `NO-CACHE` when the repo/cache is unavailable.

Cache path:
    <workspace-root>/.tmp/rocketclaw/repo-profile/<root-sha>/<revision-sha>.json
  root-sha = lexicographically-first commit in `roots(::@ ~ root())`
              (deterministic even for multi-root histories) — the repo identity.
  revision-sha = the commit ID of `@` — the working-copy state.

Validity (HIT) requires ALL of:
  - the cache file exists and parses as JSON,
  - stored `revision_sha` == the current working-copy revision,
  - stored `profile_schema_version` == PROFILE_SCHEMA_VERSION,
  - no profile-input path differs from the parent per `jj diff -r @ --name-only`
    (the schema-derived superset in `is_profile_input`; a newly-added manifest
    or AGENTS.md must invalidate).

Cardinal rule: this cache is an optimization, never a correctness dependency.
Every failure mode (not a JJ repo, unreadable/malformed cache, no writable
workspace-local `.tmp`, JJ errors) degrades to NO-CACHE/MISS and exits 0 — it
never raises and never serves a profile it cannot prove fresh.

Pure stdlib. No third-party dependencies.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

# Bump when the profile schema changes so a newer reader never reuses an
# entry written under an older (narrower) schema.
PROFILE_SCHEMA_VERSION = "2"

# --- Profile-input set (the schema-derived superset, per the plan's R3) -------
# Any change to one of these — including a NEW untracked file — must invalidate
# the cached profile. Conservative by design: over-invalidating costs a
# re-derive; under-invalidating serves a stale profile (a cardinal-rule break).

# Dependency manifests + lockfiles. Matched by basename at ANY depth so a
# monorepo workspace's manifest also invalidates. The profiler derives
# stack/deps for ANY language, so this list must span ecosystems, not just JS —
# an omitted manifest means a dirty dep bump at an unchanged base serves a stale
# profile (a cardinal-rule break).
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
    ".cursor/", ".github/workflows/", ".circleci/",
    "terraform/", "k8s/", "kubernetes/",
)

# Root-level instruction/doc files cached in the profile. Matched ONLY at the
# repo root — subdirectory-scoped instruction files (e.g. nested CLAUDE.md /
# AGENTS.md) are NOT cached; consumers re-glob those fresh, so a subdir change
# must not invalidate the root profile.
_ROOT_DOCS = {
    "AGENTS.md", "CLAUDE.md", "GEMINI.md",
    "CONCEPTS.md", "STRATEGY.md",
    "ARCHITECTURE.md", "README.md", "CONTRIBUTING.md",
    ".cursorrules",  # legacy root-level Cursor rules (the profiler reads it)
}

# Runtime / tool version selectors that pin a language or tool version OUTSIDE
# the manifests (the profiler reads these for stack versions). Basename match.
_VERSION_SELECTORS = {
    ".nvmrc", ".node-version", ".python-version", ".ruby-version",
    ".java-version", ".go-version", ".terraform-version",
    ".tool-versions", "mise.toml", ".mise.toml", ".sdkmanrc",
}


def is_profile_input(path: str) -> bool:
    """True when a changed path is one the cached profile derives from.

    Deliberately a conservative superset: anything plausibly feeding the
    stack/deps/topology/conventions profile invalidates. Over-matching costs a
    re-derive; under-matching serves a stale profile (a cardinal-rule break).
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


def root_sha() -> "str | None":
    out = jj(
        "log",
        "-r",
        "roots(::@ ~ root())",
        "--no-graph",
        "-T",
        'commit_id ++ "\\n"',
    )
    if not out:
        return None
    # Multi-root histories print several SHAs; pick a deterministic one.
    return sorted(out.split("\n"))[0]


def changed_paths() -> "list[str] | None":
    """Paths changed in `@`, or None if JJ could not determine them.

    JJ snapshots non-ignored working-copy files, so newly-added inputs appear.
    None signals "could not determine cleanliness" — the caller treats that
    conservatively as a miss rather than serving an unverified profile.
    """
    out = jj("diff", "-r", "@", "--name-only")
    if out is None:
        return None
    return [line for line in out.splitlines() if line]


def workspace_root() -> str:
    """Return the JJ workspace root, or the current directory as fallback."""
    return jj("workspace", "root") or os.getcwd()


def cache_root() -> str:
    return os.path.join(workspace_root(), ".tmp", "rocketclaw", "repo-profile")


def cache_path(root: str, revision: str) -> str:
    return os.path.join(cache_root(), root, f"{revision}.json")


def resolve_keys() -> "tuple[str, str] | None":
    """The (root-sha, revision-sha) key, or None outside a usable JJ repo."""
    root = root_sha()
    revision = jj("log", "-r", "@", "--no-graph", "-T", "commit_id")
    if not root or not revision:
        return None
    return root, revision


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
    root, revision = keys
    path = cache_path(root, revision)

    def miss() -> int:
        print("MISS")
        print(path)
        return 0

    # A missing file raises FileNotFoundError (an OSError) and degrades to the
    # same MISS, so no separate existence check is needed.
    try:
        with open(path) as f:
            # Reject cache files not owned by us before loading agent context.
            geteuid = getattr(os, "geteuid", None)
            if geteuid is not None and os.fstat(f.fileno()).st_uid != geteuid():
                return miss()
            doc = json.load(f)
    except (OSError, ValueError):
        return miss()

    profile = doc.get("profile") if isinstance(doc, dict) else None
    if (
        not isinstance(doc, dict)
        or doc.get("revision_sha") != revision
        or doc.get("profile_schema_version") != PROFILE_SCHEMA_VERSION
        or not is_valid_profile(profile)
    ):
        return miss()

    changed = changed_paths()
    # Could not determine cleanliness, or a profile input changed/was added.
    if changed is None or any(is_profile_input(p) for p in changed):
        return miss()

    print("HIT")
    print(json.dumps(profile))
    return 0


def do_put(profile_file: str) -> int:
    keys = resolve_keys()
    if keys is None:
        print("NO-CACHE")
        return 0
    root, revision = keys

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

    # Do not cache a profile while the working-copy revision changes profile
    # inputs. This preserves the clean-base reuse contract across workspaces.
    changed = changed_paths()
    if changed is None or any(is_profile_input(p) for p in changed):
        sys.stderr.write(
            "repo-profile-cache: profile inputs are dirty; not caching\n"
        )
        print("NO-CACHE")
        return 0

    doc = {
        "profile_schema_version": PROFILE_SCHEMA_VERSION,
        "root_sha": root,
        "revision_sha": revision,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
    }

    path = cache_path(root, revision)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Atomic write: a unique file in the workspace-local cache directory
        # plus os.replace so a concurrent reader never sees torn JSON.
        tmp = os.path.join(
            os.path.dirname(path), f".write-{os.getpid()}-{time.time_ns()}.json"
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
