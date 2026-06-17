"""Singleton wrapper around a local, persistent ChromaDB collection.

Embeddings are computed manually with sentence-transformers and passed to
ChromaDB directly (embedding_function=None) so the model is loaded exactly
once at process startup, not on every request and not inside ChromaDB's
own embedding pipeline.
"""

import threading
from datetime import datetime, timezone

import chromadb
from sentence_transformers import SentenceTransformer

_CHROMA_PATH = "./chroma_db"
_COLLECTION_NAME = "documind"
_EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


class VectorStore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialize()
                cls._instance = instance
        return cls._instance

    def _initialize(self) -> None:
        self._client = chromadb.PersistentClient(path=_CHROMA_PATH)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=None,
        )
        # Loaded once, shared by every request for the lifetime of the process.
        self._model = SentenceTransformer(_EMBEDDING_MODEL_NAME)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def add_source(
        self,
        source_id: str,
        source_title: str,
        source_type: str,
        chunks: list[str],
    ) -> int:
        """Embed and store all chunks for a source. Returns chunk count."""
        if not chunks:
            return 0

        embeddings = self._embed(chunks)
        ids = [f"{source_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source_id": source_id,
                "source_title": source_title,
                "source_type": source_type,
                "chunk_index": i,
                "added_at": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(len(chunks))
        ]

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return len(chunks)

    def query(self, question: str, top_k: int = 5) -> list[dict]:
        """Return the top_k most relevant chunks across all sources."""
        if self._collection.count() == 0:
            return []

        query_embedding = self._embed([question])[0]
        n_results = min(top_k, self._collection.count())

        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        chunks: list[dict] = []
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            chunks.append(
                {
                    "chunk_text": doc,
                    "source_id": meta.get("source_id"),
                    "source_title": meta.get("source_title"),
                    "source_type": meta.get("source_type"),
                    "distance": dist,
                }
            )
        return chunks

    def list_sources(self) -> list[dict]:
        """Return unique sources currently stored, with chunk counts."""
        if self._collection.count() == 0:
            return []

        all_items = self._collection.get(include=["metadatas"])
        metadatas = all_items.get("metadatas", [])

        sources: dict[str, dict] = {}
        for meta in metadatas:
            source_id = meta.get("source_id")
            if source_id is None:
                continue
            if source_id not in sources:
                sources[source_id] = {
                    "id": source_id,
                    "type": meta.get("source_type"),
                    "title": meta.get("source_title"),
                    "chunk_count": 0,
                    "added_at": meta.get("added_at"),
                }
            sources[source_id]["chunk_count"] += 1

        return sorted(
            sources.values(), key=lambda s: s["added_at"] or "", reverse=True
        )


# Module-level singleton instance, shared across the whole app.
vector_store = VectorStore()
