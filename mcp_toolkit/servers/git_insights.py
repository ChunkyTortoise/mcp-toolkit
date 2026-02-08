"""Git repository analytics, blame, and contributor statistics."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import git
from fastmcp import FastMCP

SERVER_INFO = {
    "name": "git-insights",
    "description": "Git repository analytics, blame, and contributor statistics",
    "tools": [
        "get_repo_stats",
        "get_commit_history",
        "get_blame",
        "get_contributor_stats",
        "find_large_files",
    ],
}

mcp = FastMCP(SERVER_INFO["name"])


def _open_repo(repo_path: str) -> git.Repo:
    """Open a git repository, raising a clear error for invalid paths."""
    try:
        return git.Repo(repo_path)
    except git.InvalidGitRepositoryError:
        raise ValueError(f"Not a valid git repository: {repo_path}")


def _commit_date_iso(commit: git.Commit) -> str:
    """Return the authored date of a commit as an ISO 8601 string."""
    return datetime.fromtimestamp(commit.authored_date, tz=timezone.utc).isoformat()


@mcp.tool()
def get_repo_stats(repo_path: str = ".") -> dict:
    """Return high-level repository statistics.

    Returns a dict with total_commits, total_contributors, total_branches,
    active_branch, first_commit_date, and latest_commit_date.
    """
    repo = _open_repo(repo_path)

    commits = list(repo.iter_commits())
    contributors = {c.author.email for c in commits}
    branches = [ref.name for ref in repo.branches]

    return {
        "total_commits": len(commits),
        "total_contributors": len(contributors),
        "total_branches": len(branches),
        "active_branch": (
            repo.active_branch.name if not repo.head.is_detached else "(detached HEAD)"
        ),
        "first_commit_date": _commit_date_iso(commits[-1]) if commits else None,
        "latest_commit_date": _commit_date_iso(commits[0]) if commits else None,
    }


@mcp.tool()
def get_commit_history(repo_path: str = ".", limit: int = 20) -> list[dict]:
    """Return the most recent commits.

    Each entry contains hash, short_hash, author, date (ISO string), and message.
    """
    repo = _open_repo(repo_path)

    results: list[dict] = []
    for commit in repo.iter_commits(max_count=limit):
        results.append(
            {
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:7],
                "author": str(commit.author),
                "date": _commit_date_iso(commit),
                "message": commit.message.strip(),
            }
        )
    return results


@mcp.tool()
def get_blame(repo_path: str, file_path: str) -> list[dict]:
    """Return per-line blame information for a file.

    Each entry contains line_number, author, commit_hash, and content.
    """
    repo = _open_repo(repo_path)

    results: list[dict] = []
    line_number = 1
    for commit, lines in repo.blame(rev="HEAD", file=file_path):
        for line in lines:
            results.append(
                {
                    "line_number": line_number,
                    "author": str(commit.author),
                    "commit_hash": commit.hexsha,
                    "content": line,
                }
            )
            line_number += 1
    return results


@mcp.tool()
def get_contributor_stats(repo_path: str = ".") -> list[dict]:
    """Return per-contributor commit statistics sorted by commit count descending.

    Each entry contains author, email, commit_count, first_commit, and latest_commit.
    """
    repo = _open_repo(repo_path)

    contributors: dict[str, dict] = {}
    for commit in repo.iter_commits():
        email = commit.author.email
        date = _commit_date_iso(commit)
        if email not in contributors:
            contributors[email] = {
                "author": str(commit.author),
                "email": email,
                "commit_count": 0,
                "first_commit": date,
                "latest_commit": date,
            }
        entry = contributors[email]
        entry["commit_count"] += 1
        # first_commit should be the oldest; latest_commit the newest
        if date < entry["first_commit"]:
            entry["first_commit"] = date
        if date > entry["latest_commit"]:
            entry["latest_commit"] = date

    return sorted(contributors.values(), key=lambda c: c["commit_count"], reverse=True)


@mcp.tool()
def find_large_files(repo_path: str = ".", threshold_kb: int = 100) -> list[dict]:
    """Find tracked files exceeding a size threshold.

    Returns a list of dicts with path and size_kb, sorted by size descending.
    """
    repo = _open_repo(repo_path)

    large_files: list[dict] = []
    tracked = repo.git.ls_files().splitlines()
    for rel_path in tracked:
        abs_path = os.path.join(repo.working_dir, rel_path)
        try:
            size_bytes = os.path.getsize(abs_path)
        except OSError:
            continue
        size_kb = round(size_bytes / 1024, 2)
        if size_kb >= threshold_kb:
            large_files.append({"path": rel_path, "size_kb": size_kb})

    return sorted(large_files, key=lambda f: f["size_kb"], reverse=True)
