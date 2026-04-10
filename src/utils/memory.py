import os
import json
from typing import Any, List
import numpy as np
from langchain_core.embeddings import Embeddings


def _is_likely_real_key(value: str | None) -> bool:
    if not value:
        return False
    v = value.strip()
    if not v:
        return False
    placeholders = ["fake", "your_", "changeme", "replace_me", "dummy", "test"]
    return not any(p in v.lower() for p in placeholders)


class VectorMemory:
    """
    Vector memory with automatic backend fallback:
    - Preferred: Chroma (if import/runtime works)
    - Fallback: Local JSON + cosine similarity over embedding vectors
    """

    def __init__(self, collection_name: str = "sweat_memory", persist_directory: str = "./memory/chroma_db"):
        self.embeddings = self._get_embeddings()
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.local_store_path = "./memory/vector_memory.json"

        self.backend = "local"
        self.vector_store = None

        # Try Chroma first (lazy import to avoid import-time crash on incompatible py versions)
        try:
            from langchain_chroma import Chroma
            self.vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory,
            )
            self.backend = "chroma"
        except Exception:
            self._ensure_local_store()
            self.backend = "local"

    def _ensure_local_store(self) -> None:
        os.makedirs(os.path.dirname(self.local_store_path), exist_ok=True)
        if not os.path.exists(self.local_store_path):
            with open(self.local_store_path, "w") as f:
                json.dump([], f)

    def _load_local(self) -> list[dict]:
        self._ensure_local_store()
        with open(self.local_store_path, "r") as f:
            return json.load(f)

    def _save_local(self, rows: list[dict]) -> None:
        with open(self.local_store_path, "w") as f:
            json.dump(rows, f)

    def _get_embeddings(self) -> Embeddings:
        """
        Factory to get the right embedding model based on environment.
        Priority: OpenAI -> Gemini -> Ollama -> Fake (for testing)
        """
        if _is_likely_real_key(os.getenv("OPENAI_API_KEY")):
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(model="text-embedding-3-small")

        if _is_likely_real_key(os.getenv("GEMINI_API_KEY")):
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        if os.getenv("SWEAT_USE_OLLAMA", "false").lower() in {"1", "true", "yes", "on"}:
            from langchain_ollama import OllamaEmbeddings
            # NOTE: ideally use nomic-embed-text. using llama3.2:1b for local-only setup parity.
            return OllamaEmbeddings(model="llama3.2:1b")

        from langchain_core.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=384)

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def save_context(self, text: str, metadata: dict) -> None:
        """Saves a text snippet with metadata to vector memory."""
        if self.backend == "chroma" and self.vector_store is not None:
            self.vector_store.add_texts(texts=[text], metadatas=[metadata])
            return

        # local fallback
        vec = self.embeddings.embed_documents([text])[0]
        rows = self._load_local()
        rows.append({"text": text, "metadata": metadata, "embedding": vec})
        self._save_local(rows)

    def retrieve_context(self, query: str, k: int = 3) -> List[str]:
        """Retrieves top-k relevant snippets."""
        if self.backend == "chroma" and self.vector_store is not None:
            docs = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]

        # local fallback
        rows = self._load_local()
        if not rows:
            return []

        q = np.array(self.embeddings.embed_query(query), dtype=float)
        scored = []
        for r in rows:
            emb = np.array(r["embedding"], dtype=float)
            if emb.shape != q.shape:
                # Skip stale vectors from prior embedding model dimensions.
                continue
            scored.append((self._cosine(q, emb), r["text"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:k]]


_memory_instance = None


def get_memory() -> VectorMemory:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = VectorMemory()
    return _memory_instance
