from sqlalchemy import Column, String, Float, Boolean, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.database.connection import Base


# ─── Search History ──────────────────────────────────────

class SearchHistory(Base):
    __tablename__ = "search_history"
    __table_args__ = {"schema": "contentpulse"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = Column(String, nullable=False, index=True)
    query = Column(Text, nullable=False)
    extracted_filters = Column(JSONB, nullable=True)
    results_count = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# ─── Film Sentiments ─────────────────────────────────────

class FilmSentiment(Base):
    __tablename__ = "film_sentiments"
    __table_args__ = {"schema": "contentpulse"}

    film_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    is_hidden_gem = Column(Boolean, default=False)
    last_updated = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )