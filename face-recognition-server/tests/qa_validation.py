"""Reproducible second-pass QA; uses generated non-face images and an isolated DB.

Run from the project: .venv/Scripts/python.exe tests/qa_validation.py
No consented human dataset is synthesized, downloaded, or inferred by this runner.
"""
import asyncio
import argparse
import base64
from collections import Counter
from datetime import datetime
import hashlib
from importlib import metadata, util, import_module
from io import BytesIO
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
from time import perf_counter, monotonic, sleep
import traceback
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx
import numpy as np
from PIL import Image, ImageDraw
import onnxruntime as ort
import websockets
from app.core.config import Settings
from app.schemas.recognition import RecognitionResponse
from app.services.face_matcher import FaceMatcher
from app.utils.vector_utils import normalize_embedding

ART = ROOT / 'test_artifacts'
RESULTS: list[dict] = []
API: list[dict] = []
WS: list[dict] = []


def save(relative: str, value) -> None:
    path = ART / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def case(name, operation):
    start = perf_counter()
    try:
        detail = operation()
        result = {'case': name, 'status': 'PASS', 'detail': detail}
    except Exception as exc:
        result = {'case': name, 'status': 'FAIL', 'error': str(exc), 'traceback': traceback.format_exc()}
    result['duration_ms'] = (perf_counter() - start) * 1000
    RESULTS.append(result)
    save('reports/live_results.json', RESULTS)
    print(f'{result["status"]}: {name}', flush=True)
    return result


def command(name: str, args: list[str], env=None, expected=0, cwd=ROOT):
    result = subprocess.run([sys.executable, *args], cwd=cwd, env=env, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=90)
    save('logs/' + name + '.txt', '$ ' + ' '.join(args) + '\n' + result.stdout + result.stderr)
    assert result.returncode == expected, f'{name}: exit {result.returncode}; see its log'
    return result.stdout


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--face-image', type=Path, help='Explicit user-provided image, enrollment/extraction checks only')
    args = parser.parse_args()
    if args.face_image and not args.face_image.is_file():
        parser.error('--face-image does not exist')
    for directory in ('logs', 'reports', 'benchmark', 'calibration', 'api', 'websocket', 'screenshots_or_outputs'):
        (ART / directory).mkdir(parents=True, exist_ok=True)
    settings = Settings()
    official_db = ROOT / 'data/database/face.db'
    before = sha(official_db)
    versions = {name: metadata.version(name) for name in ('pip', 'fastapi', 'uvicorn', 'insightface',
        'onnxruntime', 'numpy', 'opencv-python-headless', 'SQLAlchemy', 'pytest', 'pydantic', 'Pillow')}
    cpu = platform.processor()
    if os.name == 'nt':
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            cpu = winreg.QueryValueEx(key, 'ProcessorNameString')[0]
    cuda_command = shutil.which('nvidia-smi')
    gpu = {'nvidia_smi_found': bool(cuda_command), 'onnx_cuda_provider_available': 'CUDAExecutionProvider' in ort.get_available_providers()}
    if cuda_command:
        process = subprocess.run([cuda_command, '--query-gpu=name,driver_version', '--format=csv,noheader'],
                                 capture_output=True, text=True, timeout=10)
        gpu.update({'exit_code': process.returncode, 'output': process.stdout.strip()})
    git_head = subprocess.run(['git', '-c', 'safe.directory=D:/ai面试官', 'rev-parse', 'HEAD'], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip()
    git_status = subprocess.run(['git', '-c', 'safe.directory=D:/ai面试官', 'status', '--short', '--', '.'],
                                cwd=ROOT, capture_output=True, text=True).stdout.strip()
    inventory = {str(p.relative_to(ROOT)): [str(f.relative_to(ROOT)) for f in p.rglob('*')
        if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png')] if p.exists() else []
        for p in [ROOT / x for x in ('data/test_images', 'tests/assets', 'test_data', 'dataset', 'test_dataset')]}
    environment = {'date_local': datetime.now().astimezone().isoformat(), 'executable': sys.executable,
        'python': sys.version, 'os': platform.platform(), 'cpu': cpu, 'logical_cpus': os.cpu_count(),
        'onnx_providers': ort.get_available_providers(), 'gpu': gpu, 'versions': versions,
        'coverage_installed': util.find_spec('pytest_cov') is not None, 'git_head': git_head,
        'git_status_scoped': git_status, 'model_root': str(settings.face_model_root),
        'model_files': [{'name': p.name, 'bytes': p.stat().st_size} for p in settings.face_model_root.rglob('*.onnx')],
        'user_image_inventory': inventory, 'official_database_sha256_before': before}
    if args.face_image:
        environment['explicit_user_sample'] = {'path': str(args.face_image), 'sha256': sha(args.face_image),
            'count': 1, 'purpose': 'Detection, embedding, empty-index request, enrollment, persistence; no identification accuracy'}
    save('reports/environment.json', environment)
    command('pip_list', ['-m', 'pip', 'list', '--format=json'])
    case('Dependency consistency', lambda: command('pip_check', ['-m', 'pip', 'check']))
    def imports():
        modules = ['app.main', 'app.services.face_engine', 'app.services.face_matcher', 'app.models.database',
                   'app.models.face_embedding', 'app.schemas.recognition', 'app.schemas.person', 'app.api.websocket']
        for name in modules:
            import_module(name)
        return modules
    case('Core module import', imports)
    # Unique name ensures a repeat run never damages existing test or production DBs.
    db = ART / 'api' / f'测试数据库_{uuid4().hex[:8]}.db'
    env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONUNBUFFERED': '1', 'DATABASE_URL': f'sqlite:///{db}',
        'FACE_MODEL_ROOT': str(settings.face_model_root), 'FACE_MODEL_NAME': 'buffalo_l',
        'FACE_DEVICE': 'cpu', 'ALLOW_MODEL_DOWNLOAD': 'false', 'DEBUG': 'true', 'RETURN_DEBUG_INFO': 'true',
        'SAVE_DEBUG_IMAGES': 'false', 'MAX_IMAGE_SIZE_MB': '8', 'MAX_IMAGE_PIXELS': '20000000',
        'MAX_REQUESTS_PER_SECOND': '5', 'MAX_PENDING_JOBS': '8', 'STABLE_FRAME_COUNT': '3'}
    case('Initialize isolated SQLite via CLI', lambda: command('init_db', ['scripts/init_db.py'], env=env))
    def inspect_db():
        assert db.is_file()
        with sqlite3.connect(db) as connection:
            tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            details = {table: {'columns': connection.execute(f'PRAGMA table_info({table})').fetchall(),
                'indexes': connection.execute(f'PRAGMA index_list({table})').fetchall(),
                'foreign_keys': connection.execute(f'PRAGMA foreign_key_list({table})').fetchall()} for table in tables}
            assert set(tables) == {'persons', 'face_embeddings'}
            assert details['face_embeddings']['foreign_keys'][0][6] == 'CASCADE'
            assert connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        save('reports/database_schema.json', details)
        return {'database': str(db), 'tables': tables, 'integrity_check': 'ok'}
    case('Inspect tables indexes foreign keys', inspect_db)
    def mathematics():
        vector = normalize_embedding([3, 4])
        np.testing.assert_allclose(vector, [.6, .8], atol=1e-6)
        matcher = FaceMatcher(2)
        matcher.replace([(1, 'same', np.array([1, 0])), (2, 'orthogonal', np.array([0, 1])),
                         (3, 'opposite', np.array([-1, 0]))])
        result = matcher.match(np.array([1, 0]), 3)
        assert [c.similarity for c in result] == [1, 0, -1]
        return {'normalized': vector.tolist(), 'norm': float(np.linalg.norm(vector)), 'top_k': [c.model_dump() for c in result]}
    case('Matcher mathematical sanity', mathematics)
    image_dir = ART / 'screenshots_or_outputs' / '生成图片'
    image_dir.mkdir(exist_ok=True)
    for name, color in [('black', 'black'), ('white', 'white')]:
        Image.new('RGB', (320, 240), color).save(image_dir / f'{name}.jpg')
    rng = np.random.default_rng(20261009)
    Image.fromarray(rng.integers(0, 256, (240, 320, 3), dtype=np.uint8)).save(image_dir / 'random_noise.jpg')
    geometry = Image.new('RGB', (320, 240), 'blue')
    ImageDraw.Draw(geometry).rectangle((20, 20, 100, 100), fill='green')
    geometry.save(image_dir / 'geometry.png')
    Image.new('RGB', (1, 1), 'black').save(image_dir / 'tiny.jpg')
    Image.new('RGB', (6000, 4000), 'white').save(image_dir / 'large_dimensions.jpg')
    Image.new('RGB', (2, 2), 'black').save(image_dir / 'unsupported.gif')
    (image_dir / 'empty.jpg').write_bytes(b'')
    (image_dir / 'invalid.jpg').write_bytes(b'this is not a JPEG')
    raw = (image_dir / 'black.jpg').read_bytes()
    encoded = base64.b64encode(raw).decode()
    # Probe before binding, never stop an existing service.
    port = None
    for candidate in (18081, 18082):
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', candidate))
                port = candidate
                break
            except OSError:
                continue
    if port is None:
        raise RuntimeError('18081 and 18082 are occupied; no process was stopped')
    env['APP_PORT'] = str(port)
    url = f'http://127.0.0.1:{port}'
    ws_url = f'ws://127.0.0.1:{port}/ws/recognition'
    environment['selected_port'] = port
    environment['test_database'] = str(db)
    save('reports/environment.json', environment)
    with httpx.Client(base_url=url, trust_env=False, timeout=30) as client:
        def request(method, path, expected_status=200, **kwargs):
            if '/recognize/' in path:
                sleep(.23)
            began = perf_counter()
            response = client.request(method, path, **kwargs)
            is_json = 'application/json' in response.headers.get('content-type', '')
            body = response.json() if is_json else response.text[:200]
            API.append({'method': method, 'path': path, 'status': response.status_code,
                'content_type': response.headers.get('content-type'), 'headers': {'x-request-id': response.headers.get('x-request-id')},
                'body': body, 'elapsed_ms': (perf_counter() - began) * 1000})
            save('api/responses.json', API)
            assert response.status_code == expected_status, str(body)
            return body
        def json_frame(**extra):
            return request('POST', '/api/v1/recognize/base64', json={'request_id': uuid4().hex, 'image_base64': encoded, **extra})
        def error_code(body, code):
            assert body['error']['code'] == code, body
            assert body['matched'] is False and body['person'] is None
            RecognitionResponse.model_validate(body)
            return code
        for cycle in range(1, 4):
            stop = ART / 'logs' / f'stop_{cycle}_{uuid4().hex}.flag'
            env['QA_STOP_FILE'] = str(stop)
            log_path = ART / 'logs' / f'uvicorn_cycle_{cycle}.txt'
            with log_path.open('w', encoding='utf-8') as log:
                process = subprocess.Popen([sys.executable, 'tests/qa_server_runner.py'], cwd=ROOT, env=env,
                    stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                started = perf_counter()
                try:
                    deadline = monotonic() + 60
                    while monotonic() < deadline:
                        if process.poll() is not None:
                            raise RuntimeError(log_path.read_text(encoding='utf-8'))
                        try:
                            health = client.get('/health')
                            if health.status_code == 200:
                                break
                        except httpx.ConnectError:
                            sleep(.2)
                    else:
                        raise RuntimeError('Server startup timeout')
                    def ready():
                        body = health.json()
                        assert body['model_ready'] and body['database_ready'] and body['status'] == 'ok'
                        return {'health': body, 'startup_to_health_ms': (perf_counter() - started) * 1000,
                                'port': port, 'pid': process.pid}
                    case(f'Start cycle {cycle}: real CPU model and health', ready)
                    if cycle != 1:
                        case(f'Restart cycle {cycle}: DB integrity', inspect_db)
                        continue
                    case('Docs and OpenAPI schema', lambda: (
                        request('GET', '/docs'),
                        save('api/openapi.json', request('GET', '/openapi.json')),
                        '/api/v1/recognize/base64' in client.get('/openapi.json').json()['paths']))
                    def crud():
                        profile = {'person_id': 'test_student_001', 'name': '测试同学1', 'student_no': 'TEST001',
                            'school': 'Test University', 'major': 'Software Engineering', 'description': 'Automated test participant'}
                        result = request('POST', '/api/v1/persons', 201, json=profile, headers={'X-Request-ID': 'crud-create'})
                        assert result['request_id'] == 'crud-create'
                        for key, value in profile.items():
                            assert result['person'][key] == value
                        assert any(p['person_id'] == profile['person_id'] for p in request('GET', '/api/v1/persons')['persons'])
                        assert request('GET', '/api/v1/persons/test_student_001')['person']['name'] == profile['name']
                        assert request('POST', '/api/v1/persons', 409, json=profile)['error']['code'] == 'PERSON_ALREADY_EXISTS'
                        assert request('GET', '/api/v1/persons/not_found', 404)['error']['code'] == 'PERSON_NOT_FOUND'
                        # Real inference rejects enrollment of a generated non-face image.
                        rejected = request('POST', '/api/v1/persons/test_student_001/faces', 400,
                            files=[('files', ('black.jpg', raw))])
                        assert rejected['error']['code'] == 'NO_FACE'
                        request('DELETE', '/api/v1/persons/test_student_001')
                        assert request('DELETE', '/api/v1/persons/test_student_001', 404)['error']['code'] == 'PERSON_NOT_FOUND'
                        assert request('GET', '/health')['registered_persons'] == 0
                        return 'Create/list/get/duplicate/missing/enrollment rejection/delete/cleanup'
                    case('Live Person CRUD and enrollment rejection', crud)
                    case('Real generated JPEG NO_FACE', lambda: error_code(json_frame(request_id='no-face'), 'NO_FACE'))
                    for filename in ('white.jpg', 'random_noise.jpg', 'geometry.png', 'tiny.jpg'):
                        case(f'Real generated input {filename}', lambda filename=filename: error_code(
                            request('POST', '/api/v1/recognize/image', files={'file': (filename, (image_dir / filename).read_bytes())},
                                    data={'request_id': filename}), 'NO_FACE'))
                    def missing_id():
                        body = request('POST', '/api/v1/recognize/base64', json={'image_base64': encoded})
                        assert body['request_id']
                        return error_code(body, 'NO_FACE')
                    case('Base64 without optional request_id', missing_id)
                    for label, body in [('missing image', {'request_id': 'missing-image'}), ('empty Base64', {'request_id': 'empty-b64', 'image_base64': ''})]:
                        case(label, lambda body=body: error_code(request('POST', '/api/v1/recognize/base64', 422, json=body), 'INVALID_REQUEST'))
                    case('Invalid Base64', lambda: error_code(request('POST', '/api/v1/recognize/base64', 400,
                        json={'request_id': 'invalid-b64', 'image_base64': '!!!'}), 'INVALID_BASE64'))
                    case('Unicode request_id live transport', lambda: (
                        error_code(json_frame(request_id='请求_实测_001'), 'NO_FACE')))
                    for filename, code in [('empty.jpg', 'INVALID_IMAGE'), ('invalid.jpg', 'IMAGE_DECODE_FAILED'),
                                           ('unsupported.gif', 'INVALID_IMAGE_FORMAT'), ('large_dimensions.jpg', 'IMAGE_TOO_LARGE')]:
                        case(f'Multipart rejection {filename}', lambda filename=filename, code=code: error_code(
                            request('POST', '/api/v1/recognize/image', 400 if filename == 'unsupported.gif' else 200,
                                    files={'file': (filename, (image_dir / filename).read_bytes())},
                                    data={'request_id': filename}), code))
                    case('Corrupt JPEG bytes', lambda: error_code(request('POST', '/api/v1/recognize/image',
                        files={'file': ('corrupt.jpg', raw[:100])}, data={'request_id': 'corrupt'}), 'IMAGE_DECODE_FAILED'))
                    case('Oversized file > 8 MiB', lambda: error_code(request('POST', '/api/v1/recognize/image',
                        files={'file': ('oversized.jpg', b'x' * (8 * 1024 * 1024 + 1))}, data={'request_id': 'oversized'}), 'IMAGE_TOO_LARGE'))
                    case('Valid data URL', lambda: error_code(json_frame(image_base64='data:image/jpeg;base64,' + encoded), 'NO_FACE'))
                    def cache():
                        count = request('GET', '/api/v1/stats')['recognition_count']
                        a = json_frame(request_id='cache-live')
                        b = json_frame(request_id='cache-live')
                        assert a == b
                        assert request('GET', '/api/v1/stats')['recognition_count'] == count + 1
                        return 'Identical response; only one inference added'
                    case('Live duplicate request cache', cache)
                    case('Reload running index CLI', lambda: command('reload_index', ['scripts/rebuild_face_index.py', '--url', url], env=env))
                    case('HTTP example multipart', lambda: command('example_http', ['examples/http_client.py', '--url', url, '--image', str(image_dir / 'black.jpg')], env=env))
                    sleep(1.1)
                    case('HTTP example Base64', lambda: command('example_base64', ['examples/http_client.py', '--url', url, '--image', str(image_dir / 'black.jpg'), '--base64'], env=env))
                    sleep(1.1)
                    async def websocket_cases():
                        async with websockets.connect(ws_url, proxy=None) as connection:
                            for text in ('', 'not json', '{"type":"unknown"}'):
                                await connection.send(text)
                                response = json.loads(await connection.recv())
                                WS.append({'sent': text, 'received': response})
                                assert response['error']['code'] == 'INVALID_REQUEST'
                            for message in [{'type': 'ping', 'request_id': 'ws-ping'},
                                {'type': 'recognize', 'request_id': 'ws-frame', 'session_id': 'session_test',
                                 'device_id': 'glass_test', 'image_base64': encoded},
                                {'type': 'person_left', 'request_id': 'ws-left', 'session_id': 'session_test', 'device_id': 'glass_test'}]:
                                await connection.send(json.dumps(message))
                                response = json.loads(await connection.recv())
                                WS.append({'sent': {k: v for k, v in message.items() if k != 'image_base64'}, 'received': response})
                                assert response['request_id'] == message['request_id']
                                assert response['type'] == {'ping': 'pong', 'recognize': 'recognition_result', 'person_left': 'clear'}[message['type']]
                                if message['type'] == 'recognize':
                                    error_code(response, 'NO_FACE')
                        async with websockets.connect(ws_url, proxy=None) as connection:
                            await connection.send('{"type":"ping","request_id":"reconnect"}')
                            assert json.loads(await connection.recv())['type'] == 'pong'
                        save('websocket/responses.json', WS)
                        return 'ping, invalid JSON/type/empty, recognition, clear, reconnect'
                    case('Real WebSocket protocol and reconnect', lambda: asyncio.run(websocket_cases()))
                    sleep(1.1)
                    case('WebSocket example CLI', lambda: command('example_websocket', ['examples/websocket_client.py', '--url', ws_url,
                        '--image', str(image_dir / 'black.jpg'), '--frames', '3'], env=env))
                    if args.face_image:
                        sleep(1.1)
                        user_raw = args.face_image.read_bytes()
                        def real_empty_index():
                            body = request('POST', '/api/v1/recognize/image', files={'file': (args.face_image.name, user_raw)},
                                           data={'request_id': 'user-face-before-enrollment'})
                            assert body['face_detected'] is True
                            assert body['processing']['embedding_ms'] > 0
                            return error_code(body, 'NO_REGISTERED_FACES')
                        case('User photo real detection + ArcFace before enrollment', real_empty_index)
                        async def real_socket_empty_index():
                            await asyncio.sleep(.25)
                            async with websockets.connect(ws_url, proxy=None) as connection:
                                await connection.send(json.dumps({'type': 'recognize', 'request_id': 'user-real-ws-before-enrollment',
                                    'session_id': 'user-real-ws', 'image_base64': base64.b64encode(user_raw).decode()}))
                                body = json.loads(await connection.recv())
                                assert body['face_detected'] is True and body['processing']['embedding_ms'] > 0
                                WS.append({'sent': {'type': 'recognize', 'request_id': 'user-real-ws-before-enrollment'}, 'received': body})
                                save('websocket/responses.json', WS)
                                return error_code(body, 'NO_REGISTERED_FACES')
                        case('User photo real WebSocket inference before enrollment', lambda: asyncio.run(real_socket_empty_index()))
                        sleep(1.1)
                        def real_inference_benchmark():
                            output = command('benchmark_face_empty_index', ['scripts/benchmark.py', '--url', url,
                                '--image', str(args.face_image), '--iterations', '10'], env=env)
                            report = json.loads(output)
                            assert report['outcomes'] == {'NO_REGISTERED_FACES': 10} and not report['errors']
                            assert report['stage_means_ms']['embedding_ms'] > 0
                            save('benchmark/user_face_empty_index.json', report)
                            return report
                        case('Real user-face inference benchmark (empty index, not accuracy)', real_inference_benchmark)
                        def real_enrollment():
                            output = command('register_user_photo', ['scripts/register_person.py', '--url', url,
                                '--person-id', 'qa_user_supplied', '--name', 'QA supplied participant',
                                '--images', str(args.face_image)], env=env)
                            registered = json.loads(output)
                            assert registered['registered_embeddings'] == 1
                            health = request('GET', '/health')
                            assert health['registered_persons'] == 1 and health['registered_embeddings'] == 1
                            from app.utils.vector_utils import deserialize_embedding
                            with sqlite3.connect(db) as connection:
                                rows = connection.execute('SELECT embedding,embedding_dim,model_name,is_centroid FROM face_embeddings WHERE person_id=?',
                                                          ('qa_user_supplied',)).fetchall()
                            assert len(rows) == 2 and sorted(row[3] for row in rows) == [0, 1]
                            for blob, dimension, model_name, _ in rows:
                                vector = deserialize_embedding(blob, dimension)
                                assert dimension == 512 and model_name == 'buffalo_l' and vector.dtype == np.float32
                                assert abs(float(np.linalg.norm(vector)) - 1) < 1e-5
                            command('reload_index_with_real_embedding', ['scripts/rebuild_face_index.py', '--url', url], env=env)
                            request('DELETE', '/api/v1/persons/qa_user_supplied')
                            with sqlite3.connect(db) as connection:
                                assert connection.execute('SELECT COUNT(*) FROM face_embeddings').fetchone()[0] == 0
                            return {'enrollment': registered, 'sample_vectors': 1, 'centroids': 1, 'dimension': 512,
                                    'independent_identity_accuracy': 'NEED_USER_DATA', 'deleted_after_test': True}
                        case('Real registration CLI, persistence, reload and cascade deletion', real_enrollment)
                    sleep(1.1)
                    async def burst(count):
                        async with httpx.AsyncClient(base_url=url, trust_env=False, timeout=60) as concurrent:
                            async def send(i):
                                began = perf_counter()
                                rid = f'concurrency_{count}_{i}'
                                response = await concurrent.post('/api/v1/recognize/base64', json={'request_id': rid, 'image_base64': encoded})
                                body = response.json()
                                assert body['request_id'] == rid
                                assert (response.status_code == 200 and body['error']['code'] == 'NO_FACE') or (
                                    response.status_code == 429 and body['error']['code'] == 'RATE_LIMITED')
                                return {'status': response.status_code, 'error_code': body['error']['code'],
                                        'latency_ms': (perf_counter() - began) * 1000}
                            items = await asyncio.gather(*(send(i) for i in range(count)))
                        return {'requests': count, 'transport_and_protocol_success_rate': 1.0,
                            'accepted_count': sum(row['status'] == 200 for row in items),
                            'rate_limited_count': sum(row['status'] == 429 for row in items),
                            'mean_ms': float(np.mean([row['latency_ms'] for row in items])), 'results': items}
                    for count in (10, 20):
                        sleep(1.1)
                        def concurrency(count=count):
                            detail = asyncio.run(burst(count))
                            save(f'benchmark/concurrency_{count}.json', detail)
                            assert detail['rate_limited_count'] > 0
                            return detail
                        case(f'Concurrent HTTP {count} + rate limit', concurrency)
                    sleep(1.1)
                    case('Rate window recovery live', lambda: error_code(json_frame(), 'NO_FACE'))
                    sleep(1.1)
                    def benchmark():
                        output = command('benchmark', ['scripts/benchmark.py', '--url', url, '--image', str(image_dir / 'black.jpg'),
                            '--iterations', '20'], env=env)
                        report = json.loads(output)
                        assert report['outcomes'] == {'NO_FACE': 20} and not report['errors']
                        save('benchmark/benchmark_results.txt', output)
                        save('benchmark/benchmark_results.json', report)
                        return report
                    case('Real NO_FACE API benchmark 20 iterations', benchmark)
                finally:
                    stop.write_text('stop', encoding='utf-8')
                    try:
                        process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        process.wait(timeout=10)
                        RESULTS.append({'case': f'Shutdown cycle {cycle}', 'status': 'FAIL', 'error': 'Graceful shutdown timed out'})
                    log.flush()
                    def shutdown():
                        text = log_path.read_text(encoding='utf-8')
                        assert process.returncode == 0
                        assert 'Application shutdown complete' in text
                        assert 'Traceback' not in text and 'ERROR' not in text
                        return {'exit_code': process.returncode, 'shutdown_complete_logged': True}
                    case(f'Graceful shutdown cycle {cycle}', shutdown)
    # Synthetic score fixture verifies calibration mechanics, never face accuracy.
    pairs = ART / 'calibration' / 'synthetic_pairs.csv'
    pairs.write_text('label,similarity\n1,0.9\n1,0.8\n0,0.3\n0,0.2\n', encoding='utf-8')
    case('Calibration CLI synthetic scores only', lambda: command('calibration_synthetic', ['scripts/calibrate_threshold.py',
        '--pairs-csv', str(pairs), '--output', str(ART / 'calibration' / 'synthetic_threshold_results.csv')], env=env))
    def matcher_benchmark():
        vectors = rng.normal(size=(2500, 512)).astype(np.float32)
        vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
        matcher = FaceMatcher(512)
        matcher.replace([(i, f'p{i // 5:03d}', v) for i, v in enumerate(vectors)])
        timings = []
        for _ in range(100):
            start = perf_counter()
            matcher.match(vectors[0], 3)
            timings.append((perf_counter() - start) * 1000)
        detail = {'synthetic_vectors': 2500, 'persons': 500, 'dimension': 512, 'iterations': 100,
            'mean_ms': float(np.mean(timings)), 'p50_ms': float(np.percentile(timings, 50)),
            'p95_ms': float(np.percentile(timings, 95)), 'p99_ms': float(np.percentile(timings, 99)),
            'throughput_rps': 100000 / sum(timings)}
        save('benchmark/matcher_benchmark.json', detail)
        return detail
    case('Matcher-only synthetic benchmark', matcher_benchmark)
    case('Package install plan matches README requirements', lambda: command('pip_dry_run',
        ['-m', 'pip', 'install', '--dry-run', '--no-index', '-r', 'requirements-model.txt']))
    for script in ('scripts/register_person.py', 'scripts/benchmark.py', 'scripts/calibrate_threshold.py',
                   'examples/http_client.py', 'examples/websocket_client.py'):
        case(f'CLI usage {script}', lambda script=script: command(Path(script).stem + '_help', [script, '--help']))
    def registration_cli_rejection():
        # The server is stopped; its actual HTTP registration was checked above. Usage is checked here.
        return 'Successful real-face register_person CLI: NEED_USER_DATA; no samples registered'
    RESULTS.append({'case': 'Independent identification/unknown participant/multiple-face/real calibration',
                    'status': 'SKIPPED', 'reason': 'NEED_USER_DATA: only one user photo; no independent identity test images or multiple subjects'})
    after = sha(official_db)
    environment['official_database_sha256_after'] = after
    environment['official_database_unchanged'] = before == after
    if args.face_image:
        environment['explicit_user_sample']['sha256_after'] = sha(args.face_image)
        environment['explicit_user_sample']['original_unchanged'] = environment['explicit_user_sample']['sha256'] == sha(args.face_image)
    save('reports/environment.json', environment)
    case('Production SQLite unchanged', lambda: None if before == after else (_ for _ in ()).throw(AssertionError('Official DB changed')))
    case('Test DB final integrity and CRUD cleanup', inspect_db)
    save('reports/live_results.json', RESULTS)
    manifest = {str(p.relative_to(ROOT)): sha(p) for directory in ('app', 'scripts', 'examples', 'tests')
        for p in (ROOT / directory).rglob('*.py')}
    save('reports/code_sha256.json', manifest)
    counts = dict(Counter(r['status'] for r in RESULTS))
    print(json.dumps({'summary': counts, 'selected_port': port, 'artifacts': str(ART)}, ensure_ascii=False), flush=True)
    raise SystemExit(1 if counts.get('FAIL') else 0)


if __name__ == '__main__':
    main()
