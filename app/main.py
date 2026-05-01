import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import close_engine
from app.database.listener import listen_for_product_changes
from app.search.elasticsearch import es_client
from app.search.router import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    print("🚀 Starting server...")

    # SQLAlchemy engine is created lazily on first use — nothing to init here.
    # The pool is configured in connection.py (pool_size, max_overflow, etc.)

    # Ensure the Elasticsearch index exists
    await es_client.create_product_index()

    # Start the LISTEN/NOTIFY background task.
    # We keep a reference so we can cancel it cleanly on shutdown.
    listener_task = asyncio.create_task(
        listen_for_product_changes(),
        name="product-change-listener",
    )

    # Optional: full re-index on every cold start (usually not needed in prod)
    # from app.search.indexer import index_all_products
    # await index_all_products()

    yield  # ── server is running ─────────────────────────────────────────────

    # ── Shutdown ──────────────────────────────────────────────────────────────
    print("🛑 Shutting down...")

    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass  # expected — listener cleaned up its own connection

    await es_client.close()
    await close_engine()   # disposes the SQLAlchemy connection pool


app = FastAPI(
    title="Seller Dashboard Search API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)


@app.get("/")
async def root():
    return {"message": "Seller Dashboard Search API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}