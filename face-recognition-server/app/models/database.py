"""SQLAlchemy sessions and SQLite foreign key enforcement."""
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import ROOT


class Base(DeclarativeBase):
    pass


def create_database(url: str):
    parsed = make_url(url)
    kwargs = {}
    if parsed.drivername.startswith('sqlite'):
        kwargs['connect_args'] = {'check_same_thread': False}
        if parsed.database and parsed.database != ':memory:':
            path = Path(parsed.database)
            path = path if path.is_absolute() else ROOT / path
            path.parent.mkdir(parents=True, exist_ok=True)
            parsed = parsed.set(database=str(path))
        elif parsed.database == ':memory:':
            from sqlalchemy.pool import StaticPool
            kwargs['poolclass'] = StaticPool
    engine = create_engine(parsed, **kwargs)
    if parsed.drivername.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def foreign_keys(connection, _record):
            connection.execute('PRAGMA foreign_keys=ON')
    return engine, sessionmaker(engine, expire_on_commit=False)
