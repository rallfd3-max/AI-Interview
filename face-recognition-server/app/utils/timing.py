"""Wall-clock stage timings in milliseconds."""
from contextlib import contextmanager
from time import perf_counter
from collections.abc import Iterator


class Timer:
    def __init__(self) -> None:
        self.started = perf_counter()
        self.values: dict[str, float] = {}

    @contextmanager
    def measure(self, name: str) -> Iterator[None]:
        start = perf_counter()
        try:
            yield
        finally:
            self.values[name + '_ms'] = (perf_counter() - start) * 1000

    def result(self) -> dict[str, float]:
        return {**self.values, 'total_ms': (perf_counter() - self.started) * 1000}
