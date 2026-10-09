"""Serial end-to-end HTTP benchmark; report errors separately from latency."""
import argparse
import json
from pathlib import Path
from time import perf_counter, sleep
from uuid import uuid4
import httpx
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--iterations', type=int, default=100)
    parser.add_argument('--interval', type=float, default=0.21, help='Seconds between requests; avoids default 5 RPS limit')
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    if args.iterations < 1 or args.interval < 0:
        parser.error('iterations must be positive and interval nonnegative')
    raw = args.image.read_bytes()
    latencies, stages, errors, outcomes = [], {}, {}, {}
    start = perf_counter()
    with httpx.Client(base_url=args.url, timeout=120, trust_env=False) as client:
        for i in range(args.iterations):
            began = perf_counter()
            response = client.post('/api/v1/recognize/image', files={'file': (args.image.name, raw)},
                                   data={'request_id': uuid4().hex, 'stable_frames': 1})
            latencies.append((perf_counter() - began) * 1000)
            result = response.json()
            code = result.get('error', {}).get('code') if result.get('error') else None
            outcome = code or ('MATCHED' if result.get('matched') else 'UNMATCHED')
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
            if response.status_code >= 400 or not result.get('success'):
                errors[code or str(response.status_code)] = errors.get(code or str(response.status_code), 0) + 1
            for name, value in (result.get('processing') or {}).items():
                stages.setdefault(name, []).append(value)
            if i + 1 < args.iterations:
                sleep(args.interval)
    elapsed = perf_counter() - start
    print(json.dumps({'requests': args.iterations, 'errors': errors, 'outcomes': outcomes, 'mean_ms': float(np.mean(latencies)),
        'p50_ms': float(np.percentile(latencies, 50)), 'p95_ms': float(np.percentile(latencies, 95)),
        'p99_ms': float(np.percentile(latencies, 99)), 'throughput_rps_including_interval': args.iterations / elapsed,
        'service_rps_excluding_interval': 1000 / float(np.mean(latencies)),
        'stage_means_ms': {k: float(np.mean(v)) for k, v in stages.items()}}, indent=2))


if __name__ == '__main__':
    main()
