"""python examples/http_client.py --image test.jpg [--base64]"""
import argparse
import base64
import json
from pathlib import Path
from uuid import uuid4
import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--base64', action='store_true')
    args = parser.parse_args()
    raw = args.image.read_bytes()
    meta = {'request_id': uuid4().hex, 'device_id': 'example-phone', 'stable_frames': 1}
    with httpx.Client(base_url=args.url, timeout=120, trust_env=False) as client:
        if args.base64:
            response = client.post('/api/v1/recognize/base64', json={**meta,
                'image_format': args.image.suffix.lstrip('.'), 'image_base64': base64.b64encode(raw).decode()})
        else:
            response = client.post('/api/v1/recognize/image', data=meta, files={'file': (args.image.name, raw)})
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    response.raise_for_status()


if __name__ == '__main__':
    main()
