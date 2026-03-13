import logging

from sqlmodel import Session, SQLModel, create_engine

from backend import config

logger = logging.getLogger(__name__)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        if not config.settings.database_url:
            logger.warning("Database is not configured yet, skipping database initialization")
            return None
        _engine = create_engine(config.settings.database_url, echo=False)
    return _engine


def init_db():
    engine = get_engine()
    if engine is not None:
        SQLModel.metadata.create_all(engine)


def get_session():
    engine = get_engine()
    if engine is None:
        yield None
        return
    with Session(engine) as session:
        yield session
