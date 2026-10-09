"""Application factory with injectable model for isolated tests."""
import json
import logging
from contextlib import asynccontextmanager
from time import perf_counter
from urllib.parse import quote
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import Settings
from app.core.logging import configure_logging
from app.core.exceptions import AppError
from app.schemas.common import Envelope, ErrorDetail, new_request_id
from app.schemas.recognition import RecognitionResponse
from app.services.runtime import Runtime
from app.api import routes_health, routes_person, routes_recognition, websocket

logger = logging.getLogger('face_server')


def error_response(request: Request, code: str, message: str, status: int) -> JSONResponse:
    schema = RecognitionResponse if '/recognize/' in request.url.path else Envelope
    result = schema(type='recognition_result' if '/recognize/' in request.url.path else 'error',
        request_id=getattr(request.state, 'request_id', new_request_id()), success=False,
        error=ErrorDetail(code=code, message=message))
    logger.warning('Request rejected', extra={'fields': {'request_id': result.request_id, 'code': code}})
    return JSONResponse(result.model_dump(mode='json'), status_code=status,
                        headers={'X-Request-ID': quote(result.request_id, safe='')})


def create_app(settings: Settings | None = None, face_engine=None) -> FastAPI:
    settings = settings or Settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        runtime = Runtime(settings, face_engine)
        application.state.runtime = runtime
        await runtime.run(runtime.initialize)
        try:
            yield
        finally:
            runtime.executor.shutdown(wait=True, cancel_futures=True)
            if runtime.engine:
                runtime.engine.dispose()

    application = FastAPI(title='Course Face Recognition Server', version='1.0.0', lifespan=lifespan,
                          responses={status: {'model': Envelope} for status in (400, 404, 409, 413, 422, 429, 500, 503)})

    @application.middleware('http')
    async def request_context(request: Request, call_next):
        started = perf_counter()
        request.state.request_id = request.headers.get('X-Request-ID', '')[:128] or new_request_id()
        if request.method in ('POST', 'PUT', 'PATCH'):
            # Read with a bounded stream before JSON or multipart parsing.
            limit = settings.max_image_bytes * (5 if request.url.path.endswith('/faces') else 4 / 3) + 65536
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > limit:
                    return error_response(request, 'IMAGE_TOO_LARGE', 'Request body is too large.', 413)
            request._body = bytes(body)
            if 'application/json' in request.headers.get('content-type', ''):
                try:
                    data = json.loads(body)
                    if isinstance(data, dict) and isinstance(data.get('request_id'), str) and 0 < len(data['request_id']) <= 128:
                        request.state.request_id = data['request_id']
                except (ValueError, UnicodeDecodeError):
                    # FastAPI reports malformed JSON through the validation handler.
                    logger.info('Malformed JSON received', extra={'fields': {'request_id': request.state.request_id}})
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception('Request failed', extra={'fields': {'request_id': request.state.request_id}})
            response = error_response(request, 'DATABASE_ERROR' if isinstance(exc, SQLAlchemyError) else 'INTERNAL_ERROR',
                                      'Server processing failed.', 503 if isinstance(exc, SQLAlchemyError) else 500)
        # JSON accepts Unicode/control characters; HTTP headers require safe bytes.
        response.headers['X-Request-ID'] = quote(request.state.request_id, safe='')
        logger.info('HTTP request completed', extra={'fields': {'request_id': request.state.request_id,
            'path': request.url.path, 'status': response.status_code, 'total_ms': (perf_counter() - started) * 1000}})
        return response

    @application.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError):
        return error_response(request, exc.code, exc.message, exc.status)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        if hasattr(exc.body, 'get'):
            supplied_id = exc.body.get('request_id')
            if isinstance(supplied_id, str) and 0 < len(supplied_id) <= 128:
                request.state.request_id = supplied_id
        face_box_error = any('face_box' in e['loc'] for e in exc.errors())
        return error_response(request, 'INVALID_FACE_BOX' if face_box_error else 'INVALID_REQUEST',
                              'Request validation failed; check the API schema.', 422)

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return error_response(request, 'INVALID_REQUEST', str(exc.detail), exc.status_code)

    for router in (routes_health.router, routes_person.router, routes_recognition.router, websocket.router):
        application.include_router(router)
    return application


app = create_app()
