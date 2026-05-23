import faiss
import numpy as np
import pandas as pd
import pickle
import os
from loguru import logger
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


# ─── Singleton State ─────────────────────────────────────

_faiss_index = None
_embeddings_model: OpenAIEmbeddings = None
_film_ids: list[str] = []
_film_metadata: list[dict] = []


# ─── Init Embeddings Model ───────────────────────────────

def get_embeddings_model() -> OpenAIEmbeddings:
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=settings.OPENAI_API_KEY
        )
        logger.info("OpenAI embeddings model initialized")
    return _embeddings_model


# ─── Build FAISS Index ───────────────────────────────────

async def build_faiss_index(df: pd.DataFrame):
    """
    Embeds all films and builds FAISS index.
    Called once during startup if index doesn't exist.
    """
    global _faiss_index, _film_ids, _film_metadata

    index_path = f"{settings.FAISS_INDEX_PATH}.index"
    meta_path = f"{settings.FAISS_INDEX_PATH}.pkl"

    # Load existing index if available
    if os.path.exists(index_path) and os.path.exists(meta_path):
        logger.info("Loading existing FAISS index from disk...")
        _faiss_index = faiss.read_index(index_path)
        with open(meta_path, "rb") as f:
            data = pickle.load(f)
            _film_ids = data["film_ids"]
            _film_metadata = data["film_metadata"]
        logger.info(f"FAISS index loaded — {_faiss_index.ntotal} vectors")
        return

    logger.info("Building new FAISS index — this may take a few minutes...")

    embeddings_model = get_embeddings_model()

    texts = []
    film_ids = []
    film_metadata = []

    for _, row in df.iterrows():
        # Build rich text for embedding
        text = (
            f"{row.get('title', '')}. "
            f"Genres: {row.get('genres', '')}. "
            f"{row.get('overview', '')}. "
            f"Keywords: {row.get('keywords', '')}"
        )
        texts.append(text)
        film_ids.append(str(row.get("film_id", "")))
        film_metadata.append({
            "film_id": str(row.get("film_id", "")),
            "title": str(row.get("title", "")),
            "genres": str(row.get("genres", "")),
            "overview": str(row.get("overview", "")),
            "release_date": str(row.get("release_date", "")),
            "runtime": row.get("runtime", 0),
            "sentiment_score": float(row.get("sentiment_score", 0.5)),
            "is_hidden_gem": bool(row.get("is_hidden_gem", False)),
            "vote_count": int(row.get("vote_count", 0)),
        })

    # Embed in batches of 100
    all_embeddings = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        logger.info(f"Embedding batch {i // batch_size + 1}/{(len(texts) // batch_size) + 1}")
        batch_embeddings = await embeddings_model.aembed_documents(batch)
        all_embeddings.extend(batch_embeddings)

    # Build FAISS index
    vectors = np.array(all_embeddings).astype("float32")
    dimension = vectors.shape[1]

    _faiss_index = faiss.IndexFlatL2(dimension)
    _faiss_index.add(vectors)

    _film_ids = film_ids
    _film_metadata = film_metadata

    # Save to disk
    os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(_faiss_index, index_path)
    with open(meta_path, "wb") as f:
        pickle.dump({
            "film_ids": _film_ids,
            "film_metadata": _film_metadata
        }, f)

    logger.info(f"FAISS index built and saved — {_faiss_index.ntotal} vectors")


# ─── Embed Single Query ──────────────────────────────────

async def embed_query(text: str) -> np.ndarray:
    """Embed a single query string for FAISS search."""
    embeddings_model = get_embeddings_model()
    vector = await embeddings_model.aembed_query(text)
    return np.array(vector).astype("float32")


# ─── Getters ─────────────────────────────────────────────

def get_faiss_index():
    return _faiss_index

def get_film_ids() -> list[str]:
    return _film_ids

def get_film_metadata() -> list[dict]:
    return _film_metadata