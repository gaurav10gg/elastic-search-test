import re
from sqlalchemy import select

from app.database.connection import AsyncSessionLocal
from app.database.models import Product
from app.search.elasticsearch import es_client
from app.config import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_gender(name: str) -> str:
    """
    Derive gender from product name.
    Returns: "womens" | "mens" | "kids" | "unisex"
    """
    n = name.lower()
    if re.search(r"\b(kid|kids|child|children|youth|junior|toddler|infant|baby)\b", n):
        return "kids"
    if re.search(r"\bwomen'?s?\b|\bfemale\b|\bladies\b|\bgirl\b", n):
        return "womens"
    if re.search(r"\bmen'?s?\b|\bmale\b|\bguy\b", n):
        return "mens"
    if re.search(r"\bunisex\b", n):
        return "unisex"
    return "unisex"


def clean_name_for_search(name: str) -> str:
    """Strip trailing size/color info from parentheses."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()


def _build_doc(product: Product) -> dict:
    """Build the Elasticsearch document body from an ORM Product instance."""
    name = product.name or ""
    color = product.color or ""
    category = product.category or ""
    return {
        "id":          str(product.id),
        "name":        clean_name_for_search(name),
        "color":       color,
        "color_text":  color,
        "category":    category,
        "gender":      extract_gender(name),
        "description": product.description,
        "image_url":   product.image_url,
        "status":      product.status,
        "created_at":  product.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Public indexing functions
# ---------------------------------------------------------------------------

async def index_all_products() -> None:
    """Fetch every active product from Postgres and push to Elasticsearch."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Product).where(Product.status == "active")
        )
        products = result.scalars().all()

    print(f"📦 Indexing {len(products)} products...")

    for product in products:
        await es_client.client.index(
            index=settings.ES_PRODUCT_INDEX,
            id=str(product.id),
            body=_build_doc(product),
        )

    print(f"✅ Indexed {len(products)} products")


async def index_single_product(product_id: str) -> None:
    """
    Fetch one product by UUID and upsert it into Elasticsearch.
    Called by the LISTEN/NOTIFY listener on every INSERT or UPDATE.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

    if not product:
        print(f"⚠️  Product {product_id} not found — skipping index")
        return

    await es_client.client.index(
        index=settings.ES_PRODUCT_INDEX,
        id=str(product.id),
        body=_build_doc(product),
    )
    print(f"✅ Indexed product: {product.id}")