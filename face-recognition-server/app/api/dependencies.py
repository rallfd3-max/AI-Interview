"""Application-scoped dependency injection."""
from fastapi import Request
from app.services.runtime import Runtime


def get_runtime(request: Request) -> Runtime:
    return request.app.state.runtime


def peer_scope(request) -> str:
    # Do not trust a caller-provided device ID for rate-limit isolation.
    return request.client.host if request.client else 'local'
