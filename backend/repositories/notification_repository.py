"""Repositorio para notificaciones del sistema."""
import logging

from services.database import db

logger = logging.getLogger(__name__)


class NotificationRepository:
    @staticmethod
    async def create(data: dict) -> dict:
        """Inserta una notificación en la base de datos."""
        await db.notifications.insert_one(data)
        return data

    @staticmethod
    async def get_all(user_id: str, skip: int = 0, limit: int = 50) -> list:
        return await db.notifications.find(
            {"user_id": user_id}, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    @staticmethod
    async def count_unread(user_id: str) -> int:
        return await db.notifications.count_documents({"user_id": user_id, "read": False})

    @staticmethod
    async def mark_read(notification_id: str, user_id: str) -> None:
        await db.notifications.update_one(
            {"id": notification_id, "user_id": user_id}, {"$set": {"read": True}}
        )

    @staticmethod
    async def mark_all_read(user_id: str) -> None:
        await db.notifications.update_many({"user_id": user_id}, {"$set": {"read": True}})

    @staticmethod
    async def delete(notification_id: str, user_id: str) -> bool:
        result = await db.notifications.delete_one({"id": notification_id, "user_id": user_id})
        return result.deleted_count > 0

    @staticmethod
    async def find_by_query(user_id: str, extra_query: dict, limit: int = 20) -> list:
        """Busca notificaciones con filtros adicionales además del user_id."""
        full_query = {"user_id": user_id, **extra_query}
        return await db.notifications.find(
            full_query, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
