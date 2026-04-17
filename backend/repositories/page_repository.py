"""Repositorio para acceso a la colección pages (Landing Page CMS)."""
import logging

from services.database import db

logger = logging.getLogger(__name__)

# Campos que se excluyen en respuestas al cliente
_SAFE_PROJECTION = {"_id": 0}


class PageRepository:
    """Repositorio para operaciones CRUD en la colección de páginas."""

    @staticmethod
    async def get_by_id(page_id: str) -> dict | None:
        """Obtiene una página por su ID."""
        return await db.pages.find_one(
            {"id": page_id},
            _SAFE_PROJECTION
        )

    @staticmethod
    async def get_by_slug(slug: str) -> dict | None:
        """Obtiene una página por su slug único."""
        return await db.pages.find_one(
            {"slug": slug},
            _SAFE_PROJECTION
        )

    @staticmethod
    async def get_all(
        skip: int = 0,
        limit: int = 100,
        filter_query: dict | None = None
    ) -> list:
        """Lista todas las páginas con paginación y filtrado opcional."""
        query = filter_query or {}
        return await db.pages.find(query, _SAFE_PROJECTION).skip(skip).limit(limit).to_list(limit)

    @staticmethod
    async def get_published() -> list:
        """Obtiene todas las páginas publicadas."""
        return await db.pages.find(
            {"is_published": True},
            _SAFE_PROJECTION
        ).to_list(1000)

    @staticmethod
    async def get_public_published() -> list:
        """Obtiene todas las páginas públicas y publicadas."""
        return await db.pages.find(
            {"is_published": True, "is_public": True},
            _SAFE_PROJECTION
        ).to_list(1000)

    @staticmethod
    async def create(data: dict) -> dict:
        """Crea una nueva página."""
        await db.pages.insert_one(data)
        return data

    @staticmethod
    async def update(page_id: str, updates: dict) -> dict | None:
        """Actualiza una página y devuelve el documento actualizado."""
        await db.pages.update_one(
            {"id": page_id},
            {"$set": updates}
        )
        return await db.pages.find_one({"id": page_id}, _SAFE_PROJECTION)

    @staticmethod
    async def update_by_slug(slug: str, updates: dict) -> dict | None:
        """Actualiza una página por slug."""
        await db.pages.update_one(
            {"slug": slug},
            {"$set": updates}
        )
        return await db.pages.find_one({"slug": slug}, _SAFE_PROJECTION)

    @staticmethod
    async def delete(page_id: str) -> bool:
        """Elimina una página por ID."""
        result = await db.pages.delete_one({"id": page_id})
        return result.deleted_count > 0

    @staticmethod
    async def delete_by_slug(slug: str) -> bool:
        """Elimina una página por slug."""
        result = await db.pages.delete_one({"slug": slug})
        return result.deleted_count > 0

    @staticmethod
    async def count(filter_query: dict | None = None) -> int:
        """Cuenta el número de páginas."""
        query = filter_query or {}
        return await db.pages.count_documents(query)

    @staticmethod
    async def exists_slug(slug: str, exclude_id: str | None = None) -> bool:
        """Verifica si un slug ya existe (útil para validación de unicidad)."""
        query = {"slug": slug}
        if exclude_id:
            query["id"] = {"$ne": exclude_id}
        count = await db.pages.count_documents(query)
        return count > 0

    @staticmethod
    async def get_by_page_type(page_type: str, skip: int = 0, limit: int = 100) -> list:
        """Obtiene páginas filtradas por tipo."""
        return await db.pages.find(
            {"page_type": page_type},
            _SAFE_PROJECTION
        ).skip(skip).limit(limit).to_list(limit)

    @staticmethod
    async def search(search_query: str, skip: int = 0, limit: int = 100) -> list:
        """Busca páginas por título o slug."""
        query = {
            "$or": [
                {"title": {"$regex": search_query, "$options": "i"}},
                {"slug": {"$regex": search_query, "$options": "i"}}
            ]
        }
        return await db.pages.find(query, _SAFE_PROJECTION).skip(skip).limit(limit).to_list(limit)

    @staticmethod
    async def update_publication_status(page_id: str, is_published: bool) -> dict | None:
        """Actualiza el estado de publicación de una página."""
        from datetime import UTC, datetime
        updates = {
            "is_published": is_published,
            "updated_at": datetime.now(UTC).isoformat()
        }
        return await PageRepository.update(page_id, updates)

    @staticmethod
    async def bulk_update_status(page_ids: list, is_published: bool) -> int:
        """Actualiza el estado de publicación de múltiples páginas."""
        from datetime import UTC, datetime
        updates = {
            "is_published": is_published,
            "updated_at": datetime.now(UTC).isoformat()
        }
        result = await db.pages.update_many(
            {"id": {"$in": page_ids}},
            {"$set": updates}
        )
        return result.modified_count
