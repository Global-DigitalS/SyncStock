"""Repositorio para acceso a la colección branding (Singleton)."""
import logging

from services.database import db

logger = logging.getLogger(__name__)

# Campos que se excluyen en respuestas al cliente
_SAFE_PROJECTION = {"_id": 0}


class BrandingRepository:
    """Repositorio para operaciones con la configuración de marca (singleton).

    La colección branding contiene un único documento con la configuración global
    de marca para la instancia. Se gestiona como singleton.
    """

    @staticmethod
    async def get_current() -> dict | None:
        """Obtiene la configuración actual de marca.

        Retorna el único documento de configuración de marca, o None si no existe.
        """
        return await db.branding.find_one({}, _SAFE_PROJECTION)

    @staticmethod
    async def create_or_update(data: dict) -> dict:
        """Crea o actualiza la configuración de marca.

        Dado que es singleton, verifica si existe un documento.
        Si existe, lo actualiza. Si no, lo crea.

        Args:
            data: Diccionario con los datos de marca a guardar

        Returns:
            El documento de branding actualizado/creado
        """
        existing = await db.branding.find_one({})

        if existing:
            # Actualizar documento existente
            await db.branding.update_one({}, {"$set": data})
        else:
            # Crear nuevo documento
            await db.branding.insert_one(data)

        return await db.branding.find_one({}, _SAFE_PROJECTION)

    @staticmethod
    async def update(updates: dict) -> dict | None:
        """Actualiza la configuración de marca existente.

        Args:
            updates: Diccionario con los campos a actualizar

        Returns:
            El documento actualizado, o None si no existe configuración
        """
        # Verificar que existe un documento
        existing = await db.branding.find_one({})
        if not existing:
            return None

        await db.branding.update_one({}, {"$set": updates})
        return await db.branding.find_one({}, _SAFE_PROJECTION)

    @staticmethod
    async def delete() -> bool:
        """Elimina la configuración de marca.

        Returns:
            True si se eliminó exitosamente, False si no existía
        """
        result = await db.branding.delete_one({})
        return result.deleted_count > 0

    @staticmethod
    async def exists() -> bool:
        """Verifica si existe configuración de marca.

        Returns:
            True si existe, False en caso contrario
        """
        count = await db.branding.count_documents({})
        return count > 0

    @staticmethod
    async def upsert(data: dict) -> dict:
        """Upsert (actualizar o insertar) la configuración de marca.

        Operación atómica que inserta si no existe o actualiza si existe.

        Args:
            data: Diccionario con los datos de marca

        Returns:
            El documento después de la operación
        """
        await db.branding.update_one({}, {"$set": data}, upsert=True)
        return await db.branding.find_one({}, _SAFE_PROJECTION)
