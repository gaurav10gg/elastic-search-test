from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Single declarative base shared across all models.
    Alembic's env.py imports this so it can auto-detect schema changes.
    """
    pass