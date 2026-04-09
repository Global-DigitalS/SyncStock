import logging

logger = logging.getLogger(__name__)


def sanitize_ean_quotes(value) -> str:
    """Remove single-quote variants that some suppliers prepend/append to EAN values."""
    if value is None:
        return ""
    # ASCII apostrophe + common unicode apostrophe variants
    quote_chars = "'''´`＇"
    return str(value).strip().translate({ord(ch): None for ch in quote_chars})


def normalize_product_data(raw: dict, strip_ean_quotes: bool = False) -> dict:
    mapping = {
        'sku': ['sku', 'codigo', 'code', 'ref', 'referencia', 'reference', 'id', 'product_id', 'partnumber', 'part_number',
                'articulo', 'codigo_articulo', 'cod', 'item_code', 'cod_articulo', 'ref_articulo', 'codigo_producto',
                'product_code', 'item_id', 'article', 'article_id', 'num_art', 'numero_articulo', 'codigoarticulo',
                'codart', 'refart', 'art', 'producto_id', 'id_producto', 'idproducto', 'producto'],
        'name': ['name', 'nombre', 'title', 'titulo', 'product_name', 'descripcion', 'description', 'producto',
                 'articulo_nombre', 'item_name', 'denominacion', 'denominación', 'nombre_producto', 'product',
                 'item', 'nombreprod', 'nombproducto', 'nombre_articulo', 'articulo', 'desc', 'descriptivo'],
        'price': ['price', 'precio', 'pvp', 'cost', 'coste', 'unit_price', 'tarifa', 'importe', 'pricen',
                  'precio_neto', 'net_price', 'preciopvp', 'precioventa', 'precio_venta', 'preciofinal',
                  'precio_final', 'priceunit', 'unitprice', 'precio_unitario', 'pvd', 'pvr', 'eur', 'euro'],
        'stock': ['stock', 'quantity', 'cantidad', 'qty', 'inventory', 'disponible', 'existencias', 'unidades',
                  'disponibilidad', 'units', 'existencia', 'cantstock', 'stockdisponible', 'stock_disponible',
                  'en_stock', 'enstock', 'cantidad_stock', 'total_stock', 'stockactual', 'stock_actual'],
        'category': ['category', 'categoria', 'cat', 'type', 'tipo', 'familia', 'family', 'grupo', 'group',
                     'categorie', 'categoria1', 'cat1', 'groupo', 'seccion', 'sección'],
        'brand': ['brand', 'marca', 'manufacturer', 'fabricante', 'vendor', 'proveedor', 'make', 'brand_name',
                  'nombremarca', 'nombre_marca', 'marcafabricante'],
        'ean': ['ean', 'ean13', 'barcode', 'upc', 'codigo_barras', 'gtin', 'ean_code', 'codigobarras',
                'cod_barras', 'codigo_barra', 'bar_code', 'ean8', 'codean'],
        'weight': ['weight', 'peso', 'kg', 'mass', 'peso_kg', 'pesokg', 'weightkg'],
        'image_url': ['image', 'imagen', 'image_url', 'photo', 'foto', 'picture', 'url_imagen', 'img',
                      'urlimagen', 'imageurl', 'fotografia', 'pic', 'imagen_url', 'url_image', 'link_imagen'],
        'description': ['description', 'descripcion', 'desc', 'details', 'detalles', 'long_description',
                        'short_description', 'descripcion_larga', 'descripcion_corta', 'texto', 'detalle']
    }
    result = {}
    raw_lower = {str(k).lower().strip().replace(' ', '_').replace('-', '_'): v for k, v in raw.items()}
    raw_original_lower = {str(k).lower().strip(): v for k, v in raw.items()}
    # Merge both for more flexible matching
    combined_raw = {**raw_original_lower, **raw_lower}

    logger.debug(f"Normalizing product - columns available: {list(combined_raw.keys())}")

    for field, aliases in mapping.items():
        for alias in aliases:
            if alias in combined_raw and combined_raw[alias]:
                value = combined_raw[alias]
                if field in ['price', 'weight']:
                    try:
                        value = float(str(value).replace(',', '.').replace('€', '').replace('$', '').strip())
                    except Exception:
                        value = 0.0
                elif field == 'stock':
                    try:
                        value = int(float(str(value).replace(',', '.')))
                    except Exception:
                        value = 0
                elif field == 'ean' and strip_ean_quotes:
                    # Remove single quotes from EAN if strip_ean_quotes is enabled
                    value = sanitize_ean_quotes(value)
                result[field] = value
                break

    # Log what was detected
    if not result.get('sku') or not result.get('name'):
        available_cols = list(raw.keys())[:15]
        logger.warning(f"Product missing required fields. SKU: {result.get('sku')}, Name: {result.get('name')}. Available columns: {available_cols}")

    return result


def apply_column_mapping(raw_data: dict, column_mapping: dict, strip_ean_quotes: bool = False) -> dict:
    if not column_mapping:
        return normalize_product_data(raw_data, strip_ean_quotes)
    result = {}
    raw_lower = {str(k).lower().strip(): v for k, v in raw_data.items()}
    raw_original = {str(k).strip(): v for k, v in raw_data.items()}
    field_types = {
        'sku': 'string', 'name': 'string', 'description': 'string',
        'price': 'float', 'price2': 'float', 'stock': 'int',
        'ean': 'string', 'brand': 'string', 'category': 'string',
        'subcategory': 'string', 'subcategory2': 'string',
        'weight': 'float', 'image_url': 'string', 'image_url2': 'string',
        'image_url3': 'string', 'short_description': 'string', 'long_description': 'string'
    }
    for system_field, m in column_mapping.items():
        if not m:
            continue
        columns = [m] if isinstance(m, str) else m if isinstance(m, list) else []
        values = []
        for col in columns:
            if not col:
                continue
            value = raw_original.get(col) or raw_lower.get(col.lower().strip())
            if value is not None and str(value).strip() != '':
                values.append(str(value).strip())
        if values:
            combined_value = ' > '.join(values) if system_field.startswith('category') else ' '.join(values)
            field_type = field_types.get(system_field, 'string')
            try:
                if field_type == 'float':
                    combined_value = float(str(combined_value).replace(',', '.').replace('€', '').replace('$', '').strip())
                elif field_type == 'int':
                    combined_value = int(float(str(combined_value).replace(',', '.')))
                elif field_type == 'string' and system_field == 'ean' and strip_ean_quotes:
                    # Remove single quotes from EAN if strip_ean_quotes is enabled
                    combined_value = sanitize_ean_quotes(combined_value)
            except Exception:
                if field_type in ['float', 'int']:
                    combined_value = 0
            result[system_field] = combined_value
    product = {
        'sku': result.get('sku', ''), 'name': result.get('name', ''),
        'description': result.get('description') or result.get('long_description') or result.get('short_description', ''),
        'price': result.get('price', 0), 'stock': result.get('stock', 0),
        'category': result.get('category', ''), 'brand': result.get('brand', ''),
        'ean': result.get('ean', ''), 'weight': result.get('weight'),
        'image_url': result.get('image_url', '')
    }
    categories = [result.get('category', '')]
    if result.get('subcategory'):
        categories.append(result['subcategory'])
    if result.get('subcategory2'):
        categories.append(result['subcategory2'])
    product['category'] = ' > '.join([c for c in categories if c])
    return product
