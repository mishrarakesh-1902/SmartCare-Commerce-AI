import os
import glob
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "ecommerce_support_docs"

class ECommerceRetriever:
    """
    Retrieves grounded e-commerce policy documents using semantic search (ChromaDB + Ollama)
    with a graceful semantic-scoring fallback.
    """
    def __init__(self):
        self.documents = self._load_documents()
        self.chroma_collection = None
        self._init_chroma()

    def _load_documents(self) -> List[Dict]:
        docs = []
        if not os.path.exists(KB_DIR):
            return docs

        for filepath in glob.glob(os.path.join(KB_DIR, "*.txt")):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    docs.append({
                        "filename": filename,
                        "content": content
                    })
            except Exception as e:
                logger.error(f"Error reading doc {filepath}: {e}")
        return docs

    def _init_chroma(self):
        try:
            import chromadb
            client = chromadb.PersistentClient(path=CHROMA_DIR)
            self.chroma_collection = client.get_or_create_collection(name=COLLECTION_NAME)
            
            # If collection is empty, ingest current documents
            if self.chroma_collection.count() == 0 and self.documents:
                import ollama
                for doc in self.documents:
                    try:
                        emb = ollama.embeddings(model=EMBED_MODEL, prompt=doc["content"])["embedding"]
                        self.chroma_collection.add(
                            ids=[doc["filename"]],
                            embeddings=[emb],
                            documents=[doc["content"]],
                            metadatas=[{"filename": doc["filename"]}]
                        )
                    except Exception as emb_err:
                        logger.warning(f"Chroma indexing skipped for {doc['filename']}: {emb_err}")
        except Exception as e:
            logger.info(f"Using keyword fallback retrieval (ChromaDB not active): {e}")

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict]:
        """
        Retrieves the top-k most relevant policies for the given query.
        """
        # Try semantic retrieval via ChromaDB if available
        if self.chroma_collection and self.chroma_collection.count() > 0:
            try:
                import ollama
                query_emb = ollama.embeddings(model=EMBED_MODEL, prompt=query)["embedding"]
                results = self.chroma_collection.query(
                    query_embeddings=[query_emb],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"]
                )
                if results["ids"] and len(results["ids"][0]) > 0:
                    matched = []
                    for i in range(len(results["ids"][0])):
                        matched.append({
                            "filename": results["metadatas"][0][i]["filename"],
                            "content": results["documents"][0][i],
                            "score": round(results["distances"][0][i], 4)
                        })
                    return matched
            except Exception as e:
                logger.debug(f"Semantic query fallback triggered: {e}")

        # High-precision Keyword & Relevance Fallback
        query_words = set(query.lower().split())
        scored_docs = []
        for doc in self.documents:
            content_lower = doc["content"].lower()
            # Calculate match frequency
            score = sum(content_lower.count(word) for word in query_words if len(word) > 2)
            scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [{"filename": d["filename"], "content": d["content"], "score": 0.5} for _, d in scored_docs[:top_k]]

def search_ecommerce_docs(query: str, top_k: int = 2) -> List[Dict]:
    retriever = ECommerceRetriever()
    return retriever.retrieve(query, top_k=top_k)
