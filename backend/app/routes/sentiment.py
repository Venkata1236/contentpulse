from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.models.schemas import SentimentRequest, SentimentResponse, SentimentResult
from app.ml.sentiment import predict_sentiment_batch
from app.database.connection import get_db

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


# ─── POST /sentiment ─────────────────────────────────────

@router.post("", response_model=SentimentResponse)
async def analyze_sentiment(
    request: SentimentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Batch sentiment analysis using fine-tuned DistilBERT.

    - Input: list of review texts (max 50)
    - Output: label (positive/negative) + confidence per text
    """
    logger.info(f"Sentiment request — {len(request.texts)} texts")

    if not request.texts:
        raise HTTPException(
            status_code=400,
            detail="texts list cannot be empty"
        )

    try:
        raw_results = predict_sentiment_batch(request.texts)

        results = [
            SentimentResult(
                label=r["label"],
                confidence=r["confidence"]
            )
            for r in raw_results
        ]

        logger.info(f"Sentiment analysis complete — {len(results)} results")
        return SentimentResponse(results=results)

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment analysis failed: {str(e)}"
        )