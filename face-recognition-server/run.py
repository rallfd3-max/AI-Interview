"""Start one process: in-memory sessions and index are local to this worker."""
import uvicorn
from app.core.config import Settings

if __name__ == '__main__':
    settings = Settings()
    uvicorn.run('app.main:app', host=settings.app_host, port=settings.app_port,
                workers=1, ws_max_size=int(settings.max_image_bytes * 4 / 3) + 65536)
