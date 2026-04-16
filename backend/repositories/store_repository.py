"""Repositorio para woocommerce_configs (tiendas)."""
import logging

from services.database import db

logger = logging.getLogger(__name__)


class StoreRepository:
    @staticmethod
    async def get_by_id(config_id: str, user_id: str) -> dict | None:
        return await db.woocommerce_configs.find_one({"id": config_id, "user_id": user_id})

    @staticmethod
    async def get_by_id_clean(config_id: str, user_id: str) -> dict | None:
        return await db.woocommerce_configs.find_one(
            {"id": config_id, "user_id": user_id}, {"_id": 0}
        )

    @staticmethod
    async def get_all(user_id: str) -> list:
        return await db.woocommerce_configs.find({"user_id": user_id}, {"_id": 0}).to_list(100)

    @staticmethod
    async def create(data: dict) -> dict:
        await db.woocommerce_configs.insert_one(data)
        return data

    @staticmethod
    async def update(config_id: str, user_id: str, updates: dict) -> dict | None:
        existing = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user_id})
        if not existing:
            return None
        await db.woocommerce_configs.update_one({"id": config_id}, {"$set": updates})
        return await db.woocommerce_configs.find_one({"id": config_id}, {"_id": 0})

    @staticmethod
    async def update_connection_status(config_id: str, is_connected: bool) -> None:
        await db.woocommerce_configs.update_one(
            {"id": config_id}, {"$set": {"is_connected": is_connected}}
        )

    @staticmethod
    async def update_sync_result(config_id: str, updates: dict) -> None:
        await db.woocommerce_configs.update_one({"id": config_id}, {"$set": updates})

    @staticmethod
    async def delete(config_id: str, user_id: str) -> bool:
        result = await db.woocommerce_configs.delete_one({"id": config_id, "user_id": user_id})
        return result.deleted_count > 0

    @staticmethod
    async def count(user_id: str) -> int:
        return await db.woocommerce_configs.count_documents({"user_id": user_id})

    @staticmethod
    async def get_active_with_auto_sync() -> list:
        return await db.woocommerce_configs.find({
            "auto_sync_enabled": True,
            "catalog_id": {"$nin": [None, ""]}
        }, {"_id": 0}).to_list(1000)
