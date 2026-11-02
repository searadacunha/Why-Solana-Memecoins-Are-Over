#!/usr/bin/env python3
"""Human-reviewed, diff-derived follow-up titles; retain original SHA trailers."""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = "searadacunha/Why-Solana-Memecoins-Are-Over"
TITLES = {
  "2b26a2961": "docs(readme): remove redundant introductory summary",
  "b8a43aa9c": "docs(readme): add reproducibility and investigation overview",
  "1e4f27d44": "docs(readme): clarify 2024 trading record and attribution limits",
  "763ca0193": "research(reentry): publish known-group reentry signal evaluation",
  "22d23b2b8": "research(funders): publish final capital destination network study",
  "3ab961d71": "research(exits): test post-hoc wallet sweeps and capital recycling",
  "1c8ab4873": "research(exits): introduce exit-wallet capital return investigation",
  "31b3cca79": "research(economics): map coordinated sniper capital lifecycle",
  "75d4f756f": "research(coordination): classify synchronized launch buying",
  "19abd4807": "research(forensics): report non-robust predictive wallet features",
  "8ff11735a": "research(entries): reject unvalidated entry-zone filters",
  "1bfb7c46a": "research(edge): measure post-detection returns after trading costs",
  "3b39e024f": "research(forensics): pre-register post-detection feature analysis",
  "b69a1de27": "research(capital): test whether sniper stake size predicts outcomes",
  "6df47a26a": "docs(readme): remove redundant research-scope appendix",
  "a10258962": "docs(readme): expand measured claims and evidence classifications",
  "c2c1629bf": "docs(case-study): qualify claims about the ANSEM token launch",
  "8d1e75a81": "docs(reproducibility): expand offline validation instructions",
  "90de80c67": "docs(case-study): clarify 2026 launch-mechanism example",
  "184c53548": "docs(case-study): document ANSEM creation-slot chronology",
  "f5cbaee0b": "docs(case-study): add a contemporary creation-block example",
  "1aeae3df8": "docs(trading): explain the first-buy trigger after a funding split",
  "5985d04a7": "docs(case-study): correct SUMIKO ticker notation",
  "7fa53c765": "docs(funding): describe the migration from splits to wallet reserves",
  "0745b0c9f": "docs(attribution): limit claims about cluster operator identities",
  "7cb08db0b": "docs(trading): clarify the early entry signal and wallet provisioning",
  "596dedcfe": "docs(trading): relate the live funding split to bundle-snipe adoption",
  "e6f414bcb": "docs(trading): refine the sequence of 2024 split-based entries",
  "b27c67848": "docs(trading): distinguish split size from group supply control",
  "ab8455a40": "docs(funding): clarify the role of ChangeNOW routing",
  "2ba65c3a6": "docs(trading): explain discretionary position sizing",
  "d42fdd4a1": "docs(trading): document split detection and qualifying purchases",
  "8cce965ea": "docs(pitfalls): connect failed hypotheses with the lost trading edge",
  "d37b2d755": "docs(readme): introduce the 2024 wallet-funding evidence",
  "c4fe5adec": "docs(readme): reorganize the investigation into three acts",
  "68a92b37a": "docs(readme): present bundle-snipe changes and graduation rates",
  "f20a1935a": "docs(readme): revise the three-act thesis and translation exclusions",
  "20eda32de": "docs(trading): explain historical exit decisions and regime change",
  "04f22fef2": "docs(attribution): state limits of gateway-linked wallet inference",
  "ced293e66": "docs(readme): expand the three-act research narrative",
  "16267d4e4": "docs(readme): correct the pitfalls and trade-receipt counts",
  "49ea68776": "feat(reentry): freeze known-group features and analysis protocol",
  "6fe2686ca": "feat(funders): define funder-network tracing and collection protocol",
  "001587758": "feat(exits): freeze exit-wallet tracing selection and collection",
  "4c2f0f726": "feat(economics): freeze coordinated capital-cycle study inputs",
  "b891e44c9": "feat(coordination): establish independent buyer-coordination protocol",
  "cd151f17d": "feat(capital): freeze sniper-risk ratios and study table",
  "296b4a3a2": "feat(entries): prepare entry-zone dataset and validation protocol",
  "44bdf0dc1": "fix(null-model): exclude missing signatures from shared transactions",
  "611b40d58": "fix(null-model): match split-detector semantics in falsification tests",
  "f3eee14e9": "fix(rpc): reject malformed signature-history response types",
  "b004fbb48": "fix(rpc): distinguish missing result fields from null transactions",
  "2d8993a1f": "fix(solana): validate Base58 keys by decoded byte length",
  "4c84c1a34": "test(solana): cover Base58 public-key overflow boundaries",
  "024a2ccde": "docs(trading): separate reported seed capital from ledger withdrawals",
  "abb88266d": "fix(readme): align the claim ledger and published measurement fields",
  "03ef7b8bd": "docs(readme): simplify trade figures and claim-check output",
  "bfb1ce556": "refactor(funding): harmonize scanner interfaces across tracing tools",
  "5a35e48c2": "refactor(funding): clarify APIs for funding and split scanners",
  "4d01b93aa": "refactor(funding): standardize imports in wallet-tracing scripts",
  "29a88cf61": "fix(funding): guard against invalid wallet-transfer fields",
  "281af6793": "docs(pattern): tighten 2024 gateway attribution boundaries",
  "2869d3472": "docs(pattern): add exact split evidence and gateway identification",
  "6ae6711e9": "docs(results): reorganize launch mechanics and operator findings",
  "1bcce180a": "docs(results): expand the executive summary of measured outcomes",
  "60f77be56": "docs(pitfalls): refine denominators and limitations across tests",
  "23101f207": "docs(pitfalls): expand the fifteen falsification case studies",
  "f6195f0df": "refactor(onchain): harden launch and bundle collectors",
  "47dbdcc22": "refactor(onchain): align input paths for public dataset scripts",
  "9481c50af": "refactor(core): harmonize analysis and verification helpers",
  "a09d87aaf": "refactor(backtests): centralize SOL-USD conversions in exit tests",
  "1eef756d2": "refactor(publication): align trace exports and generated figures",
  "0a7350d40": "refactor(funding): simplify RPC callers and split-detector APIs",
  "b5c2b958d": "fix(research): add guards to result-generation scripts",
  "e803937bc": "refactor(research): harmonize ledger and measurement script contracts"
}
FOOTER = re.compile(r"(?m)^Original-Commit: ([0-9a-f]{40})$")
JOKE = "fixed the thing that broke the other thing"

def git(*args):
    return subprocess.check_output(["git", *args], text=True).rstrip("\n")

def map_file():
    return Path(os.environ["RUNNER_TEMP"]) / "research-refined-messages.json"

def plan():
    if os.environ.get("GITHUB_REPOSITORY") != REPO:
        raise RuntimeError("Refusing unrelated repository")
    if git("rev-parse", "main") != os.environ.get("GITHUB_SHA"):
        raise RuntimeError("Main moved during run")
    mapping = {}
    located = set()
    subjects = []
    for sha in git("rev-list", "--reverse", "main").splitlines():
        message = git("show", "-s", "--format=%B", sha)
        match = FOOTER.search(message)
        title = message.split("\n")[0]
        if match:
            prefix = match.group(1)[:9]
            if prefix in TITLES:
                located.add(prefix)
                newtitle = TITLES[prefix]
                if title != newtitle:
                    mapping[sha] = newtitle
                title = newtitle
        subjects.append(title)
    if located != set(TITLES):
        raise RuntimeError(f"Missing original commit identifiers: {set(TITLES)-located}")
    if not mapping:
        raise RuntimeError("Nothing requires refinement")
    if len(set(subjects)) < 115:
        raise RuntimeError("Commit subjects are not sufficiently distinctive")
    map_file().write_text(json.dumps(mapping, sort_keys=True, indent=2) + "\n")
    print("Planned refinements:", len(mapping),
          "; distinct subjects afterwards:", len(set(subjects)))
    for sha, newtitle in mapping.items():
        print(sha[:12], newtitle)

def filter_message():
    original = sys.stdin.buffer.read()
    mapping = json.loads(map_file().read_text())
    new_title = mapping.get(os.environ.get("GIT_COMMIT", ""))
    if new_title is None:
        sys.stdout.buffer.write(original)
    else:
        raw = original.decode("utf-8")
        rest = raw.split("\n", 1)[1] if "\n" in raw else ""
        sys.stdout.buffer.write((new_title + "\n" + rest).encode("utf-8"))

def verify():
    prev = os.environ["ORIGINAL_HEAD"]
    if git("rev-parse", prev + "^{tree}") != git("rev-parse", "main^{tree}"):
        raise RuntimeError("Rewritten HEAD changed the file tree")
    if git("rev-list", "--count", prev) != git("rev-list", "--count", "main"):
        raise RuntimeError("Commit graph has different size")
    seen = set()
    subjects = []
    for sha in git("rev-list", "main").splitlines():
        msg = git("show", "-s", "--format=%B", sha)
        subject = msg.split("\n")[0]
        if subject == JOKE:
            raise RuntimeError("Placeholder subject remains")
        subjects.append(subject)
        match = FOOTER.search(msg)
        if match:
            original = match.group(1)
            prefix = original[:9]
            if prefix in TITLES:
                if subject != TITLES[prefix]:
                    raise RuntimeError("Unexpected curated commit subject")
                seen.add(prefix)
            if git("rev-parse", original + "^{tree}") != git("rev-parse", sha + "^{tree}"):
                raise RuntimeError("Historical file content changed")
            fmt = "%aN%x00%aE%x00%aI%x00%cN%x00%cE%x00%cI"
            if git("show", "-s", "--format=" + fmt, original) != git("show", "-s", "--format=" + fmt, sha):
                raise RuntimeError("Historical authorship or dates changed")
    if seen != set(TITLES):
        raise RuntimeError("Not all curated titles made it into the new history")
    if len(set(subjects)) < 115:
        raise RuntimeError("Too many generic or duplicate subjects")
    print("Validated", len(seen), "curated subjects; unique:", len(set(subjects)),
          "; dates and trees unchanged")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--filter-message", action="store_true")
    g.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.plan:
        plan()
    elif a.filter_message:
        filter_message()
    else:
        verify()
