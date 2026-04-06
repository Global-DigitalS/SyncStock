"""
Rutas de administración para SuperAdmin.
Gestión de branding, planes de suscripción, plantillas de email,
integraciones y configuración del sistema.

Este paquete divide las rutas en sub-módulos para mejor organización.
La variable `router` se exporta para mantener compatibilidad con server.py:
    from routes.admin import router as admin_router
"""
from fastapi import APIRouter

from .branding import sub_router as branding_router
from .content import sub_router as content_router
from .email_templates import sub_router as email_templates_router
from .integrations import sub_router as integrations_router
from .plans import sub_router as plans_router
from .system import sub_router as system_router

router = APIRouter()

router.include_router(branding_router)
router.include_router(content_router)
router.include_router(plans_router)
router.include_router(email_templates_router)
router.include_router(integrations_router)
router.include_router(system_router)
