"""Safe portable float32 vector storage and normalization."""
import numpy as np
from numpy.typing import NDArray
from app.core.exceptions import AppError


def normalize_embedding(value: NDArray | list[float]) -> NDArray[np.float32]:
    vector = np.asarray(value, dtype=np.float32)
    if vector.ndim != 1 or not vector.size or not np.isfinite(vector).all():
        raise AppError('FACE_EXTRACTION_FAILED', 'Invalid embedding.')
    norm = float(np.linalg.norm(vector))
    if not np.isfinite(norm) or norm <= 1e-12:
        raise AppError('FACE_EXTRACTION_FAILED', 'Embedding norm is zero or invalid.')
    return np.ascontiguousarray(vector / norm, dtype=np.float32)


def serialize_embedding(value: NDArray) -> bytes:
    return normalize_embedding(value).astype('<f4').tobytes()


def deserialize_embedding(blob: bytes, dimension: int) -> NDArray[np.float32]:
    if dimension <= 0 or len(blob) != dimension * 4:
        raise AppError('DATABASE_ERROR', 'Stored embedding dimension mismatch.', 503)
    return normalize_embedding(np.frombuffer(blob, dtype='<f4').copy())
