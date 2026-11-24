# Workspace and scratch paths

Run `jj root` with the tool cwd set to the absolute starting directory to identify the active workspace. Set the cwd for repo commands and helpers to the absolute workspace. Outside JJ, find the nearest existing checkout by its `.git` directory or file for read-only config discovery. Do not run Git or initialize a repo.

Use the workspace's `.tmp/` for temporary data, or the absolute starting directory's `.tmp/` outside JJ. Require that `.tmp/` is writable, user-owned, and not a symlink. Create a private unique directory inside it for each run. If local scratch is unavailable, report the blocker and follow the affected phase's fallback. Never switch to system temp.
