from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Sentiment ───────────────────────────────────────────

class SentimentRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=50)

class SentimentResult(BaseModel):
    label: str
    confidence: float

class SentimentResponse(BaseModel):
    results: list[SentimentResult]


# ─── Recommend ───────────────────────────────────────────

class RecommendRequest(BaseModel):
    film_id: str
    user_id: str
    n: int = Field(default=10, ge=1, le=50)

class ContentResult(BaseModel):
    film_id: str
    title: str
    genres: list[str]
    overview: str
    release_year: Optional[int] = None
    duration_mins: Optional[int] = None
    sentiment_score: float
    similarity_score: float
    is_hidden_gem: bool
    why_recommended: str
    poster_url: Optional[str] = None

class RecommendResponse(BaseModel):
    recommendations: list[ContentResult]
    total: int


# ─── Search ──────────────────────────────────────────────

class SearchRequest(BaseModel):
    user_id: str
    query: str = Field(..., min_length=3, max_length=500)

class ExtractedFilters(BaseModel):
    genres: Optional[list[str]] = None
    mood: Optional[str] = None
    max_duration_mins: Optional[int] = None
    min_sentiment: Optional[float] = None
    decade: Optional[str] = None

class SearchResponse(BaseModel):
    results: list[ContentResult]
    extracted_filters: ExtractedFilters
    total_found: int
    query: str


# ─── Database ────────────────────────────────────────────

class SearchHistoryCreate(BaseModel):
    user_id: str
    query: str
    extracted_filters: dict
    results_count: int

class FilmSentimentCreate(BaseModel):
    film_id: str
    title: str
    sentiment_score: float
    is_hidden_gem: bool


# ─── Health ──────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime