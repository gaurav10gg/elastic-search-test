class Product(Base):
    __tablename__ = "products"

    # Tell SQLAlchemy this table is managed externally —
    # Alembic autogenerate will ignore it completely
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(512))
    color: Mapped[str | None] = mapped_column(String(128))
    category: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))