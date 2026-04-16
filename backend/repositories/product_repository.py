"""Repositorio para acceso a la coleccion products."""
import logging

from services.database import db

logger = logging.getLogger(__name__)


class ProductRepository:
    @staticmethod
    async def get_by_id(product_id: str, user_id: str, projection: dict = None) -> dict | None:
        proj = projection or {"_id": 0, "user_id": 0}
        return await db.products.find_one({"id": product_id, "user_id": user_id}, proj)

    @staticmethod
    async def get_paginated(query: dict, skip: int, limit: int) -> list:
        return await db.products.find(query, {"_id": 0, "user_id": 0}).skip(skip).limit(limit).to_list(limit)

    @staticmethod
    async def get_by_supplier(supplier_id: str, user_id: str, query: dict, skip: int, limit: int) -> list:
        full_query = {"supplier_id": supplier_id, "user_id": user_id, **query}
        return await db.products.find(full_query, {"_id": 0, "user_id": 0}).skip(skip).limit(limit).to_list(limit)

    @staticmethod
    async def count(query: dict) -> int:
        return await db.products.count_documents(query)

    @staticmethod
    async def get_categories(user_id: str) -> list:
        return await db.products.distinct("category", {"user_id": user_id, "category": {"$ne": None}})

    @staticmethod
    async def get_brands(query: dict) -> list:
        return await db.products.distinct("brand", query)

    @staticmethod
    async def find_by_ids(product_ids: list, projection: dict = None) -> list:
        proj = projection or {"_id": 0}
        return await db.products.find({"id": {"$in": product_ids}}, proj).to_list(len(product_ids))

    @staticmethod
    async def find_by_ean(user_id: str, ean: str) -> list:
        return await db.products.find({"user_id": user_id, "ean": ean}, {"_id": 0}).to_list(100)

    @staticmethod
    async def update(product_id: str, user_id: str, updates: dict) -> dict | None:
        await db.products.update_one({"id": product_id, "user_id": user_id}, {"$set": updates})
        return await db.products.find_one({"id": product_id}, {"_id": 0, "user_id": 0})

    @staticmethod
    async def update_many(filter_query: dict, updates: dict):
        return await db.products.update_many(filter_query, updates)

    @staticmethod
    async def delete(product_id: str, user_id: str) -> bool:
        result = await db.products.delete_one({"id": product_id, "user_id": user_id})
        return result.deleted_count > 0

    @staticmethod
    async def delete_many(product_ids: list, user_id: str) -> int:
        result = await db.products.delete_many({"id": {"$in": product_ids}, "user_id": user_id})
        return result.deleted_count

    @staticmethod
    async def delete_by_supplier(supplier_id: str) -> int:
        result = await db.products.delete_many({"supplier_id": supplier_id})
        return result.deleted_count

    @staticmethod
    async def aggregate(pipeline: list, limit: int = 1000) -> list:
        return await db.products.aggregate(pipeline).to_list(limit)

    @staticmethod
    async def get_gallery(product_id: str, user_id: str) -> dict | None:
        return await db.products.find_one(
            {"id": product_id, "user_id": user_id}, {"_id": 0, "id": 1, "gallery_images": 1}
        )

    @staticmethod
    async def update_gallery(product_id: str, updates: dict) -> None:
        await db.products.update_one({"id": product_id}, {"$set": updates})

    @staticmethod
    async def find_one(query: dict, projection: dict = None) -> dict | None:
        proj = projection or {"_id": 0}
        return await db.products.find_one(query, proj)

    @staticmethod
    async def find_by_sku(user_id: str, sku: str, projection: dict = None) -> dict | None:
        proj = projection or {"_id": 0, "price": 1}
        return await db.products.find_one({"user_id": user_id, "sku": sku}, proj)

    @staticmethod
    async def find_paginated(query: dict, skip: int, limit: int, projection: dict = None) -> list:
        proj = projection or {"_id": 0}
        return await db.products.find(query, proj).skip(skip).limit(limit).to_list(limit)
