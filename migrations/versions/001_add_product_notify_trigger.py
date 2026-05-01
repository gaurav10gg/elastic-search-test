"""add product notify trigger

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We do NOT create the products table — it is owned by another service.
    # This migration only installs the LISTEN/NOTIFY plumbing that belongs
    # to our search service.

    # 1. Notification function
    op.execute("""
        CREATE OR REPLACE FUNCTION public.notify_product_change()
        RETURNS trigger AS $$
        BEGIN
            PERFORM pg_notify('product_changes', NEW.id::text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 2. Drop old trigger if exists, then recreate cleanly
    op.execute("DROP TRIGGER IF EXISTS product_upsert_notify ON products;")

    op.execute("""
        CREATE TRIGGER product_upsert_notify
        AFTER INSERT OR UPDATE ON products
        FOR EACH ROW
        EXECUTE FUNCTION public.notify_product_change();
    """)


def downgrade() -> None:
    # Only removes what this migration added — never touches the table itself
    op.execute("DROP TRIGGER IF EXISTS product_upsert_notify ON products;")
    op.execute("DROP FUNCTION IF EXISTS public.notify_product_change();")