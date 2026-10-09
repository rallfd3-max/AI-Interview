"""Person table and cascading enrollment relationship."""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Person(Base):
    __tablename__ = 'persons'
    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    student_no: Mapped[str | None] = mapped_column(String(128))
    school: Mapped[str | None] = mapped_column(String(256))
    major: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    embeddings: Mapped[list['FaceEmbedding']] = relationship(
        cascade='all, delete-orphan', passive_deletes=True)
