"""One bounded worker owns DB/index/session mutations, avoiding event-loop blocking."""
import asyncio
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from time import monotonic
from collections import deque
from collections.abc import Callable
from typing import TypeVar
from cachetools import TTLCache
from sqlalchemy import select, func
from app.core.config import Settings
from app.core.exceptions import AppError
from app.models.database import Base, create_database
from app.models.person import Person
from app.models.face_embedding import FaceEmbedding
from app.repositories.embedding_repository import EmbeddingRepository
from app.services.face_engine import FaceEngine
from app.services.face_matcher import FaceMatcher
from app.services.person_service import PersonService
from app.services.recognition_service import RecognitionService
from app.services.session_service import SessionService
from app.utils.vector_utils import deserialize_embedding
from app.schemas.recognition import RecognitionMeta, RecognitionResponse

logger = logging.getLogger('face_server')
Result = TypeVar('Result')


class Runtime:
    def __init__(self, settings: Settings, face_engine: FaceEngine | None = None):
        self.settings = settings
        self.face_engine = face_engine or FaceEngine(settings)
        self.matcher = FaceMatcher(self.face_engine.dimension, settings.person_score_strategy,
                                   settings.person_score_top_n)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='face-worker')
        self.pending = 0
        self.engine = self.sessions = None
        self.database_ready = False
        self.session_service = SessionService(settings.session_timeout_seconds)
        self.cache = TTLCache(settings.request_cache_size, settings.request_cache_ttl_seconds)
        self.rates = TTLCache(4096, 2)
        self.person_service = PersonService(self)
        self.recognition_service = RecognitionService(self)
        self.recognition_count = 0
        self.total_recognition_ms = 0.0

    def initialize(self) -> None:
        self.face_engine.initialize()
        self.matcher = FaceMatcher(self.face_engine.dimension, self.settings.person_score_strategy,
                                   self.settings.person_score_top_n)
        try:
            self.engine, self.sessions = create_database(self.settings.database_url)
            Base.metadata.create_all(self.engine)
            self.reload_index()
        except Exception:
            logger.exception('Database/index initialization failed')
            self.database_ready = False

    async def run(self, operation: Callable[..., Result], *args) -> Result:
        """Admission is bounded; cancelled requests retain a slot until work ends."""
        if self.pending >= self.settings.max_pending_jobs:
            raise AppError('RATE_LIMITED', 'Inference queue is full.', 429)
        self.pending += 1
        future = asyncio.get_running_loop().run_in_executor(self.executor, operation, *args)
        future.add_done_callback(lambda _: setattr(self, 'pending', self.pending - 1))
        return await asyncio.shield(future)

    def reload_index(self) -> int:
        try:
            with self.sessions() as session:
                samples = EmbeddingRepository(session).samples()
                if any(e.model_name != self.face_engine.model_name or e.embedding_dim != self.face_engine.dimension for e in samples):
                    raise AppError('DATABASE_ERROR', 'Stored vectors use a different model/dimension; re-enroll them.', 503)
                rows = [(e.id, e.person_id, deserialize_embedding(e.embedding, e.embedding_dim)) for e in samples]
            self.matcher.replace(rows)
            self.database_ready = True
            self.invalidate_state()
            return len(rows)
        except Exception:
            self.database_ready = False
            self.matcher.replace([])
            logger.exception('Index rebuild failed')
            raise

    def invalidate_state(self) -> None:
        self.cache.clear()
        self.session_service.states.clear()

    def rate_limit(self, scope: str) -> None:
        now = monotonic()
        times = self.rates.get(scope, deque())
        while times and times[0] <= now - 1:
            times.popleft()
        if len(times) >= self.settings.max_requests_per_second:
            raise AppError('RATE_LIMITED', 'Too many requests from this peer.', 429)
        times.append(now)
        self.rates[scope] = times

    def recognize(self, raw: bytes, meta: RecognitionMeta, scope: str) -> RecognitionResponse:
        key = (scope, meta.device_id, meta.session_id, meta.request_id)
        payload = meta.model_dump(exclude={'request_id'})
        digest = hashlib.sha256(raw + repr(payload).encode()).digest()
        cached = self.cache.get(key)
        if cached:
            if digest != cached[0]:
                raise AppError('INVALID_REQUEST', 'request_id was reused for a different payload.', 409)
            logger.info('Recognition cache hit', extra={'fields': {'request_id': meta.request_id}})
            return cached[1].model_copy(deep=True)
        self.rate_limit(scope)
        result = self.recognition_service.recognize(raw, meta, scope)
        if result.success or (result.error and result.error.code == 'MULTIPLE_FACES'):
            self.cache[key] = (digest, result.model_copy(deep=True))
        return result

    def clear_session(self, scope: str, device: str | None, session: str | None) -> None:
        key = (scope, device or '', session or '')
        self.session_service.clear(key)
        for cache_key in list(self.cache):
            if cache_key[:3] == (scope, device, session):
                del self.cache[cache_key]

    def health(self, request_id: str) -> dict:
        persons = embeddings = 0
        try:
            if self.sessions:
                with self.sessions() as session:
                    persons = session.scalar(select(func.count()).select_from(Person))
                    embeddings = session.scalar(select(func.count()).select_from(FaceEmbedding).where(FaceEmbedding.is_centroid.is_(False)))
                    session.execute(select(1))
        except Exception:
            logger.exception('Database health check failed')
            self.database_ready = False
        from app.schemas.common import Envelope
        return {**Envelope(type='health_result', request_id=request_id).model_dump(),
            'status': 'ok' if self.face_engine.ready and self.database_ready else 'degraded',
            'model_ready': self.face_engine.ready, 'database_ready': self.database_ready,
            'registered_persons': persons, 'registered_embeddings': embeddings}
