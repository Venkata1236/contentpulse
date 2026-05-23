from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from loguru import logger
from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    ContentResult,
    ExtractedFilters
)
from app.agents.chain import run_recommendation_chain
from app.database.connection import get_db
from app.database.models import SearchHistory

router = APIRouter(prefix="/search", tags=["Search"])


# ─── POST /search ─────────────────────────────────────────

@router.post("", response_model=SearchResponse)
async def natural_language_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Natural language content search powered by LangChain chain.

    - Input: user_id + natural language query
    - Output: filtered, ranked, explained content list
    - Saves every search to Supabase search_history
    """
    logger.info(
        f"Search request — user_id={request.user_id} "
        f"query='{request.query}'"
    )

    try:
        # ── Run LangChain recommendation chain ────────────
        chain_result = await run_recommendation_chain(
            user_id=request.user_id,
            query=request.query
        )

        results_data = chain_result.get("results", [])
        filters_data = chain_result.get("extracted_filters", {})
        total_found = chain_result.get("total_found", 0)

        # ── Build ContentResult list ───────────────────────
        results = [
            ContentResult(
                film_id=r["film_id"],
                title=r["title"],
                genres=r["genres"],
                overview=r["overview"],
                release_year=r.get("release_year"),
                duration_mins=r.get("duration_mins"),
                sentiment_score=r["sentiment_score"],
                similarity_score=r["similarity_score"],
                is_hidden_gem=r["is_hidden_gem"],
                why_recommended=r["why_recommended"],
                poster_url=r.get("poster_url"),
            )
            for r in results_data
        ]

        # ── Build ExtractedFilters ─────────────────────────
        extracted_filters = ExtractedFilters(
            genres=filters_data.get("genres"),
            mood=filters_data.get("mood"),
            max_duration_mins=filters_data.get("max_duration_mins"),
            min_sentiment=filters_data.get("min_sentiment"),
            decade=filters_data.get("decade"),
        )

        # ── Save to Supabase ───────────────────────────────
        await db.execute(
            insert(SearchHistory).values(
                user_id=request.user_id,
                query=request.query,
                extracted_filters=filters_data,
                results_count=total_found,
            )
        )
        await db.commit()
        logger.info(f"Search saved to Supabase — user={request.user_id}")

        return SearchResponse(
            results=results,
            extracted_filters=extracted_filters,
            total_found=total_found,
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )