"""Knowledge base search across markdown documents using TF-IDF.

Indexes markdown files and provides full-text search via TF-IDF vectorization
and cosine similarity ranking.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastmcp import FastMCP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SERVER_INFO = {
    "name": "markdown-kb",
    "description": "Knowledge base search across markdown documents using TF-IDF",
    "tools": ["index_documents", "search", "get_document", "list_documents", "get_stats"],
}

mcp = FastMCP(SERVER_INFO["name"])

# Module-level state for the TF-IDF index
_index_state: dict = {
    "documents": {},  # doc_id -> {title, content, path}
    "tfidf_matrix": None,
    "vectorizer": None,
    "doc_ids": [],
}


def _extract_title(content: str, filename: str) -> str:
    """Extract title from the first '# ' heading or fall back to filename."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return Path(filename).stem.replace("-", " ").replace("_", " ").title()


def _make_doc_id(filepath: str) -> str:
    """Derive a document ID from the filename without extension."""
    return Path(filepath).stem


@mcp.tool()
def index_documents(path: str, extensions: list[str] | None = None) -> str:
    """Build a TF-IDF index from files at the given path.

    Args:
        path: Directory path to scan for documents.
        extensions: File extensions to include. Defaults to [".md"].

    Returns:
        Summary string with the count of indexed documents.
    """
    if extensions is None:
        extensions = [".md"]

    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        return f"Error: '{path}' is not a valid directory."

    documents: dict[str, dict] = {}
    doc_ids: list[str] = []
    corpus: list[str] = []

    for ext in extensions:
        for filepath in sorted(root.rglob(f"*{ext}")):
            if not filepath.is_file():
                continue
            try:
                content = filepath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            doc_id = _make_doc_id(str(filepath))
            # Handle duplicate doc_ids by appending parent directory name
            if doc_id in documents:
                doc_id = f"{filepath.parent.name}_{doc_id}"

            title = _extract_title(content, filepath.name)
            documents[doc_id] = {
                "title": title,
                "content": content,
                "path": str(filepath),
            }
            doc_ids.append(doc_id)
            corpus.append(content)

    if not corpus:
        _index_state["documents"] = {}
        _index_state["tfidf_matrix"] = None
        _index_state["vectorizer"] = None
        _index_state["doc_ids"] = []
        return "Indexed 0 documents. No matching files found."

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    _index_state["documents"] = documents
    _index_state["tfidf_matrix"] = tfidf_matrix
    _index_state["vectorizer"] = vectorizer
    _index_state["doc_ids"] = doc_ids

    return f"Indexed {len(doc_ids)} documents from '{path}'."


@mcp.tool()
def search(query: str, top_k: int = 5) -> list[dict]:
    """Search indexed documents using TF-IDF cosine similarity.

    Args:
        query: Search query string.
        top_k: Maximum number of results to return.

    Returns:
        List of search results with doc_id, title, score, and snippet.
    """
    vectorizer = _index_state.get("vectorizer")
    tfidf_matrix = _index_state.get("tfidf_matrix")
    doc_ids = _index_state.get("doc_ids", [])
    documents = _index_state.get("documents", {})

    if vectorizer is None or tfidf_matrix is None or not doc_ids:
        return []

    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

    ranked_indices = similarities.argsort()[::-1][:top_k]

    results = []
    for idx in ranked_indices:
        score = float(similarities[idx])
        if score <= 0.0:
            continue
        doc_id = doc_ids[idx]
        doc = documents[doc_id]
        results.append(
            {
                "doc_id": doc_id,
                "title": doc["title"],
                "score": round(score, 4),
                "snippet": doc["content"][:200],
            }
        )

    return results


@mcp.tool()
def get_document(doc_id: str) -> dict:
    """Retrieve the full content of a document by its ID.

    Args:
        doc_id: Document identifier (filename without extension).

    Returns:
        Dictionary with doc_id, title, content, and path.
    """
    documents = _index_state.get("documents", {})
    doc = documents.get(doc_id)
    if doc is None:
        return {"error": f"Document '{doc_id}' not found."}
    return {
        "doc_id": doc_id,
        "title": doc["title"],
        "content": doc["content"],
        "path": doc["path"],
    }


@mcp.tool()
def list_documents() -> list[dict]:
    """List all indexed documents with metadata.

    Returns:
        List of dictionaries with doc_id, title, path, and size.
    """
    documents = _index_state.get("documents", {})
    return [
        {
            "doc_id": doc_id,
            "title": doc["title"],
            "path": doc["path"],
            "size": len(doc["content"]),
        }
        for doc_id, doc in documents.items()
    ]


@mcp.tool()
def get_stats() -> dict:
    """Return index statistics.

    Returns:
        Dictionary with total_docs, total_tokens, avg_doc_length, and vocabulary_size.
    """
    documents = _index_state.get("documents", {})
    vectorizer = _index_state.get("vectorizer")

    total_docs = len(documents)
    if total_docs == 0:
        return {
            "total_docs": 0,
            "total_tokens": 0,
            "avg_doc_length": 0,
            "vocabulary_size": 0,
        }

    doc_lengths = [len(doc["content"].split()) for doc in documents.values()]
    total_tokens = sum(doc_lengths)
    avg_doc_length = round(total_tokens / total_docs, 2)
    vocabulary_size = len(vectorizer.vocabulary_) if vectorizer else 0

    return {
        "total_docs": total_docs,
        "total_tokens": total_tokens,
        "avg_doc_length": avg_doc_length,
        "vocabulary_size": vocabulary_size,
    }
