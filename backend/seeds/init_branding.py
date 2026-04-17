"""
Script de inicialización de branding para SyncStock.

Este script crea una configuración de branding predeterminada en MongoDB.
Se ejecuta de forma idempotente: si ya existe un documento de branding,
no lo modifica.

Uso:
    python backend/seeds/init_branding.py
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio backend al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncClient
from config import config


# Datos de branding por defecto de SyncStock
DEFAULT_BRANDING = {
    "company_name": "SyncStock",
    "app_slogan": "Sincronización de Inventario B2B",
    "logo_url": None,
    "logo_dark_url": None,
    "favicon_url": None,
    "primary_color": "#4f46e5",
    "secondary_color": "#0f172a",
    "accent_color": "#10b981",
    "company_description": (
        "Plataforma SaaS B2B para gestión y sincronización automática de catálogos "
        "de proveedores a múltiples tiendas online."
    ),
    "support_email": "support@syncstock.com",
    "support_phone": None,
    "footer_text": (
        "Copyright © 2024 SyncStock. Todos los derechos reservados. "
        "Automatiza la sincronización de tu inventario."
    ),
    "page_title": "SyncStock — Sincronización de Inventario B2B Automatizada",
    "hero_title": "Gestiona tu inventario de forma inteligente",
    "hero_subtitle": (
        "Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos."
    ),
    "social_links": {
        "facebook": "https://facebook.com/syncstock",
        "twitter": "https://twitter.com/syncstock",
        "linkedin": "https://linkedin.com/company/syncstock",
        "instagram": "https://instagram.com/syncstock",
    },
    "subscription_plans": [
        {
            "id": "free",
            "name": "Free",
            "description": "Para probar la plataforma",
            "price_monthly": 0,
            "price_yearly": 0,
            "trial_days": 0,
            "max_suppliers": 2,
            "max_catalogs": 1,
            "max_products": 200,
            "max_stores": 1,
            "features": [
                "2 proveedores",
                "1 catálogo",
                "200 productos",
                "1 tienda",
                "Soporte por email",
            ],
            "is_default": True,
            "sort_order": 0,
        },
        {
            "id": "starter",
            "name": "Starter",
            "description": "Para pequeños negocios",
            "price_monthly": 29,
            "price_yearly": 290,
            "trial_days": 14,
            "max_suppliers": 5,
            "max_catalogs": 3,
            "max_products": 2000,
            "max_stores": 2,
            "features": [
                "5 proveedores",
                "3 catálogos",
                "2.000 productos",
                "2 tiendas",
                "Soporte prioritario",
                "Sincronización automática",
            ],
            "sort_order": 1,
        },
        {
            "id": "professional",
            "name": "Professional",
            "description": "Para negocios en crecimiento",
            "price_monthly": 79,
            "price_yearly": 790,
            "trial_days": 14,
            "max_suppliers": 20,
            "max_catalogs": 10,
            "max_products": 20000,
            "max_stores": 5,
            "features": [
                "20 proveedores",
                "10 catálogos",
                "20.000 productos",
                "5 tiendas",
                "CRM integrado",
                "Soporte 24/7",
                "Sincronización automática",
                "Exportación CSV/Excel",
            ],
            "is_popular": True,
            "sort_order": 2,
        },
        {
            "id": "enterprise",
            "name": "Enterprise",
            "description": "Para grandes empresas",
            "price_monthly": 199,
            "price_yearly": 1990,
            "trial_days": 30,
            "max_suppliers": 9999,
            "max_catalogs": 9999,
            "max_products": 9999999,
            "max_stores": 9999,
            "features": [
                "Proveedores ilimitados",
                "Catálogos ilimitados",
                "Productos ilimitados",
                "Tiendas ilimitadas",
                "8 CRMs: HubSpot, Salesforce, Odoo...",
                "Soporte dedicado 24/7",
                "API personalizada",
                "Facturación personalizada",
            ],
            "sort_order": 3,
        },
    ],
}


async def init_branding():
    """
    Inicializa el documento de branding en MongoDB.

    Si ya existe un documento de branding, no lo modifica (idempotente).
    Si no existe, crea uno con los valores predeterminados de SyncStock.
    """
    # Obtener configuración
    mongo_url = config.get("mongo_url", "mongodb://localhost:27017")
    db_name = config.get("db_name", "syncstock_db")

    print(f"Conectando a MongoDB: {mongo_url}")
    print(f"Base de datos: {db_name}")

    # Crear cliente MongoDB
    client = AsyncClient(mongo_url)

    try:
        db = client[db_name]
        branding_collection = db["branding"]

        # Verificar si ya existe un documento de branding
        existing_branding = await branding_collection.find_one({})

        if existing_branding:
            print(
                "Documento de branding ya existe. No se realiza ningún cambio (idempotente)."
            )
            print(f"  ID: {existing_branding.get('_id')}")
            print(f"  Empresa: {existing_branding.get('company_name')}")
            return True

        # Si no existe, crear uno con los valores predeterminados
        print("Creando documento de branding predeterminado...")
        result = await branding_collection.insert_one(DEFAULT_BRANDING)
        print(f"Documento de branding creado exitosamente.")
        print(f"  ID MongoDB: {result.inserted_id}")
        print(f"  Empresa: {DEFAULT_BRANDING['company_name']}")
        print(f"  Color primario: {DEFAULT_BRANDING['primary_color']}")
        print(f"  Planes de suscripción: {len(DEFAULT_BRANDING['subscription_plans'])}")

        return True

    except Exception as e:
        print(f"Error al inicializar branding: {e}", file=sys.stderr)
        return False

    finally:
        # Cerrar conexión
        client.close()
        print("Conexión a MongoDB cerrada.")


async def main():
    """Función principal del script."""
    success = await init_branding()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
