"""Servicio de lógica de negocio para páginas del CMS."""
import logging
import uuid
from datetime import UTC, datetime

from repositories.page_repository import PageRepository

logger = logging.getLogger(__name__)


class PageService:
    """Servicio de páginas que encapsula la lógica de negocio."""

    @staticmethod
    async def create_page(
        slug: str,
        title: str,
        page_type: str,
        created_by: str | None = None,
        **kwargs
    ) -> dict:
        """Crea una nueva página con validaciones.

        Args:
            slug: Slug único de la página
            title: Título de la página
            page_type: Tipo de página (HOME, FEATURES, PRICING, ABOUT, CONTACT, CUSTOM)
            created_by: ID del usuario que creó la página
            **kwargs: Otros campos de la página (hero_section, content, meta_description, etc.)

        Returns:
            Documento de página creado

        Raises:
            ValueError: Si el slug ya existe o faltan campos requeridos
        """
        if not slug or not title:
            raise ValueError("El slug y el título son requeridos")

        if await PageRepository.exists_slug(slug):
            raise ValueError(f"El slug '{slug}' ya existe")

        now = datetime.now(UTC).isoformat()
        page_data = {
            "id": str(uuid.uuid4()),
            "slug": slug,
            "title": title,
            "page_type": page_type,
            "is_published": kwargs.get("is_published", False),
            "is_public": kwargs.get("is_public", True),
            "created_at": now,
            "updated_at": now,
            "created_by": created_by,
            "updated_by": None,
        }

        # Incluir campos opcionales si están proporcionados
        if "hero_section" in kwargs and kwargs["hero_section"]:
            page_data["hero_section"] = kwargs["hero_section"]
        if "content" in kwargs and kwargs["content"]:
            page_data["content"] = kwargs["content"]
        if "meta_description" in kwargs:
            page_data["meta_description"] = kwargs["meta_description"]
        if "meta_keywords" in kwargs:
            page_data["meta_keywords"] = kwargs["meta_keywords"]

        return await PageRepository.create(page_data)

    @staticmethod
    async def get_page(page_id: str) -> dict | None:
        """Obtiene una página por ID."""
        return await PageRepository.get_by_id(page_id)

    @staticmethod
    async def get_page_by_slug(slug: str) -> dict | None:
        """Obtiene una página por slug."""
        return await PageRepository.get_by_slug(slug)

    @staticmethod
    async def list_pages(
        skip: int = 0,
        limit: int = 100,
        page_type: str | None = None,
        search_query: str | None = None
    ) -> list:
        """Lista páginas con opciones de filtrado.

        Args:
            skip: Número de registros a saltar (paginación)
            limit: Número máximo de registros a retornar
            page_type: Filtrar por tipo de página (opcional)
            search_query: Buscar en título o slug (opcional)

        Returns:
            Lista de páginas
        """
        if search_query:
            return await PageRepository.search(search_query, skip, limit)
        elif page_type:
            return await PageRepository.get_by_page_type(page_type, skip, limit)
        else:
            return await PageRepository.get_all(skip, limit)

    @staticmethod
    async def list_public_pages(skip: int = 0, limit: int = 100) -> list:
        """Lista todas las páginas públicas y publicadas.

        Returns:
            Lista de páginas públicas y publicadas
        """
        return await PageRepository.get_public_published()

    @staticmethod
    async def update_page(
        page_id: str,
        updated_by: str | None = None,
        **kwargs
    ) -> dict | None:
        """Actualiza una página existente.

        Args:
            page_id: ID de la página a actualizar
            updated_by: ID del usuario que actualiza
            **kwargs: Campos a actualizar

        Returns:
            Página actualizada o None si no existe

        Raises:
            ValueError: Si hay conflicto con slug único
        """
        # Verificar que la página existe
        page = await PageRepository.get_by_id(page_id)
        if not page:
            return None

        # Validar slug único si se intenta cambiar
        if "slug" in kwargs and kwargs["slug"] != page.get("slug"):
            if await PageRepository.exists_slug(kwargs["slug"], exclude_id=page_id):
                raise ValueError(f"El slug '{kwargs['slug']}' ya existe")

        updates = {**kwargs}
        updates["updated_at"] = datetime.now(UTC).isoformat()
        if updated_by:
            updates["updated_by"] = updated_by

        return await PageRepository.update(page_id, updates)

    @staticmethod
    async def delete_page(page_id: str) -> bool:
        """Elimina una página por ID.

        Args:
            page_id: ID de la página a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        return await PageRepository.delete(page_id)

    @staticmethod
    async def publish_page(page_id: str, published: bool = True) -> dict | None:
        """Publica o despublica una página.

        Args:
            page_id: ID de la página
            published: True para publicar, False para despublicar

        Returns:
            Página actualizada o None si no existe
        """
        return await PageRepository.update_publication_status(page_id, published)

    @staticmethod
    async def bulk_publish(page_ids: list, published: bool = True) -> int:
        """Publica o despublica múltiples páginas.

        Args:
            page_ids: Lista de IDs de páginas
            published: True para publicar, False para despublicar

        Returns:
            Número de páginas actualizadas
        """
        return await PageRepository.bulk_update_status(page_ids, published)

    @staticmethod
    async def count_pages(page_type: str | None = None) -> int:
        """Cuenta el número de páginas, opcionalmente por tipo.

        Args:
            page_type: Tipo de página para filtrar (opcional)

        Returns:
            Número de páginas
        """
        filter_query = {"page_type": page_type} if page_type else None
        return await PageRepository.count(filter_query)
