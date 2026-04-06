"""
Rutas de contenido de la landing page para SuperAdmin.
"""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from services.auth import get_superadmin_user
from services.database import db

sub_router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== LANDING PAGE CONTENT ====================

@sub_router.get("/landing/content")
async def get_landing_content():
    """Get landing page content (public endpoint)"""
    try:
        content = await db.app_config.find_one({"type": "landing_content"})
    except Exception:
        logger.warning("No se pudo leer el contenido de la landing de la BD")
        content = None

    # Default content if not configured
    default_content = {
        "hero": {
            "title": "Sincroniza tu inventario con un clic",
            "subtitle": "Conecta proveedores, gestiona catálogos y actualiza tus tiendas online automáticamente. Ahorra horas de trabajo manual cada semana.",
            "cta_primary": "Empezar Gratis",
            "cta_secondary": "Ver Demo",
            "image_url": None
        },
        "features": [
            {
                "icon": "Zap",
                "title": "Sincronización Automática",
                "description": "Actualiza precios, stock y productos en todas tus tiendas sin mover un dedo."
            },
            {
                "icon": "Database",
                "title": "Multi-Proveedor",
                "description": "Importa catálogos de múltiples proveedores en diferentes formatos (CSV, Excel, XML)."
            },
            {
                "icon": "Store",
                "title": "Multi-Tienda",
                "description": "Gestiona WooCommerce, PrestaShop, Shopify y más desde un solo panel."
            },
            {
                "icon": "Calculator",
                "title": "Márgenes Inteligentes",
                "description": "Configura reglas de precios por categoría, proveedor o producto individual."
            },
            {
                "icon": "RefreshCw",
                "title": "CRM Integrado",
                "description": "Sincroniza con Dolibarr y otros ERPs para mantener todo actualizado."
            },
            {
                "icon": "Shield",
                "title": "Datos Seguros",
                "description": "Encriptación de extremo a extremo y backups automáticos diarios."
            }
        ],
        "benefits": {
            "title": "¿Por qué elegir SyncStock?",
            "items": [
                {"stat": "80%", "text": "Menos tiempo en gestión de inventario"},
                {"stat": "0", "text": "Errores de sincronización manual"},
                {"stat": "24/7", "text": "Actualización automática disponible"},
                {"stat": "+500", "text": "Negocios ya confían en nosotros"}
            ]
        },
        "testimonials": [
            {
                "quote": "SyncStock nos ha ahorrado más de 20 horas semanales en gestión de catálogos.",
                "author": "María García",
                "role": "CEO, TechStore",
                "avatar": None
            },
            {
                "quote": "La sincronización con nuestro ERP funciona perfectamente. Muy recomendable.",
                "author": "Carlos López",
                "role": "Director de Operaciones, Distribuciones López",
                "avatar": None
            }
        ],
        "faq": [
            {
                "question": "¿Cuánto tiempo tarda la configuración inicial?",
                "answer": "La mayoría de usuarios están operativos en menos de 15 minutos. Solo necesitas conectar tus proveedores y tiendas."
            },
            {
                "question": "¿Puedo probar antes de pagar?",
                "answer": "¡Por supuesto! Ofrecemos 14 días de prueba gratuita con todas las funciones premium."
            },
            {
                "question": "¿Qué pasa si supero los límites de mi plan?",
                "answer": "Te avisaremos antes de llegar al límite y podrás actualizar tu plan en cualquier momento."
            },
            {
                "question": "¿Ofrecen soporte técnico?",
                "answer": "Sí, todos los planes incluyen soporte por email. Los planes Professional y Enterprise incluyen soporte prioritario 24/7."
            }
        ],
        "cta_final": {
            "title": "¿Listo para automatizar tu negocio?",
            "subtitle": "Únete a cientos de empresas que ya optimizan su gestión de inventario",
            "button_text": "Comenzar Prueba Gratuita"
        },
        "footer": {
            "company_description": "SyncStock es la plataforma líder en sincronización de inventarios para eCommerce.",
            "links": [
                {"label": "Términos", "url": "/terms"},
                {"label": "Privacidad", "url": "/privacy"},
                {"label": "Contacto", "url": "/contact"}
            ],
            "social": {
                "twitter": "",
                "linkedin": "",
                "facebook": ""
            }
        }
    }

    if not content:
        return default_content

    # Merge with defaults to ensure all fields exist
    result = default_content.copy()
    for key in default_content:
        if key in content and content[key]:
            result[key] = content[key]

    return result


@sub_router.put("/admin/landing/content")
async def update_landing_content(data: dict, user: dict = Depends(get_superadmin_user)):
    """Update landing page content"""
    data["type"] = "landing_content"
    data["updated_at"] = datetime.now(UTC).isoformat()

    await db.app_config.update_one(
        {"type": "landing_content"},
        {"$set": data},
        upsert=True
    )

    return {"success": True, "message": "Contenido actualizado"}


@sub_router.get("/admin/landing/content")
async def get_admin_landing_content(user: dict = Depends(get_superadmin_user)):
    """Get landing page content for admin editing"""
    content = await db.app_config.find_one({"type": "landing_content"}, {"_id": 0})
    return content or {}
