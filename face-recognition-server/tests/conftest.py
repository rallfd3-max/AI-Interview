"""Fake inference is confined to tests; actual image decoding remains enabled."""
import base64
from io import BytesIO
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app.core.config import Settings
from app.core.exceptions import AppError
from app.main import create_app


class MockFaceEngine:
    dimension = 3
    model_name = 'test-model'
    providers = ['MockProvider']
    ready = True

    def __init__(self):
        self.calls = 0
        self.vector = np.array([1, 0, 0], np.float32)
        self.error = None

    def initialize(self):
        return None

    def extract_single_face_embedding(self, image, timer=None, allow_multiple=False):
        self.calls += 1
        if not self.ready:
            raise AppError('MODEL_NOT_READY', 'Unavailable', 503)
        if self.error:
            raise AppError(self.error, self.error)
        return self.vector


@pytest.fixture
def image():
    stream = BytesIO()
    Image.new('RGB', (32, 24), 'white').save(stream, format='JPEG')
    return stream.getvalue()


@pytest.fixture
def encoded(image):
    return base64.b64encode(image).decode()


@pytest.fixture
def client(tmp_path):
    model = MockFaceEngine()
    settings = Settings(_env_file=None, database_url=f'sqlite:///{tmp_path / "test.db"}',
                        max_requests_per_second=1000, face_match_threshold=0.8)
    with TestClient(create_app(settings, model)) as test_client:
        test_client.model = model
        yield test_client


@pytest.fixture
def enrolled(client, image):
    assert client.post('/api/v1/persons', json={'person_id': 'student_001', 'name': '测试同学'}).status_code == 201
    response = client.post('/api/v1/persons/student_001/faces', files=[('files', ('a.jpg', image, 'image/jpeg'))])
    assert response.status_code == 200, response.text
    return client
