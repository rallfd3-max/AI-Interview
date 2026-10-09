"""InsightFace 0.7.3 adapter: SCRFD landmarks -> aligned ArcFace ONNX vector."""
import logging
from threading import RLock
from time import perf_counter
import numpy as np
from app.core.config import Settings
from app.core.exceptions import AppError
from app.utils.timing import Timer
from app.utils.vector_utils import normalize_embedding

logger = logging.getLogger('face_server')


class FaceEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ready = False
        self.dimension = 512
        self.providers: list[str] = []
        self.model_name = settings.face_model_name
        self._app = None
        self._lock = RLock()

    def initialize(self) -> None:
        """Load once. Offline mode never implicitly downloads model files."""
        with self._lock:
            if self.ready:
                return
            started = perf_counter()
            try:
                model_dir = self.settings.face_model_root / 'models' / self.model_name
                if not self.settings.allow_model_download and not list(model_dir.glob('*.onnx')):
                    raise FileNotFoundError(f'Place InsightFace ONNX models in {model_dir} or run download_models.py')
                import onnxruntime as ort
                from insightface.app import FaceAnalysis
                providers = ['CPUExecutionProvider']
                if self.settings.face_device == 'cuda' and 'CUDAExecutionProvider' in ort.get_available_providers():
                    providers.insert(0, 'CUDAExecutionProvider')
                elif self.settings.face_device == 'cuda':
                    logger.warning('CUDA unavailable; using CPU')
                def load(selected):
                    analysis = FaceAnalysis(name=self.model_name, root=str(self.settings.face_model_root),
                                            allowed_modules=['detection', 'recognition'], providers=selected)
                    analysis.prepare(ctx_id=0 if selected[0] == 'CUDAExecutionProvider' else -1,
                                     det_size=(640, 640))
                    return analysis
                try:
                    self._app = load(providers)
                except Exception:
                    if providers[0] != 'CUDAExecutionProvider':
                        raise
                    logger.exception('CUDA initialization failed; retrying on CPU')
                    self._app = load(['CPUExecutionProvider'])
                recognizer = self._app.models['recognition']
                self.dimension = int(recognizer.output_shape[1])
                self.providers = recognizer.session.get_providers()
                self.ready = True
                logger.info('Model initialized', extra={'fields': {'model': self.model_name,
                    'providers': self.providers, 'embedding_dim': self.dimension,
                    'initialization_ms': (perf_counter() - started) * 1000}})
            except Exception:
                self.ready = False
                logger.exception('Face model initialization failed')

    def detect_faces(self, image: np.ndarray) -> list:
        """Detect every face, retaining five landmarks needed for alignment."""
        if not self.ready:
            raise AppError('MODEL_NOT_READY', 'Face model is unavailable.', 503)
        from insightface.app.common import Face
        with self._lock:
            boxes, landmarks = self._app.det_model.detect(image, max_num=0, metric='default')
        return [Face(bbox=box[:4], det_score=box[4], kps=landmarks[i] if landmarks is not None else None)
                for i, box in enumerate(boxes)]

    def extract_embedding(self, image: np.ndarray, face) -> np.ndarray:
        """Recognizer.get performs landmark alignment via norm_crop internally."""
        with self._lock:
            self._app.models['recognition'].get(image, face)
        return normalize_embedding(face.embedding)

    def extract_single_face_embedding(self, image: np.ndarray, timer: Timer | None = None,
                                      allow_multiple: bool = False) -> np.ndarray:
        timer = timer or Timer()
        if not self.ready:
            raise AppError('MODEL_NOT_READY', 'Face model is unavailable.', 503)
        try:
            with self._lock:
                with timer.measure('face_detection'):
                    faces = self.detect_faces(image)
                if not faces:
                    raise AppError('NO_FACE', 'No face detected.')
                if len(faces) > 1 and not allow_multiple:
                    raise AppError('MULTIPLE_FACES', 'Multiple faces detected.')
                # Explicit opt-in only: choose largest face, never for enrollment.
                face = max(faces, key=lambda f: float(np.prod(f.bbox[2:] - f.bbox[:2])))
                with timer.measure('embedding'):
                    return self.extract_embedding(image, face)
        except AppError:
            raise
        except Exception as exc:
            logger.exception('Face inference failed')
            raise AppError('FACE_EXTRACTION_FAILED', 'Face feature extraction failed.', 503) from exc
