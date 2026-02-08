"""Tests for the git_insights MCP server."""

from __future__ import annotations

import git
import pytest

from mcp_toolkit.servers.git_insights import (
    find_large_files,
    get_blame,
    get_commit_history,
    get_contributor_stats,
    get_repo_stats,
)


@pytest.fixture
def git_repo(tmp_dir):
    """Create a temporary git repository with an initial commit."""
    repo = git.Repo.init(str(tmp_dir))
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    repo.config_writer().set_value("user", "name", "Test User").release()

    (tmp_dir / "test.txt").write_text("hello")
    repo.index.add(["test.txt"])
    repo.index.commit("Initial commit")
    return repo


class TestRepoStats:
    def test_get_repo_stats(self, git_repo):
        """Returns dict with expected repo stat keys."""
        result = get_repo_stats.fn(repo_path=git_repo.working_dir)
        assert isinstance(result, dict)
        for key in (
            "total_commits",
            "total_contributors",
            "total_branches",
            "active_branch",
            "first_commit_date",
            "latest_commit_date",
        ):
            assert key in result

    def test_get_repo_stats_counts(self, git_repo):
        """Single commit repo has correct counts."""
        result = get_repo_stats.fn(repo_path=git_repo.working_dir)
        assert result["total_commits"] == 1
        assert result["total_contributors"] == 1
        assert result["total_branches"] == 1


class TestCommitHistory:
    def test_get_commit_history(self, git_repo):
        """Returns list of commits with expected keys."""
        result = get_commit_history.fn(repo_path=git_repo.working_dir)
        assert isinstance(result, list)
        assert len(result) == 1
        entry = result[0]
        for key in ("hash", "short_hash", "author", "date", "message"):
            assert key in entry
        assert entry["message"] == "Initial commit"

    def test_get_commit_history_limit(self, git_repo, tmp_dir):
        """Limit parameter caps the number of returned commits."""
        # Add 2 more commits (3 total)
        for i in range(2):
            (tmp_dir / f"file_{i}.txt").write_text(f"content {i}")
            git_repo.index.add([f"file_{i}.txt"])
            git_repo.index.commit(f"Commit {i + 2}")

        result = get_commit_history.fn(repo_path=git_repo.working_dir, limit=2)
        assert len(result) == 2

    def test_multiple_commits(self, git_repo, tmp_dir):
        """Three commits are returned in newest-first order."""
        for i in range(2):
            (tmp_dir / f"extra_{i}.txt").write_text(f"data {i}")
            git_repo.index.add([f"extra_{i}.txt"])
            git_repo.index.commit(f"Commit {i + 2}")

        result = get_commit_history.fn(repo_path=git_repo.working_dir)
        assert len(result) == 3
        # Newest first
        assert result[0]["message"] == "Commit 3"
        assert result[-1]["message"] == "Initial commit"


class TestBlame:
    def test_get_blame(self, git_repo):
        """Blame on test.txt returns 1 line attributed to Test User."""
        result = get_blame.fn(
            repo_path=git_repo.working_dir,
            file_path="test.txt",
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["line_number"] == 1
        assert result[0]["author"] == "Test User"
        assert "commit_hash" in result[0]


class TestContributorStats:
    def test_get_contributor_stats(self, git_repo):
        """Returns contributor list with expected keys."""
        result = get_contributor_stats.fn(repo_path=git_repo.working_dir)
        assert isinstance(result, list)
        assert len(result) == 1
        entry = result[0]
        assert entry["author"] == "Test User"
        assert entry["email"] == "test@example.com"
        assert entry["commit_count"] == 1


class TestFindLargeFiles:
    def test_find_large_files_none(self, git_repo):
        """Small files below threshold return empty list."""
        result = find_large_files.fn(
            repo_path=git_repo.working_dir,
            threshold_kb=100,
        )
        assert result == []

    def test_find_large_files_match(self, git_repo, tmp_dir):
        """A 200 KB file exceeds the 100 KB threshold."""
        big_file = tmp_dir / "bigfile.bin"
        big_file.write_bytes(b"x" * (200 * 1024))
        git_repo.index.add(["bigfile.bin"])
        git_repo.index.commit("Add large file")

        result = find_large_files.fn(
            repo_path=git_repo.working_dir,
            threshold_kb=100,
        )
        assert len(result) == 1
        assert result[0]["path"] == "bigfile.bin"
        assert result[0]["size_kb"] >= 200


class TestInvalidRepo:
    def test_invalid_repo(self, tmp_dir):
        """Non-repo path raises ValueError."""
        non_repo = tmp_dir / "not_a_repo"
        non_repo.mkdir()
        with pytest.raises(ValueError, match="Not a valid git repository"):
            get_repo_stats.fn(repo_path=str(non_repo))
