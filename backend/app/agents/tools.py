from langchain.tools import tool
from loguru import logger
from app.rag.retriever import retrieve_similar_content, retrieve_hidden_gems
from app.ml.recommender import get_dataframe
import pandas as pd


# ─── Tool 1: FAISS Content Search ────────────────────────

@tool
async def search_content(query: str) -> str:
    """
    Search for films and content using semantic similarity.
    Input: natural language query like 'inspiring biopics'
    Output: JSON string of matching films with metadata
    """
    try:
        results = await retrieve_similar_content(query, k=15)
        if not results:
            return "No results found for the given query."

        output = []
        for r in results:
            output.append(
                f"Title: {r['title']} | "
                f"Genres: {r['genres']} | "
                f"Sentiment: {r['sentiment_score']} | "
                f"Runtime: {r.get('runtime', 'N/A')} mins | "
                f"Hidden Gem: {r['is_hidden_gem']} | "
                f"Overview: {r['overview'][:150]}..."
            )

        logger.info(f"search_content tool returned {len(output)} results")
        return "\n".join(output)

    except Exception as e:
        logger.error(f"search_content tool error: {e}")
        return f"Search failed: {str(e)}"


# ─── Tool 2: Filter by Genre ─────────────────────────────

@tool
async def filter_by_genre(genre: str) -> str:
    """
    Filter films by a specific genre.
    Input: genre name like 'Comedy', 'Drama', 'Action'
    Output: list of matching films
    """
    try:
        df = get_dataframe()
        if df is None:
            return "Film database not loaded."

        mask = df["genres"].str.contains(genre, case=False, na=False)
        filtered = df[mask].head(20)

        if filtered.empty:
            return f"No films found for genre: {genre}"

        output = []
        for _, row in filtered.iterrows():
            output.append(
                f"Title: {row['title']} | "
                f"Sentiment: {round(float(row.get('sentiment_score', 0.5)), 2)} | "
                f"Runtime: {row.get('runtime', 'N/A')} mins | "
                f"Hidden Gem: {row.get('is_hidden_gem', False)}"
            )

        logger.info(f"filter_by_genre tool: {len(output)} results for genre={genre}")
        return "\n".join(output)

    except Exception as e:
        logger.error(f"filter_by_genre tool error: {e}")
        return f"Filter failed: {str(e)}"


# ─── Tool 3: Filter by Duration ──────────────────────────

@tool
async def filter_by_duration(max_minutes: int) -> str:
    """
    Filter films by maximum duration in minutes.
    Input: integer max duration like 120
    Output: list of films under that duration
    """
    try:
        df = get_dataframe()
        if df is None:
            return "Film database not loaded."

        filtered = df[
            (df["runtime"] > 0) &
            (df["runtime"] <= max_minutes)
        ].head(20)

        if filtered.empty:
            return f"No films found under {max_minutes} minutes."

        output = []
        for _, row in filtered.iterrows():
            output.append(
                f"Title: {row['title']} | "
                f"Runtime: {int(row['runtime'])} mins | "
                f"Genres: {row.get('genres', '')} | "
                f"Sentiment: {round(float(row.get('sentiment_score', 0.5)), 2)}"
            )

        logger.info(f"filter_by_duration: {len(output)} results under {max_minutes} mins")
        return "\n".join(output)

    except Exception as e:
        logger.error(f"filter_by_duration tool error: {e}")
        return f"Filter failed: {str(e)}"


# ─── Tool 4: Get Hidden Gems ─────────────────────────────

@tool
async def get_hidden_gems(limit: int = 10) -> str:
    """
    Retrieve hidden gem films — high sentiment but low popularity.
    Input: number of results to return (default 10)
    Output: list of hidden gem films
    """
    try:
        gems = await retrieve_hidden_gems(k=limit)
        if not gems:
            return "No hidden gems found in the database."

        output = []
        for g in gems:
            output.append(
                f"Title: {g['title']} | "
                f"Sentiment: {g['sentiment_score']} | "
                f"Genres: {g['genres']} | "
                f"Votes: {g.get('vote_count', 'N/A')}"
            )

        logger.info(f"get_hidden_gems tool returned {len(output)} gems")
        return "\n".join(output)

    except Exception as e:
        logger.error(f"get_hidden_gems tool error: {e}")
        return f"Hidden gems fetch failed: {str(e)}"


# ─── Tool 5: Filter by Sentiment ─────────────────────────

@tool
async def filter_by_sentiment(min_score: float) -> str:
    """
    Filter films by minimum sentiment score.
    Input: float between 0 and 1, e.g. 0.75
    Output: list of films above that sentiment threshold
    """
    try:
        df = get_dataframe()
        if df is None:
            return "Film database not loaded."

        filtered = df[
            df["sentiment_score"] >= min_score
        ].sort_values("sentiment_score", ascending=False).head(20)

        if filtered.empty:
            return f"No films found with sentiment >= {min_score}"

        output = []
        for _, row in filtered.iterrows():
            output.append(
                f"Title: {row['title']} | "
                f"Sentiment: {round(float(row['sentiment_score']), 2)} | "
                f"Genres: {row.get('genres', '')} | "
                f"Hidden Gem: {row.get('is_hidden_gem', False)}"
            )

        logger.info(f"filter_by_sentiment: {len(output)} results above {min_score}")
        return "\n".join(output)

    except Exception as e:
        logger.error(f"filter_by_sentiment tool error: {e}")
        return f"Filter failed: {str(e)}"


# ─── Export All Tools ─────────────────────────────────────

all_tools = [
    search_content,
    filter_by_genre,
    filter_by_duration,
    get_hidden_gems,
    filter_by_sentiment,
]