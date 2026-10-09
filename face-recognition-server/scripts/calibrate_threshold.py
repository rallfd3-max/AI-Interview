"""Compare held-out same/different-person pairs and export threshold metrics."""
import argparse
import csv
from pathlib import Path
import numpy as np
try:
    from . import _bootstrap
except ImportError:
    import _bootstrap
from app.core.config import Settings
from app.core.logging import configure_logging
from app.services.face_engine import FaceEngine
from app.utils.image_utils import decode_image


def metrics(positive: np.ndarray, negative: np.ndarray, thresholds: np.ndarray) -> list[dict]:
    """FAR is false accepts / negative pairs, FRR false rejects / positive pairs."""
    if not positive.size or not negative.size:
        raise ValueError('Need both positive and negative comparisons')
    if not np.isfinite(positive).all() or not np.isfinite(negative).all():
        raise ValueError('Scores must be finite')
    output = []
    for threshold in thresholds:
        tp, fp = int(np.sum(positive >= threshold)), int(np.sum(negative >= threshold))
        fn, tn = len(positive) - tp, len(negative) - fp
        output.append({'threshold': float(threshold), 'accuracy': (tp + tn) / (tp + tn + fp + fn),
            'precision': tp / (tp + fp) if tp + fp else 0.0, 'recall': tp / (tp + fn),
            'FAR': fp / (fp + tn), 'FRR': fn / (fn + tp), 'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn})
    return output


def pair_scores(vectors: np.ndarray, identities: list[str], max_pairs: int, seed: int = 42):
    """Reservoir-sample each pair class, bounded memory and deterministic seed."""
    rng = np.random.default_rng(seed)
    positive, negative = [], []
    counts = [0, 0]
    for i in range(len(vectors)):
        scores = vectors[i + 1:] @ vectors[i]
        for j, score in enumerate(scores, start=i + 1):
            category = int(identities[i] != identities[j])
            target = negative if category else positive
            counts[category] += 1
            if len(target) < max_pairs:
                target.append(float(score))
            else:
                slot = int(rng.integers(counts[category]))
                if slot < max_pairs:
                    target[slot] = float(score)
    return np.asarray(positive), np.asarray(negative)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--dataset', type=Path, help='dataset/person_id/*.jpg; use photos separate from enrollment')
    source.add_argument('--pairs-csv', type=Path, help='CSV columns: label (1 same/0 different), similarity')
    parser.add_argument('--output', type=Path, default=Path('calibration.csv'))
    parser.add_argument('--max-far', type=float, default=0.01)
    parser.add_argument('--max-pairs', type=int, default=100000)
    args = parser.parse_args()
    if not 0 <= args.max_far <= 1 or args.max_pairs < 1:
        parser.error('Invalid max-far or max-pairs')
    if args.dataset:
        settings = Settings()
        configure_logging()
        engine = FaceEngine(settings)
        engine.initialize()
        if not engine.ready:
            raise SystemExit('Model unavailable; cannot calibrate')
        vectors, identities = [], []
        for directory in sorted(args.dataset.iterdir()):
            if directory.is_dir():
                for path in sorted(directory.iterdir()):
                    if path.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                        # Invalid or multiple-face photos fail visibly; never silently drop samples.
                        vector = engine.extract_single_face_embedding(decode_image(path.read_bytes(), settings))
                        vectors.append(vector)
                        identities.append(directory.name)
        if not vectors:
            raise SystemExit('Dataset contains no photos')
        positive, negative = pair_scores(np.stack(vectors), identities, args.max_pairs)
    else:
        with args.pairs_csv.open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        if any(row['label'] not in ('0', '1') for row in rows):
            raise SystemExit('labels must be 0 or 1')
        positive = np.array([float(row['similarity']) for row in rows if row['label'] == '1'])
        negative = np.array([float(row['similarity']) for row in rows if row['label'] == '0'])
    if not positive.size or not negative.size:
        raise SystemExit('Need both positive and negative pairs (at least two people, one with multiple photos)')
    scores = np.concatenate([positive, negative])
    if not np.isfinite(scores).all() or np.any(np.abs(scores) > 1.000001):
        raise SystemExit('Cosine scores must be finite and within [-1,1]')
    thresholds = np.unique(np.concatenate([np.linspace(-1, 1, 401), scores, np.nextafter(scores, np.inf)]))
    thresholds = thresholds[(thresholds >= -1) & (thresholds <= 1)]
    rows = metrics(positive, negative, thresholds)
    with args.output.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    valid = [row for row in rows if row['FAR'] <= args.max_far]
    if not valid:
        raise SystemExit(f'Wrote {args.output}; no threshold satisfies the requested FAR')
    recommended = max(valid, key=lambda row: (row['recall'], row['precision'], -row['threshold']))
    print(f'Positive pairs={len(positive)}, negative pairs={len(negative)}; CSV={args.output}')
    print(f'Recommended FACE_MATCH_THRESHOLD={recommended["threshold"]:.9g}; {recommended}')
    print('This is pair-level calibration, not a guarantee of 1:N identification accuracy. Validate on a separate held-out set.')


if __name__ == '__main__':
    main()
