"""QA edge cases discovered or required during the second acceptance pass."""
import base64
from io import BytesIO
import numpy as np
import pytest
from cachetools import TTLCache
from PIL import Image
from app.utils.image_utils import decode_image
from app.core.config import Settings


@pytest.mark.parametrize('request_id', ['请求_测试_001', 'req\r\nInjected: bad'])
def test_unicode_request_id_is_echoed_without_header_crash(enrolled, encoded, request_id):
    response = enrolled.post('/api/v1/recognize/base64', json={'request_id': request_id, 'image_base64': encoded})
    assert response.status_code == 200
    assert response.json()['request_id'] == request_id
    from urllib.parse import unquote
    assert unquote(response.headers['X-Request-ID']) == request_id


@pytest.mark.parametrize('orientation,expected', [(3, (20, 40, 3)), (6, (40, 20, 3)), (8, (40, 20, 3))])
def test_exif_all_rotations(orientation, expected):
    # Spatial markers verify rotation, not only changed dimensions.
    image = Image.new('RGB', (40, 20), 'black')
    for x in range(20):
        for y in range(10):
            image.putpixel((x, y), (255, 0, 0))
    exif = image.getexif()
    exif[274] = orientation
    stream = BytesIO()
    image.save(stream, format='JPEG', exif=exif, quality=100)
    result = decode_image(stream.getvalue(), Settings(_env_file=None))
    assert result.shape == expected
    corner = {3: (-2, -2), 6: (2, -2), 8: (-2, 2)}[orientation]
    assert result[corner][2] > 200


@pytest.mark.parametrize('box', [
    {'x': -1, 'y': 0, 'w': 1, 'h': 1}, {'x': 0, 'y': -1, 'w': 1, 'h': 1},
    {'x': 32, 'y': 0, 'w': 1, 'h': 1}, {'x': 0, 'y': 24, 'w': 1, 'h': 1},
    {'x': 0, 'y': 0, 'w': 0, 'h': 1}, {'x': 0, 'y': 0, 'w': 1, 'h': 0},
    {'x': 0, 'y': 0, 'w': 1000000, 'h': 1000000}, {'x': 31, 'y': 23, 'w': 2, 'h': 2},
])
def test_face_box_boundaries(client, encoded, box):
    response = client.post('/api/v1/recognize/base64', json={'request_id': 'roi', 'image_base64': encoded, 'face_box': box})
    assert response.status_code < 500
    assert response.json()['error']['code'] == 'INVALID_FACE_BOX'


def test_cache_expiry_reprocesses(enrolled, encoded):
    now = [0.0]
    runtime = enrolled.app.state.runtime
    runtime.cache = TTLCache(20, 30, timer=lambda: now[0])
    payload = {'request_id': 'expire', 'session_id': 's', 'image_base64': encoded}
    before = enrolled.model.calls
    first = enrolled.post('/api/v1/recognize/base64', json=payload).json()
    second = enrolled.post('/api/v1/recognize/base64', json=payload).json()
    assert first == second
    assert enrolled.model.calls == before + 1
    now[0] = 31
    third = enrolled.post('/api/v1/recognize/base64', json=payload).json()
    assert enrolled.model.calls == before + 2
    assert third['stability']['consistent_frames'] == 2


def test_rate_window_recovers(client, encoded, monkeypatch):
    import app.services.runtime as runtime_module
    clock = [0.0]
    monkeypatch.setattr(runtime_module, 'monotonic', lambda: clock[0])
    client.app.state.runtime.settings.max_requests_per_second = 1
    def send(request_id):
        return client.post('/api/v1/recognize/base64', json={'request_id': request_id, 'image_base64': encoded})
    assert send('first').status_code == 200
    assert send('second').json()['error']['code'] == 'RATE_LIMITED'
    clock[0] = 1.01
    assert send('third').status_code == 200


def test_two_websocket_sessions_are_isolated(enrolled, encoded):
    with enrolled.websocket_connect('/ws/recognition') as a, enrolled.websocket_connect('/ws/recognition') as b:
        def frame(socket, session, seq):
            socket.send_json({'type': 'recognize', 'request_id': f'{session}_{seq}', 'session_id': session,
                              'device_id': 'test_device', 'image_base64': encoded})
            return socket.receive_json()
        assert frame(a, 'A', 1)['stability']['consistent_frames'] == 1
        assert frame(b, 'B', 1)['stability']['consistent_frames'] == 1
        assert frame(a, 'A', 2)['stability']['consistent_frames'] == 2
        assert not frame(b, 'B', 2)['stability']['confirmed']
        assert frame(a, 'A', 3)['stability']['confirmed']
        a.send_json({'type': 'person_left', 'session_id': 'A', 'device_id': 'test_device'})
        assert a.receive_json()['type'] == 'clear'
        assert frame(b, 'B', 3)['stability']['confirmed']
        assert not frame(a, 'A', 4)['stability']['confirmed']


def test_debounce_one_bad_frame_then_original(enrolled, encoded, image):
    enrolled.post('/api/v1/persons', json={'person_id': 'student_002', 'name': 'Second'})
    enrolled.model.vector = np.array([0, 1, 0], np.float32)
    enrolled.post('/api/v1/persons/student_002/faces', files=[('files', ('other.jpg', image))])
    enrolled.model.vector = np.array([1, 0, 0], np.float32)
    def send():
        return enrolled.post('/api/v1/recognize/base64', json={'session_id': 'debounce', 'image_base64': encoded}).json()
    for _ in range(3):
        original = send()
    assert original['person']['person_id'] == 'student_001'
    enrolled.model.vector = np.array([0, 1, 0], np.float32)
    assert send()['stability']['confirmed_person_id'] == 'student_001'
    enrolled.model.vector = np.array([1, 0, 0], np.float32)
    assert send()['person']['person_id'] == 'student_001'


def test_sqlite_embedding_roundtrip(client):
    from app.models.face_embedding import FaceEmbedding
    from app.schemas.person import PersonCreate
    from app.utils.vector_utils import normalize_embedding, serialize_embedding, deserialize_embedding
    runtime = client.app.state.runtime
    original = normalize_embedding(np.array([3, 4, 5], np.float32))
    runtime.person_service.create(PersonCreate(person_id='blob_test', name='Vector only'))
    with runtime.sessions.begin() as session:
        row = FaceEmbedding(person_id='blob_test', embedding=serialize_embedding(original),
                            model_name=runtime.face_engine.model_name, embedding_dim=3, is_centroid=False)
        session.add(row)
        session.flush()
        row_id = row.id
    with runtime.sessions() as session:
        row = session.get(FaceEmbedding, row_id)
        restored = deserialize_embedding(row.embedding, row.embedding_dim)
    assert restored.dtype == np.float32 and restored.shape == original.shape
    np.testing.assert_allclose(original, restored, rtol=1e-6)


def test_schema_can_describe_unicode_id(client):
    # Request schema permits Unicode, so transport must not silently reject it.
    from app.schemas.recognition import RecognitionRequest
    assert RecognitionRequest(request_id='请求1', image_base64='x').request_id == '请求1'


def test_multipart_validation_error_keeps_request_id(client):
    response = client.post('/api/v1/recognize/image', data={'request_id': 'missing-file-id'})
    assert response.status_code == 422
    assert response.json()['request_id'] == 'missing-file-id'


def test_body_limit_keeps_request_id_header(client):
    # Force a small app setting to test the pre-parser rejection branch.
    from fastapi.testclient import TestClient
    from app.main import create_app
    from tests.conftest import MockFaceEngine
    settings = Settings(_env_file=None, database_url='sqlite:///:memory:', max_image_size_mb=0.001)
    with TestClient(create_app(settings, MockFaceEngine())) as test_client:
        response = test_client.post('/api/v1/recognize/base64', content=b'x' * 100_000,
            headers={'Content-Type': 'application/json', 'X-Request-ID': 'body-limit'})
        assert response.status_code == 413
        assert response.json()['request_id'] == 'body-limit'
        assert response.headers['X-Request-ID'] == 'body-limit'


def test_reload_index_matches_persisted_sample_counts(enrolled, image):
    response = enrolled.post('/api/v1/persons/student_001/faces', files=[('files', ('second.jpg', image))])
    assert response.json()['registered_embeddings'] == 2
    assert enrolled.post('/api/v1/index/reload').status_code == 200
    runtime = enrolled.app.state.runtime
    from app.repositories.embedding_repository import EmbeddingRepository
    with runtime.sessions() as session:
        rows = EmbeddingRepository(session).samples()
    assert runtime.matcher.embedding_matrix.shape == (len(rows), 3)
    assert runtime.matcher.embedding_ids.tolist() == [row.id for row in rows]
    assert runtime.matcher.person_ids.tolist() == [row.person_id for row in rows]


def test_relative_model_path_independent_of_current_directory(tmp_path, monkeypatch):
    from app.core.config import ROOT
    monkeypatch.chdir(tmp_path)
    settings = Settings(_env_file=None, face_model_root='data/face_models')
    assert settings.face_model_root == ROOT / 'data/face_models'
