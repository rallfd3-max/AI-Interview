"""Real model enrollment and index structure; deliberately no enrollment-image accuracy test."""
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app


@pytest.mark.integration
def test_user_photo_real_enrollment_index_and_delete(tmp_path):
    value = os.environ.get('FACE_INTEGRATION_IMAGE')
    if not value:
        pytest.skip('NEED_USER_DATA: set FACE_INTEGRATION_IMAGE to an explicitly supplied photo')
    path = Path(value)
    settings = Settings(database_url=f'sqlite:///{tmp_path / "real_enrollment.db"}')
    with TestClient(create_app(settings)) as client:
        runtime = client.app.state.runtime
        assert runtime.face_engine.ready
        assert client.post('/api/v1/persons', json={'person_id': 'qa_real', 'name': 'QA supplied participant'}).status_code == 201
        response = client.post('/api/v1/persons/qa_real/faces', files=[('files', (path.name, path.read_bytes()))])
        assert response.status_code == 200, response.text
        assert response.json()['registered_embeddings'] == 1
        assert runtime.matcher.embedding_matrix.shape == (1, 512)
        assert runtime.matcher.person_ids.tolist() == ['qa_real']
        assert len(runtime.matcher.embedding_ids) == 1
        assert client.post('/api/v1/index/reload').status_code == 200
        assert runtime.matcher.embedding_matrix.shape == (1, 512)
        assert client.delete('/api/v1/persons/qa_real').status_code == 200
        assert runtime.matcher.embedding_matrix.shape == (0, 512)
        assert len(runtime.matcher.person_ids) == len(runtime.matcher.embedding_ids) == 0
