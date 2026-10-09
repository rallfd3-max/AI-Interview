"""Person profiles deliberately independent of the matching algorithm."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import Envelope


class PersonCreate(BaseModel):
    person_id: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_-]+$')
    name: str = Field(min_length=1, max_length=128)
    student_no: str | None = Field(None, max_length=128)
    school: str | None = Field(None, max_length=256)
    major: str | None = Field(None, max_length=256)
    description: str | None = Field(None, max_length=4000)


class PersonOut(PersonCreate):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime
    updated_at: datetime


class PersonResponse(Envelope):
    type: str = 'person_result'
    person: PersonOut | None = None


class PersonList(Envelope):
    type: str = 'persons_result'
    persons: list[PersonOut] = Field(default_factory=list)


class FaceRegistration(Envelope):
    type: str = 'registration_result'
    person_id: str
    registered_embeddings: int
