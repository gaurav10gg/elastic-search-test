from elasticsearch import AsyncElasticsearch
from app.config import settings
from typing import List


class ElasticSearchClient:
    def __init__(self):
        self.client = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
        self.index_name = settings.ES_PRODUCT_INDEX

    async def create_product_index(self):
        """
        Create the products index with full mapping if it doesn't exist yet.

        ⚠️  If you change the mapping, delete the index and re-run the indexer:
              DELETE /products   (or: curl -X DELETE http://localhost:9200/products)
              python run_indexer.py
        """
        mapping = {
            "mappings": {
                "properties": {
                    "id":          {"type": "keyword"},
                    "name":        {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "exact": {"type": "text", "analyzer": "standard"}
                        },
                    },
                    "color":       {"type": "keyword"},
                    "color_text":  {"type": "text"},
                    "category":    {"type": "text", "analyzer": "standard"},
                    "gender":      {"type": "keyword"},
                    "description": {"type": "text"},
                    "image_url":   {"type": "keyword", "index": False},
                    "status":      {"type": "keyword"},
                    "created_at":  {"type": "date"},
                }
            },
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
            },
        }

        if not await self.client.indices.exists(index=self.index_name):
            await self.client.indices.create(index=self.index_name, body=mapping)
            print(f"✅ Created index: {self.index_name}")

    async def search_products(self, query: str, limit: int = 20) -> List[dict]:
        """
        Ranking logic (highest → lowest priority):
          1. Gender + category + color all match  (e.g. "women navy t-shirt")
          2. Gender + category match              (e.g. "women hoodie")
          3. Category + color cross-field match   (e.g. "navy t-shirt")
          4. Color exact / fuzzy match
          5. Category match alone
          6. Partial / fuzzy fallback on name / description
        """
        q_lower = query.lower()
        gender_boost_clause = None

        if any(w in q_lower for w in ["women", "woman", "female", "ladies", "girl"]):
            gender_boost_clause = {"term": {"gender": {"value": "womens", "boost": 8}}}
        elif any(w in q_lower for w in ["kids", "kid", "child", "children", "youth", "junior"]):
            gender_boost_clause = {"term": {"gender": {"value": "kids", "boost": 8}}}
        elif any(w in q_lower for w in ["men", "man", "male", "guys"]):
            if not any(w in q_lower for w in ["women", "woman"]):
                gender_boost_clause = {"term": {"gender": {"value": "mens", "boost": 8}}}
        elif "unisex" in q_lower:
            gender_boost_clause = {"term": {"gender": {"value": "unisex", "boost": 6}}}

        should_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "color_text^5", "category^4"],
                    "type": "cross_fields",
                    "operator": "and",
                    "boost": 12,
                }
            },
            {
                "multi_match": {
                    "query": query,
                    "fields": ["color_text^5", "category^4", "name^2"],
                    "type": "cross_fields",
                    "operator": "and",
                    "boost": 9,
                }
            },
            {"term": {"color": {"value": query.title(), "boost": 6}}},
            {"match": {"color_text": {"query": query, "fuzziness": "AUTO", "boost": 5}}},
            {"match": {"category": {"query": query, "boost": 4, "fuzziness": "AUTO"}}},
            {"match_phrase": {"name": {"query": query, "boost": 4, "slop": 2}}},
            {"match": {"name": {"query": query, "operator": "and", "boost": 3}}},
            {"match": {"description": {"query": query, "operator": "or", "boost": 1}}},
        ]

        if gender_boost_clause:
            should_clauses.insert(0, gender_boost_clause)

        search_body = {
            "query": {
                "bool": {
                    "filter": [{"term": {"status": "active"}}],
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^2", "color_text^2", "category^2", "description"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "operator": "or",
                            }
                        }
                    ],
                    "should": should_clauses,
                    "minimum_should_match": 0,
                }
            },
            "size": limit,
            "_source": ["id", "image_url"],
            "sort": [
                {"_score": {"order": "desc"}},
                {"created_at": {"order": "desc"}},
            ],
        }

        try:
            response = await self.client.search(
                index=self.index_name,
                body=search_body,
            )
            return [
                {
                    "id": hit["_source"]["id"],
                    "image_url": hit["_source"].get("image_url"),
                }
                for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            print(f"❌ ElasticSearch error: {e}")
            return []

    async def close(self):
        await self.client.close()


es_client = ElasticSearchClient()