#!/usr/bin/env python3
"""Check a committed tree against its branch's correction anchor, without changing Git or files.

Only README files that already exist at the anchor are protected. New research,
including new README files, may be added. No missing object or policy is skipped.
The caller must supply the destination branch; a pull request's head branch name
does not identify the policy of its destination.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

DEFAULT_POLICY = Path(__file__).with_name("publication_policy.json")
DEFAULT_REPO = Path(__file__).resolve().parents[1]
FULL_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")


class GuardError(RuntimeError):
    """The candidate cannot be accepted with the available local evidence."""


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    try:
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, env=env)
    except OSError as exc:
        raise GuardError(f"Cannot run Git: {exc}") from exc
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise GuardError(f"Git {' '.join(args)} failed: {detail}")
    return result


def anchor_for(policy_path: Path, branch: str) -> str:
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GuardError(f"Cannot read publication policy: {exc}") from exc
    if not isinstance(policy, dict) or policy.get("version") != 1:
        raise GuardError("Publication policy must have version 1")
    branches = policy.get("branches")
    if not isinstance(branches, dict) or branch not in branches:
        raise GuardError(f"No publication policy for destination branch {branch!r}")
    entry = branches[branch]
    anchor = entry.get("baseline") if isinstance(entry, dict) else None
    if not isinstance(anchor, str) or not FULL_SHA.fullmatch(anchor):
        raise GuardError(f"Invalid full baseline commit for {branch!r}")
    return anchor


def commit(repo: Path, revision: str, description: str) -> str:
    result = git(repo, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}", check=False)
    if result.returncode:
        raise GuardError(f"{description} commit is unavailable locally: {revision}. Fetch full history and retry.")
    return result.stdout.decode("ascii").strip()


def readmes(repo: Path, revision: str) -> dict[bytes, tuple[bytes, bytes, bytes]]:
    """Git mode, object kind and blob identity preserve contents and the original path."""
    result = {}
    for record in git(repo, "ls-tree", "-r", "-z", "--full-tree", revision).stdout.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        name = path.rsplit(b"/", 1)[-1].lower()
        if name == b"readme" or name.startswith(b"readme."):
            mode, kind, oid = metadata.split(b" ")
            result[path] = (mode, kind, oid)
    return result


def check_publication(repo: Path, branch: str, revision: str, policy_path: Path = DEFAULT_POLICY) -> dict:
    anchor = commit(repo, anchor_for(policy_path, branch), "Required baseline")
    candidate = commit(repo, revision, "Candidate")
    ancestry = git(repo, "merge-base", "--is-ancestor", anchor, candidate, check=False)
    if ancestry.returncode == 1:
        raise GuardError(f"Candidate {candidate} does not contain required baseline {anchor} for {branch}")
    if ancestry.returncode:
        raise GuardError("Cannot establish baseline ancestry; fetch full history before publishing")
    before = readmes(repo, anchor)
    if not before:
        raise GuardError("The baseline contains no README files; refusing an empty protection set")
    after = readmes(repo, candidate)
    changed = sorted(path for path, entry in before.items() if after.get(path) != entry)
    if changed:
        paths = ", ".join(path.decode("utf-8", errors="backslashreplace") for path in changed)
        raise GuardError("Protected README changed, removed, renamed or changed mode: " + paths)
    return {
        "branch": branch,
        "baseline": anchor,
        "candidate": candidate,
        "protected_readmes": len(before),
        "new_readmes": len(after.keys() - before.keys()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch", required=True, help="Destination branch, not the PR head branch")
    parser.add_argument("--commit", default="HEAD", help="Committed candidate to inspect (default: HEAD)")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args(argv)
    try:
        result = check_publication(args.repo, args.branch, args.commit, args.policy)
    except GuardError as exc:
        print(f"PUBLICATION BLOCKED: {exc}", file=sys.stderr)
        return 1
    print("PUBLICATION GUARD PASS: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
