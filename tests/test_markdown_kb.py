"""Tests for the markdown_kb MCP server."""

from __future__ import annotations

from mcp_toolkit.servers.markdown_kb import (
    _index_state,
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
