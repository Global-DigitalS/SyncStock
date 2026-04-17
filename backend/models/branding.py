import re
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ==================== SOCIAL LINKS ====================

class SocialLink(BaseModel):
    """Definición de un enlace a redes sociales."""
    platform: str = Field(..., description="Nombre de la plataforma (ej: 'facebook', 'twitter', 'linkedin')")
    url: str = Field(..., description="URL del perfil en la red social")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validar que la URL sea válida."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('La URL debe comenzar con http:// o https://')
        return v


# ==================== SUBSCRIPTION PLAN ====================

class SubscriptionPlanConfig(BaseModel):
    """Configuración de un plan de suscripción (singleton)."""
    name: str = Field(..., description="Nombre del plan (ej: 'Starter', 'Pro', 'Enterprise')")
    description: str | None = Field(None, description="Descripción corta del plan")
    price: float = Field(..., description="Precio del plan en USD")
    currency: str = Field(default="USD", description="Moneda del precio")
    billing_period: str = Field(default="monthly", description="Período de facturación (monthly, annual)")
    features: list[str] = Field(default_factory=list, description="Lista de características incluidas")


# ==================== BRANDING MODELS ====================

class BrandingBase(BaseModel):
    """Modelo base para la configuración de marca."""
    logo_url: str | None = Field(None, description="URL del logo de la marca")
    logo_dark_url: str | None = Field(None, description="URL del logo en versión oscura")
    favicon_url: str | None = Field(None, description="URL del favicon (16x16, 32x32, 64x64)")
    primary_color: str = Field(..., description="Color primario en formato hexadecimal (ej: #FF5733)")
    secondary_color: str = Field(..., description="Color secundario en formato hexadecimal (ej: #33FF57)")
    company_name: str = Field(..., description="Nombre de la empresa")
    company_description: str | None = Field(None, description="Descripción breve de la empresa")
    support_email: str = Field(..., description="Email de soporte de la empresa")
    support_phone: str | None = Field(None, description="Teléfono de soporte")
    social_links: dict[str, str] | None = Field(
        default=None,
        description="Enlaces a redes sociales como JSON (ej: {\"facebook\": \"https://...\", \"twitter\": \"https://...\"})"
    )
    subscription_plans: list[dict[str, Any]] | None = Field(
        default=None,
        description="Planes de suscripción disponibles como JSON"
    )

    @field_validator('primary_color', 'secondary_color')
    @classmethod
    def validate_color_format(cls, v: str) -> str:
        """Validar que el color esté en formato hexadecimal válido."""
        if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', v):
            raise ValueError('El color debe estar en formato hexadecimal válido (ej: #FF5733 o #F57)')
        return v

    @field_validator('support_email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validar que el email sea válido."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('El email de soporte no es válido')
        return v

    @field_validator('logo_url', 'logo_dark_url', 'favicon_url', mode='before')
    @classmethod
    def validate_url_format(cls, v: Optional[str]) -> Optional[str]:
        """Validar que las URLs sean válidas si se proporcionan."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError('La URL debe ser una cadena de texto')
        if not v.startswith(('http://', 'https://')):
            raise ValueError('La URL debe comenzar con http:// o https://')
        return v


class BrandingCreate(BrandingBase):
    """Modelo para crear una nueva configuración de marca."""
    pass


class BrandingUpdate(BaseModel):
    """Modelo para actualizar una configuración de marca existente."""
    logo_url: str | None = None
    logo_dark_url: str | None = None
    favicon_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    company_name: str | None = None
    company_description: str | None = None
    support_email: str | None = None
    support_phone: str | None = None
    social_links: dict[str, str] | None = None
    subscription_plans: list[dict[str, Any]] | None = None

    @field_validator('primary_color', 'secondary_color')
    @classmethod
    def validate_color_format(cls, v: Optional[str]) -> Optional[str]:
        """Validar que el color esté en formato hexadecimal válido si se proporciona."""
        if v is None:
            return v
        if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', v):
            raise ValueError('El color debe estar en formato hexadecimal válido (ej: #FF5733 o #F57)')
        return v

    @field_validator('support_email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validar que el email sea válido si se proporciona."""
        if v is None:
            return v
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('El email de soporte no es válido')
        return v

    @field_validator('logo_url', 'logo_dark_url', 'favicon_url', mode='before')
    @classmethod
    def validate_url_format(cls, v: Optional[str]) -> Optional[str]:
        """Validar que las URLs sean válidas si se proporcionan."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError('La URL debe ser una cadena de texto')
        if not v.startswith(('http://', 'https://')):
            raise ValueError('La URL debe comenzar con http:// o https://')
        return v


class BrandingResponse(BaseModel):
    """Modelo de respuesta para la configuración de marca completa."""
    model_config = {"extra": "ignore"}

    id: str
    logo_url: str | None = None
    logo_dark_url: str | None = None
    favicon_url: str | None = None
    primary_color: str
    secondary_color: str
    company_name: str
    company_description: str | None = None
    support_email: str
    support_phone: str | None = None
    social_links: dict[str, str] | None = None
    subscription_plans: list[dict[str, Any]] | None = None
    created_at: str
    updated_at: str
    created_by: str | None = None
    updated_by: str | None = None
