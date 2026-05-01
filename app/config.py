from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/product_catalog_db"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ES_PRODUCT_INDEX: str = "products"

    class Config:
        env_file = ".env"


settings = Settings()