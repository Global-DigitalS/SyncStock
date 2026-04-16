"""Repositorio para acceso a la coleccion suppliers."""
import logging

from services.database import db

logger = logging.getLogger(__name__)

# Campos que se excluyen siempre en respuestas al cliente
_SAFE_PROJECTION = {"_id": 0, "ftp_password": 0, "url_password": 0, "user_id": 0}
_INTERNAL_PROJECTION = {"_id": 0}


class SupplierRepository:
    @staticmethod
    async def get_by_id(supplier_id: str, user_id: str) -> dict | None:
        """Devuelve el supplier completo (con passwords) para uso interno."""
        return await db.suppliers.find_one({"id": supplier_id, "user_id": user_id})

    @staticmethod
    async def get_by_id_safe(supplier_id: str, user_id: str) -> dict | None:
        """Devuelve el supplier sin passwords para respuestas al cliente."""
        return await db.suppliers.find_one(
            {"id": supplier_id, "user_id": user_id}, _SAFE_PROJECTION
        )

    @staticmethod
    async def get_all(user_id: str) -> list:
        """Lista todos los suppliers del usuario, sin campos sensibles."""
        return await db.suppliers.find({"user_id": user_id}, _SAFE_PROJECTION).to_list(1000)

    @staticmethod
    async def create(data: dict) -> dict:
        await db.suppliers.insert_one(data)
        return data

    @staticmethod
    async def update(supplier_id: str, user_id: str, updates: dict) -> dict | None:
        """Actualiza y devuelve el supplier sin passwords."""
        await db.suppliers.update_one(
            {"id": supplier_id, "user_id": user_id}, {"$set": updates}
        )
        return await db.suppliers.find_one({"id": supplier_id}, _SAFE_PROJECTION)

    @staticmethod
    async def update_by_id(supplier_id: str, updates: dict) -> None:
        """Actualiza sin verificar user_id (para operaciones internas como sync)."""
        await db.suppliers.update_one({"id": supplier_id}, {"$set": updates})

    @staticmethod
    async def delete(supplier_id: str, user_id: str) -> bool:
        result = await db.suppliers.delete_one({"id": supplier_id, "user_id": user_id})
        if result.deleted_count > 0:
            await db.products.delete_many({"supplier_id": supplier_id})
            return True
        return False

    @staticmethod
    async def count(user_id: str) -> int:
        return await db.suppliers.count_documents({"user_id": user_id})

    @staticmethod
    async def update_product_count(supplier_id: str, now: str) -> None:
        count = await db.products.count_documents({"supplier_id": supplier_id})
        await db.suppliers.update_one(
            {"id": supplier_id},
            {"$set": {"product_count": count, "last_sync": now}}
        )
