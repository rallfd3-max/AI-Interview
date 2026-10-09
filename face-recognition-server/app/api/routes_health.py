"""Readiness stays accessible when model initialization fails."""
from fastapi import APIRouter, Depends, Request
from pydantic import Field
from app.api.dependencies import get_runtime
from app.core.exceptions import AppError
from app.schemas.common import Envelope
from app.services.runtime import Runtime

router = APIRouter(tags=['health'])


class HealthResponse(Envelope):
    status: str
    model_ready: bool
    database_ready: bool
    registered_persons: int
    registered_embeddings: int


class StatsResponse(HealthResponse):
    type: str = 'stats_result'
    model_name: str
    providers: list[str]
    embedding_dimension: int
    recognition_count: int
    average_recognition_ms: float


@router.get('/health', response_model=HealthResponse)
async def health(request: Request, runtime: Runtime = Depends(get_runtime)):
    return await runtime.run(runtime.health, request.state.request_id)


@router.get('/api/v1/stats', response_model=StatsResponse)
async def stats(request: Request, runtime: Runtime = Depends(get_runtime)):
    if not runtime.settings.debug:
        raise AppError('INVALID_REQUEST', 'Stats require DEBUG=true.', 404)
    data = await runtime.run(runtime.health, request.state.request_id)
    return {**data, 'type': 'stats_result', 'model_name': runtime.face_engine.model_name,
            'providers': runtime.face_engine.providers, 'embedding_dimension': runtime.face_engine.dimension,
            'recognition_count': runtime.recognition_count,
            'average_recognition_ms': runtime.total_recognition_ms / max(1, runtime.recognition_count)}


@router.post('/api/v1/index/reload', response_model=Envelope)
async def reload_index(request: Request, runtime: Runtime = Depends(get_runtime)):
    if not runtime.settings.debug:
        raise AppError('INVALID_REQUEST', 'Index reload requires DEBUG=true.', 404)
    await runtime.run(runtime.reload_index)
    return Envelope(type='index_reloaded', request_id=request.state.request_id)
