"""Enrollment validates the entire batch before committing any vector."""
from __future__ import annotations
import numpy as np
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import AppError
from app.models.face_embedding import FaceEmbedding
from app.models.person import utcnow
from app.repositories.person_repository import PersonRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.person import PersonCreate, PersonOut
from app.utils.image_utils import decode_image
from app.utils.vector_utils import serialize_embedding, deserialize_embedding, normalize_embedding


class PersonService:
    def __init__(self, runtime):
        self.runtime = runtime

    def _require_database(self) -> None:
        if self.runtime.sessions is None:
            raise AppError('DATABASE_ERROR', 'Database is unavailable.', 503)

    def create(self, profile: PersonCreate) -> PersonOut:
        self._require_database()
        try:
            with self.runtime.sessions.begin() as session:
                person = PersonRepository(session).create(profile)
                result = PersonOut.model_validate(person)
            return result
        except IntegrityError as exc:
            raise AppError('PERSON_ALREADY_EXISTS', 'person_id already exists.', 409) from exc

    def get(self, person_id: str) -> PersonOut:
        self._require_database()
        with self.runtime.sessions() as session:
            person = PersonRepository(session).get(person_id)
            if person is None:
                raise AppError('PERSON_NOT_FOUND', 'Person not found.', 404)
            return PersonOut.model_validate(person)

    def list(self, offset: int = 0, limit: int = 500) -> list[PersonOut]:
        self._require_database()
        with self.runtime.sessions() as session:
            return [PersonOut.model_validate(p) for p in PersonRepository(session).list(offset, limit)]

    def delete(self, person_id: str) -> None:
        self._require_database()
        with self.runtime.sessions.begin() as session:
            repository = PersonRepository(session)
            person = repository.get(person_id)
            if person is None:
                raise AppError('PERSON_NOT_FOUND', 'Person not found.', 404)
            repository.delete(person)
        self.runtime.reload_index()
        self.runtime.invalidate_state()

    def register(self, person_id: str, images: list[tuple[str, bytes]]) -> int:
        self.get(person_id)
        if not 1 <= len(images) <= 5:
            raise AppError('INVALID_REQUEST', 'Upload 1 to 5 enrollment images.')
        with self.runtime.sessions() as session:
            count = len(EmbeddingRepository(session).samples(person_id))
        if count + len(images) > 5:
            raise AppError('INVALID_REQUEST', 'At most 5 enrollment photos per person; delete and recreate to replace.')
        vectors = [self.runtime.face_engine.extract_single_face_embedding(decode_image(raw, self.runtime.settings))
                   for _, raw in images]
        with self.runtime.sessions.begin() as session:
            repo = EmbeddingRepository(session)
            existing = repo.samples(person_id)
            if any(e.model_name != self.runtime.face_engine.model_name for e in existing):
                raise AppError('DATABASE_ERROR', 'Enrollment model differs from stored model.', 503)
            for (filename, _), vector in zip(images, vectors):
                session.add(FaceEmbedding(person_id=person_id, embedding=serialize_embedding(vector),
                    embedding_dim=len(vector), model_name=self.runtime.face_engine.model_name,
                    image_source=filename[:256], is_centroid=False))
            all_vectors = [deserialize_embedding(e.embedding, e.embedding_dim) for e in existing] + vectors
            centroid = repo.centroid(person_id)
            if centroid is None:
                centroid = FaceEmbedding(person_id=person_id, is_centroid=True,
                    embedding_dim=len(vectors[0]), model_name=self.runtime.face_engine.model_name,
                    image_source='centroid')
                session.add(centroid)
            centroid.embedding = serialize_embedding(normalize_embedding(np.mean(all_vectors, axis=0)))
            PersonRepository(session).get(person_id).updated_at = utcnow()
        self.runtime.reload_index()
        self.runtime.invalidate_state()
        return count + len(images)
