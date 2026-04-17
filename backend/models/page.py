from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ==================== ENUMERATIONS ====================

class PageType(str, Enum):
    """Tipos de páginas disponibles en el CMS."""
    HOME = "HOME"
    FEATURES = "FEATURES"
    PRICING = "PRICING"
    ABOUT = "ABOUT"
    CONTACT = "CONTACT"
    CUSTOM = "CUSTOM"


# ==================== HERO SECTION ====================

class HeroSection(BaseModel):
    """Definición de la sección hero de una página."""
    title: str
    subtitle: str | None = None
    image_url: str | None = None
    button_text: str | None = None
    button_link: str | None = None
    background_color: str | None = None


# ==================== PAGE MODELS ====================

class PageCreate(BaseModel):
    """Modelo para crear una nueva página."""
    slug: str = Field(..., description="Slug único de la página (ej: 'home', 'features')")
    title: str = Field(..., description="Título de la página")
    page_type: PageType = Field(..., description="Tipo de página")
    hero_section: HeroSection | None = None
    content: dict[str, Any] | None = Field(default=None, description="Contenido JSON de la página")
    meta_description: str | None = Field(None, description="Descripción meta para SEO")
    meta_keywords: str | None = Field(None, description="Palabras clave meta para SEO")
    is_published: bool = Field(default=False, description="Indicador de publicación")
    is_public: bool = Field(default=True, description="Indicador de visibilidad pública")


class PageUpdate(BaseModel):
    """Modelo para actualizar una página existente."""
    slug: str | None = None
    title: str | None = None
    page_type: PageType | None = None
    hero_section: HeroSection | None = None
    content: dict[str, Any] | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    is_published: bool | None = None
    is_public: bool | None = None


class PageResponse(BaseModel):
    """Modelo de respuesta para una página completa."""
    model_config = {"extra": "ignore"}

    id: str
    slug: str
    title: str
    page_type: PageType
    hero_section: HeroSection | None = None
    content: dict[str, Any] | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    is_published: bool
    is_public: bool
    created_at: str
    updated_at: str
    created_by: str | None = None
    updated_by: str | None = None


class PageListResponse(BaseModel):
    """Modelo de respuesta para listar páginas (versión resumida)."""
    model_config = {"extra": "ignore"}

    id: str
    slug: str
    title: str
    page_type: PageType
    is_published: bool
    is_public: bool
    created_at: str
    updated_at: str
