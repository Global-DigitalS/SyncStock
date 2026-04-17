"""Rutas de páginas del CMS para administración y acceso público."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from models.page import PageCreate, PageResponse, PageUpdate, PageListResponse
from services.auth import get_admin_user, get_superadmin_user
from services.page_service import PageService

router = APIRouter(prefix="/pages", tags=["pages"])
logger = logging.getLogger(__name__)


# ==================== ENDPOINTS PÚBLICOS ====================

@router.get("/public", response_model=list[PageListResponse])
async def get_public_pages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Obtiene todas las páginas públicas y publicadas.

    Este endpoint NO requiere autenticación.

    Returns:
        Lista de páginas públicas y publicadas
    """
    try:
        pages = await PageService.list_public_pages(skip=skip, limit=limit)
        return pages
    except Exception as e:
        logger.error(f"Error al obtener páginas públicas: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener páginas")


@router.get("/public/{slug}", response_model=PageResponse)
async def get_public_page(slug: str):
    """Obtiene una página pública por slug.

    Este endpoint NO requiere autenticación.

    Args:
        slug: Slug único de la página

    Returns:
        Página solicitada

    Raises:
        404: Si la página no existe, no es pública o no está publicada
    """
    try:
        page = await PageService.get_page_by_slug(slug)
        if not page or not page.get("is_public") or not page.get("is_published"):
            raise HTTPException(status_code=404, detail="Página no encontrada")
        return page
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener página pública {slug}: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener la página")


# ==================== ENDPOINTS ADMINISTRATIVOS ====================

@router.get("", response_model=list[PageListResponse])
async def list_pages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    page_type: str | None = Query(None),
    search: str | None = Query(None),
    current_user: dict = Depends(get_admin_user)
):
    """Lista todas las páginas (requiere rol Admin o SuperAdmin).

    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros
        page_type: Filtrar por tipo de página (opcional)
        search: Buscar en título o slug (opcional)
        current_user: Usuario autenticado (Admin o SuperAdmin)

    Returns:
        Lista de páginas
    """
    try:
        pages = await PageService.list_pages(
            skip=skip,
            limit=limit,
            page_type=page_type,
            search_query=search
        )
        return pages
    except Exception as e:
        logger.error(f"Error al listar páginas: {e}")
        raise HTTPException(status_code=500, detail="Error al listar páginas")


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """Obtiene una página por ID (requiere rol Admin o SuperAdmin).

    Args:
        page_id: ID de la página
        current_user: Usuario autenticado (Admin o SuperAdmin)

    Returns:
        Página solicitada

    Raises:
        404: Si la página no existe
    """
    try:
        page = await PageService.get_page(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Página no encontrada")
        return page
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener página {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener la página")


@router.post("", response_model=PageResponse, status_code=201)
async def create_page(
    page_create: PageCreate,
    current_user: dict = Depends(get_superadmin_user)
):
    """Crea una nueva página (requiere rol SuperAdmin).

    Args:
        page_create: Datos de la nueva página
        current_user: Usuario autenticado (SuperAdmin)

    Returns:
        Página creada

    Raises:
        400: Si hay validación de datos o slug duplicado
    """
    try:
        page = await PageService.create_page(
            slug=page_create.slug,
            title=page_create.title,
            page_type=page_create.page_type.value,
            created_by=current_user.get("id"),
            hero_section=page_create.hero_section,
            content=page_create.content,
            meta_description=page_create.meta_description,
            meta_keywords=page_create.meta_keywords,
            is_published=page_create.is_published,
            is_public=page_create.is_public
        )
        return page
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al crear página: {e}")
        raise HTTPException(status_code=500, detail="Error al crear la página")


@router.put("/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: str,
    page_update: PageUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Actualiza una página (requiere rol Admin o SuperAdmin).

    Args:
        page_id: ID de la página a actualizar
        page_update: Datos a actualizar
        current_user: Usuario autenticado (Admin o SuperAdmin)

    Returns:
        Página actualizada

    Raises:
        404: Si la página no existe
        400: Si hay validación de datos o slug duplicado
    """
    try:
        # Preparar datos de actualización (solo incluir campos no None)
        updates = {}
        if page_update.slug is not None:
            updates["slug"] = page_update.slug
        if page_update.title is not None:
            updates["title"] = page_update.title
        if page_update.page_type is not None:
            updates["page_type"] = page_update.page_type.value
        if page_update.hero_section is not None:
            updates["hero_section"] = page_update.hero_section
        if page_update.content is not None:
            updates["content"] = page_update.content
        if page_update.meta_description is not None:
            updates["meta_description"] = page_update.meta_description
        if page_update.meta_keywords is not None:
            updates["meta_keywords"] = page_update.meta_keywords
        if page_update.is_published is not None:
            updates["is_published"] = page_update.is_published
        if page_update.is_public is not None:
            updates["is_public"] = page_update.is_public

        page = await PageService.update_page(
            page_id,
            updated_by=current_user.get("id"),
            **updates
        )

        if not page:
            raise HTTPException(status_code=404, detail="Página no encontrada")

        return page
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar página {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar la página")


@router.delete("/{page_id}", status_code=204)
async def delete_page(
    page_id: str,
    current_user: dict = Depends(get_superadmin_user)
):
    """Elimina una página (requiere rol SuperAdmin).

    Args:
        page_id: ID de la página a eliminar
        current_user: Usuario autenticado (SuperAdmin)

    Raises:
        404: Si la página no existe
    """
    try:
        deleted = await PageService.delete_page(page_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Página no encontrada")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar página {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar la página")


# ==================== ENDPOINTS AUXILIARES ====================

@router.put("/{page_id}/publish", response_model=PageResponse)
async def publish_page(
    page_id: str,
    published: bool = Query(True),
    current_user: dict = Depends(get_admin_user)
):
    """Publica o despublica una página (requiere rol Admin o SuperAdmin).

    Args:
        page_id: ID de la página
        published: True para publicar, False para despublicar
        current_user: Usuario autenticado (Admin o SuperAdmin)

    Returns:
        Página actualizada

    Raises:
        404: Si la página no existe
    """
    try:
        page = await PageService.publish_page(page_id, published)
        if not page:
            raise HTTPException(status_code=404, detail="Página no encontrada")
        return page
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al cambiar estado de publicación {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al cambiar estado de publicación")


@router.post("/bulk/publish", status_code=200)
async def bulk_publish_pages(
    page_ids: list[str],
    published: bool = Query(True),
    current_user: dict = Depends(get_admin_user)
):
    """Publica o despublica múltiples páginas (requiere rol Admin o SuperAdmin).

    Args:
        page_ids: Lista de IDs de páginas
        published: True para publicar, False para despublicar
        current_user: Usuario autenticado (Admin o SuperAdmin)

    Returns:
        Número de páginas actualizadas
    """
    try:
        count = await PageService.bulk_publish(page_ids, published)
        return {"modified_count": count}
    except Exception as e:
        logger.error(f"Error en actualización masiva: {e}")
        raise HTTPException(status_code=500, detail="Error en actualización masiva")
