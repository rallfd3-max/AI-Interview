"""Create schema without loading a face model."""
try:
    from . import _bootstrap
except ImportError:
    import _bootstrap
from app.core.config import Settings
from app.models.database import Base, create_database
from app.models.person import Person
from app.models.face_embedding import FaceEmbedding


def main() -> None:
    engine, _ = create_database(Settings().database_url)
    Base.metadata.create_all(engine)
    engine.dispose()
    print('Database initialized (persons, face_embeddings).')


if __name__ == '__main__':
    main()
