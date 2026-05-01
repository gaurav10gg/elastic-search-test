from strawberry.dataloader import DataLoader
from typing import List

from app.graphql.resolvers import resolve_products_by_ids
from app.graphql.schema import Product


async def batch_load_products(keys: List[str]) -> List[Product]:
    return await resolve_products_by_ids(keys)


product_loader = DataLoader(load_fn=batch_load_products)