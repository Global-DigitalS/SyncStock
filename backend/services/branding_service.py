"""Servicio de lógica de negocio para configuración de marca (Branding)."""
import logging
import uuid
from datetime import UTC, datetime

from repositories.branding_repository import BrandingRepository

logger = logging.getLogger(__name__)


class BrandingService:
    """Servicio de marca que encapsula la lógica de negocio para la configuración global.

    La marca es un singleton: existe una única configuración de marca para toda la instancia.
    """

    @staticmethod
    async def get_branding() -> dict | None:
        """Obtiene la configuración actual de marca.

        Returns:
            Configuración de marca o None si no existe
        """
        return await BrandingRepository.get_current()

    @staticmethod
    async def update_branding(
        updated_by: str | None = None,
        **kwargs
    ) -> dict:
        """Actualiza la configuración de marca.

        Args:
            updated_by: ID del usuario que realiza la actualización
            **kwargs: Campos de marca a actualizar

        Returns:
            Configuración de marca actualizada

        Raises:
            ValueError: Si no existe configuración de marca
        """
        branding = await BrandingRepository.get_current()
        if not branding:
            raise ValueError("No existe configuración de marca. Usar initialize_branding primero.")

        updates = {**kwargs}
        updates["updated_at"] = datetime.now(UTC).isoformat()
        if updated_by:
            updates["updated_by"] = updated_by

        result = await BrandingRepository.update(updates)
        if not result:
            raise ValueError("Error al actualizar la configuración de marca")

        return result

    @staticmethod
    async def initialize_branding(
        company_name: str,
        primary_color: str,
        secondary_color: str,
        support_email: str,
        created_by: str | None = None,
        **kwargs
    ) -> dict:
        """Inicializa la configuración de marca (primera creación).

        Args:
            company_name: Nombre de la empresa
            primary_color: Color primario en formato hexadecimal
            secondary_color: Color secundario en formato hexadecimal
            support_email: Email de soporte
            created_by: ID del usuario que crea la configuración
            **kwargs: Otros campos de marca (logo_url, company_description, etc.)

        Returns:
            Configuración de marca creada

        Raises:
            ValueError: Si la configuración ya existe
        """
        existing = await BrandingRepository.get_current()
        if existing:
            raise ValueError("La configuración de marca ya existe. Usar update_branding para modificarla.")

        now = datetime.now(UTC).isoformat()
        branding_data = {
            "id": str(uuid.uuid4()),
            "company_name": company_name,
            "primary_color": primary_color,
            "secondary_color": secondary_color,
            "support_email": support_email,
            "created_at": now,
            "updated_at": now,
            "created_by": created_by,
            "updated_by": None,
        }

        # Incluir campos opcionales si están proporcionados
        if "logo_url" in kwargs:
            branding_data["logo_url"] = kwargs["logo_url"]
        if "logo_dark_url" in kwargs:
            branding_data["logo_dark_url"] = kwargs["logo_dark_url"]
        if "favicon_url" in kwargs:
            branding_data["favicon_url"] = kwargs["favicon_url"]
        if "company_description" in kwargs:
            branding_data["company_description"] = kwargs["company_description"]
        if "support_phone" in kwargs:
            branding_data["support_phone"] = kwargs["support_phone"]
        if "social_links" in kwargs:
            branding_data["social_links"] = kwargs["social_links"]
        if "subscription_plans" in kwargs:
            branding_data["subscription_plans"] = kwargs["subscription_plans"]

        return await BrandingRepository.create_or_update(branding_data)

    @staticmethod
    async def get_or_initialize_branding(
        company_name: str = "SyncStock",
        primary_color: str = "#007AFF",
        secondary_color: str = "#5AC8FA",
        support_email: str = "support@syncstock.local",
        **kwargs
    ) -> dict:
        """Obtiene la configuración de marca o la inicializa con valores por defecto.

        Args:
            company_name: Nombre de la empresa (usado si se debe inicializar)
            primary_color: Color primario (usado si se debe inicializar)
            secondary_color: Color secundario (usado si se debe inicializar)
            support_email: Email de soporte (usado si se debe inicializar)
            **kwargs: Otros parámetros de inicialización

        Returns:
            Configuración de marca existente o nueva inicializada
        """
        existing = await BrandingRepository.get_current()
        if existing:
            return existing

        # Inicializar con valores por defecto
        return await BrandingService.initialize_branding(
            company_name=company_name,
            primary_color=primary_color,
            secondary_color=secondary_color,
            support_email=support_email,
            **kwargs
        )

    @staticmethod
    async def exists() -> bool:
        """Verifica si existe configuración de marca.

        Returns:
            True si existe, False en caso contrario
        """
        return await BrandingRepository.exists()

    @staticmethod
    async def update_colors(primary_color: str, secondary_color: str, updated_by: str | None = None) -> dict:
        """Actualiza rápidamente los colores de marca.

        Args:
            primary_color: Nuevo color primario
            secondary_color: Nuevo color secundario
            updated_by: ID del usuario que actualiza

        Returns:
            Configuración de marca actualizada

        Raises:
            ValueError: Si no existe configuración de marca
        """
        return await BrandingService.update_branding(
            updated_by=updated_by,
            primary_color=primary_color,
            secondary_color=secondary_color
        )

    @staticmethod
    async def update_company_info(
        company_name: str | None = None,
        company_description: str | None = None,
        support_email: str | None = None,
        support_phone: str | None = None,
        updated_by: str | None = None
    ) -> dict:
        """Actualiza rápidamente la información de la empresa.

        Args:
            company_name: Nombre de la empresa
            company_description: Descripción de la empresa
            support_email: Email de soporte
            support_phone: Teléfono de soporte
            updated_by: ID del usuario que actualiza

        Returns:
            Configuración de marca actualizada

        Raises:
            ValueError: Si no existe configuración de marca
        """
        updates = {}
        if company_name is not None:
            updates["company_name"] = company_name
        if company_description is not None:
            updates["company_description"] = company_description
        if support_email is not None:
            updates["support_email"] = support_email
        if support_phone is not None:
            updates["support_phone"] = support_phone

        return await BrandingService.update_branding(updated_by=updated_by, **updates)

    @staticmethod
    async def update_logos(
        logo_url: str | None = None,
        logo_dark_url: str | None = None,
        favicon_url: str | None = None,
        updated_by: str | None = None
    ) -> dict:
        """Actualiza rápidamente los logos y favicon.

        Args:
            logo_url: URL del logo
            logo_dark_url: URL del logo en versión oscura
            favicon_url: URL del favicon
            updated_by: ID del usuario que actualiza

        Returns:
            Configuración de marca actualizada

        Raises:
            ValueError: Si no existe configuración de marca
        """
        updates = {}
        if logo_url is not None:
            updates["logo_url"] = logo_url
        if logo_dark_url is not None:
            updates["logo_dark_url"] = logo_dark_url
        if favicon_url is not None:
            updates["favicon_url"] = favicon_url

        return await BrandingService.update_branding(updated_by=updated_by, **updates)

    @staticmethod
    async def update_social_links(
        social_links: dict | None = None,
        updated_by: str | None = None
    ) -> dict:
        """Actualiza rápidamente los enlaces a redes sociales.

        Args:
            social_links: Diccionario con plataforma: URL
            updated_by: ID del usuario que actualiza

        Returns:
            Configuración de marca actualizada

        Raises:
            ValueError: Si no existe configuración de marca
        """
        return await BrandingService.update_branding(
            updated_by=updated_by,
            social_links=social_links
        )

    @staticmethod
    async def update_subscription_plans(
        subscription_plans: list | None = None,
        updated_by: str | None = None
    ) -> dict:
        """Actualiza rápidamente los planes de suscripción.

        Args:
            subscription_plans: Lista de configuraciones de planes
            updated_by: ID del usuario que actualiza

        Returns:
            Configuración de marca actualizada

        Raises:
            ValueError: Si no existe configuración de marca
        """
        return await BrandingService.update_branding(
            updated_by=updated_by,
            subscription_plans=subscription_plans
        )
