import numpy as np
import pytest


def recognize(client, encoded, **kwargs):
    return client.post('/api/v1/recognize/base64', json={'image_base64': encoded, **kwargs})


def test_success_threshold(enrolled, encoded):
    result = recognize(enrolled, encoded, request_id='req_1').json()
    assert result['matched'] is True
    assert result['person']['person_id'] == 'student_001'
    assert result['request_id'] == 'req_1'
    assert result['timestamp'] > 0
    assert result['match']['similarity'] >= result['match']['threshold']
    assert len(result['top_k']) == 1
    assert result['processing']['total_ms'] > 0
    # Equality is accepted.
    enrolled.app.state.runtime.settings.face_match_threshold = 1
    assert recognize(enrolled, encoded).json()['matched']


def test_unknown(enrolled, encoded):
    enrolled.model.vector = np.array([0, 1, 0], np.float32)
    result = recognize(enrolled, encoded).json()
    assert result['matched'] is False
    assert result['error']['code'] == 'UNKNOWN_FACE'
    assert result['person'] is None


def test_debounce_never_returns_new_profile_early(enrolled, encoded, image):
    for i in range(3):
        recognize(enrolled, encoded, session_id='switch')
    enrolled.post('/api/v1/persons', json={'person_id': 'student_002', 'name': 'Other'})
    enrolled.model.vector = np.array([0, 1, 0], np.float32)
    enrolled.post('/api/v1/persons/student_002/faces', files=[('files', ('b.jpg', image))])
    # Enrollment invalidates session state; establish the first person again.
    enrolled.model.vector = np.array([1, 0, 0], np.float32)
    for i in range(3):
        recognize(enrolled, encoded, session_id='switch')
    enrolled.model.vector = np.array([0, 1, 0], np.float32)
    for i in range(3):
        result = recognize(enrolled, encoded, session_id='switch').json()
        assert result['matched'] is (i == 2)
        if i < 2:
            assert result['person'] is None
            assert result['stability']['confirmed_person_id'] == 'student_001'
        else:
            assert result['person']['person_id'] == 'student_002'


@pytest.mark.parametrize('code,success,detected', [('NO_FACE', True, False), ('MULTIPLE_FACES', False, True), ('FACE_EXTRACTION_FAILED', False, False)])
def test_face_errors(enrolled, encoded, code, success, detected):
    enrolled.model.error = code
    result = recognize(enrolled, encoded).json()
    assert result['success'] is success
    assert result['face_detected'] is detected
    assert result['error']['code'] == code


def test_empty_database(client, encoded):
    assert recognize(client, encoded).json()['error']['code'] == 'NO_REGISTERED_FACES'


def test_invalid_base64(client):
    result = recognize(client, '!!!', request_id='bad').json()
    assert result['error']['code'] == 'INVALID_BASE64'
    assert result['request_id'] == 'bad'


def test_invalid_image(client):
    assert recognize(client, 'YmFk').json()['error']['code'] == 'IMAGE_DECODE_FAILED'


def test_oversized(client, encoded):
    client.app.state.runtime.settings.max_image_size_mb = 0.00001
    assert recognize(client, encoded).json()['error']['code'] == 'IMAGE_TOO_LARGE'


def test_face_box(enrolled, encoded):
    assert recognize(enrolled, encoded, face_box={'x': 30, 'y': 0, 'w': 10, 'h': 10}).json()['error']['code'] == 'INVALID_FACE_BOX'
    assert recognize(enrolled, encoded, face_box={'x': -1, 'y': 0, 'w': 10, 'h': 10}).json()['error']['code'] == 'INVALID_FACE_BOX'
    assert recognize(enrolled, encoded, face_box={'x': 0, 'y': 0, 'w': 20, 'h': 20}).json()['matched']


def test_multipart_and_data_url(enrolled, image, encoded):
    result = enrolled.post('/api/v1/recognize/image', files={'file': ('test.jpg', image)}, data={'request_id': 'multipart'}).json()
    assert result['request_id'] == 'multipart'
    assert result['matched']
    assert recognize(enrolled, 'data:image/jpeg;base64,' + encoded).json()['matched']


def test_invalid_format(client, encoded):
    assert recognize(client, encoded, image_format='gif').json()['error']['code'] == 'INVALID_IMAGE_FORMAT'


def test_model_unavailable(client, encoded):
    client.model.ready = False
    assert client.get('/health').json()['model_ready'] is False
    assert recognize(client, encoded).json()['error']['code'] == 'MODEL_NOT_READY'


def test_duplicate_not_counted_and_payload_conflict(enrolled, encoded):
    payload = {'request_id': 'same', 'session_id': 's'}
    first = recognize(enrolled, encoded, **payload).json()
    calls = enrolled.model.calls
    second = recognize(enrolled, encoded, **payload).json()
    assert first == second
    assert enrolled.model.calls == calls
    conflict = recognize(enrolled, encoded, **payload, stable_frames=1)
    assert conflict.status_code == 409


def test_rate_limit(client, encoded):
    client.app.state.runtime.settings.max_requests_per_second = 1
    recognize(client, encoded)
    assert recognize(client, encoded).status_code == 429


def test_validation_and_docs(client):
    response = client.post('/api/v1/recognize/base64', json={'request_id': 'validate'})
    assert response.status_code == 422
    assert response.json()['request_id'] == 'validate'
    assert client.get('/missing').json()['error']['code'] == 'INVALID_REQUEST'
    assert client.get('/openapi.json').status_code == 200
    assert client.get('/api/v1/stats').json()['model_name'] == 'test-model'
