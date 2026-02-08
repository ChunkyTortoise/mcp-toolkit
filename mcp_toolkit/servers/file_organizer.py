"""Smart file search, deduplication, and metadata extraction MCP server."""

from __future__ import annotations

import hashlib
import mimetypes
import re
from collections import defaultdict
from pathlib import Path

from fastmcp import FastMCP

SERVER_INFO = {
    "name": "file-organizer",
    "description": "Smart file search, deduplication, and metadata extraction",
    "tools": [
        "search_files",
        "find_duplicates",
        "get_metadata",
        "analyze_directory",
        "bulk_rename",
    ],
}

mcp = FastMCP(SERVER_INFO["name"])

# 64 KiB read buffer for hashing large files
_HASH_BUF_SIZE = 65_536


def _sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(_HASH_BUF_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _file_info(p: Path) -> dict:
    """Build a basic info dict for a file path."""
    stat = p.stat()
    return {
        "path": str(p),
        "size": stat.st_size,
        "modified": stat.st_mtime,
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_files(
    path: str,
    pattern: str = "*",
    max_depth: int = 10,
) -> list[dict]:
    """Recursively search for files matching a glob pattern.

    Args:
        path: Root directory to search.
        pattern: Glob pattern to match file names against (e.g. ``"*.py"``).
        max_depth: Maximum directory depth to recurse into.

    Returns:
        List of dicts, each containing ``path``, ``size``, and ``modified``.
    """
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"Path is not a directory: {root}")

    results: list[dict] = []

    def _walk(directory: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return
        for entry in entries:
            if entry.is_file() and entry.match(pattern):
                try:
                    results.append(_file_info(entry))
                except OSError:
                    continue
            elif entry.is_dir() and not entry.is_symlink():
                _walk(entry, depth + 1)

    _walk(root, 1)
    return results


@mcp.tool()
def find_duplicates(path: str, method: str = "hash") -> list[list[str]]:
    """Find duplicate files by SHA-256 content hash.

    Files are first grouped by size to avoid unnecessary hashing, then
    groups with identical hashes are reported.

    Args:
        path: Root directory to scan.
        method: Deduplication method (currently only ``"hash"``).

    Returns:
        List of groups, where each group is a list of file paths that
        share identical content.
    """
    if method != "hash":
        raise ValueError(f"Unsupported method: {method}. Only 'hash' is supported.")

    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"Path is not a directory: {root}")

    # Phase 1 -- group files by size to reduce hashing work
    size_groups: dict[int, list[Path]] = defaultdict(list)
    for p in root.rglob("*"):
        if p.is_file() and not p.is_symlink():
            try:
                size_groups[p.stat().st_size].append(p)
            except OSError:
                continue

    # Phase 2 -- hash only size-colliding files
    hash_groups: dict[str, list[str]] = defaultdict(list)
    for files in size_groups.values():
        if len(files) < 2:
            continue
        for f in files:
            try:
                digest = _sha256(f)
                hash_groups[digest].append(str(f))
            except OSError:
                continue

    return [group for group in hash_groups.values() if len(group) >= 2]


@mcp.tool()
def get_metadata(file_path: str) -> dict:
    """Return detailed metadata for a single file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        Dict with ``path``, ``size``, ``modified``, ``created``,
        ``mime_type``, and ``sha256`` keys.
    """
    p = Path(file_path).resolve()
    if not p.is_file():
        raise ValueError(f"Path is not a file: {p}")

    stat = p.stat()
    mime, _ = mimetypes.guess_type(str(p))

    return {
        "path": str(p),
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "created": stat.st_ctime,
        "mime_type": mime or "application/octet-stream",
        "sha256": _sha256(p),
    }


@mcp.tool()
def analyze_directory(path: str) -> dict:
    """Analyze a directory with a size breakdown by file extension.

    Args:
        path: Root directory to analyze.

    Returns:
        Dict with ``total_files``, ``total_size``, and ``by_extension``
        (mapping each extension to ``{count, size}``).
    """
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"Path is not a directory: {root}")

    total_files = 0
    total_size = 0
    by_ext: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "size": 0})

    for p in root.rglob("*"):
        if not p.is_file() or p.is_symlink():
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        ext = p.suffix.lower() if p.suffix else "(no extension)"
        total_files += 1
        total_size += size
        by_ext[ext]["count"] += 1
        by_ext[ext]["size"] += size

    return {
        "total_files": total_files,
        "total_size": total_size,
        "by_extension": dict(by_ext),
    }


@mcp.tool()
def bulk_rename(
    path: str,
    pattern: str,
    replacement: str,
    dry_run: bool = True,
) -> list[dict]:
    """Rename files in a directory using a regex pattern.

    Only files in the immediate directory are considered (non-recursive).
    By default this performs a dry run; set ``dry_run=False`` to execute
    the renames.

    Args:
        path: Directory containing files to rename.
        pattern: Regex pattern to match against file names.
        replacement: Replacement string (supports regex back-references).
        dry_run: If True, report planned renames without executing them.

    Returns:
        List of dicts with ``old`` and ``new`` keys showing each rename.
    """
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"Path is not a directory: {root}")

    compiled = re.compile(pattern)
    renames: list[dict] = []

    for p in sorted(root.iterdir()):
        if not p.is_file():
            continue
        new_name = compiled.sub(replacement, p.name)
        if new_name == p.name:
            continue
        new_path = root / new_name
        renames.append({"old": str(p), "new": str(new_path)})

        if not dry_run:
            p.rename(new_path)

    return renames
