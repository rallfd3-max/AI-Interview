"""Send distinct frame request IDs, then clear the session."""
import argparse
import asyncio
import base64
import json
from pathlib import Path
from uuid import uuid4
import websockets


async def run(args) -> None:
    encoded = base64.b64encode(args.image.read_bytes()).decode()
    session = uuid4().hex
    async with websockets.connect(args.url, max_size=16 * 1024 * 1024, proxy=None) as socket:
        await socket.send(json.dumps({'type': 'ping', 'request_id': uuid4().hex}))
        print(await socket.recv())
        for _ in range(args.frames):
            await socket.send(json.dumps({'type': 'recognize', 'request_id': uuid4().hex,
                'session_id': session, 'device_id': 'example-phone',
                'image_format': args.image.suffix.lstrip('.'), 'image_base64': encoded}))
            print(await socket.recv())
            await asyncio.sleep(0.25)
        await socket.send(json.dumps({'type': 'person_left', 'request_id': uuid4().hex,
                                     'session_id': session, 'device_id': 'example-phone'}))
        print(await socket.recv())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--url', default='ws://127.0.0.1:8000/ws/recognition')
    parser.add_argument('--frames', type=int, default=3)
    asyncio.run(run(parser.parse_args()))
