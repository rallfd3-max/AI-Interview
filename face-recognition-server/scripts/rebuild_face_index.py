"""Reload the live server's cache, rather than a short-lived local copy."""
import argparse
from uuid import uuid4
import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    response = httpx.post(args.url + '/api/v1/index/reload', headers={'X-Request-ID': uuid4().hex}, timeout=60, trust_env=False)
    print(response.text)
    response.raise_for_status()


if __name__ == '__main__':
    main()
