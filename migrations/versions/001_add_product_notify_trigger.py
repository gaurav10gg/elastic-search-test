def upgrade() -> None:
    # We do NOT create the products table — it's owned by another service.
    # We only add the notify trigger that belongs to our search service.

    op.execute("""
        CREATE OR REPLACE FUNCTION public.notify_product_change()
        RETURNS trigger AS $$
        BEGIN
            PERFORM pg_notify('product_changes', NEW.id::text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS product_upsert_notify ON products;
        CREATE TRIGGER product_upsert_notify
        AFTER INSERT OR UPDATE ON products
        FOR EACH ROW
        EXECUTE FUNCTION public.notify_product_change();
    """)

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS product_upsert_notify ON products;")
    op.execute("DROP FUNCTION IF EXISTS public.notify_product_change();")