import asyncio
from app.search.indexer import index_all_products

async def main():
    await index_all_products()

if __name__ == "__main__":
    asyncio.run(main())