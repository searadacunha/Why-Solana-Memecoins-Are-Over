#!/usr/bin/env python3
"""One-time, auditable replacement of generic Git subjects in this repository.

The rewrite changes messages only. Original SHA references are retained as
footers, while author/committer names and dates and all tree objects stay intact.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = "searadacunha/Why-Solana-Memecoins-Are-Over"
JOKE = "fixed the thing that broke the other thing"
TOPICS = {
    "rpc_client": "RPC response validation",
    "a1_null_model": "shared-funder null-model detection",
    "hlib": "Solana public-key checks",
    "p1_readme_check": "README claim verification",
    "run_all": "offline reproducibility",
    "statlib": "statistical estimators",
    "splitlib": "funding-split detection",
    "settings": "Helius API settings",
    "expl_ledger": "on-chain withdrawal accounting",
    "05_trace_origin": "multi-hop funding tracing",
    "scan_gateway_dispatch": "gateway funding monitoring",
    "p0_pitfalls_check": "methodological falsification",
    "check_no_secrets": "publication security checks",
    "sanitize_data": "public data sanitization",
    "redact": "sensitive data redaction",
    "exit_ladder": "exit-policy backtesting",
    "v05_creation_block": "creation-slot purchases",
    "v06_curve_ladder": "bonding-curve reconstruction",
    "ACT_IV": "out-of-sample research",
    "METHODOLOGY": "research methodology",
    "PITFALLS": "failure-mode investigations",
    "PATTERN": "2024 funding pattern",
    "EXPLOITATION": "historical trade execution",
    "README": "research narrative",
    "ci": "CI checks",
}
def git(*args):
    return subprocess.check_output(["git", *args], text=True).rstrip("\n")
def parents(sha):
    return git("rev-list", "--parents", "-n", "1", sha).split()[1:]
def changes(sha, ps):
    args = (["diff", "--name-status", "--no-renames", ps[0], sha] if ps else
            ["diff-tree", "--root", "--no-commit-id", "--name-status", "-r", sha])
    out = []
    for line in git(*args).splitlines():
        parts = line.split("\t")
        if len(parts) > 1:
            out.append((parts[0], parts[-1]))
    return out
def title(sha, ps, pairs):
    if not ps:
        return "chore: initialize the on-chain memecoin research repository"
    paths = [p for _, p in pairs]
    if not paths:
        return "chore(history): record a metadata-only change"
    code = [p for p in paths if p.startswith("code/") and p.endswith(".py")]
    tests = [p for p in paths if p.startswith("tests/")]
    docs = [p for p in paths if p.endswith(".md") or p.startswith("docs/")]
    data = [p for p in paths if p.startswith(("data/", "figures/"))]
    ci = [p for p in paths if p.startswith(".github/")]
    configs = [p for p in paths if p in ("mypy.ini", "ruff.toml", "requirements.txt")]
    key = (code or docs or tests or paths)[0]
    stem = Path(key).stem
    topic = TOPICS.get(stem, stem.replace("_", " ").replace("-", " "))
    scope = ("rpc" if stem == "rpc_client" else
             "funding" if any(t in stem.lower() for t in ("split", "funder", "gateway", "origin")) else
             "research" if stem == "README" else "analysis")
    if len(ps) > 1:
        return f"merge({scope}): integrate {topic} investigation changes"
    if code and tests:
        return f"fix({scope}): cover {topic} with regression tests"
    if code and data:
        return f"research({scope}): update {topic} and measured artefacts"
    if code and docs:
        return f"research({scope}): align {topic} code and documentation"
    if code:
        if any(status == "A" and p in code for status, p in pairs):
            return f"feat({scope}): implement {topic}"
        return f"refactor({scope}): refine {topic} implementation"
    if tests:
        return f"test({scope}): expand {topic} regression coverage"
    if docs and data:
        return f"docs({scope}): update {topic} and supporting evidence"
    if docs:
        return f"docs({scope}): revise {topic} and its limitations"
    if data:
        return f"data(research): update {Path(data[0]).stem.replace('_', ' ')} evidence"
    if ci:
        return "ci: improve reproducibility and validation checks"
    if configs:
        return f"chore(tooling): update {Path(configs[0]).name}"
    return f"chore(research): update {topic} files"
def path():
    return Path(os.environ["RUNNER_TEMP"]) / "research-commit-messages.json"
def plan():
    if os.environ.get("GITHUB_REPOSITORY") != REPO:
        raise RuntimeError("Not authorized to change this repository")
    if git("rev-parse", "main") != os.environ.get("GITHUB_SHA"):
        raise RuntimeError("Main has moved since this workflow was started")
    mapping = {}
    for sha in git("rev-list", "--reverse", "main").splitlines():
        if git("show", "-s", "--format=%B", sha).strip() == JOKE:
            ps = parents(sha)
            mapping[sha] = title(sha, ps, changes(sha, ps))
    if len(mapping) != 124:
        raise RuntimeError(f"Expected 124 original generic messages; got {len(mapping)}")
    assert all(s != JOKE and ": " in s for s in mapping.values())
    path().write_text(json.dumps(mapping, indent=2) + "\n")
    print("124 planned replacements, unique subjects:", len(set(mapping.values())))
    for sha, subject in mapping.items():
        print(sha[:12], subject)
def filter_message():
    raw = sys.stdin.buffer.read()
    mapping = json.loads(path().read_text())
    sha = os.environ.get("GIT_COMMIT", "")
    if sha in mapping:
        sys.stdout.buffer.write(
            (mapping[sha] + "\n\nOriginal-Commit: " + sha + "\n").encode())
    else:
        sys.stdout.buffer.write(raw)
def verify():
    mapping = json.loads(path().read_text())
    old = os.environ["ORIGINAL_HEAD"]
    if git("rev-parse", old + "^{tree}") != git("rev-parse", "main^{tree}"):
        raise RuntimeError("HEAD tree changed unexpectedly")
    if git("rev-list", "--count", old) != git("rev-list", "--count", "main"):
        raise RuntimeError("History has a different number of commits")
    seen = []
    for sha in git("rev-list", "main").splitlines():
        subject = git("show", "-s", "--format=%s", sha)
        if subject == JOKE:
            raise RuntimeError("Generic subject remains on main")
        match = re.search(
            r"(?m)^Original-Commit: ([0-9a-f]{40})$",
            git("show", "-s", "--format=%B", sha))
        if match:
            before = match.group(1)
            seen.append(before)
            if before not in mapping or subject != mapping[before]:
                raise RuntimeError("Message mismatch")
            if git("rev-parse", before + "^{tree}") != git("rev-parse", sha + "^{tree}"):
                raise RuntimeError("Historical file tree differs")
            fmt = "%aN%x00%aE%x00%aI%x00%cN%x00%cE%x00%cI"
            if git("show", "-s", "--format=" + fmt, before) != git("show", "-s", "--format=" + fmt, sha):
                raise RuntimeError("Author/committer metadata or dates changed")
    if set(seen) != set(mapping) or len(seen) != 124:
        raise RuntimeError("Historical SHA coverage incomplete")
    print("Verified 124 messages, complete author/date preservation and byte-identical trees")
def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--filter-message", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.plan:
        plan()
    elif args.filter_message:
        filter_message()
    else:
        verify()
if __name__ == "__main__":
    main()
