from typing import Any

from pydantic import BaseModel


class ProductBase(BaseModel):
    sku: str
    name: str
    description: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    price: float
    stock: int
    category: str | None = None
    brand: str | None = None
    ean: str | None = None
    weight: float | None = None
    image_url: str | None = None
    gallery_images: list[str] | None = None
    attributes: dict[str, Any] | None = None


class ProductResponse(ProductBase):
    id: str
    supplier_id: str
    supplier_name: str
    created_at: str
    updated_at: str
    is_selected: bool = False
    referencia: str | None = None
    part_number: str | None = None
    asin: str | None = None
    upc: str | None = None
    gtin: str | None = None
    oem: str | None = None
    id_erp: str | None = None
    activado: bool = True
    descatalogado: bool = False
    condicion: str | None = None
    activar_pos: bool = False
    tipo_pack: bool = False
    vender_sin_stock: bool = False
    nuevo: str | None = None
    fecha_disponibilidad: str | None = None
    stock_disponible: int | None = None
    stock_fantasma: int | None = None
    stock_market: int | None = None
    unid_caja: int | None = None
    cantidad_minima: int | None = 0
    dias_entrega: int | None = None
    cantidad_maxima_carrito: int | None = None
    resto_stock: bool = True
    requiere_envio: bool = True
    envio_gratis: bool = False
    gastos_envio: float | None = None
    largo: float | None = 0
    ancho: float | None = 0
    alto: float | None = 0
    tipo_peso: str | None = "kilogram"
    formas_pago: str | None = "todas"
    formas_envio: str | None = "todas"
    permite_actualizar_coste: bool = True
    permite_actualizar_stock: bool = True
    tipo_cheque_regalo: bool = False
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    slug: str | None = None
    cost_price: float | None = None
    compare_at_price: float | None = None
    tax_class: str | None = None
    currency: str | None = "EUR"
    tags: list[str] | None = None
    custom_attributes: list[dict[str, str]] | None = None
    manufacturer: str | None = None
    mpn: str | None = None
    video_url: str | None = None
    country_of_origin: str | None = None
    warranty: str | None = None
    notas_internas: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    price: float | None = None
    stock: int | None = None
    category: str | None = None
    brand: str | None = None
    ean: str | None = None
    weight: float | None = None
    image_url: str | None = None
    gallery_images: list[str] | None = None
    is_selected: bool | None = None
    referencia: str | None = None
    part_number: str | None = None
    asin: str | None = None
    upc: str | None = None
    gtin: str | None = None
    oem: str | None = None
    id_erp: str | None = None
    activado: bool | None = None
    descatalogado: bool | None = None
    condicion: str | None = None
    activar_pos: bool | None = None
    tipo_pack: bool | None = None
    vender_sin_stock: bool | None = None
    nuevo: str | None = None
    fecha_disponibilidad: str | None = None
    stock_disponible: int | None = None
    stock_fantasma: int | None = None
    stock_market: int | None = None
    unid_caja: int | None = None
    cantidad_minima: int | None = None
    dias_entrega: int | None = None
    cantidad_maxima_carrito: int | None = None
    resto_stock: bool | None = None
    requiere_envio: bool | None = None
    envio_gratis: bool | None = None
    gastos_envio: float | None = None
    largo: float | None = None
    ancho: float | None = None
    alto: float | None = None
    tipo_peso: str | None = None
    formas_pago: str | None = None
    formas_envio: str | None = None
    permite_actualizar_coste: bool | None = None
    permite_actualizar_stock: bool | None = None
    tipo_cheque_regalo: bool | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    slug: str | None = None
    cost_price: float | None = None
    compare_at_price: float | None = None
    tax_class: str | None = None
    currency: str | None = None
    tags: list[str] | None = None
    custom_attributes: list[dict[str, str]] | None = None
    manufacturer: str | None = None
    mpn: str | None = None
    video_url: str | None = None
    country_of_origin: str | None = None
    warranty: str | None = None
    notas_internas: str | None = None


class SupplierOffer(BaseModel):
    supplier_id: str
    supplier_name: str
    price: float
    stock: int
    sku: str
    is_best_offer: bool = False
    product_id: str


class UnifiedProductResponse(BaseModel):
    ean: str | None = None
    name: str
    description: str | None = None
    category: str | None = None
    brand: str | None = None
    image_url: str | None = None
    best_price: float
    best_supplier: str
    best_supplier_id: str
    total_stock: int
    supplier_count: int
    suppliers: list[SupplierOffer]
    weight: float | None = None
    short_description: str | None = None
    long_description: str | None = None
