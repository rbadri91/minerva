"""Unit tests for .claude/branch-guard.sh — the PreToolUse branch discipline hook.

Each test builds an isolated git repo in a tmp directory so nothing touches the
real repo.  Tests cover the three rules documented in the script:

  Rule 1  On master                                     → block (continue=false)
  Rule 2  Pushed branch, 0 commits ahead of origin/master → auto-create branch
  Rule 3  WIP branch or fresh local branch              → silent pass-through
"""
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / ".claude" / "branch-guard.sh"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _git(args: list[str], cwd: Path, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        **kwargs,
    )


def _run_hook(repo: Path) -> tuple[int, dict]:
    """Run branch-guard.sh with empty stdin; return (exit_code, parsed_output)."""
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        input="{}",
        capture_output=True,
        text=True,
        cwd=str(repo),
    )
    out = result.stdout.strip()
    return result.returncode, json.loads(out) if out else {}


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """Bare remote + local clone with one commit on master pushed to origin."""
    remote = tmp_path / "remote.git"
    local = tmp_path / "local"

    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "clone", str(remote), str(local)], check=True, capture_output=True)

    for cmd in [["config", "user.email", "test@test.com"], ["config", "user.name", "Test"]]:
        _git(cmd, local, check=True)

    (local / "README.md").write_text("init")
    _git(["checkout", "-b", "master"], local, check=True)
    _git(["add", "README.md"], local, check=True)
    _git(["commit", "-m", "init"], local, check=True)
    _git(["push", "-u", "origin", "master"], local, check=True)

    return local


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_blocks_on_master(repo: Path):
    """Rule 1: hook blocks any write/edit when on master."""
    assert _git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip() == "master"

    code, data = _run_hook(repo)

    assert code == 0
    assert data.get("continue") is False
    assert "master" in data.get("stopReason", "").lower()
    assert _git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip() == "master"


def test_blocks_merged_branch(repo: Path):
    """Rule 2: if a pushed branch has 0 commits ahead of origin/master the hook
    blocks and tells Claude to create a descriptively-named branch."""
    # Feature work on a branch, pushed, then merged into master
    _git(["checkout", "-b", "feature/done"], repo, check=True)
    (repo / "work.txt").write_text("work")
    _git(["add", "work.txt"], repo, check=True)
    _git(["commit", "-m", "work"], repo, check=True)
    _git(["push", "-u", "origin", "feature/done"], repo, check=True)

    _git(["checkout", "master"], repo, check=True)
    _git(["merge", "--ff-only", "feature/done"], repo, check=True)
    _git(["push", "origin", "master"], repo, check=True)

    # Back on the now-merged feature branch (0 commits ahead, has remote tracking)
    _git(["checkout", "feature/done"], repo, check=True)

    code, data = _run_hook(repo)

    assert code == 0
    assert data.get("continue") is False
    assert "feature/done" in data.get("stopReason", "")
    # Hook must NOT switch branches — Claude will create one with a meaningful name
    assert _git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip() == "feature/done"


def test_allows_renamed_branch_with_stale_tracking(repo: Path):
    """Rule 3: a locally-renamed branch whose remote tracking points to the old name
    should pass through silently — it hasn't been merged, just renamed locally."""
    # Push a feature branch then locally rename it (simulates what branch-guard.sh
    # itself does when the user renames after the auto-create)
    _git(["checkout", "-b", "feature/old-name"], repo, check=True)
    (repo / "feat.txt").write_text("feat")
    _git(["add", "feat.txt"], repo, check=True)
    _git(["commit", "-m", "feat"], repo, check=True)
    _git(["push", "-u", "origin", "feature/old-name"], repo, check=True)

    # Merge into master so the branch is 0 commits ahead
    _git(["checkout", "master"], repo, check=True)
    _git(["merge", "--ff-only", "feature/old-name"], repo, check=True)
    _git(["push", "origin", "master"], repo, check=True)

    # Rename locally — tracking still points to origin/feature/old-name
    _git(["checkout", "feature/old-name"], repo, check=True)
    _git(["branch", "-m", "feature/old-name", "feature/new-name"], repo, check=True)

    # Hook must NOT auto-create a branch: local name ≠ remote tracking name
    code, data = _run_hook(repo)

    assert code == 0
    assert data == {}, f"Expected silent pass-through for renamed branch, got: {data}"
    assert _git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip() == "feature/new-name"


def test_allows_wip_branch(repo: Path):
    """Rule 3: a branch with unmerged commits passes through silently."""
    _git(["checkout", "-b", "feature/wip"], repo, check=True)
    (repo / "wip.txt").write_text("wip")
    _git(["add", "wip.txt"], repo, check=True)
    _git(["commit", "-m", "wip"], repo, check=True)
    _git(["push", "-u", "origin", "feature/wip"], repo, check=True)

    code, data = _run_hook(repo)

    assert code == 0
    assert data == {}, f"Expected no hook output for WIP branch, got: {data}"
    assert _git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip() == "feature/wip"


def test_allows_fresh_local_branch(repo: Path):
    """Rule 3: a brand-new local branch that hasn't been pushed passes through silently."""
    _git(["checkout", "-b", "feature/fresh"], repo, check=True)
    # Intentionally not pushed — no remote tracking branch

    code, data = _run_hook(repo)

    assert code == 0
    assert data == {}, f"Expected no hook output for fresh branch, got: {data}"
    assert _git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip() == "feature/fresh"
