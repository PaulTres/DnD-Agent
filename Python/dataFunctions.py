"""Compatibility helpers for the legacy console prototype.

Retrieval now delegates to the application's edition-scoped Chroma collections;
this module no longer builds or loads a FAISS index.
"""

from __future__ import annotations

from dnd_agent.retrieval import EditionKnowledgeBase


def split_into_chunks(text: str, max_words: int = 100, overlap: int = 20) -> list[str]:
    """Retained for old callers; production chunking uses the shared text splitter."""
    if max_words < 1 or overlap < 0 or overlap >= max_words:
        raise ValueError("Require max_words > overlap >= 0.")
    words = text.split()
    step = max_words - overlap
    return [" ".join(words[start:start + max_words]) for start in range(0, len(words), step)]


def build_prompt(context: list[str], question: str) -> str:
    context_text = "\n".join(context)
    return f"Context:\n{context_text}\n\nQuestion: {question}\nAnswer:"


def prepare_embeddings(force_reload: bool = False):
    """Return the Chroma knowledge base through the former helper's tuple shape.

    Run ``python -m dnd_agent.ingest --edition 5e_srd`` to ingest the corpus.
    ``force_reload`` is preserved as an explicit re-ingest option.
    """
    knowledge_base = EditionKnowledgeBase()
    if force_reload:
        knowledge_base.ingest_edition("5e_srd")
    return None, knowledge_base, None


def retrieve_context(query: str, embedder, index, metadata, top_k: int = 3) -> str:
    """Search the configured 5e Chroma domains and include source labels."""
    del embedder, metadata
    if not isinstance(index, EditionKnowledgeBase):
        raise TypeError("Expected the Chroma knowledge base returned by prepare_embeddings().")
    matches = []
    for domain in ("rules", "creatures", "spells", "items"):
        matches.extend(index.search(query, "5e_srd", domain, k=top_k))
    matches.sort(key=lambda document: (
        document.metadata.get("domain", ""),
        document.metadata.get("source_title", ""),
    ))
    return "\n\n".join(
        f"[Source: {doc.metadata.get('source_title', 'SRD')} · "
        f"{doc.metadata.get('source_file', 'unknown')}]\n{doc.page_content}"
        for doc in matches[:top_k]
    )
