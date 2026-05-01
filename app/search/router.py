from fastapi import APIRouter, Query, HTTPException
from typing import Dict

from app.search.elasticsearch import es_client
from app.graphql.schema import schema
from app.graphql.dataloaders import product_loader

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def search_products(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
) -> Dict:
    """
    Search products by name, colour, or description.

    Returns:
        {
            "results": [
                {
                    "type":      "product",
                    "id":        "uuid",
                    "label":     "Product Name",
                    "url":       "/products/uuid",
                    "image_url": "https://..."
                }
            ],
            "total": 5
        }
    """
    # Step 1: Elasticsearch → matching product IDs + image_urls
    es_results = await es_client.search_products(query=q, limit=limit)

    if not es_results:
        return {"results": [], "total": 0}

    product_ids = [r["id"] for r in es_results]
    image_url_map = {r["id"]: r["image_url"] for r in es_results}

    # Step 2: GraphQL → fetch name for each id (batched via DataLoader)
    graphql_query = """
        query GetProducts($ids: [String!]!) {
            products(ids: $ids) {
                id
                name
            }
        }
    """

    result = await schema.execute(
        graphql_query,
        variable_values={"ids": product_ids},
        context_value={"product_loader": product_loader},
    )

    if result.errors:
        raise HTTPException(
            status_code=500,
            detail=f"GraphQL error: {result.errors[0].message}",
        )

    # Step 3: Format response
    results = []
    if result.data and result.data.get("products"):
        for product in result.data["products"]:
            pid = product["id"]
            results.append({
                "type":      "product",
                "id":        pid,
                "label":     product["name"],
                "url":       f"/products/{pid}",
                "image_url": image_url_map.get(pid),
            })

    return {"results": results, "total": len(results)}