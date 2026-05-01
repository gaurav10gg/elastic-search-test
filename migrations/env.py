def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        # Never autogenerate migrations for externally-owned tables
        include_object=exclude_external_tables,
    )

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=exclude_external_tables,
    )

# Tables owned by other services — Alembic will never touch these
EXTERNAL_TABLES = {"products"}

def exclude_external_tables(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in EXTERNAL_TABLES:
        return False
    return True