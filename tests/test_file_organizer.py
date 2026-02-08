"""Tests for the file_organizer MCP server."""

from __future__ import annotations

import pytest

from mcp_toolkit.servers.file_organizer import (
    analyze_directory,
    bulk_rename,
    find_duplicates,
    get_metadata,
    search_files,
)


class TestSearchFiles:
    def test_search_files_all(self, demo_data_dir):
        """Searches demo_data_dir with default glob, finds all files."""
        results = search_files.fn(path=str(demo_data_dir))
        assert len(results) >= 5
        paths = [r["path"] for r in results]
        assert any("q1_sales.csv" in p for p in paths)
        assert any("logo.png" in p for p in paths)

    def test_search_files_pattern(self, demo_data_dir):
        """Searches for *.csv, finds only CSV files."""
        results = search_files.fn(path=str(demo_data_dir), pattern="*.csv")
        assert len(results) >= 2
        for r in results:
            assert r["path"].endswith(".csv")

    def test_search_files_not_dir(self, demo_data_dir):
        """Raises ValueError for a path that is not a directory."""
        fake_path = str(demo_data_dir / "reports" / "q1_sales.csv")
        with pytest.raises(ValueError, match="not a directory"):
            search_files.fn(path=fake_path)


class TestFindDuplicates:
    def test_find_duplicates(self, demo_data_dir):
        """Finds duplicate readme files in demo_data/duplicates."""
        groups = find_duplicates.fn(path=str(demo_data_dir / "duplicates"))
        assert len(groups) >= 1
        dup_group = groups[0]
        assert len(dup_group) == 2
        filenames = [p.split("/")[-1] for p in dup_group]
        assert "readme.txt" in filenames
        assert "readme_copy.txt" in filenames


class TestGetMetadata:
    def test_get_metadata_csv(self, demo_data_dir):
        """Checks metadata of q1_sales.csv."""
        csv_path = str(demo_data_dir / "reports" / "q1_sales.csv")
        meta = get_metadata.fn(file_path=csv_path)
        assert meta["size"] > 0
        assert meta["mime_type"] == "text/csv"
        assert "sha256" in meta
        assert len(meta["sha256"]) == 64

    def test_get_metadata_not_found(self, tmp_dir):
        """Raises ValueError for a nonexistent file."""
        with pytest.raises(ValueError, match="not a file"):
            get_metadata.fn(file_path=str(tmp_dir / "ghost.txt"))


class TestAnalyzeDirectory:
    def test_analyze_directory(self, demo_data_dir):
        """Analyzes demo_data_dir, checks structure."""
        result = analyze_directory.fn(path=str(demo_data_dir))
        assert result["total_files"] >= 5
        assert result["total_size"] > 0
        assert "by_extension" in result

    def test_analyze_extensions(self, demo_data_dir):
        """Verifies by_extension has correct extension keys."""
        result = analyze_directory.fn(path=str(demo_data_dir))
        ext_keys = set(result["by_extension"].keys())
        assert ".csv" in ext_keys
        assert ".txt" in ext_keys
        assert ".png" in ext_keys
        for ext_data in result["by_extension"].values():
            assert "count" in ext_data
            assert "size" in ext_data
            assert ext_data["count"] >= 1


class TestBulkRename:
    def test_bulk_rename_dry_run(self, tmp_dir):
        """Dry run returns planned renames but does not execute them."""
        (tmp_dir / "file_001.txt").write_text("a")
        (tmp_dir / "file_002.txt").write_text("b")
        (tmp_dir / "file_003.txt").write_text("c")

        renames = bulk_rename.fn(
            path=str(tmp_dir),
            pattern=r"file_(\d+)",
            replacement=r"doc_\1",
            dry_run=True,
        )
        assert len(renames) == 3
        # Original files should still exist (dry run)
        assert (tmp_dir / "file_001.txt").exists()
        assert (tmp_dir / "file_002.txt").exists()
        assert (tmp_dir / "file_003.txt").exists()

    def test_bulk_rename_execute(self, tmp_dir):
        """Executes rename and verifies files are renamed."""
        (tmp_dir / "img_a.png").write_bytes(b"\x89PNG")
        (tmp_dir / "img_b.png").write_bytes(b"\x89PNG")

        renames = bulk_rename.fn(
            path=str(tmp_dir),
            pattern=r"img_",
            replacement="photo_",
            dry_run=False,
        )
        assert len(renames) == 2
        # Old files should be gone
        assert not (tmp_dir / "img_a.png").exists()
        assert not (tmp_dir / "img_b.png").exists()
        # New files should exist
        assert (tmp_dir / "photo_a.png").exists()
        assert (tmp_dir / "photo_b.png").exists()
