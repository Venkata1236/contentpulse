from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langsmith import traceable
from loguru import logger
from app.core.config import settings
from app.rag.retriever import retrieve_similar_content
from app.models.schemas import ExtractedFilters
import json
import re


# ─── LLM Init ────────────────────────────────────────────

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.2,
        openai_api_key=settings.OPENAI_API_KEY,
    )


# ─── Step 1: Filter Extraction Prompt ────────────────────

FILTER_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a film search assistant. Extract structured filters from the user's natural language query.

Return ONLY a valid JSON object with these fields:
{{
    "genres": ["list of genres or empty list"],
    "mood": "one word mood or null",
    "max_duration_mins": integer or null,
    "min_sentiment": float 0-1 or null,
    "decade": "e.g. 1990s or null",
    "search_query": "cleaned semantic search query"
}}

Genre options: Action, Comedy, Drama, Horror, Romance, Thriller, 
Biography, Animation, Documentary, Crime, Fantasy, Science Fiction

Mood options: inspiring, feel-good, dark, emotional, thought-provoking, 
funny, suspenseful, romantic, nostalgic

Examples:
- "inspiring biopics under 2 hours" → genres: ["Biography"], mood: "inspiring", max_duration_mins: 120
- "feel-good comedies from the 90s" → genres: ["Comedy"], mood: "feel-good", decade: "1990s"
- "dark psychological thrillers" → genres: ["Thriller"], mood: "dark", min_sentiment: null
"""),
    ("human", "{query}")
])


# ─── Step 2: Why Recommended Prompt ──────────────────────

WHY_RECOMMENDED_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a film recommendation assistant.
Given a film's metadata, write a single compelling sentence (max 20 words) explaining 
why a user would enjoy it. Be specific — mention genre, mood, or a unique quality.
Never start with 'This film' or 'This movie'."""),
    ("human", """Film: {title}
Genres: {genres}
Overview: {overview}
Sentiment Score: {sentiment_score}
Is Hidden Gem: {is_hidden_gem}

Write one sentence why someone would love this film:""")
])


# ─── Filter Extraction Chain ─────────────────────────────

async def extract_filters(query: str) -> dict:
    """
    Step 1: Parse natural language query into structured filters.
    Returns dict with genres, mood, max_duration_mins, etc.
    """
    llm = get_llm()
    chain = FILTER_EXTRACTION_PROMPT | llm | StrOutputParser()

    try:
        raw = await chain.ainvoke({"query": query})
        # Strip markdown code fences if present
        raw = re.sub(r"```json|```", "", raw).strip()
        filters = json.loads(raw)
        logger.info(f"Extracted filters: {filters}")
        return filters
    except json.JSONDecodeError as e:
        logger.warning(f"Filter extraction JSON parse failed: {e} — using defaults")
        return {
            "genres": [],
            "mood": None,
            "max_duration_mins": None,
            "min_sentiment": None,
            "decade": None,
            "search_query": query
        }


# ─── Why Recommended Generation ──────────────────────────

async def generate_why_recommended(film: dict) -> str:
    """
    Step 4: Generate a personalized reason for each recommendation.
    """
    llm = get_llm()
    chain = WHY_RECOMMENDED_PROMPT | llm | StrOutputParser()

    try:
        reason = await chain.ainvoke({
            "title": film.get("title", ""),
            "genres": film.get("genres", ""),
            "overview": film.get("overview", "")[:300],
            "sentiment_score": film.get("sentiment_score", 0.5),
            "is_hidden_gem": film.get("is_hidden_gem", False),
        })
        return reason.strip()
    except Exception as e:
        logger.warning(f"why_recommended generation failed: {e}")
        return "A highly rated film that matches your taste."


# ─── Main Recommendation Chain ───────────────────────────

@traceable(name="contentpulse-recommendation-chain")
async def run_recommendation_chain(user_id: str, query: str) -> dict:
    """
    Full LangChain recommendation chain — 4 steps:
    1. Extract filters from NL query
    2. FAISS retrieval with extracted filters
    3. Re-rank by sentiment + relevance
    4. Generate why_recommended per film

    Returns structured response for /search endpoint.
    """
    logger.info(f"Running recommendation chain — user={user_id}, query='{query}'")

    # ── Step 1: Extract filters ───────────────────────────
    filters = await extract_filters(query)
    search_query = filters.pop("search_query", query)

    # ── Step 2: FAISS retrieval ───────────────────────────
    candidates = await retrieve_similar_content(
        query=search_query,
        k=20,
        filters=filters
    )

    if not candidates:
        logger.warning(f"No candidates found for query: '{query}'")
        return {
            "results": [],
            "extracted_filters": filters,
            "total_found": 0,
            "query": query
        }

    # ── Step 3: Re-rank by sentiment + relevance ──────────
    for c in candidates:
        sentiment = float(c.get("sentiment_score", 0.5))
        relevance = float(c.get("relevance_score", 0.5))

        # Apply sentiment boost
        if sentiment > settings.SENTIMENT_BOOST_THRESHOLD:
            sentiment_adj = sentiment * settings.SENTIMENT_BOOST_MULTIPLIER
        elif sentiment < settings.SENTIMENT_PENALTY_THRESHOLD:
            sentiment_adj = sentiment * settings.SENTIMENT_PENALTY_MULTIPLIER
        else:
            sentiment_adj = sentiment

        c["final_score"] = (
            settings.TFIDF_WEIGHT * relevance +
            settings.SENTIMENT_WEIGHT * min(sentiment_adj, 1.0)
        )

    candidates.sort(key=lambda x: x["final_score"], reverse=True)
    top_results = candidates[:10]

    # ── Step 4: Generate why_recommended ─────────────────
    for film in top_results:
        film["why_recommended"] = await generate_why_recommended(film)

    # ── Build response ────────────────────────────────────
    results = []
    for film in top_results:
        genres_raw = film.get("genres", "")
        genres_list = (
            [g.strip() for g in genres_raw.split(",") if g.strip()]
            if isinstance(genres_raw, str)
            else genres_raw
        )
        results.append({
            "film_id": str(film.get("film_id", "")),
            "title": str(film.get("title", "")),
            "genres": genres_list,
            "overview": str(film.get("overview", "")),
            "release_year": _parse_year(film.get("release_date", "")),
            "duration_mins": int(film.get("runtime", 0)) or None,
            "sentiment_score": round(float(film.get("sentiment_score", 0.5)), 4),
            "similarity_score": round(float(film.get("relevance_score", 0.5)), 4),
            "is_hidden_gem": bool(film.get("is_hidden_gem", False)),
            "why_recommended": film.get("why_recommended", ""),
            "poster_url": None,
        })

    logger.info(f"Chain complete — {len(results)} results returned")

    return {
        "results": results,
        "extracted_filters": filters,
        "total_found": len(results),
        "query": query
    }


# ─── Helper ──────────────────────────────────────────────

def _parse_year(release_date: str):
    try:
        return int(str(release_date)[:4])
    except (ValueError, TypeError):
        return None