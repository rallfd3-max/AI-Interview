"""Bounded expiring session state and consecutive-frame debounce."""
from dataclasses import dataclass, field
from time import monotonic
from cachetools import TTLCache
from app.schemas.recognition import Stability


@dataclass
class RecognitionSession:
    session_id: str
    last_candidates: list[str] = field(default_factory=list)
    last_confirmed_person: str | None = None
    last_seen_time: float = field(default_factory=monotonic)
    required: int = 3


class SessionService:
    def __init__(self, timeout: float, capacity: int = 2048):
        self.states = TTLCache(maxsize=capacity, ttl=timeout)

    def update(self, key: tuple, candidate: str | None, required: int) -> Stability:
        state = self.states.get(key)
        if state is None or state.required != required:
            state = RecognitionSession(session_id=str(key[-1]), required=required)
        if candidate is None:
            state.last_candidates.clear()
        elif state.last_candidates and state.last_candidates[-1] == candidate:
            state.last_candidates = (state.last_candidates + [candidate])[-required:]
        else:
            state.last_candidates = [candidate]
        if candidate and len(state.last_candidates) >= required:
            state.last_confirmed_person = candidate
        state.last_seen_time = monotonic()
        self.states[key] = state
        return Stability(confirmed=state.last_confirmed_person is not None,
                         consistent_frames=len(state.last_candidates),
                         confirmed_person_id=state.last_confirmed_person)

    def clear(self, key: tuple) -> None:
        self.states.pop(key, None)
