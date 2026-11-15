"""Lazy, provenance-preserving, edition-isolated Chroma rule retrieval."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Iterable

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import EDITIONS, RULE_DOMAINS, RuntimeSettings, get_settings


class CorpusError(RuntimeError):
    """Raised when edition source data cannot be loaded or ingested."""


@dataclass(frozen=True)
class IngestSummary:
    edition: str
    domain: str
    documents: int
    collection: str


def _json_records(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusError(f"Could not read SRD source file {path}: {exc}") from exc
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("results", [payload])
    else:
        raise CorpusError(f"Expected a JSON object or array in {path}.")
    if not all(isinstance(record, dict) for record in records):
        raise CorpusError(f"Expected each entry in {path} to be a JSON object.")
    return records


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return "\n".join(f"{key}: {_flatten(item)}" for key, item in value.items())
    if isinstance(value, list):
        return "\n".join(_flatten(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _record_document(record: dict[str, Any], *, edition: str, domain: str,
                     source_file: str, source_name: str) -> Document:
    title = str(record.get("name") or record.get("index") or source_file)
    record_id = str(record.get("index") or record.get("id") or title)
    text = _flatten(record)
    metadata: dict[str, str] = {
        "edition": edition,
        "domain": domain,
        "source_name": source_name,
        "source_file": source_file,
        "source_record_id": record_id,
        "source_title": title,
    }
    for key in ("url", "source_url"):
        value = record.get(key)
        if isinstance(value, str) and value:
            metadata["source_url"] = value
            break
    return Document(page_content=text, metadata=metadata)


class EditionKnowledgeBase:
    """Lazily loads a selected edition's domain collections and embeddings."""

    def __init__(self, settings: RuntimeSettings | None = None) -> None:
        self.settings = settings or get_settings()
        self._stores: dict[tuple[str, str], Chroma] = {}

    @cached_property
    def _embeddings(self) -> HuggingFaceEmbeddings:
        try:
            return HuggingFaceEmbeddings(model_name=self.settings.embedding_model)
        except Exception as exc:
            raise CorpusError(
                f"Could not initialize local embedding model "
                f"{self.settings.embedding_model!r}: {exc}. Check DND_EMBEDDING_MODEL "
                "and install the model locally or allow its initial download."
            ) from exc

    def _edition_domain(self, edition_key: str, domain: str) -> tuple[Any, str]:
        try:
            edition = EDITIONS[edition_key]
        except KeyError as exc:
            raise ValueError(f"Unsupported edition {edition_key!r}.") from exc
        if domain not in RULE_DOMAINS:
            raise ValueError(f"Unsupported rules domain {domain!r}.")
        return edition, edition.collections[domain]

    def get_store(self, edition_key: str, domain: str) -> Chroma:
        """Open or create a collection only when the caller asks for it."""
        edition, collection_name = self._edition_domain(edition_key, domain)
        key = (edition_key, domain)
        if key not in self._stores:
            try:
                self._stores[key] = Chroma(
                    collection_name=collection_name,
                    embedding_function=self._embeddings,
                    persist_directory=str(self.settings.chroma_dir),
                    collection_metadata={"edition": edition_key, "domain": domain},
                )
            except Exception as exc:
                raise CorpusError(
                    f"Could not open Chroma collection {collection_name!r}: {exc}"
                ) from exc
        return self._stores[key]

    def ingest_domain(self, edition_key: str, domain: str) -> IngestSummary:
        """Chunk and ingest one configured corpus domain with stable provenance IDs."""
        edition, collection_name = self._edition_domain(edition_key, domain)
        source_files = edition.source_files.get(domain, ())
        if not source_files:
            raise CorpusError(f"No source files are configured for {edition_key}/{domain}.")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        documents: list[Document] = []
        ids: list[str] = []
        for filename in source_files:
            path = edition.source_path / filename
            if not path.is_file():
                raise CorpusError(f"Configured SRD source file does not exist: {path}")
            for record in _json_records(path):
                base = _record_document(
                    record,
                    edition=edition_key,
                    domain=domain,
                    source_file=filename,
                    source_name=edition.source_name,
                )
                for chunk_index, chunk in enumerate(splitter.split_documents([base])):
                    content_key = "\0".join(
                        (edition_key, domain, filename, base.metadata["source_record_id"],
                         str(chunk_index), chunk.page_content)
                    )
                    ids.append(hashlib.sha256(content_key.encode("utf-8")).hexdigest())
                    documents.append(chunk)
        if documents:
            store = self.get_store(edition_key, domain)
            # Stable IDs make repeated ingestion of unchanged chunks idempotent.
            try:
                for start in range(0, len(documents), 128):
                    store.add_documents(
                        documents[start:start + 128], ids=ids[start:start + 128]
                    )
            except Exception as exc:
                raise CorpusError(
                    f"Could not embed or ingest {edition_key}/{domain}: {exc}. "
                    "Check the local embedding model and writable Chroma directory."
                ) from exc
        return IngestSummary(edition_key, domain, len(documents), collection_name)

    def ingest_edition(self, edition_key: str) -> list[IngestSummary]:
        """Explicitly ingest every configured rules domain for one edition."""
        if edition_key not in EDITIONS:
            raise ValueError(f"Unsupported edition {edition_key!r}.")
        return [self.ingest_domain(edition_key, domain) for domain in RULE_DOMAINS]

    def search(self, query: str, edition_key: str, domain: str, *, k: int = 4) -> list[Document]:
        """Search one domain; edition filtering is always applied at query time."""
        if not query.strip():
            raise ValueError("Retrieval query must not be empty.")
        if k < 1 or k > 50:
            raise ValueError("k must be between 1 and 50.")
        store = self.get_store(edition_key, domain)
        try:
            return store.similarity_search(query, k=k, filter={"edition": edition_key})
        except Exception as exc:
            raise CorpusError(
                f"Could not search {edition_key}/{domain}: {exc}. "
                "Run the SRD ingestion command for this edition first."
            ) from exc


def source_documents(edition_key: str, domain: str) -> Iterable[Document]:
    """Yield unchunked source documents; useful for inspection and ingestion tools."""
    if edition_key not in EDITIONS:
        raise ValueError(f"Unsupported edition {edition_key!r}.")
    edition = EDITIONS[edition_key]
    if domain not in RULE_DOMAINS:
        raise ValueError(f"Unsupported rules domain {domain!r}.")
    for filename in edition.source_files.get(domain, ()):
        for record in _json_records(edition.source_path / filename):
            yield _record_document(record, edition=edition_key, domain=domain,
                                   source_file=filename, source_name=edition.source_name)
