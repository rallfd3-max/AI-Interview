"""Single-frame recognition, explicit unknowns, session-stable profile selection."""
import logging
from uuid import uuid4
import cv2
from app.core.config import ROOT
from app.core.exceptions import AppError
from app.schemas.common import ErrorDetail
from app.schemas.recognition import RecognitionMeta, RecognitionResponse, MatchInfo, Processing
from app.utils.image_utils import decode_image, crop_face_box
from app.utils.timing import Timer

logger = logging.getLogger('face_server')


class RecognitionService:
    def __init__(self, runtime):
        self.runtime = runtime

    def recognize(self, raw: bytes, meta: RecognitionMeta, scope: str) -> RecognitionResponse:
        runtime, settings = self.runtime, self.runtime.settings
        timer = Timer()
        response = RecognitionResponse(request_id=meta.request_id,
                                       match=MatchInfo(threshold=settings.face_match_threshold))
        key = (scope, meta.device_id or '', meta.session_id or '')
        try:
            if not runtime.database_ready:
                raise AppError('DATABASE_ERROR', 'Database/index is unavailable.', 503)
            with timer.measure('decode'):
                image = decode_image(raw, settings)
                image = crop_face_box(image, meta.face_box)
            if settings.save_debug_images:
                directory = ROOT / 'data/temp/debug'
                directory.mkdir(parents=True, exist_ok=True)
                if not cv2.imwrite(str(directory / f'{uuid4().hex}.jpg'), image):
                    raise AppError('INTERNAL_ERROR', 'Failed to save debug image.', 500)
            vector = runtime.face_engine.extract_single_face_embedding(image, timer, settings.allow_multiple_faces)
            response.face_detected = True
            with timer.measure('matching'):
                candidates = runtime.matcher.match(vector, settings.face_match_top_k)
            if settings.debug:
                response.top_k = candidates
            if not candidates:
                raise AppError('NO_REGISTERED_FACES', 'No registered face embeddings.')
            best = candidates[0]
            response.match.similarity = best.similarity
            candidate = best.person_id if best.similarity >= settings.face_match_threshold else None
            if meta.session_id:
                response.stability = runtime.session_service.update(key, candidate,
                    meta.stable_frames or settings.stable_frame_count)
                selected = response.stability.confirmed_person_id
            else:
                # Stateless single-shot HTTP; no cross-person state sharing.
                if meta.stable_frames and meta.stable_frames > 1:
                    raise AppError('INVALID_REQUEST', 'session_id is required for multi-frame confirmation.')
                from app.schemas.recognition import Stability
                response.stability = Stability(confirmed=candidate is not None,
                    consistent_frames=1 if candidate else 0, confirmed_person_id=candidate)
                selected = candidate
            with timer.measure('database'):
                if selected and candidate == selected:
                    response.person = runtime.person_service.get(selected)
                    response.matched = True
            if candidate is None:
                response.error = ErrorDetail(code='UNKNOWN_FACE', message='No registered person exceeded the matching threshold.')
            elif selected != candidate:
                response.error = ErrorDetail(code='PENDING_CONFIRMATION', message='Waiting for consecutive matching frames.')
        except AppError as exc:
            response.success = exc.code in ('NO_FACE', 'NO_REGISTERED_FACES')
            response.face_detected = response.face_detected or exc.code == 'MULTIPLE_FACES'
            response.error = ErrorDetail(code=exc.code, message=exc.message)
            if meta.session_id:
                response.stability = runtime.session_service.update(key, None,
                    meta.stable_frames or settings.stable_frame_count)
        values = timer.result()
        runtime.recognition_count += 1
        runtime.total_recognition_ms += values['total_ms']
        if settings.return_debug_info:
            response.processing = Processing(**values)
        logger.info('Recognition completed', extra={'fields': {
            'request_id': meta.request_id, 'device_id': meta.device_id, 'session_id': meta.session_id,
            'face_count': 'multiple' if response.error and response.error.code == 'MULTIPLE_FACES' else int(response.face_detected),
            'match_result': response.person.person_id if response.person else (response.error.code if response.error else None),
            'similarity': response.match.similarity, 'total_ms': values['total_ms']}})
        return response
