#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_no_secrets.py -- pre-publication gate. Exits non-zero if the repository
contains anything that must not be published.

Run it before every push:

    python3 code/check_no_secrets.py

Seven classes of leak, each with a rule that is mechanical rather than a
judgement call:

  1. API keys           any 32-hex or UUID-shaped literal in a tracked file, and
                        any live key currently present in the environment.
  2. Credential files   .env, *.key, *.pem, session/cookie dumps, key backups.
  3. Local paths        /Users/..., /home/..., C:\\Users\\... -- a path is an
                        identity leak, and it also means the code will not run
                        anywhere else.
  4. Personal handles   supplied out-of-band via --identity FILE (never
                        committed), matched case-insensitively.
  5. Bot / channel ids  Telegram bot tokens and @handles, webhook URLs.
  6. Redactions         every identifier of code/redactions.json must already be
                        substituted (delegates to sanitize_data.py --check).
  7. Oversized data     files above --max-mb that would bloat the clone; the
                        network caches are expected to be git-ignored.

The point is not that a scanner can prove a repository clean. The point is that
"I checked" becomes a command with an exit code instead of an assertion.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settings  # noqa: E402

SKIP_DIRS = {".git", "__pycache__", "cache", "cache_r1", "transition", "node_modules"}
BINARY_EXT = {".gz", ".zip", ".png", ".jpg", ".jpeg", ".pdf", ".webp", ".mp4"}

PATTERNS = [
    ("api key (32 hex)", re.compile(r"\b[0-9a-fA-F]{32}\b")),
    ("api key (uuid)", re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)),
    ("openai-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("telegram bot token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b")),
    ("telegram handle", re.compile(r"@[A-Za-z0-9_]{4,}bot\b", re.I)),
    ("local path", re.compile(r"(/Users/|/home/[a-z]|[A-Z]:\\\\Users\\\\)")),  # noqa: leakscan
    ("query-string key", re.compile(r"api[-_]?key=[A-Za-z0-9-]{8,}")),
    ("webhook", re.compile(r"https://hooks\.[A-Za-z0-9.]+/[A-Za-z0-9/_-]+")),
]

# Literals that legitimately look like a finding.
ALLOW = re.compile(
    r"api[-_]?key=(\"|'|<|%s|\+\s*_next_key|&|$)"      # documented URL templates
    r"|api[-_]?key=[A-Za-z0-9-]*<"
    r"|/Users/\.\.\."                                   # noqa: leakscan
)

FORBIDDEN_NAMES = re.compile(
    r"(^\.env$|^\.env\.|\.env\.bak|\.env_|^id_rsa|\.pem$|\.key$|"
    r"session.*\.json$|cookies.*\.(json|txt)$)", re.I)


URL_RE = re.compile(r"https?://[^\s\"'<>]+")


def in_url_path(line, pos):
    """True if position `pos` falls inside the path of a URL (before any '?')."""
    for u in URL_RE.finditer(line):
        if u.start() <= pos < u.end():
            q = u.group(0).find("?")
            return q < 0 or pos < u.start() + q
    return False


def tracked_files(root, max_mb):
    """Every file that a `git add .` would pick up, big ones flagged.

    Asks git rather than walking the tree, so that .gitignore is the single source of truth for
    what gets published. A hand-maintained skip list is a second, silent definition of "tracked"
    that drifts from the first: a directory excluded here but not in .gitignore is a file the gate
    never reads and git pushes anyway. SKIP_DIRS remains only as the fallback for a non-git tree.
    """
    rels = None
    try:
        top = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True).stdout.strip()
        # Only trust git when this directory IS the repository root. A project sitting inside a
        # larger repo inherits that repo's .gitignore, and one line there ("data/", say) would
        # silently remove a whole tree from the scan while the gate still prints PUBLISHABLE.
        # A gate that can be blinded by a file it does not read is worse than no gate.
        if os.path.realpath(top) == os.path.realpath(root):
            out = subprocess.run(
                ["git", "-C", root, "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                capture_output=True, text=True, check=True).stdout
            rels = [r for r in out.split("\0") if r]
        else:
            print("  note: %s is inside the repository rooted at %s, whose ignore rules are not\n"
                  "        this project's. Falling back to a full filesystem walk." % (root, top))
    except (subprocess.CalledProcessError, FileNotFoundError):
        rels = None

    if rels is None:
        for base, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for n in sorted(names):
                p = os.path.join(base, n)
                try:
                    size = os.path.getsize(p)
                except OSError:
                    continue
                yield os.path.relpath(p, root), p, size
        return

    for rel in sorted(rels):
        p = os.path.join(root, rel)
        try:
            size = os.path.getsize(p)
        except OSError:
            continue
        yield rel, p, size


def scan_text(rel, path, findings):
    if os.path.splitext(path)[1] in BINARY_EXT:
        return
    try:
        with open(path, encoding="utf-8", errors="strict") as f:
            text = f.read()
    except (UnicodeDecodeError, OSError):
        return
    for line_no, line in enumerate(text.splitlines(), 1):
        if "noqa: leakscan" in line:
            continue
        for name, rx in PATTERNS:
            m = rx.search(line)
            if not m:
                continue
            frag = m.group(0)
            if ALLOW.search(line):
                continue
            # A "32 hex" made of one or two distinct characters is not a key.
            # This is how the Solana System Program id (base58 all-ones,
            # 11111111111111111111111111111111) shows up in every account dump.
            if name.startswith("api key") and len(set(frag)) <= 2:
                continue
            # A key-shaped token inside a URL *path* is a public resource id --
            # token metadata URIs are full of UUIDs. A key in a URL *query
            # string* is a different matter and is caught by its own pattern.
            if name.startswith("api key") and in_url_path(line, m.start()):
                continue
            findings.append((name, rel, line_no, frag[:60]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--identity", help="file of personal strings to forbid "
                                       "(one per line); never commit it")
    ap.add_argument("--max-mb", type=float, default=60.0)
    a = ap.parse_args()
    root = settings.ROOT
    findings, oversized = [], []

    identity = []
    if a.identity:
        with open(a.identity) as f:
            identity = [l.strip().lower() for l in f
                        if l.strip() and not l.startswith("#")]

    live_keys = [k for k in settings.helius_keys() if len(k) >= 12]

    for rel, path, size in tracked_files(root, a.max_mb):
        if FORBIDDEN_NAMES.search(os.path.basename(rel)) and rel != ".env.example":
            findings.append(("credential file", rel, 0, os.path.basename(rel)))
        if size > a.max_mb * 1e6:
            oversized.append((rel, size / 1e6))
        scan_text(rel, path, findings)
        if identity or live_keys:
            if os.path.splitext(path)[1] in BINARY_EXT:
                continue
            try:
                low = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for k in live_keys:
                if k in low:
                    findings.append(("LIVE API KEY", rel, 0, k[:6] + "..."))
            low = low.lower()
            for tok in identity:
                if tok in low:
                    findings.append(("personal identifier", rel, 0, tok))

    print("scanned %s" % root)

    # 6. redaction map fully applied
    rc = subprocess.call([sys.executable,
                          os.path.join(settings.CODE, "sanitize_data.py"), "--check"])

    ok = True
    if findings:
        ok = False
        print("\n%d POTENTIAL LEAK(S):" % len(findings))
        for kind, rel, ln, frag in findings:
            print("  [%-18s] %s:%s  %s" % (kind, rel, ln or "-", frag))
    else:
        print("no key, credential file, local path or personal identifier found")

    if oversized:
        print("\nfiles above %.0f MB (check .gitignore):" % a.max_mb)
        for rel, mb in oversized:
            print("  %8.1f MB  %s" % (mb, rel))

    if rc != 0:
        ok = False
    print("\nVERDICT: %s" % ("PUBLISHABLE" if ok else "DO NOT PUBLISH"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
