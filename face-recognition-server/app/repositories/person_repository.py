"""Person persistence, leaving transaction ownership to the service."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.person import Person
from app.schemas.person import PersonCreate


class PersonRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, person_id: str) -> Person | None:
        return self.session.scalar(select(Person).where(Person.person_id == person_id))

    def list(self, offset: int = 0, limit: int = 500) -> list[Person]:
        return list(self.session.scalars(select(Person).order_by(Person.id).offset(offset).limit(limit)))

    def create(self, profile: PersonCreate) -> Person:
        person = Person(**profile.model_dump())
        self.session.add(person)
        self.session.flush()
        return person

    def delete(self, person: Person) -> None:
        self.session.delete(person)
