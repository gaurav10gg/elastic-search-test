import asyncio

import asyncpg

from app.config import settings


async def listen_for_product_changes() -> None:
    """
    Opens a *dedicated* asyncpg connection (not from the SQLAlchemy pool —
    LISTEN requires a persistent, long-lived connection that must never be
    recycled) and waits for Postgres NOTIFY events on the 'product_changes'
    channel.

    The Postgres trigger sends the affected product's UUID as the payload.
    We call index_single_product() for each notification so Elasticsearch
    stays in sync within milliseconds of any INSERT or UPDATE.

    The import of index_single_product is deferred to inside the function to
    avoid a circular import at module load time.
    """
    from app.search.indexer import index_single_product

    # asyncpg uses the plain postgresql:// scheme (not +asyncpg)
    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn: asyncpg.Connection = await asyncpg.connect(dsn)

    async def on_notify(
        connection: asyncpg.Connection,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        print(f"🔔 Product change detected — id: {payload}")
        try:
            await index_single_product(payload)
            print(f"✅ Re-indexed product: {payload}")
        except Exception as exc:
            # Log but never crash the listener loop
            print(f"❌ Failed to index product {payload}: {exc}")

    await conn.add_listener("product_changes", on_notify)
    print("👂 Listening on Postgres channel: product_changes")

    try:
        # Keep the coroutine alive; asyncpg fires on_notify on the event loop
        # whenever a NOTIFY arrives — no polling required.
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        # Graceful shutdown
        await conn.remove_listener("product_changes", on_notify)
        await conn.close()
        print("🛑 Product change listener stopped")