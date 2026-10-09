import asyncio
from threading import Event
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.core.config import Settings
from app.core.exceptions import AppError
from app.services.runtime import Runtime
from tests.conftest import MockFaceEngine


def test_worker_admission_is_bounded():
    async def scenario():
        runtime = Runtime(Settings(_env_file=None, max_pending_jobs=1), MockFaceEngine())
        entered, release = Event(), Event()
        def job():
            entered.set()
            release.wait(2)
        pending = asyncio.create_task(runtime.run(job))
        await asyncio.to_thread(entered.wait, 2)
        try:
            with pytest.raises(AppError) as exc:
                await runtime.run(lambda: None)
            assert exc.value.code == 'RATE_LIMITED'
            pending.cancel()
            with pytest.raises(asyncio.CancelledError):
                await pending
            assert runtime.pending == 1
        finally:
            release.set()
            await asyncio.to_thread(runtime.executor.shutdown, True)
            await asyncio.sleep(0)
    asyncio.run(scenario())


def test_concurrent_duplicates_execute_once(enrolled, encoded):
    payload = {'request_id': 'concurrent', 'image_base64': encoded}
    before = enrolled.model.calls
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(enrolled.post, '/api/v1/recognize/base64', json=payload) for _ in range(2)]
        results = [future.result().json() for future in futures]
    assert results[0] == results[1]
    assert enrolled.model.calls == before + 1
