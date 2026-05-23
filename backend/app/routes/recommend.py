from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.models.schemas import (
    RecommendRequest,
    RecommendResponse,
    ContentResult
)
from app.ml.recommender import get_recommendations
from app.database.connection import get_db

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


# ─── POST /recommend ─────────────────────────────────────

@router.post("", response_model=RecommendResponse)
async def get_film_recommendations(
    request: RecommendRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Hybrid content-based recommendations for a given film.

    - Input: film_id, user_id, n (number of results)
    - Output: ranked list with sentiment scores + hidden gem flags
    """
    logger.info(
        f"Recommend request — film_id={request.film_id} "
        f"user_id={request.user_id} n={request.n}"
    )

    try:
        raw_results = get_recommendations(
            film_id=request.film_id,
            n=request.n
        )

        if not raw_results:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for film_id: {request.film_id}"
            )

        recommendations = [
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
            for r in raw_results
        ]

        logger.info(
            f"Recommendations returned — "
            f"film_id={request.film_id} count={len(recommendations)}"
        )

        return RecommendResponse(
            recommendations=recommendations,
            total=len(recommendations)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation engine failed: {str(e)}"
        )