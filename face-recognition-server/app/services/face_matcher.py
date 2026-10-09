"""Replaceable vector index with atomic immutable NumPy snapshots."""
from abc import ABC, abstractmethod
from threading import RLock
import numpy as np
from app.core.exceptions import AppError
from app.schemas.recognition import Candidate
from app.utils.vector_utils import normalize_embedding


class FaceVectorIndex(ABC):
    @abstractmethod
    def replace(self, rows: list[tuple[int, str, np.ndarray]]) -> None: ...

    @abstractmethod
    def match(self, query_embedding: np.ndarray, top_k: int = 3) -> list[Candidate]: ...


class FaceMatcher(FaceVectorIndex):
    def __init__(self, dimension: int = 512, strategy: str = 'max', top_n: int = 2):
        self.dimension, self.strategy, self.top_n = dimension, strategy, top_n
        self._lock = RLock()
        self.replace([])

    def replace(self, rows: list[tuple[int, str, np.ndarray]]) -> None:
        matrix = np.stack([normalize_embedding(row[2]) for row in rows]) if rows else np.empty((0, self.dimension), np.float32)
        if matrix.shape[1] != self.dimension:
            raise AppError('DATABASE_ERROR', 'Index embedding dimension mismatch.', 503)
        ids = np.asarray([row[1] for row in rows], dtype=str)
        with self._lock:
            self.embedding_matrix = matrix
            self.person_ids = ids
            self.embedding_ids = np.asarray([row[0] for row in rows], dtype=np.int64)

    def match(self, query_embedding: np.ndarray, top_k: int = 3) -> list[Candidate]:
        query = normalize_embedding(query_embedding)
        if query.size != self.dimension:
            raise AppError('FACE_EXTRACTION_FAILED', 'Query embedding dimension mismatch.')
        if top_k < 1:
            raise ValueError('top_k must be positive')
        with self._lock:
            matrix, ids = self.embedding_matrix, self.person_ids
        if not len(ids):
            return []
        scores = np.clip(matrix @ query, -1, 1)
        people, groups = np.unique(ids, return_inverse=True)
        if self.strategy == 'max':
            aggregated = np.full(len(people), -np.inf)
            np.maximum.at(aggregated, groups, scores)
        elif self.strategy == 'mean':
            aggregated = np.bincount(groups, weights=scores) / np.bincount(groups)
        elif self.strategy == 'top_n_mean':
            aggregated = np.asarray([np.sort(scores[groups == i])[-self.top_n:].mean() for i in range(len(people))])
        else:
            raise ValueError('Unknown score strategy')
        order = np.argsort(-aggregated, kind='stable')[:top_k]
        return [Candidate(person_id=str(people[i]), similarity=float(aggregated[i])) for i in order]
