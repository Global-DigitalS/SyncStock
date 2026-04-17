"""Rutas de configuración de marca (Branding) del CMS."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from models.branding import BrandingCreate, BrandingResponse, BrandingUpdate
from services.auth import get_superadmin_user
from services.branding_service import BrandingService

router = APIRouter(tags=["branding"])
logger = logging.getLogger(__name__)


# ==================== ENDPOINTS PÚBLICOS ====================

@router.get("/branding", response_model=BrandingResponse)
async def get_branding():
    """Obtiene la configuración actual de marca.

    Este endpoint NO requiere autenticación y es públicamente accesible.

    Returns:
        Configuración de marca

    Raises:
        404: Si no existe configuración de marca
    """
    try:
        branding = await BrandingService.get_branding()
        if not branding:
            raise HTTPException(status_code=404, detail="Configuración de marca no encontrada")
        return branding
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener configuración de marca: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener la configuración de marca")


# ==================== ENDPOINTS ADMINISTRATIVOS ====================

@router.put("/branding", response_model=BrandingResponse)
async def update_branding(
    branding_update: BrandingUpdate,
    current_user: dict = Depends(get_superadmin_user)
):
    """Actualiza la configuración de marca (requiere rol SuperAdmin).

    Este endpoint permite actualizar cualquier campo de la configuración de marca.
    La configuración es un singleton: existe una única configuración global.

    Args:
        branding_update: Datos de marca a actualizar
        current_user: Usuario autenticado (SuperAdmin)

    Returns:
        Configuración de marca actualizada

    Raises:
        404: Si no existe configuración de marca
        400: Si hay errores de validación
    """
    try:
        # Preparar datos de actualización (solo incluir campos no None)
        updates = {}

        if branding_update.logo_url is not None:
            updates["logo_url"] = branding_update.logo_url
        if branding_update.logo_dark_url is not None:
            updates["logo_dark_url"] = branding_update.logo_dark_url
        if branding_update.favicon_url is not None:
            updates["favicon_url"] = branding_update.favicon_url
        if branding_update.primary_color is not None:
            updates["primary_color"] = branding_update.primary_color
        if branding_update.secondary_color is not None:
            updates["secondary_color"] = branding_update.secondary_color
        if branding_update.company_name is not None:
            updates["company_name"] = branding_update.company_name
        if branding_update.company_description is not None:
            updates["company_description"] = branding_update.company_description
        if branding_update.support_email is not None:
            updates["support_email"] = branding_update.support_email
        if branding_update.support_phone is not None:
            updates["support_phone"] = branding_update.support_phone
        if branding_update.social_links is not None:
            updates["social_links"] = branding_update.social_links
        if branding_update.subscription_plans is not None:
            updates["subscription_plans"] = branding_update.subscription_plans

        branding = await BrandingService.update_branding(
            updated_by=current_user.get("id"),
            **updates
        )

        return branding
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al actualizar configuración de marca: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar la configuración de marca")


@router.post("/branding", response_model=BrandingResponse, status_code=201)
async def initialize_branding(
    branding_create: BrandingCreate,
    current_user: dict = Depends(get_superadmin_user)
):
    """Inicializa la configuración de marca por primera vez (requiere rol SuperAdmin).

    Este endpoint solo puede usarse si no existe configuración de marca previa.
    Para modificar una configuración existente, usar PUT /branding.

    Args:
        branding_create: Datos iniciales de marca
        current_user: Usuario autenticado (SuperAdmin)

    Returns:
        Configuración de marca creada

    Raises:
        400: Si ya existe configuración o hay errores de validación
    """
    try:
        branding = await BrandingService.initialize_branding(
            company_name=branding_create.company_name,
            primary_color=branding_create.primary_color,
            secondary_color=branding_create.secondary_color,
            support_email=branding_create.support_email,
            created_by=current_user.get("id"),
            logo_url=branding_create.logo_url,
            logo_dark_url=branding_create.logo_dark_url,
            favicon_url=branding_create.favicon_url,
            company_description=branding_create.company_description,
            support_phone=branding_create.support_phone,
            social_links=branding_create.social_links,
            subscription_plans=branding_create.subscription_plans
        )
        return branding
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al inicializar configuración de marca: {e}")
        raise HTTPException(status_code=500, detail="Error al inicializar la configuración de marca")


# ==================== ENDPOINTS AUXILIARES ====================

@router.put("/branding/colors", response_model=BrandingResponse)
async def update_colors(
    primary_color: str,
    secondary_color: str,
    current_user: dict = Depends(get_superadmin_user)
):
    """Actualiza rápidamente los colores primario y secundario (requiere rol SuperAdmin).

    Args:
        primary_color: Color primario en formato hexadecimal (ej: #FF5733)
        secondary_color: Color secundario en formato hexadecimal (ej: #33FF57)
        current_user: Usuario autenticado (SuperAdmin)

    Returns:
        Configuración de marca actualizada

    Raises:
        404: Si no existe configuración de marca
        400: Si hay errores de validación de colores
    """
    try:
        branding = await BrandingService.update_colors(
            primary_color=primary_color,
            secondary_color=secondary_color,
            updated_by=current_user.get("id")
        )
        return branding
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al actualizar colores: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar colores")


@router.put("/branding/company-info", response_model=BrandingResponse)
async def update_company_info(
    company_name: str | None = None,
    company_description: str | None = None,
    support_email: str | None = None,
    support_phone: str | None = None,
    current_user: dict = Depends(get_superadmin_user)
):
    """Actualiza información de la empresa (requiere rol SuperAdmin).

    Args:
        company_name: Nombre de la empresa
        company_description: Descripción de la empresa
        support_email: Email de soporte
        support_phone: Teléfono de soporte
        current_user: Usuario autenticado (SuperAdmin)

    Returns:
        Configuración de marca actualizada

    Raises:
        404: Si no existe configuración de marca
        400: Si hay errores de validación
    """
    try:
        branding = await BrandingService.update_company_info(
            company_name=company_name,
            company_description=company_description,
            support_email=support_email,
            support_phone=support_phone,
            updated_by=current_user.get("id")
        )
        return branding
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al actualizar información de la empresa: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar información de la empresa")


@router.put("/branding/logos", response_model=BrandingResponse)
async def update_logos(
    logo_url: str | None = None,
    logo_dark_url: str | None = None,
    favicon_url: str | None = None,
    current_user: dict = Depends(get_superadmin_user)
):
    """Actualiza logos y favicon (requiere rol SuperAdmin).

    Args:
        logo_url: URL del logo
        logo_dark_url: URL del logo en versión oscura
        favicon_url: URL del favicon
        current_user: Usuario autenticado (SuperAdmin)

    Returns:
        Configuración de marca actualizada

    Raises:
        404: Si no existe configuración de marca
        400: Si hay errores de validación de URLs
    """
    try:
        branding = await BrandingService.update_logos(
            logo_url=logo_url,
            logo_dark_url=logo_dark_url,
            favicon_url=favicon_url,
            updated_by=current_user.get("id")
        )
        return branding
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al actualizar logos: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar logos")


@router.put("/branding/social-links", response_model=BrandingResponse)
async def update_social_links(
    social_links: dict,
    current_user: dict = Depends(get_superadmin_user)
):
    """Actualiza enlaces a redes sociales (requiere rol SuperAdmin).

    Args:
        social_links: Diccionario con plataforma: URL (ej: {"facebook": "https://...", "twitter": "https://..."})
        current_user: Usuario autenticado (SuperAdmin)

    Returns:
        Configuración de marca actualizada

    Raises:
        404: Si no existe configuración de marca
        400: Si hay errores de validación de URLs
    """
    try:
        branding = await BrandingService.update_social_links(
            social_links=social_links,
            updated_by=current_user.get("id")
        )
        return branding
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al actualizar enlaces sociales: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar enlaces sociales")


@router.put("/branding/subscription-plans", response_model=BrandingResponse)
async def update_subscription_plans(
    subscription_plans: list,
    current_user: dict = Depends(get_superadmin_user)
):
    """Actualiza planes de suscripción (requiere rol SuperAdmin).

    Args:
        subscription_plans: Lista de configuraciones de planes
        current_user: Usuario autenticado (SuperAdmin)

    Returns:
        Configuración de marca actualizada

    Raises:
        404: Si no existe configuración de marca
    """
    try:
        branding = await BrandingService.update_subscription_plans(
            subscription_plans=subscription_plans,
            updated_by=current_user.get("id")
        )
        return branding
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al actualizar planes de suscripción: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar planes de suscripción")
