from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import AsyncSessionLocal
from app.database.models import Product as ProductModel
from app.graphql.schema import Product


async def resolve_products_by_ids(ids: List[str]) -> List[Product]:
    """
    Batch-load products by a list of UUIDs.
    Preserves the original ordering so the DataLoader gets results back
    in the same order as the requested keys.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ProductModel).where(
                ProductModel.id.in_(ids),
                ProductModel.status == "active",
            )
        )
        rows = result.scalars().all()

    # Re-order to match the requested id order (DataLoader requirement)
    row_map = {str(row.id): row for row in rows}
    return [
        Product(id=str(row_map[i].id), name=row_map[i].name)
        if i in row_map
        else None
        for i in ids
    ]


async def resolve_product_by_id(product_id: str) -> Optional[Product]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        row = result.scalar_one_or_none()

    if not row:
        return None

    return Product(id=str(row.id), name=row.name)