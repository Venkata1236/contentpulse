import os
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from datetime import datetime

from app.core.config import settings
from app.database.connection import init_db
from app.ml.sentiment import load_sentiment_model
from app.ml.recommender import load_recommender, detect_hidden_gems
from app.rag.embedder import build_faiss_index
from app.routes import sentiment, recommend, search
from app.models.schemas import HealthResponse


# ─── Startup & Shutdown ──────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ContentPulse starting up...")

    # ── Step 1: Init database ─────────────────────────────
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database skipped: {e}")

    # ── Step 2: Load sentiment model ──────────────────────
    load_sentiment_model()
    logger.info("✅ Sentiment model loaded")

    # ── Step 3: Load TMDB dataset ─────────────────────────
    movies_path = "backend/data/tmdb_5000_movies.csv"
    credits_path = "backend/data/tmdb_5000_credits.csv"

    if os.path.exists(movies_path):
        df_movies = pd.read_csv(movies_path)
        logger.info(f"TMDB movies loaded — {len(df_movies)} rows")

        # Parse genres from JSON string to comma-separated
        import ast
        def parse_names(json_str):
            try:
                items = ast.literal_eval(json_str)
                return ", ".join([i["name"] for i in items])
            except Exception:
                return ""

        df_movies["genres"] = df_movies["genres"].apply(parse_names)
        df_movies["keywords"] = df_movies["keywords"].apply(parse_names)

        # Rename id to film_id
        df_movies = df_movies.rename(columns={"id": "film_id"})
        df_movies["film_id"] = df_movies["film_id"].astype(str)

        # Add default sentiment score (0.5) — updated after fine-tune
        if "sentiment_score" not in df_movies.columns:
            df_movies["sentiment_score"] = 0.5

        # Add default vote_count if missing
        if "vote_count" not in df_movies.columns:
            df_movies["vote_count"] = 0

        # Detect hidden gems
        df_movies = detect_hidden_gems(df_movies)

        # ── Step 4: Load recommender ──────────────────────
        load_recommender(df_movies)
        logger.info("✅ Hybrid recommender loaded")

        # ── Step 5: Build FAISS index ─────────────────────
        await build_faiss_index(df_movies)
        logger.info("✅ FAISS index ready")

    else:
        logger.warning(
            f"TMDB dataset not found at {movies_path}. "
            "Run: kaggle datasets download -d tmdb/tmdb-movie-metadata"
        )

    logger.info("🚀 ContentPulse is live!")
    yield

    # ── Shutdown ──────────────────────────────────────────
    logger.info("ContentPulse shutting down...")


# ─── App Init ────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Content recommendation and sentiment intelligence engine",
    lifespan=lifespan,
)


# ─── CORS ────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routers ─────────────────────────────────────────────

app.include_router(sentiment.router)
app.include_router(recommend.router)
app.include_router(search.router)


# ─── Health ──────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow()
    )