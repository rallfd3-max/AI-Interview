from cachetools import TTLCache
from app.services.session_service import SessionService


def test_stable_and_switch_debounce():
    sessions = SessionService(10)
    key = ('peer', 'device', 'session')
    assert not sessions.update(key, 'a', 3).confirmed
    assert not sessions.update(key, 'a', 3).confirmed
    assert sessions.update(key, 'a', 3).confirmed_person_id == 'a'
    assert sessions.update(key, 'b', 3).confirmed_person_id == 'a'
    assert sessions.update(key, 'b', 3).confirmed_person_id == 'a'
    assert sessions.update(key, 'b', 3).confirmed_person_id == 'b'
    sessions.update(key, None, 3)
    assert sessions.update(key, 'a', 3).consistent_frames == 1
    sessions.clear(key)
    assert not sessions.update(key, 'a', 3).confirmed


def test_session_timeout_and_device_isolation():
    now = [0.0]
    sessions = SessionService(10)
    sessions.states = TTLCache(20, 10, timer=lambda: now[0])
    assert sessions.update(('p', 'a', 's'), 'person', 1).confirmed
    assert not sessions.update(('p', 'b', 's'), 'person', 3).confirmed
    now[0] = 11
    assert not sessions.update(('p', 'a', 's'), 'person', 3).confirmed
