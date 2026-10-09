import os
from pathlib import Path
import pytest
from app.core.config import Settings
from app.services.face_engine import FaceEngine
from app.utils.image_utils import decode_image


def test_missing_model_does_not_crash(tmp_path):
    engine = FaceEngine(Settings(_env_file=None, face_model_root=tmp_path))
    engine.initialize()
    assert not engine.ready


def test_failed_initialization_keeps_health_available(tmp_path, image):
    from fastapi.testclient import TestClient
    from app.main import create_app
    settings = Settings(_env_file=None, face_model_root=tmp_path / 'absent-models',
                        database_url=f'sqlite:///{tmp_path / "fallback.db"}')
    with TestClient(create_app(settings)) as client:
        health = client.get('/health').json()
        assert health['status'] == 'degraded'
        assert health['database_ready'] is True
        assert health['model_ready'] is False
        result = client.post('/api/v1/recognize/image', files={'file': ('blank.jpg', image)}).json()
        assert result['error']['code'] == 'MODEL_NOT_READY'


@pytest.mark.integration
def test_real_model():
    path = os.environ.get('FACE_INTEGRATION_IMAGE')
    if not path:
        pytest.skip('Set FACE_INTEGRATION_IMAGE to a consented single-face photo and install local models')
    settings = Settings()
    engine = FaceEngine(settings)
    engine.initialize()
    assert engine.ready, 'Real model failed to initialize'
    image = decode_image(Path(path).read_bytes(), settings)
    vector = engine.extract_single_face_embedding(image)
    assert vector.shape == (engine.dimension,)
    assert float(vector @ vector) == pytest.approx(1, abs=1e-5)


@pytest.mark.integration
def test_real_detector_blank():
    if os.environ.get('FACE_RUN_MODEL_SMOKE') != '1':
        pytest.skip('Set FACE_RUN_MODEL_SMOKE=1 to load real model and detect a blank image')
    import numpy as np
    from app.core.exceptions import AppError
    settings = Settings()
    engine = FaceEngine(settings)
    engine.initialize()
    assert engine.ready
    engine.initialize()  # idempotent
    with pytest.raises(AppError) as caught:
        engine.extract_single_face_embedding(np.zeros((480, 640, 3), np.uint8))
    assert caught.value.code == 'NO_FACE'
