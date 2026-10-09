"""Typed HTTP and WebSocket recognition protocol."""
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.common import Envelope, new_request_id
from app.schemas.person import PersonOut


class FaceBox(BaseModel):
    x: int = Field(ge=0, strict=True)
    y: int = Field(ge=0, strict=True)
    w: int = Field(gt=0, strict=True)
    h: int = Field(gt=0, strict=True)


class RecognitionMeta(BaseModel):
    request_id: str = Field(default_factory=new_request_id, min_length=1, max_length=128)
    device_id: str | None = Field(None, min_length=1, max_length=128)
    session_id: str | None = Field(None, min_length=1, max_length=128)
    face_box: FaceBox | None = None
    stable_frames: int | None = Field(None, ge=1, le=30)


class RecognitionRequest(RecognitionMeta):
    type: Literal['recognize'] = 'recognize'
    timestamp: int | None = None
    image_format: str = 'jpeg'
    image_base64: str = Field(min_length=1)


class Candidate(BaseModel):
    person_id: str
    similarity: float


class MatchInfo(BaseModel):
    similarity: float | None = None
    threshold: float


class Stability(BaseModel):
    confirmed: bool = False
    consistent_frames: int = 0
    confirmed_person_id: str | None = None


class Processing(BaseModel):
    decode_ms: float = 0
    face_detection_ms: float = 0
    embedding_ms: float = 0
    matching_ms: float = 0
    database_ms: float = 0
    total_ms: float = 0


class RecognitionResponse(Envelope):
    type: str = 'recognition_result'
    face_detected: bool = False
    matched: bool = False
    person: PersonOut | None = None
    match: MatchInfo | None = None
    stability: Stability | None = None
    top_k: list[Candidate] | None = None
    processing: Processing | None = None


class ControlMessage(BaseModel):
    type: Literal['ping', 'person_left', 'clear']
    request_id: str = Field(default_factory=new_request_id, min_length=1, max_length=128)
    session_id: str | None = Field(None, min_length=1, max_length=128)
    device_id: str | None = Field(None, min_length=1, max_length=128)


class ControlResponse(Envelope):
    session_id: str | None = None
