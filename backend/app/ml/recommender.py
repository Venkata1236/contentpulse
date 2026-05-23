import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger
from typing import Optional
from app.core.config import settings


# ─── Singleton State ─────────────────────────────────────

_df: Optional[pd.DataFrame] = None
_tfidf_matrix = None
_vectorizer: Optional[TfidfVectorizer] = None


# ─── Load & Build ────────────────────────────────────────

def load_recommender(df: pd.DataFrame):
    """
    Called once at startup with the TMDB dataframe.
    Builds TF-IDF matrix on combined content text.
    """
    global _df, _tfidf_matrix, _vectorizer

    _df = df.copy()
    _df = _df.fillna("")

    # Combine content fields for TF-IDF
    _df["content_text"] = (
        _df["title"] + " " +
        _df["genres"] + " " +
        _df["overview"] + " " +
        _df["keywords"]
    )

    logger.info("Building TF-IDF matrix on content text...")
    _vectorizer = TfidfVectorizer(
        max_features=15000,
        stop_words="english",
        ngram_range=(1, 2)
    )
    _tfidf_matrix = _vectorizer.fit_transform(_df["content_text"])
    logger.info(f"TF-IDF matrix built — shape: {_tfidf_matrix.shape}")


# ─── Hidden Gem Detection ────────────────────────────────

def detect_hidden_gems(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hidden gem = high sentiment but low view count.
    sentiment_score > 0.80 AND vote_count < median vote_count
    """
    median_votes = df["vote_count"].median()

    df["is_hidden_gem"] = (
        (df["sentiment_score"] > settings.HIDDEN_GEM_SENTIMENT_THRESHOLD) &
        (df["vote_count"] < median_votes)
    )

    hidden_count = df["is_hidden_gem"].sum()
    logger.info(f"Hidden gems detected: {hidden_count} films")
    return df


# ─── Sentiment Boost ─────────────────────────────────────

def apply_sentiment_boost(similarity_scores: np.ndarray, sentiment_scores: np.ndarray) -> np.ndarray:
    """
    Boost films with high sentiment, penalize low sentiment.
    Final score = (0.6 * similarity) + (0.4 * sentiment_boost)
    """
    boosted_sentiment = sentiment_scores.copy()

    # Apply boost
    high_mask = sentiment_scores > settings.SENTIMENT_BOOST_THRESHOLD
    boosted_sentiment[high_mask] *= settings.SENTIMENT_BOOST_MULTIPLIER

    # Apply penalty
    low_mask = sentiment_scores < settings.SENTIMENT_PENALTY_THRESHOLD
    boosted_sentiment[low_mask] *= settings.SENTIMENT_PENALTY_MULTIPLIER

    # Clip to 0-1 range
    boosted_sentiment = np.clip(boosted_sentiment, 0.0, 1.0)

    # Hybrid final score
    final_scores = (
        settings.TFIDF_WEIGHT * similarity_scores +
        settings.SENTIMENT_WEIGHT * boosted_sentiment
    )

    return final_scores


# ─── Get Recommendations ─────────────────────────────────

def get_recommendations(film_id: str, n: int = 10) -> list[dict]:
    """
    Returns top-n recommendations for a given film_id.
    Uses hybrid: TF-IDF similarity + sentiment boost.
    """
    if _df is None or _tfidf_matrix is None:
        raise RuntimeError("Recommender not loaded. Call load_recommender() first.")

    # Find film index
    matches = _df[_df["film_id"] == film_id]
    if matches.empty:
        logger.warning(f"film_id not found: {film_id}")
        return []

    idx = matches.index[0]

    # Cosine similarity
    film_vector = _tfidf_matrix[idx]
    similarity_scores = cosine_similarity(film_vector, _tfidf_matrix).flatten()

    # Get sentiment scores array
    sentiment_scores = _df["sentiment_score"].values.astype(float)

    # Apply hybrid scoring
    final_scores = apply_sentiment_boost(similarity_scores, sentiment_scores)

    # Exclude the film itself
    final_scores[idx] = -1

    # Top-n indices
    top_indices = np.argsort(final_scores)[::-1][:n]

    results = []
    for i in top_indices:
        row = _df.iloc[i]
        results.append({
            "film_id": str(row.get("film_id", "")),
            "title": str(row.get("title", "")),
            "genres": _parse_genres(row.get("genres", "")),
            "overview": str(row.get("overview", "")),
            "release_year": _parse_year(row.get("release_date", "")),
            "duration_mins": int(row.get("runtime", 0)) or None,
            "sentiment_score": round(float(row.get("sentiment_score", 0.5)), 4),
            "similarity_score": round(float(similarity_scores[i]), 4),
            "is_hidden_gem": bool(row.get("is_hidden_gem", False)),
            "why_recommended": _generate_why(row),
            "poster_url": None,
        })

    logger.info(f"Recommendations generated for film_id={film_id} — {len(results)} results")
    return results


# ─── Helpers ─────────────────────────────────────────────

def _parse_genres(genres_str: str) -> list[str]:
    """Parse genre string into list."""
    if not genres_str:
        return []
    return [g.strip() for g in genres_str.split(",") if g.strip()]


def _parse_year(release_date: str) -> Optional[int]:
    """Extract year from release date string."""
    try:
        return int(str(release_date)[:4])
    except (ValueError, TypeError):
        return None


def _generate_why(row) -> str:
    """Simple rule-based why_recommended string."""
    sentiment = float(row.get("sentiment_score", 0.5))
    is_gem = bool(row.get("is_hidden_gem", False))
    genres = _parse_genres(row.get("genres", ""))
    genre_str = genres[0] if genres else "film"

    if is_gem:
        return f"Hidden gem {genre_str} loved by critics but overlooked by mainstream audiences."
    elif sentiment > 0.75:
        return f"Highly acclaimed {genre_str} with overwhelmingly positive audience sentiment."
    elif sentiment > 0.5:
        return f"Well-received {genre_str} that matches your taste profile."
    else:
        return f"Stylistically similar {genre_str} to your selection."


def get_dataframe() -> Optional[pd.DataFrame]:
    """Expose loaded dataframe for use in other modules."""
    return _df