import strawberry
from typing import List, Optional


@strawberry.type
class Product:
    id: str
    name: str


@strawberry.type
class Query:

    @strawberry.field
    async def products(self, ids: List[str], info) -> List[Product]:
        loader = info.context["product_loader"]
        return await loader.load_many(ids)

    @strawberry.field
    async def product(self, id: str, info) -> Optional[Product]:
        from app.graphql.resolvers import resolve_product_by_id
        return await resolve_product_by_id(id)


schema = strawberry.Schema(query=Query)