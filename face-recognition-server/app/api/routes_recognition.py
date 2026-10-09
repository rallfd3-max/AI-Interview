"""JPEG multipart and Base64 JSON entrypoints share one recognition path."""
import json
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pydantic import ValidationError
from app.api.dependencies import get_runtime, peer_scope
from app.core.exceptions import AppError
from app.schemas.recognition import RecognitionRequest, RecognitionMeta, RecognitionResponse, FaceBox
from app.services.runtime import Runtime
from app.utils.image_utils import decode_base64

router = APIRouter(prefix='/api/v1/recognize', tags=['recognition'])


def recognize_base64(runtime: Runtime, message: RecognitionRequest, scope: str):
    if message.image_format.lower() not in ('jpg', 'jpeg', 'png'):
        raise AppError('INVALID_IMAGE_FORMAT', 'Only JPEG and PNG are supported.')
    raw = decode_base64(message.image_base64, runtime.settings)
    meta = RecognitionMeta.model_validate(message.model_dump())
    return runtime.recognize(raw, meta, scope)


@router.post('/base64', response_model=RecognitionResponse)
async def base64_recognition(message: RecognitionRequest, request: Request,
                             runtime: Runtime = Depends(get_runtime)):
    request.state.request_id = message.request_id
    return await runtime.run(recognize_base64, runtime, message, peer_scope(request))


@router.post('/image', response_model=RecognitionResponse)
async def image_recognition(request: Request, file: UploadFile = File(...), request_id: str | None = Form(None),
                            device_id: str | None = Form(None), session_id: str | None = Form(None),
                            face_box: str | None = Form(None), stable_frames: int | None = Form(None),
                            runtime: Runtime = Depends(get_runtime)):
    request.state.request_id = request_id or request.state.request_id
    try:
        box = FaceBox.model_validate(json.loads(face_box)) if face_box else None
    except (ValidationError, ValueError, TypeError) as exc:
        raise AppError('INVALID_FACE_BOX', 'face_box must be a valid JSON object with integer x/y/w/h.') from exc
    try:
        meta = RecognitionMeta(request_id=request.state.request_id, device_id=device_id, session_id=session_id,
                               face_box=box, stable_frames=stable_frames)
    except ValidationError as exc:
        raise AppError('INVALID_REQUEST', 'Invalid recognition metadata.') from exc
    if Path(file.filename or '').suffix.lower() not in ('.jpg', '.jpeg', '.png'):
        raise AppError('INVALID_IMAGE_FORMAT', 'Only jpg/jpeg/png filenames are supported.')
    raw = await file.read(runtime.settings.max_image_bytes + 1)
    await file.close()
    return await runtime.run(runtime.recognize, raw, meta, peer_scope(request))
