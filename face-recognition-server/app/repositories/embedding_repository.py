"""Vector queries; centroids never double-weight individual enrollment samples."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.face_embedding import FaceEmbedding


class EmbeddingRepository:
    def __init__(self, session: Session):
        self.session = session

    def samples(self, person_id: str | None = None) -> list[FaceEmbedding]:
        query = select(FaceEmbedding).where(FaceEmbedding.is_centroid.is_(False))
        if person_id is not None:
            query = query.where(FaceEmbedding.person_id == person_id)
        return list(self.session.scalars(query.order_by(FaceEmbedding.id)))

    def centroid(self, person_id: str) -> FaceEmbedding | None:
        return self.session.scalar(select(FaceEmbedding).where(
            FaceEmbedding.person_id == person_id, FaceEmbedding.is_centroid.is_(True)))
