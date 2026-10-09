"""Local build-only Maven download bridge using the host HTTP configuration."""
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import httpx

CACHE = Path(__file__).parent / 'repository-cache'
CLIENT = httpx.Client(timeout=35, follow_redirects=True)

class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.serve(False)

    def do_GET(self):
        self.serve(True)

    def serve(self, body):
        path = urlsplit(self.path).path.lstrip('/')
        file = (CACHE / path).resolve()
        if not file.is_relative_to(CACHE.resolve()):
            self.send_error(400)
            return
        if not file.is_file():
            if path.startswith('com/rokid/'):
                repos = ['https://maven.rokid.com/repository/maven-public/']
            elif path.startswith(('com/android/', 'androidx/')):
                repos = ['https://maven.aliyun.com/repository/google/']
            elif path.startswith(('org/gradle/toolchains/', 'org/jetbrains/kotlin/plugin/')):
                repos = ['https://plugins.gradle.org/m2/', 'https://repo.maven.apache.org/maven2/']
            else:
                repos = ['https://maven.aliyun.com/repository/central/', 'https://repo.maven.apache.org/maven2/', 'https://maven.aliyun.com/repository/google/']
            for repo in repos:
                try:
                    r = CLIENT.get(repo + path)
                    if r.status_code == 200:
                        file.parent.mkdir(parents=True, exist_ok=True)
                        file.write_bytes(r.content)
                        with (CACHE.parent / 'downloads.log').open('a', encoding='utf-8') as log:
                            log.write(f'FETCH {path} {len(r.content)}\n')
                        break
                except httpx.HTTPError:
                    pass
            else:
                self.send_error(404)
                return
        raw = file.read_bytes()
        self.send_response(200)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        if body:
            self.wfile.write(raw)

    def log_message(self, *args):
        pass

class Server(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True

Server(('127.0.0.1', 18082), Handler).serve_forever()
