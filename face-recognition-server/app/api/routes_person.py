"""Enrollment and profile administration."""
from pathlib import Path
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from app.api.dependencies import get_runtime
from app.core.exceptions import AppError
from app.schemas.common import Envelope
from app.schemas.person import PersonCreate, PersonResponse, PersonList, FaceRegistration
from app.services.runtime import Runtime

router = APIRouter(prefix='/api/v1/persons', tags=['persons'])


@router.post('', response_model=PersonResponse, status_code=201)
async def create_person(profile: PersonCreate, request: Request, runtime: Runtime = Depends(get_runtime)):
    person = await runtime.run(runtime.person_service.create, profile)
    return PersonResponse(request_id=request.state.request_id, person=person)


@router.get('', response_model=PersonList)
async def list_persons(request: Request, offset: int = Query(0, ge=0), limit: int = Query(500, ge=1, le=500),
                       runtime: Runtime = Depends(get_runtime)):
    return PersonList(request_id=request.state.request_id,
                      persons=await runtime.run(runtime.person_service.list, offset, limit))


@router.get('/{person_id}', response_model=PersonResponse)
async def get_person(person_id: str, request: Request, runtime: Runtime = Depends(get_runtime)):
    return PersonResponse(request_id=request.state.request_id,
                          person=await runtime.run(runtime.person_service.get, person_id))


@router.delete('/{person_id}', response_model=Envelope)
async def delete_person(person_id: str, request: Request, runtime: Runtime = Depends(get_runtime)):
    await runtime.run(runtime.person_service.delete, person_id)
    return Envelope(type='delete_result', request_id=request.state.request_id)


@router.post('/{person_id}/faces', response_model=FaceRegistration)
async def register_faces(person_id: str, request: Request, files: list[UploadFile] = File(...),
                         runtime: Runtime = Depends(get_runtime)):
    if not 1 <= len(files) <= 5:
        raise AppError('INVALID_REQUEST', 'Upload 1 to 5 images using the files field.')
    images = []
    for file in files:
        if Path(file.filename or '').suffix.lower() not in ('.jpg', '.jpeg', '.png'):
            raise AppError('INVALID_IMAGE_FORMAT', 'Only jpg/jpeg/png filenames are supported.')
        raw = await file.read(runtime.settings.max_image_bytes + 1)
        await file.close()
        if len(raw) > runtime.settings.max_image_bytes:
            raise AppError('IMAGE_TOO_LARGE', 'Enrollment image is too large.', 413)
        images.append((Path(file.filename).name, raw))
    count = await runtime.run(runtime.person_service.register, person_id, images)
    return FaceRegistration(request_id=request.state.request_id, person_id=person_id, registered_embeddings=count)
