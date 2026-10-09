import numpy as np
from sqlalchemy import select, func
from app.models.face_embedding import FaceEmbedding
from app.repositories.person_repository import PersonRepository


def test_create_list_get_delete(client):
    response = client.post('/api/v1/persons', json={'person_id': 'p1', 'name': 'Test'}, headers={'X-Request-ID': 'create-1'})
    assert response.status_code == 201
    assert response.json()['request_id'] == 'create-1'
    assert client.get('/api/v1/persons/p1').json()['person']['name'] == 'Test'
    assert len(client.get('/api/v1/persons').json()['persons']) == 1
    with client.app.state.runtime.sessions() as session:
        assert PersonRepository(session).get('p1').name == 'Test'
    assert client.post('/api/v1/persons', json={'person_id': 'p1', 'name': 'Again'}).status_code == 409
    assert client.delete('/api/v1/persons/p1').status_code == 200
    assert client.get('/api/v1/persons/p1').status_code == 404


def test_three_photos_centroid_and_cascade(client, image, encoded):
    client.post('/api/v1/persons', json={'person_id': 'p1', 'name': 'Test'})
    response = client.post('/api/v1/persons/p1/faces', files=[('files', (f'{i}.jpg', image)) for i in range(3)])
    assert response.json()['registered_embeddings'] == 3
    runtime = client.app.state.runtime
    assert len(runtime.matcher.embedding_ids) == 3
    with runtime.sessions() as session:
        assert session.scalar(select(func.count()).select_from(FaceEmbedding)) == 4
    message = {'request_id': 'cached', 'image_base64': encoded}
    assert client.post('/api/v1/recognize/base64', json=message).json()['matched']
    client.delete('/api/v1/persons/p1')
    assert len(runtime.matcher.embedding_ids) == 0
    with runtime.sessions() as session:
        assert session.scalar(select(func.count()).select_from(FaceEmbedding)) == 0
    assert client.post('/api/v1/recognize/base64', json=message).json()['error']['code'] == 'NO_REGISTERED_FACES'


def test_registration_atomic_failure(client, image):
    client.post('/api/v1/persons', json={'person_id': 'p1', 'name': 'Test'})
    response = client.post('/api/v1/persons/p1/faces', files=[('files', ('a.jpg', image)), ('files', ('b.jpg', b'bad'))])
    assert response.status_code == 400
    assert client.get('/health').json()['registered_embeddings'] == 0


def test_limit_five_total(enrolled, image):
    response = enrolled.post('/api/v1/persons/student_001/faces', files=[('files', (f'{i}.jpg', image)) for i in range(5)])
    assert response.status_code == 400
    assert enrolled.get('/health').json()['registered_embeddings'] == 1
