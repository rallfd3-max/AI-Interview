import numpy as np
import pytest
from app.core.exceptions import AppError
from app.services.face_matcher import FaceMatcher
from app.utils.vector_utils import normalize_embedding, serialize_embedding, deserialize_embedding


def test_normalization_and_blob():
    value = normalize_embedding([3, 4])
    assert value.dtype == np.float32
    np.testing.assert_allclose(value, [0.6, 0.8])
    np.testing.assert_allclose(deserialize_embedding(serialize_embedding(value), 2), value)


@pytest.mark.parametrize('vector', [[0, 0], [float('nan'), 1], [[1, 2]], []])
def test_invalid_vector(vector):
    with pytest.raises(AppError):
        normalize_embedding(vector)


def test_invalid_blob():
    with pytest.raises(AppError):
        deserialize_embedding(b'bad', 3)


def test_cosine_top_k_and_unique_people():
    matcher = FaceMatcher(3)
    matcher.replace([(1, 'a', np.array([1, 0, 0])), (2, 'a', np.array([0.9, 0.1, 0])),
                     (3, 'b', np.array([0, 1, 0])), (4, 'c', np.array([-1, 0, 0]))])
    matches = matcher.match(np.array([1, 0, 0]), 3)
    assert [m.person_id for m in matches] == ['a', 'b', 'c']
    assert matches[0].similarity == pytest.approx(1)
    assert matches[-1].similarity == pytest.approx(-1)


@pytest.mark.parametrize('strategy,score', [('max', 1), ('mean', 0.5), ('top_n_mean', 0.5)])
def test_score_strategies(strategy, score):
    matcher = FaceMatcher(2, strategy)
    matcher.replace([(1, 'a', np.array([1, 0])), (2, 'a', np.array([0, 1]))])
    assert matcher.match(np.array([1, 0]))[0].similarity == pytest.approx(score)


def test_empty_and_dimension():
    matcher = FaceMatcher(2)
    assert matcher.match(np.array([1, 0])) == []
    with pytest.raises(AppError):
        matcher.match(np.array([1, 0, 0]))
