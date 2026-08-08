#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_no_secrets.py -- pre-publication gate. Exits non-zero if the repository
contains anything that must not be published.

Run it before every push:

    python3 code/check_no_secrets.py --identity identity.txt

Classes of leak, each with a rule that is mechanical rather than a judgement call:

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
  8. Image METADATA     the same patterns, run over text extracted from image
                        metadata (PNG text chunks; JPEG/WebP comment/EXIF/XMP
                        ASCII). Pixel content (a handle rendered in the image, a
                        QR code) is NOT machine-readable from the stdlib alone;
                        the committed OCR side-car data/screens/trades/index.json
                        is plain JSON and is text-scanned like any other file.

WHAT IS SCANNED. The set is `git ls-files --cached --others --exclude-standard`
-- everything a `git add .` then push would carry, INCLUDING files not yet
committed but not git-ignored. So a brand-new, uncommitted script is scanned
before it can ship. `--require-clean` additionally fails if the working tree has
any uncommitted change, which is how CI enforces the README's "checked by code
in this same commit".

INTENTIONAL ATTRIBUTION. Some identity strings are published ON PURPOSE -- the
author signs this dossier, and the trading handle on the committed screenshots
is part of that. They are listed in code/allow_identity.txt (--allow) and a
matching finding is reported as "allowed", never as a failure. This is the
deliberate counterpart to --identity: a denylist of what must never appear, and
an allowlist of what is meant to.

The point is not that a scanner can prove a repository clean. The point is that
"I checked" becomes a command with an exit code instead of an assertion.
"""
from __future__ import annotations

import argparse
import gzip
import os
import re
import struct
import subprocess
import sys
import zlib
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settings  # noqa: E402

SKIP_DIRS = {".git", "__pycache__", "cache", "cache_r1", "transition", "node_modules"}
BINARY_EXT = {".gz", ".zip", ".png", ".jpg", ".jpeg", ".pdf", ".webp", ".mp4"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}

PATTERNS = [
    ("api key (32 hex)", re.compile(r"\b[0-9a-fA-F]{32}\b")),
    ("api key (uuid)", re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)),
    ("openai-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("telegram bot token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b")),
    ("telegram handle", re.compile(r"@[A-Za-z0-9_]{4,}bot\b", re.I)),
    ("telegram reflink", re.compile(r"t\.me/[A-Za-z0-9_]+\?start=[A-Za-z0-9_-]+", re.I)),
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
ASCII_RUN = re.compile(rb"[\x20-\x7e]{6,}")


def in_url_path(line: str, pos: int) -> bool:
    """True if position `pos` falls inside the path of a URL (before any '?')."""
    for u in URL_RE.finditer(line):
        if u.start() <= pos < u.end():
            q = u.group(0).find("?")
            return q < 0 or pos < u.start() + q
    return False


def read_list(path: Optional[str]) -> list[str]:
    if not path or not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l.strip().lower() for l in f
                if l.strip() and not l.startswith("#")]


def tracked_files(root: str, max_mb: float):
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


# --------------------------------------------------------------- image metadata
def _png_text(data: bytes) -> str:
    """Text embedded in PNG tEXt / zTXt / iTXt chunks (never pixel data)."""
    out: list[str] = []
    i = 8  # skip the 8-byte signature
    n = len(data)
    while i + 8 <= n:
        try:
            length = struct.unpack(">I", data[i:i + 4])[0]
        except struct.error:
            break
        ctype = data[i + 4:i + 8]
        body = data[i + 8:i + 8 + length]
        i += 12 + length  # length + type + data + 4-byte CRC
        if ctype == b"tEXt":
            out.append(body.replace(b"\0", b": ").decode("latin-1", "ignore"))
        elif ctype == b"zTXt":
            k, _, rest = body.partition(b"\0")
            comp = rest[1:] if rest else b""
            try:
                out.append(k.decode("latin-1", "ignore") + ": "
                           + zlib.decompress(comp).decode("latin-1", "ignore"))
            except zlib.error:
                pass
        elif ctype == b"iTXt":
            parts = body.split(b"\0", 5)
            if len(parts) == 6:
                out.append(parts[0].decode("utf-8", "ignore") + ": "
                           + parts[5].decode("utf-8", "ignore"))
        if ctype == b"IEND":
            break
    return "\n".join(out)


def image_meta_text(path: str) -> str:
    """Human-readable text carried in an image's METADATA, stdlib only.

    PNG: the text chunks above. JPEG / WebP / others: printable ASCII runs of
    the raw bytes -- which covers EXIF/XMP/comment strings. This is a metadata
    scan, NOT OCR: a handle drawn into the pixels is invisible here (documented
    in the module docstring; its OCR side-car index.json is scanned as JSON)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return ""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return _png_text(data)
    # JPEG / WebP / others: pull printable ASCII runs. Pixel bytes almost never
    # form a 6+ char printable run that also matches a leak PATTERN, so this is
    # low-noise for the specific patterns we look for (paths, keys, handles).
    return "\n".join(m.group(0).decode("ascii", "ignore")
                     for m in ASCII_RUN.finditer(data))


# --------------------------------------------------------------------- scanning
def scan_blob(rel: str, text: str, source: str, findings: list, allow: list[str]) -> None:
    """Run the leak PATTERNS over a blob of text (file body or image metadata),
    routing anything on the allowlist to the 'allowed' bucket instead."""
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
            # A "32 hex" made of one or two distinct characters is not a key
            # (e.g. the Solana System Program id, base58 all-ones).
            if name.startswith("api key") and len(set(frag)) <= 2:
                continue
            # A key-shaped token inside a URL *path* is a public resource id.
            if name.startswith("api key") and in_url_path(line, m.start()):
                continue
            tag = "%s [%s]" % (name, source) if source else name
            # Allow only when the MATCHED fragment itself is intentional (e.g. a
            # reflink containing the author's handle) -- not merely because an
            # allowed word sits elsewhere on the same line, which would let a
            # real key ride along beside it.
            if any(a in frag.lower() for a in allow):
                findings.append(("ALLOWED " + tag, rel, line_no, frag[:60]))
            else:
                findings.append((tag, rel, line_no, frag[:60]))


def scan_identity(rel: str, text: str, source: str, findings: list,
                  identity: list[str], live_keys: list[str], allow: list[str]) -> None:
    low = text.lower()
    suffix = " [%s]" % source if source else ""
    for k in live_keys:
        if k in text:
            findings.append(("LIVE API KEY", rel, 0, k[:6] + "..."))
    for tok in identity:
        if tok in low and tok not in allow:      # denylist wins unless explicitly allowed
            findings.append(("personal identifier" + suffix, rel, 0, tok))
    for a in allow:
        if a in low:
            findings.append(("ALLOWED identifier" + suffix, rel, 0, a))


def read_text(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8", errors="strict") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--identity", help="file of personal strings to forbid "
                                       "(one per line); never commit it")
    ap.add_argument("--allow", default=os.path.join(settings.CODE, "allow_identity.txt"),
                    help="file of identity strings published on purpose (allowlist)")
    ap.add_argument("--max-mb", type=float, default=60.0)
    ap.add_argument("--require-clean", action="store_true",
                    help="also fail if the git working tree has any uncommitted change "
                         "(enforces the README's 'checked by code in this same commit')")
    a = ap.parse_args()
    root = settings.ROOT
    findings: list = []
    allowed: list = []
    oversized: list = []

    identity = read_list(a.identity)
    allow = read_list(a.allow)
    live_keys = [k for k in settings.helius_keys() if len(k) >= 12]

    for rel, path, size in tracked_files(root, a.max_mb):
        if FORBIDDEN_NAMES.search(os.path.basename(rel)) and rel != ".env.example":
            findings.append(("credential file", rel, 0, os.path.basename(rel)))
        if size > a.max_mb * 1e6:
            oversized.append((rel, size / 1e6))
        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXT:
            meta = image_meta_text(path)
            if meta:
                scan_blob(rel, meta, "image metadata", findings, allow)
                if identity or live_keys or allow:
                    scan_identity(rel, meta, "image metadata", findings,
                                  identity, live_keys, allow)
            continue
        if ext in BINARY_EXT:
            continue
        text = read_text(path)
        if text is None:
            continue
        scan_blob(rel, text, "", findings, allow)
        if identity or live_keys or allow:
            scan_identity(rel, text, "", findings, identity, live_keys, allow)

    # Split allowed (intentional) from real findings.
    allowed = [f for f in findings if f[0].startswith("ALLOWED")]
    findings = [f for f in findings if not f[0].startswith("ALLOWED")]

    print("scanned %s" % root)

    # 6. redaction map fully applied
    rc = subprocess.call([sys.executable,
                          os.path.join(settings.CODE, "sanitize_data.py"), "--check"])

    ok = True
    if findings:
        ok = False
        print("\n%d POTENTIAL LEAK(S):" % len(findings))
        for kind, rel, ln, frag in findings:
            print("  [%-24s] %s:%s  %s" % (kind, rel, ln or "-", frag))
    else:
        print("no key, credential file, local path or personal identifier found")

    if allowed:
        print("\n%d ALLOWED (published on purpose, see code/allow_identity.txt):" % len(allowed))
        for kind, rel, ln, frag in allowed:
            print("  [%-24s] %s:%s  %s" % (kind, rel, ln or "-", frag))

    if oversized:
        print("\nfiles above %.0f MB (check .gitignore):" % a.max_mb)
        for rel, mb in oversized:
            print("  %8.1f MB  %s" % (mb, rel))

    if a.require_clean:
        dirty = subprocess.run(["git", "-C", root, "status", "--porcelain"],
                               capture_output=True, text=True).stdout.strip()
        if dirty:
            ok = False
            print("\n--require-clean: the working tree has uncommitted changes:")
            for line in dirty.splitlines():
                print("   ", line)

    if rc != 0:
        ok = False
    print("\nVERDICT: %s" % ("PUBLISHABLE" if ok else "DO NOT PUBLISH"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
