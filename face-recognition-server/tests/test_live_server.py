"""Optional real Uvicorn/HTTP/WebSocket smoke test, using no personal photos."""
import asyncio
import base64
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from time import monotonic, sleep
import httpx
import pytest
import websockets
from app.core.config import ROOT, Settings


@pytest.mark.integration
def test_live_server_real_model(tmp_path, image):
    if os.environ.get('FACE_RUN_MODEL_SMOKE') != '1':
        pytest.skip('Set FACE_RUN_MODEL_SMOKE=1 for the live-server model smoke test')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    env = {**os.environ, 'DATABASE_URL': f'sqlite:///{tmp_path / "live.db"}',
           'FACE_MODEL_ROOT': str(Settings().face_model_root), 'MAX_REQUESTS_PER_SECOND': '1000',
           'ALLOW_MODEL_DOWNLOAD': 'false', 'RETURN_DEBUG_INFO': 'true', 'DEBUG': 'true'}
    log_path = tmp_path / 'server.log'
    with log_path.open('w', encoding='utf-8') as log:
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                                    '--port', str(port)], cwd=ROOT, env=env, stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        try:
            url = f'http://127.0.0.1:{port}'
            deadline = monotonic() + 60
            with httpx.Client(base_url=url, timeout=5, trust_env=False) as client:
                while monotonic() < deadline:
                    if process.poll() is not None:
                        pytest.fail(log_path.read_text(encoding='utf-8'))
                    try:
                        response = client.get('/health')
                        break
                    except httpx.ConnectError:
                        sleep(0.2)
                else:
                    pytest.fail('Live server did not start within 60 seconds')
                assert response.json()['model_ready'] is True
                assert response.json()['database_ready'] is True
                result = client.post('/api/v1/recognize/image', files={'file': ('blank.jpg', image)},
                                     data={'request_id': 'live-blank'}).json()
                assert result['error']['code'] == 'NO_FACE'
                assert result['request_id'] == 'live-blank'
                assert result['processing']['face_detection_ms'] > 0
            async def websocket_check():
                async with websockets.connect(f'ws://127.0.0.1:{port}/ws/recognition', proxy=None) as connection:
                    await connection.send(json.dumps({'type': 'ping', 'request_id': 'live-ping'}))
                    assert json.loads(await connection.recv())['type'] == 'pong'
                    await connection.send(json.dumps({'type': 'recognize', 'request_id': 'live-frame',
                        'image_base64': base64.b64encode(image).decode()}))
                    assert json.loads(await connection.recv())['error']['code'] == 'NO_FACE'
                    await connection.send(json.dumps({'type': 'person_left', 'request_id': 'live-left'}))
                    assert json.loads(await connection.recv())['type'] == 'clear'
            asyncio.run(websocket_check())
            photo = tmp_path / 'blank.jpg'
            photo.write_bytes(image)
            benchmark = subprocess.run([sys.executable, 'scripts/benchmark.py', '--url', url,
                '--image', str(photo), '--iterations', '3'], cwd=ROOT, capture_output=True, text=True, timeout=30)
            assert benchmark.returncode == 0, benchmark.stderr
            report = json.loads(benchmark.stdout)
            assert report['requests'] == 3
            assert report['stage_means_ms']['face_detection_ms'] > 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
