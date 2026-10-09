import numpy as np
from scripts.calibrate_threshold import metrics, pair_scores
from app.core.config import ROOT
import csv
import subprocess
import sys


def test_confusion_matrix_and_recommendation_inputs():
    result = metrics(np.array([0.9, 0.7]), np.array([0.8, 0.1]), np.array([0.75]))[0]
    assert [result[k] for k in ('TP', 'FP', 'TN', 'FN')] == [1, 1, 1, 1]
    assert result['FAR'] == result['FRR'] == result['accuracy'] == 0.5


def test_positive_negative_pairs():
    positive, negative = pair_scores(np.array([[1, 0], [1, 0], [0, 1]], np.float32), ['a', 'a', 'b'], 10)
    np.testing.assert_allclose(positive, [1])
    np.testing.assert_allclose(negative, [0, 0])


def test_calibration_cli_writes_csv(tmp_path):
    pairs = tmp_path / 'pairs.csv'
    pairs.write_text('label,similarity\n1,0.9\n1,0.8\n0,0.3\n0,0.2\n', encoding='utf-8')
    output = tmp_path / 'report.csv'
    result = subprocess.run([sys.executable, 'scripts/calibrate_threshold.py', '--pairs-csv', str(pairs),
                             '--output', str(output)], cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'Recommended FACE_MATCH_THRESHOLD=' in result.stdout
    with output.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) >= 401
    assert set(('threshold', 'accuracy', 'precision', 'recall', 'FAR', 'FRR', 'TP', 'FP', 'TN', 'FN')) <= set(rows[0])
