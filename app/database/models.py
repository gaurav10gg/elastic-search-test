import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Product(Base):
    """
    Read-only ORM representation of the `products` table.

    This table is owned and managed by another service — we only query it.
    Rules:
      - Never use this model to CREATE, ALTER, or DROP the table.
      - Alembic autogenerate is configured to ignore this table entirely
        (see migrations/env.py → include_object).
      - If the other service adds a column you need, just add it here —
        no migration required on our side.
    """

    __tablename__ = "products"

    # extend_existing=True → prevents SQLAlchemy from complaining if this
    # table is already registered on the metadata elsewhere.
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    color: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r}>"