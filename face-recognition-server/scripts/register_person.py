"""Enroll using the running server, keeping its index synchronized."""
import argparse
from contextlib import ExitStack
from pathlib import Path
from uuid import uuid4
import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--person-id', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--student-no')
    parser.add_argument('--school')
    parser.add_argument('--major')
    parser.add_argument('--description')
    parser.add_argument('--images', type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(p for p in args.images.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png')) if args.images.is_dir() else [args.images]
    if not 1 <= len(paths) <= 5:
        parser.error('--images must contain 1 to 5 photos')
    profile = {key: getattr(args, key) for key in ('person_id', 'name', 'student_no', 'school', 'major', 'description')}
    with httpx.Client(base_url=args.url, timeout=120, trust_env=False) as client:
        created = client.post('/api/v1/persons', json=profile, headers={'X-Request-ID': uuid4().hex})
        if created.status_code != 409:
            created.raise_for_status()
        with ExitStack() as stack:
            files = [('files', (p.name, stack.enter_context(p.open('rb')))) for p in paths]
            response = client.post(f'/api/v1/persons/{args.person_id}/faces', files=files,
                                   headers={'X-Request-ID': uuid4().hex})
        print(response.text)
        response.raise_for_status()


if __name__ == '__main__':
    main()
