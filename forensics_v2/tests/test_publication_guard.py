"""Exercise publication decisions against real, small, temporary Git histories."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

GUARD_PATH = Path(__file__).resolve().parents[1] / "publication_guard.py"
SPEC = importlib.util.spec_from_file_location("publication_guard_under_test", GUARD_PATH)
assert SPEC is not None and SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def save(repo, message):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def history(tmp_path):
    repo = tmp_path / "repository"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Publication tests")
    git(repo, "config", "user.email", "publication-tests@example.invalid")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "core.autocrlf", "false")
    git(repo, "config", "core.filemode", "true")
    for name in ("README.md", "docs/ReadMe.txt", "notes with spaces/README"):
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"Existing research, preserved exactly.\n")
    (repo / "code.py").write_text("fixed = False\n")
    old = save(repo, "Before correction")
    (repo / "code.py").write_text("fixed = True\n")
    baseline = save(repo, "Required correction")
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"version": 1, "branches": {"main": {"baseline": baseline}}}))
    return repo, policy, baseline, old


def test_new_research_and_new_readme_are_allowed_without_mutation(history):
    repo, policy, baseline, _ = history
    study = repo / "new_study"
    study.mkdir()
    (study / "README.md").write_text("A new study, outside the frozen README set.\n")
    (study / "analysis.py").write_text("answer = 42\n")
    candidate = save(repo, "Add research")
    before = (git(repo, "status", "--porcelain"), git(repo, "rev-parse", "HEAD"))
    result = guard.check_publication(repo, "main", candidate, policy)
    assert result["baseline"] == baseline
    assert result["protected_readmes"] == 3
    assert result["new_readmes"] == 1
    assert (git(repo, "status", "--porcelain"), git(repo, "rev-parse", "HEAD")) == before


@pytest.mark.parametrize("name", ["README.md", "docs/ReadMe.txt", "notes with spaces/README"])
def test_existing_readme_edit_is_rejected(history, name):
    repo, policy, _, _ = history
    (repo / name).write_bytes(b"Rewritten by an old session.\n")
    save(repo, "Replace existing README")
    with pytest.raises(guard.GuardError, match="Protected README"):
        guard.check_publication(repo, "main", "HEAD", policy)


def test_existing_readme_deletion_is_rejected(history):
    repo, policy, _, _ = history
    (repo / "README.md").unlink()
    save(repo, "Delete existing README")
    with pytest.raises(guard.GuardError, match="Protected README"):
        guard.check_publication(repo, "main", "HEAD", policy)


def test_moving_existing_readme_to_new_research_is_rejected(history):
    repo, policy, _, _ = history
    (repo / "new_study").mkdir()
    (repo / "README.md").rename(repo / "new_study" / "README.md")
    save(repo, "Move existing README")
    with pytest.raises(guard.GuardError, match="Protected README"):
        guard.check_publication(repo, "main", "HEAD", policy)


def test_existing_readme_mode_change_is_rejected(history):
    repo, policy, _, _ = history
    os.chmod(repo / "README.md", 0o755)
    save(repo, "Change README mode")
    with pytest.raises(guard.GuardError, match="Protected README"):
        guard.check_publication(repo, "main", "HEAD", policy)


def test_missing_baseline_is_a_failure_not_a_skip(history):
    repo, policy, _, _ = history
    policy.write_text(json.dumps({"version": 1, "branches": {"main": {"baseline": "0" * 40}}}))
    result = subprocess.run(
        [sys.executable, str(GUARD_PATH), "--repo", str(repo), "--policy", str(policy), "--branch", "main"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "Required baseline commit is unavailable" in result.stderr


def test_missing_policy_is_a_failure(history):
    repo, policy, _, _ = history
    policy.unlink()
    with pytest.raises(guard.GuardError, match="Cannot read publication policy"):
        guard.check_publication(repo, "main", "HEAD", policy)


def test_destination_branch_must_have_an_explicit_policy(history):
    repo, policy, _, _ = history
    with pytest.raises(guard.GuardError, match="No publication policy"):
        guard.check_publication(repo, "some-fork-branch", "HEAD", policy)


def test_stale_pr_head_is_rejected_even_when_a_merge_would_contain_the_anchor(history):
    repo, policy, _, old = history
    git(repo, "checkout", "-q", "-b", "old-session", old)
    (repo / "new_research.py").write_text("unrelated_work = True\n")
    stale_head = save(repo, "Work from before the correction")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "--no-ff", "-q", "-m", "Simulated PR merge", "old-session")
    # The merge result alone would hide the stale head. CI checks both commits.
    guard.check_publication(repo, "main", "HEAD", policy)
    with pytest.raises(guard.GuardError, match="does not contain required baseline"):
        guard.check_publication(repo, "main", stale_head, policy)
