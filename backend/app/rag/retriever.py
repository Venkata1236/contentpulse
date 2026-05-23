import numpy as np
from loguru import logger
from app.rag.embedder import embed_query, get_faiss_index, get_film_metadata
from app.core.config import settings


# ─── Core Retrieval ──────────────────────────────────────

async def retrieve_similar_content(
    query: str,
    k: int = 20,
    filters: dict = None
) -> list[dict]:
    """
    Embeds query → searches FAISS → returns top-k metadata.
    Applies optional post-retrieval filters.
    """
    faiss_index = get_faiss_index()
    film_metadata = get_film_metadata()

    if faiss_index is None:
        logger.error("FAISS index not loaded")
        raise RuntimeError("FAISS index not initialized. Run build_faiss_index() first.")

    # Embed the query
    query_vector = await embed_query(query)
    query_vector = query_vector.reshape(1, -1)

    # Search FAISS — retrieve more than needed for post-filter
    search_k = min(k * 3, faiss_index.ntotal)
    distances, indices = faiss_index.search(query_vector, search_k)

    # Collect raw results
    raw_results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        meta = film_metadata[idx].copy()
        meta["faiss_distance"] = float(dist)
        meta["relevance_score"] = _distance_to_score(dist)
        raw_results.append(meta)

    logger.info(f"FAISS retrieved {len(raw_results)} candidates for query: '{query}'")

    # Apply filters if provided
    if filters:
        raw_results = _apply_filters(raw_results, filters)
        logger.info(f"After filtering: {len(raw_results)} results remain")

    # Return top-k after filtering
    return raw_results[:k]


# ─── Filters ─────────────────────────────────────────────

def _apply_filters(results: list[dict], filters: dict) -> list[dict]:
    """
    Post-retrieval filter on metadata fields.
    Filters: genres, max_duration_mins, min_sentiment, decade
    """
    filtered = results

    # Genre filter
    if filters.get("genres"):
        target_genres = [g.lower() for g in filters["genres"]]
        filtered = [
            r for r in filtered
            if any(
                g.lower() in r.get("genres", "").lower()
                for g in target_genres
            )
        ]

    # Duration filter
    if filters.get("max_duration_mins"):
        max_dur = filters["max_duration_mins"]
        filtered = [
            r for r in filtered
            if r.get("runtime", 0) and int(r.get("runtime", 0)) <= max_dur
        ]

    # Sentiment filter
    if filters.get("min_sentiment"):
        min_sent = filters["min_sentiment"]
        filtered = [
            r for r in filtered
            if float(r.get("sentiment_score", 0)) >= min_sent
        ]

    # Decade filter — e.g. "1990s"
    if filters.get("decade"):
        decade_str = filters["decade"]
        try:
            decade_start = int(decade_str[:4])
            decade_end = decade_start + 9
            filtered = [
                r for r in filtered
                if _in_decade(r.get("release_date", ""), decade_start, decade_end)
            ]
        except (ValueError, TypeError):
            logger.warning(f"Could not parse decade filter: {decade_str}")

    return filtered


# ─── Helpers ─────────────────────────────────────────────

def _distance_to_score(distance: float) -> float:
    """
    Convert L2 distance to 0-1 relevance score.
    Lower distance = higher relevance.
    """
    return round(1 / (1 + distance), 4)


def _in_decade(release_date: str, start: int, end: int) -> bool:
    """Check if release date falls within a decade range."""
    try:
        year = int(str(release_date)[:4])
        return start <= year <= end
    except (ValueError, TypeError):
        return False


# ─── Hidden Gems Retrieval ───────────────────────────────

async def retrieve_hidden_gems(k: int = 10) -> list[dict]:
    """
    Returns top hidden gems sorted by sentiment score.
    Used to populate the Hidden Gems row in ContentGrid.
    """
    film_metadata = get_film_metadata()

    hidden_gems = [
        m for m in film_metadata
        if m.get("is_hidden_gem", False)
    ]

    # Sort by sentiment score descending
    hidden_gems.sort(
        key=lambda x: float(x.get("sentiment_score", 0)),
        reverse=True
    )

    logger.info(f"Hidden gems retrieved: {len(hidden_gems[:k])} results")
    return hidden_gems[:k]


# ─── Top Rated Retrieval ─────────────────────────────────

async def retrieve_top_rated(k: int = 10) -> list[dict]:
    """
    Returns top rated films by sentiment score.
    Used to populate the Highly Rated row in ContentGrid.
    """
    film_metadata = get_film_metadata()

    sorted_films = sorted(
        film_metadata,
        key=lambda x: float(x.get("sentiment_score", 0)),
        reverse=True
    )

    logger.info(f"Top rated retrieved: {len(sorted_films[:k])} results")
    return sorted_films[:k]