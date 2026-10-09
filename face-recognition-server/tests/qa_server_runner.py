"""QA-only process runner with a file-triggered graceful Uvicorn shutdown."""
import asyncio
from contextlib import suppress
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import uvicorn
from app.core.config import Settings


async def main() -> None:
    settings = Settings()
    server = uvicorn.Server(uvicorn.Config('app.main:app', host='127.0.0.1', port=settings.app_port,
        workers=1, ws_max_size=int(settings.max_image_bytes * 4 / 3) + 65536))
    stop = Path(os.environ['QA_STOP_FILE'])
    async def monitor():
        while not stop.exists():
            await asyncio.sleep(0.1)
        server.should_exit = True
    task = asyncio.create_task(monitor())
    try:
        await server.serve()
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


if __name__ == '__main__':
    asyncio.run(main())
