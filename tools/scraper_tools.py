from __future__ import annotations

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)


def scrape_urls(urls: list[str], max_chars: int = 8000) -> str:
    """Load and chunk web pages, returning concatenated text up to max_chars."""
    if not urls:
        return ""
    try:
        loader = WebBaseLoader(urls)
        docs = loader.load()
        chunks = _splitter.split_documents(docs)
        combined = "\n\n".join(c.page_content for c in chunks)
        return combined[:max_chars]
    except Exception as exc:
        return f"[scraper error: {exc}]"
