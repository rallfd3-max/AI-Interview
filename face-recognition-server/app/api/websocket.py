"""Bounded WebSocket protocol; CPU work is dispatched to the shared worker."""
import json
import logging
from uuid import uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.api.dependencies import peer_scope
from app.api.routes_recognition import recognize_base64
from app.core.exceptions import AppError
from app.schemas.common import Envelope, ErrorDetail, new_request_id
from app.schemas.recognition import RecognitionRequest, RecognitionResponse, ControlMessage, ControlResponse

router = APIRouter()
logger = logging.getLogger('face_server')


def normalize_glasses_message(data: dict, device_id: str | None) -> tuple[dict, bool]:
    """Adapt the shipped v1 glasses protocol without changing the HTTP contract.

    Legacy boxes are ambiguous across SDK versions, so detect on the full image.
    Legacy uploads are sparse snapshots and require single-frame confirmation.
    """
    data = dict(data)
    legacy_face = data.get('type') == 'face'
    if legacy_face:
        data['type'] = 'recognize'
        data['image_base64'] = data.get('img')
        data.setdefault('image_format', 'jpeg')
        data.setdefault('stable_frames', 1)
        data.pop('face_box', None)
    if data.get('type') == 'event' and data.get('event') == 'person_left':
        data['type'] = 'person_left'
    if not data.get('device_id') and device_id:
        data['device_id'] = device_id
    return data, legacy_face


def legacy_glasses_response(result: RecognitionResponse) -> dict:
    if result.success and result.matched and result.person:
        person = result.person
        return {'type': 'person_info', 'request_id': result.request_id,
                'id': person.person_id, 'name': person.name,
                'display_lines': [v for v in (person.school, person.major, person.description) if v],
                'ts': result.timestamp}
    code = result.error.code if result.error else 'UNKNOWN_FACE'
    return {'type': 'error', 'request_id': result.request_id,
            'code': 'unknown_face' if code in ('UNKNOWN_FACE', 'NO_FACE', 'NO_REGISTERED_FACES') else code,
            'msg': result.error.message if result.error else 'No confirmed person.',
            'ts': result.timestamp}


@router.websocket('/ws/recognition')
async def websocket_recognition(socket: WebSocket):
    await socket.accept()
    runtime = socket.app.state.runtime
    scope = peer_scope(socket)
    connection_session = 'ws_' + uuid4().hex
    touched: set[tuple[str | None, str]] = set()
    try:
        while True:
            request_id = new_request_id()
            message_type = None
            legacy_face = False
            try:
                packet = await socket.receive()
                if packet['type'] == 'websocket.disconnect':
                    break
                text = packet.get('text')
                if text is None:
                    raise AppError('INVALID_REQUEST', 'Send JSON text frames.')
                if len(text) > int(runtime.settings.max_image_bytes * 4 / 3) + 16384:
                    raise AppError('IMAGE_TOO_LARGE', 'WebSocket message is too large.', 413)
                data = json.loads(text)
                if not isinstance(data, dict):
                    raise AppError('INVALID_REQUEST', 'Expected a JSON object.')
                message_type = data.get('type')
                data, legacy_face = normalize_glasses_message(data, socket.headers.get('x-device-id'))
                if isinstance(data.get('request_id'), str) and 0 < len(data['request_id']) <= 128:
                    request_id = data['request_id']
                if data.get('type') == 'recognize':
                    message = RecognitionRequest.model_validate(data)
                    logger.info('Glasses image received', extra={'fields': {
                        'request_id': message.request_id, 'device_id': message.device_id,
                        'protocol': 'legacy_face' if legacy_face else 'recognize',
                        'base64_chars': len(message.image_base64)}})
                    message.session_id = message.session_id or connection_session
                    session_key = (message.device_id, message.session_id)
                    if session_key not in touched and len(touched) >= 128:
                        raise AppError('RATE_LIMITED', 'Too many sessions on one connection.', 429)
                    touched.add(session_key)
                    result = await runtime.run(recognize_base64, runtime, message, scope)
                elif data.get('type') == 'audio':
                    await runtime.run(runtime.rate_limit, scope)
                    await socket.send_json({'type': 'error', 'request_id': request_id,
                        'code': 'UNSUPPORTED_MESSAGE_TYPE',
                        'msg': 'This face recognition server does not process audio.'})
                    continue
                else:
                    message = ControlMessage.model_validate(data)
                    await runtime.run(runtime.rate_limit, scope)
                    session_id = message.session_id or connection_session
                    if message.type != 'ping':
                        await runtime.run(runtime.clear_session, scope, message.device_id, session_id)
                    result = ControlResponse(type='pong' if message.type == 'ping' else 'clear',
                        request_id=message.request_id, session_id=session_id if message.type != 'ping' else None)
                await socket.send_json(legacy_glasses_response(result) if legacy_face else result.model_dump(mode='json'))
            except (ValueError, ValidationError) as exc:
                code = 'INVALID_FACE_BOX' if isinstance(exc, ValidationError) and any('face_box' in e['loc'] for e in exc.errors()) else 'INVALID_REQUEST'
                fields = [{'field': '.'.join(map(str, e['loc'])), 'reason': e['type']}
                          for e in exc.errors()] if isinstance(exc, ValidationError) else []
                logger.warning('Invalid WebSocket message', extra={'fields': {
                    'request_id': request_id, 'code': code, 'message_type': message_type,
                    'validation': fields}})
                result = RecognitionResponse(request_id=request_id, success=False,
                                  error=ErrorDetail(code=code, message='Invalid WebSocket JSON message.'))
                await socket.send_json(legacy_glasses_response(result) if legacy_face else result.model_dump(mode='json'))
            except AppError as exc:
                logger.warning('WebSocket request rejected', extra={'fields': {'request_id': request_id, 'code': exc.code}})
                result = RecognitionResponse(request_id=request_id, success=False,
                    error=ErrorDetail(code=exc.code, message=exc.message))
                await socket.send_json(legacy_glasses_response(result) if legacy_face else result.model_dump(mode='json'))
            except WebSocketDisconnect:
                break
            except Exception as exc:
                logger.exception('WebSocket processing failed', extra={'fields': {'request_id': request_id}})
                code = 'DATABASE_ERROR' if isinstance(exc, SQLAlchemyError) else 'INTERNAL_ERROR'
                await socket.send_json(RecognitionResponse(request_id=request_id, success=False,
                    error=ErrorDetail(code=code, message='Server processing failed.')).model_dump(mode='json'))
    finally:
        # Explicit session IDs may resume across reconnects; only connection-owned state is removed.
        for device, session in touched:
            if session == connection_session:
                await runtime.run(runtime.clear_session, scope, device, session)
