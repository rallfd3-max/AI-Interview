"""Individual normalized vectors and a separately maintained centroid."""
from datetime import datetime
from sqlalchemy import ForeignKey, String, LargeBinary, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base
from app.models.person import utcnow


class FaceEmbedding(Base):
    __tablename__ = 'face_embeddings'
    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[str] = mapped_column(ForeignKey('persons.person_id', ondelete='CASCADE'), index=True)
    embedding: Mapped[bytes] = mapped_column(LargeBinary)
    model_name: Mapped[str] = mapped_column(String(256))
    embedding_dim: Mapped[int]
    image_source: Mapped[str | None] = mapped_column(String(256))
    is_centroid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
