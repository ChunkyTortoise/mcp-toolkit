"""Tests for the markdown_kb MCP server."""

from __future__ import annotations

from mcp_toolkit.servers.markdown_kb import (
    _extract_title,
    _index_state,
    _make_doc_id,
    get_document,
    get_stats,
    index_documents,
    list_documents,
    search,
)


def _clear_index():
    """Reset module-level index state between tests."""
    _index_state["documents"] = {}
    _index_state["tfidf_matrix"] = None
    _index_state["vectorizer"] = None
    _index_state["doc_ids"] = []


class TestIndexDocuments:
    def test_index_documents(self, sample_markdown_dir):
        """Indexes sample_markdown_dir and returns '3 documents'."""
        _clear_index()
        result = index_documents.fn(path=str(sample_markdown_dir))
        assert "3 documents" in result
        assert len(_index_state["documents"]) == 3

    def test_index_empty_dir(self, tmp_dir):
        """Indexing an empty directory returns '0 documents'."""
        _clear_index()
        result = index_documents.fn(path=str(tmp_dir))
        assert "0 documents" in result
        assert len(_index_state["documents"]) == 0


class TestSearch:
    def test_search_returns_results(self, sample_markdown_dir):
        """After indexing, search for 'API' returns results."""
        _clear_index()
        index_documents.fn(path=str(sample_markdown_dir))
        results = search.fn(query="API")
        assert len(results) >= 1
        assert any(r["doc_id"] == "api" for r in results)

    def test_search_empty_index(self):
        """Searching without indexing returns an empty list."""
        _clear_index()
        results = search.fn(query="anything")
        assert results == []

    def test_search_ranking(self, sample_markdown_dir):
        """Search 'REST API CRUD' ranks api.md highest."""
        _clear_index()
        index_documents.fn(path=str(sample_markdown_dir))
        results = search.fn(query="REST API CRUD")
        assert len(results) >= 1
        assert results[0]["doc_id"] == "api"


class TestGetDocument:
    def test_get_document(self, sample_markdown_dir):
        """Retrieves a document by ID."""
        _clear_index()
        index_documents.fn(path=str(sample_markdown_dir))
        doc = get_document.fn(doc_id="intro")
        assert doc["doc_id"] == "intro"
        assert doc["title"] == "Introduction"
        assert "Welcome" in doc["content"]

    def test_get_document_not_found(self, sample_markdown_dir):
        """Returns an error dict for a missing document."""
        _clear_index()
        index_documents.fn(path=str(sample_markdown_dir))
        doc = get_document.fn(doc_id="nonexistent")
        assert "error" in doc


class TestListAndStats:
    def test_list_documents(self, sample_markdown_dir):
        """Lists all indexed documents."""
        _clear_index()
        index_documents.fn(path=str(sample_markdown_dir))
        docs = list_documents.fn()
        assert len(docs) == 3
        doc_ids = {d["doc_id"] for d in docs}
        assert doc_ids == {"intro", "setup", "api"}
        for d in docs:
            assert "title" in d
            assert "path" in d
            assert "size" in d

    def test_get_stats(self, sample_markdown_dir):
        """Checks total_docs, total_tokens, and vocabulary_size."""
        _clear_index()
        index_documents.fn(path=str(sample_markdown_dir))
        stats = get_stats.fn()
        assert stats["total_docs"] == 3
        assert stats["total_tokens"] > 0
        assert stats["vocabulary_size"] > 0

    def test_title_extraction(self, sample_markdown_dir):
        """Verifies titles are extracted from # headings."""
        _clear_index()
        index_documents.fn(path=str(sample_markdown_dir))
        docs = list_documents.fn()
        titles = {d["doc_id"]: d["title"] for d in docs}
        assert titles["intro"] == "Introduction"
        assert titles["setup"] == "Setup Guide"
        assert titles["api"] == "API Reference"


class TestIndexEdgeCases:
    def test_index_invalid_directory(self):
        """Indexing a nonexistent directory returns an error string."""
        _clear_index()
        result = index_documents.fn(path="/nonexistent/path/xyz")
        assert "Error" in result

    def test_index_custom_extensions(self, tmp_dir):
        """Indexing with custom extensions only picks those files."""
        _clear_index()
        (tmp_dir / "doc.md").write_text("# Markdown\nSome markdown content")
        (tmp_dir / "notes.txt").write_text("Plain text notes about things")
        result = index_documents.fn(path=str(tmp_dir), extensions=[".txt"])
        assert "1 documents" in result
        docs = list_documents.fn()
        assert len(docs) == 1
        assert docs[0]["doc_id"] == "notes"

    def test_index_duplicate_doc_ids(self, tmp_dir):
        """Duplicate file stems get parent dir name prepended."""
        _clear_index()
        sub1 = tmp_dir / "a"
        sub1.mkdir()
        sub2 = tmp_dir / "b"
        sub2.mkdir()
        (sub1 / "readme.md").write_text("# First Readme\nContent A")
        (sub2 / "readme.md").write_text("# Second Readme\nContent B")
        index_documents.fn(path=str(tmp_dir))
        docs = list_documents.fn()
        assert len(docs) == 2
        doc_ids = {d["doc_id"] for d in docs}
        # One is "readme", the other should be "b_readme" (or "a_readme")
        assert len(doc_ids) == 2


class TestSearchEdgeCases:
    def test_search_top_k_limits_results(self, sample_markdown_dir):
        """top_k=1 returns at most 1 result."""
        _clear_index()
        index_documents.fn(path=str(sample_markdown_dir))
        results = search.fn(query="documentation", top_k=1)
        assert len(results) <= 1

    def test_search_irrelevant_query(self, sample_markdown_dir):
        """Query with no matching terms returns empty list."""
        _clear_index()
        index_documents.fn(path=str(sample_markdown_dir))
        results = search.fn(query="xylophone zebra quantum")
        assert results == []


class TestStatsEdgeCases:
    def test_stats_empty_index(self):
        """Stats on an empty index returns all zeros."""
        _clear_index()
        stats = get_stats.fn()
        assert stats["total_docs"] == 0
        assert stats["total_tokens"] == 0
        assert stats["avg_doc_length"] == 0
        assert stats["vocabulary_size"] == 0


class TestHelperFunctions:
    def test_extract_title_with_heading(self):
        """Extracts title from '# Heading' line."""
        assert _extract_title("# My Title\n\nSome body text", "file.md") == "My Title"

    def test_extract_title_fallback(self):
        """Falls back to cleaned filename when no heading exists."""
        assert _extract_title("No heading here\nJust text", "my-cool-doc.md") == "My Cool Doc"

    def test_extract_title_underscore_fallback(self):
        """Underscores in filename are replaced with spaces and title-cased."""
        assert _extract_title("no heading", "data_pipeline_notes.md") == "Data Pipeline Notes"

    def test_make_doc_id(self):
        """Derives doc ID from filename stem."""
        assert _make_doc_id("path/to/readme.md") == "readme"
        assert _make_doc_id("report.txt") == "report"
