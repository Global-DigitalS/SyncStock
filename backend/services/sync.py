import io
import csv
import logging
import uuid
import ftplib
import asyncio
import zipfile
import paramiko
import requests
from datetime import datetime, timezone
from openpyxl import load_workbook
import xlrd
import xmltodict
from woocommerce import API as WooCommerceAPI
from services.database import db
from config import PRICE_CHANGE_THRESHOLD_PERCENT, LOW_STOCK_THRESHOLD

logger = logging.getLogger(__name__)


async def send_realtime_notification(user_id: str, notification: dict):
    """Send notification via WebSocket if user is connected"""
    try:
        # Import here to avoid circular imports
        from server import ws_manager
        await ws_manager.send_to_user(user_id, {
            "type": "notification",
            "data": notification
        })
    except Exception as e:
        logger.debug(f"Could not send realtime notification: {e}")


# ==================== FILE DOWNLOAD ====================

def download_file_from_ftp_sync(supplier: dict) -> bytes:
    schema = supplier.get('ftp_schema', 'ftp').lower()
    host = supplier.get('ftp_host')
    port = supplier.get('ftp_port', 21)
    user = supplier.get('ftp_user', '')
    password = supplier.get('ftp_password', '')
    file_path = supplier.get('ftp_path', '')
    mode = supplier.get('ftp_mode', 'passive')
    if not host or not file_path:
        raise ValueError("FTP host and path are required")
    logger.info(f"Connecting to {schema.upper()}://{host}:{port}{file_path}")
    content = io.BytesIO()
    if schema == 'sftp':
        port = port or 22
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            sftp.getfo(file_path, content)
            logger.info(f"SFTP download completed: {content.tell()} bytes")
        finally:
            sftp.close()
            transport.close()
    else:
        port = port or 21
        ftp = ftplib.FTP_TLS() if schema == 'ftps' else ftplib.FTP()
        try:
            ftp.connect(host, port, timeout=15)
            ftp.login(user or 'anonymous', password or '')
            if schema == 'ftps':
                ftp.prot_p()
            ftp.set_pasv(mode == 'passive')
            logger.info(f"FTP connected, downloading {file_path}")
            ftp.retrbinary(f'RETR {file_path}', content.write)
            logger.info(f"FTP download completed: {content.tell()} bytes")
        finally:
            try:
                ftp.quit()
            except Exception:
                pass
    content.seek(0)
    return content.read()


async def download_file_from_ftp(supplier: dict) -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, download_file_from_ftp_sync, supplier)


def download_file_from_url_sync(url: str) -> bytes:
    logger.info(f"Downloading from URL: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        content = response.content
        logger.info(f"URL download completed: {len(content)} bytes")
        return content
    except requests.exceptions.RequestException as e:
        logger.error(f"URL download failed: {e}")
        raise Exception(f"Error descargando desde URL: {str(e)}")


async def download_file_from_url(url: str) -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, download_file_from_url_sync, url)


# ==================== FILE PARSING ====================

def parse_csv_content(content: bytes) -> list:
    try:
        decoded = content.decode('utf-8')
    except Exception:
        decoded = content.decode('latin-1')
    reader = csv.DictReader(io.StringIO(decoded))
    return list(reader)


def parse_xlsx_content(content: bytes) -> list:
    wb = load_workbook(filename=io.BytesIO(content), read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).lower().strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
    return [dict(zip(headers, row)) for row in rows[1:] if any(row)]


def parse_xls_content(content: bytes) -> list:
    wb = xlrd.open_workbook(file_contents=content)
    ws = wb.sheet_by_index(0)
    headers = [str(ws.cell_value(0, c)).lower().strip() for c in range(ws.ncols)]
    return [{headers[c]: ws.cell_value(r, c) for c in range(ws.ncols)} for r in range(1, ws.nrows)]


def parse_xml_content(content: bytes) -> list:
    try:
        decoded = content.decode('utf-8')
    except Exception:
        decoded = content.decode('latin-1')
    data = xmltodict.parse(decoded)
    for key in ['products', 'items', 'catalog', 'data', 'root']:
        if key in data:
            items = data[key]
            if isinstance(items, dict):
                for subkey in items:
                    if isinstance(items[subkey], list):
                        return items[subkey]
            elif isinstance(items, list):
                return items
    return []


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
                    value = str(value).strip().replace("'", "")
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
            if value is not None and value != '':
                values.append(str(value))
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
                    combined_value = str(combined_value).strip().replace("'", "")
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


# ==================== SUPPLIER SYNC ====================

async def process_supplier_file(supplier: dict, content: bytes) -> dict:
    file_format = supplier.get('file_format', 'csv').lower()
    separator = supplier.get('csv_separator', ';')
    enclosure = supplier.get('csv_enclosure', '"')
    _header_row_raw = supplier.get('csv_header_row', 1)
    header_row = 1 if _header_row_raw is None else int(_header_row_raw)
    column_mapping = supplier.get('column_mapping')
    strip_ean_quotes = supplier.get('strip_ean_quotes', False)
    detected_columns = []

    # Auto-detect ZIP by magic bytes (PK signature) regardless of configured file_format
    if len(content) >= 4 and content[:2] == b'PK':
        file_format = 'zip'

    try:
        if file_format == 'zip':
            # Extract and find compatible files inside the ZIP
            try:
                extracted = extract_zip_files(content)
            except Exception as e:
                return {"imported": 0, "updated": 0, "errors": 0, "message": f"Error al descomprimir ZIP: {e}"}

            if not extracted:
                return {"imported": 0, "updated": 0, "errors": 0, "message": "El archivo ZIP está vacío"}

            logger.info(f"ZIP detectado con {len(extracted)} archivo(s): {list(extracted.keys())}")

            # Collect all compatible flat files (csv, txt, xlsx, xls, xml)
            compatible_exts = ('.csv', '.txt', '.xlsx', '.xls', '.xml')
            compatible_files = [
                (fname, fcontent)
                for fname, fcontent in extracted.items()
                if fname.lower().endswith(compatible_exts)
                and not fname.split('/')[-1].startswith('.')
                and not fname.split('/')[-1].startswith('__')
            ]

            if not compatible_files:
                names = list(extracted.keys())
                return {
                    "imported": 0, "updated": 0, "errors": 0,
                    "message": f"El ZIP no contiene archivos compatibles (csv/xlsx/xls/xml/txt). Archivos encontrados: {names}"
                }

            # If only one compatible file, process it directly
            if len(compatible_files) == 1:
                best_fname, best_content = compatible_files[0]
                best_fmt = 'csv' if best_fname.lower().endswith(('.csv', '.txt')) else best_fname.rsplit('.', 1)[-1].lower()
                logger.info(f"ZIP (único archivo): procesando '{best_fname}' como {best_fmt.upper()}")
                zip_supplier = {**supplier, 'file_format': best_fmt}
                return await process_supplier_file(zip_supplier, best_content)

            # Multiple compatible files: auto-detect roles from filenames and merge
            logger.info(f"ZIP multi-archivo: detectando roles automáticamente para {len(compatible_files)} archivos")
            role_keywords = {
                'stock':    ['stock', 'inventory', 'disponibilidad', 'existencias', 'qty', 'quantity'],
                'prices':   ['price', 'precio', 'tarif', 'coste', 'cost', 'pvp', 'pvd'],
                'products': ['product', 'catalog', 'article', 'catalogo', 'articulo', 'master', 'items'],
            }

            all_file_data = {}
            for fname, fcontent in compatible_files:
                fname_base = fname.split('/')[-1].lower()
                detected_role = 'products'  # default
                for role, keywords in role_keywords.items():
                    if any(kw in fname_base for kw in keywords):
                        detected_role = role
                        break

                # Determine header_row per file (StockFile.txt-style files often have header)
                # Use supplier setting; individual files can override if needed
                file_hdr = header_row
                try:
                    if fname.lower().endswith(('.xlsx', '.xls')):
                        fmt = 'xlsx' if fname.lower().endswith('.xlsx') else 'xls'
                        if fmt == 'xlsx':
                            wb = load_workbook(filename=io.BytesIO(fcontent), read_only=True)
                            ws = wb.active
                            rows = list(ws.iter_rows(values_only=True))
                            hdrs = [str(h).strip() if h else f'col_{i}' for i, h in enumerate(rows[0])]
                            file_rows = [dict(zip(hdrs, r)) for r in rows[1:] if any(r)]
                        else:
                            wb = xlrd.open_workbook(file_contents=fcontent)
                            ws = wb.sheet_by_index(0)
                            hdrs = [str(ws.cell_value(0, c)).strip() or f'col_{c}' for c in range(ws.ncols)]
                            file_rows = [{hdrs[c]: ws.cell_value(r, c) for c in range(ws.ncols)} for r in range(1, ws.nrows)]
                    else:
                        file_rows = parse_text_file(fcontent, separator, file_hdr)
                except Exception as fe:
                    logger.warning(f"  No se pudo parsear {fname}: {fe}")
                    continue

                # Don't overwrite an existing role with fewer rows
                if detected_role not in all_file_data or len(file_rows) > len(all_file_data[detected_role]):
                    all_file_data[detected_role] = file_rows
                logger.info(f"  {fname} → role={detected_role}, filas={len(file_rows)}")

            if not all_file_data:
                return {"imported": 0, "updated": 0, "errors": 0, "message": "No se pudo parsear ningún archivo del ZIP"}

            products_data = all_file_data.get('products', [])
            prices_data   = all_file_data.get('prices', [])
            stock_data    = all_file_data.get('stock', [])

            # Fallback: if no 'products' role detected, use the largest file
            if not products_data:
                largest_role = max(all_file_data, key=lambda r: len(all_file_data[r]))
                products_data = all_file_data[largest_role]

            # Build lookup tables for price and stock
            prices_merge_key = None
            prices_lookup = {}
            if prices_data:
                prices_merge_key = list(prices_data[0].keys())[0] if prices_data else None
                if prices_merge_key:
                    for row in prices_data:
                        k = str(row.get(prices_merge_key, '')).strip()
                        if k:
                            prices_lookup[k] = row

            stock_merge_key = None
            stock_lookup = {}
            if stock_data:
                stock_merge_key = list(stock_data[0].keys())[0] if stock_data else None
                if stock_merge_key:
                    for row in stock_data:
                        k = str(row.get(stock_merge_key, '')).strip()
                        if k:
                            stock_lookup[k] = row

            logger.info(f"ZIP merge: {len(products_data)} productos, {len(prices_lookup)} precios, {len(stock_lookup)} stock")

            # Build detected_columns from a sample merged row (product + prefixed prices/stock)
            # so the ColumnMappingDialog shows the real available columns
            zip_detected_cols = []
            if products_data:
                sample = dict(products_data[0])
                sample_id = str(sample.get(list(sample.keys())[0], '')).strip()
                if prices_merge_key and sample_id in prices_lookup:
                    for k in prices_lookup[sample_id]:
                        if header_row == 0:
                            if k != prices_merge_key:
                                sample[f"prices_{k}"] = prices_lookup[sample_id][k]
                        elif k not in sample:
                            sample[k] = prices_lookup[sample_id][k]
                if stock_merge_key and sample_id in stock_lookup:
                    for k in stock_lookup[sample_id]:
                        if header_row == 0:
                            if k != stock_merge_key:
                                sample[f"stock_{k}"] = stock_lookup[sample_id][k]
                        elif k not in sample:
                            sample[k] = stock_lookup[sample_id][k]
                zip_detected_cols = list(sample.keys())
                await db.suppliers.update_one(
                    {"id": supplier['id']},
                    {"$set": {"detected_columns": zip_detected_cols}}
                )

            # Merge and upsert products
            now = datetime.now(timezone.utc).isoformat()
            imported = 0
            updated = 0
            errors = 0
            needs_mapping = False
            merge_key = list(products_data[0].keys())[0] if products_data else None
            column_mapping = supplier.get('column_mapping')

            for raw in products_data:
                try:
                    prod_id = str(raw.get(merge_key, '')).strip() if merge_key else ''
                    merged = dict(raw)
                    if prod_id and prod_id in prices_lookup:
                        for k, v in prices_lookup[prod_id].items():
                            if header_row == 0:
                                # Headerless files: all files use col_0, col_1, ... so we
                                # prefix prices columns to avoid overwriting product fields
                                if k != prices_merge_key:
                                    merged[f"prices_{k}"] = v
                            elif k not in merged or not merged[k]:
                                merged[k] = v
                    if prod_id and prod_id in stock_lookup:
                        for k, v in stock_lookup[prod_id].items():
                            if header_row == 0:
                                # Same prefix strategy for stock columns
                                if k != stock_merge_key:
                                    merged[f"stock_{k}"] = v
                            elif k not in merged or not merged[k]:
                                merged[k] = v

                    normalized = apply_column_mapping(merged, column_mapping, strip_ean_quotes) if column_mapping else normalize_product_data(merged, strip_ean_quotes)
                    sku = normalized.get('sku') or prod_id
                    name = normalized.get('name', '')
                    if not sku or not name:
                        errors += 1
                        needs_mapping = True
                        continue

                    existing = await db.products.find_one({"sku": sku, "supplier_id": supplier['id']})
                    product_doc = {
                        "sku": sku, "name": name,
                        "description": normalized.get('description'),
                        "price": normalized.get('price', 0),
                        "stock": normalized.get('stock', 0),
                        "category": normalized.get('category'),
                        "brand": normalized.get('brand'),
                        "ean": normalized.get('ean'),
                        "weight": normalized.get('weight'),
                        "image_url": normalized.get('image_url'),
                        "supplier_id": supplier['id'],
                        "supplier_name": supplier["name"],
                        "user_id": supplier["user_id"],
                        "updated_at": now
                    }
                    if existing:
                        await db.products.update_one({"id": existing['id']}, {"$set": {**product_doc, "updated_at": now}})
                        updated += 1
                    else:
                        product_doc["id"] = str(uuid.uuid4())
                        product_doc["created_at"] = now
                        await db.products.insert_one(product_doc)
                        imported += 1
                except Exception as e:
                    logger.error(f"Error procesando producto ZIP: {e}")
                    errors += 1

            msg = f"ZIP procesado: {imported} importados, {updated} actualizados"
            result = {"imported": imported, "updated": updated, "errors": errors, "message": msg,
                      "needs_mapping": needs_mapping, "detected_columns": zip_detected_cols}
            if needs_mapping and imported + updated == 0:
                result["status"] = "needs_mapping"
                result["message"] = (
                    f"El ZIP se procesó pero no se importaron productos. "
                    f"Columnas disponibles: {', '.join(zip_detected_cols[:8])}... "
                    f"Configura el mapeo de columnas o re-aplica la plantilla del proveedor."
                )
            return result

        elif file_format == 'csv':
            try:
                decoded = content.decode('utf-8-sig')
            except Exception:
                try:
                    decoded = content.decode('utf-8')
                except Exception:
                    decoded = content.decode('latin-1')
            lines = decoded.split('\n')
            if header_row > 1:
                lines = lines[header_row-1:]
            if separator == '\\t':
                separator = '\t'
            if header_row == 0:
                # Headerless file: generate positional column names (col_0, col_1, ...)
                first_line = lines[0].rstrip('\r') if lines else ''
                first_row_parsed = list(csv.reader([first_line], delimiter=separator, quotechar=enclosure if enclosure else '"'))
                num_cols = len(first_row_parsed[0]) if first_row_parsed else 0
                fieldnames = [f'col_{i}' for i in range(num_cols)]
                reader = csv.DictReader(lines, fieldnames=fieldnames, delimiter=separator, quotechar=enclosure if enclosure else '"')
            else:
                reader = csv.DictReader(lines, delimiter=separator, quotechar=enclosure if enclosure else '"')
            raw_products = list(reader)
            if raw_products:
                detected_columns = list(raw_products[0].keys())
        elif file_format in ['xlsx', 'xls']:
            if file_format == 'xlsx':
                wb = load_workbook(filename=io.BytesIO(content), read_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
            else:
                wb = xlrd.open_workbook(file_contents=content)
                ws = wb.sheet_by_index(0)
                rows = [[ws.cell_value(r, c) for c in range(ws.ncols)] for r in range(ws.nrows)]
            if not rows:
                return {"imported": 0, "updated": 0, "errors": 0}
            if header_row > 1:
                rows = rows[header_row-1:]
            headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
            detected_columns = headers
            raw_products = [dict(zip(headers, row)) for row in rows[1:] if any(row)]
        elif file_format == 'xml':
            raw_products = parse_xml_content(content)
            if raw_products:
                detected_columns = list(raw_products[0].keys())
        else:
            return {"imported": 0, "updated": 0, "errors": 0, "message": "Unsupported format"}
        if detected_columns:
            await db.suppliers.update_one({"id": supplier['id']}, {"$set": {"detected_columns": detected_columns}})
        now = datetime.now(timezone.utc).isoformat()
        imported = 0
        updated = 0
        errors = 0
        needs_mapping = False
        if not column_mapping and detected_columns:
            col_names_lower = [c.lower().strip().replace(' ', '_').replace('-', '_') for c in detected_columns]
            col_names_simple = [c.lower().strip() for c in detected_columns]
            all_col_variants = col_names_lower + col_names_simple
            
            sku_aliases = ['sku', 'codigo', 'referencia', 'ref', 'reference', 'id', 'cod', 'articulo', 
                          'codigo_articulo', 'product_id', 'item_code', 'code', 'producto']
            name_aliases = ['name', 'nombre', 'title', 'titulo', 'product', 'producto', 'descripcion',
                           'description', 'denominacion', 'item', 'articulo', 'desc']
            
            has_sku = any(alias in all_col_variants for alias in sku_aliases)
            has_name = any(alias in all_col_variants for alias in name_aliases)
            
            if not has_sku or not has_name:
                needs_mapping = True
                logger.warning(f"Supplier {supplier.get('name')}: needs_mapping=True. Columns detected: {detected_columns[:10]}. has_sku={has_sku}, has_name={has_name}")
            if not has_sku or not has_name:
                needs_mapping = True
        for raw in raw_products:
            try:
                normalized = apply_column_mapping(raw, column_mapping, strip_ean_quotes) if column_mapping else normalize_product_data(raw, strip_ean_quotes)
                if not normalized.get('sku') or not normalized.get('name'):
                    errors += 1
                    continue
                existing = await db.products.find_one({"sku": normalized['sku'], "supplier_id": supplier['id']})
                product_doc = {
                    "sku": normalized.get('sku'), "name": normalized.get('name'),
                    "description": normalized.get('description'), "price": normalized.get('price', 0),
                    "stock": normalized.get('stock', 0), "category": normalized.get('category'),
                    "brand": normalized.get('brand'), "ean": normalized.get('ean'),
                    "weight": normalized.get('weight'), "image_url": normalized.get('image_url'),
                    "supplier_id": supplier['id'], "supplier_name": supplier["name"],
                    "user_id": supplier["user_id"], "updated_at": now
                }
                if existing:
                    old_price = existing.get('price', 0)
                    new_price = product_doc['price']
                    # Registrar historial de precios si hay cambio
                    if old_price != new_price and old_price > 0:
                        change_pct = ((new_price - old_price) / old_price) * 100
                        await db.price_history.insert_one({
                            "id": str(uuid.uuid4()), "product_id": existing["id"],
                            "product_name": product_doc["name"], "old_price": old_price,
                            "new_price": new_price, "change_percentage": change_pct,
                            "user_id": supplier["user_id"], "created_at": now
                        })
                        # Notificar si el cambio de precio supera el umbral configurado
                        if abs(change_pct) >= PRICE_CHANGE_THRESHOLD_PERCENT:
                            direction = "subido" if change_pct > 0 else "bajado"
                            await db.notifications.insert_one({
                                "id": str(uuid.uuid4()), "type": "price_change",
                                "message": f"Precio de '{product_doc['name'][:40]}' ha {direction} {abs(change_pct):.1f}% ({old_price:.2f}€ → {new_price:.2f}€)",
                                "product_id": existing["id"], "product_name": product_doc["name"],
                                "user_id": supplier["user_id"], "read": False, "created_at": now
                            })
                    # Notificar cambios de stock
                    old_stock = existing.get('stock', 0)
                    new_stock = product_doc['stock']
                    if old_stock > 0 and new_stock == 0:
                        await db.notifications.insert_one({
                            "id": str(uuid.uuid4()), "type": "stock_out",
                            "message": f"Producto '{product_doc['name'][:40]}' sin stock",
                            "product_id": existing["id"], "product_name": product_doc["name"],
                            "user_id": supplier["user_id"], "read": False, "created_at": now
                        })
                    elif old_stock > LOW_STOCK_THRESHOLD and new_stock <= LOW_STOCK_THRESHOLD and new_stock > 0:
                        await db.notifications.insert_one({
                            "id": str(uuid.uuid4()), "type": "stock_low",
                            "message": f"Producto '{product_doc['name'][:40]}' con stock bajo ({new_stock} uds)",
                            "product_id": existing["id"], "product_name": product_doc["name"],
                            "user_id": supplier["user_id"], "read": False, "created_at": now
                        })
                    await db.products.update_one({"id": existing["id"]}, {"$set": product_doc})
                    updated += 1
                else:
                    product_doc["id"] = str(uuid.uuid4())
                    product_doc["created_at"] = now
                    await db.products.insert_one(product_doc)
                    imported += 1
            except Exception as e:
                logger.error(f"Error processing product: {e}")
                errors += 1
        result = {"imported": imported, "updated": updated, "errors": errors, "detected_columns": detected_columns}
        
        # Provide better feedback about mapping needs
        if needs_mapping:
            result["needs_mapping"] = True
            if errors > 0 and (imported + updated) == 0:
                result["message"] = f"Las columnas detectadas ({', '.join(detected_columns[:5])}...) no coinciden con los nombres estándar. Configura el mapeo de columnas para este proveedor."
                result["status"] = "needs_mapping"
            else:
                result["message"] = "Importación parcial. Se recomienda configurar el mapeo de columnas para mejores resultados."
        elif errors > 0 and (imported + updated) == 0:
            result["message"] = f"No se pudieron importar productos. Verifica el formato del archivo y las columnas: {', '.join(detected_columns[:5])}"
            result["status"] = "error"
        
        return result
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return {"imported": 0, "updated": 0, "errors": 1, "message": str(e), "detected_columns": []}


async def record_sync_history(supplier: dict, result: dict, sync_type: str, duration: float, error_message: str = None):
    """Registrar historial de sincronización"""
    status = "success" if result.get("status") == "success" else "error" if result.get("status") == "error" else "partial"
    if result.get("errors", 0) > 0 and result.get("imported", 0) + result.get("updated", 0) > 0:
        status = "partial"
    
    await db.sync_history.insert_one({
        "id": str(uuid.uuid4()),
        "supplier_id": supplier["id"],
        "supplier_name": supplier["name"],
        "sync_type": sync_type,
        "status": status,
        "imported": result.get("imported", 0),
        "updated": result.get("updated", 0),
        "errors": result.get("errors", 0),
        "duration_seconds": round(duration, 2),
        "error_message": error_message or result.get("message"),
        "user_id": supplier["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })


async def sync_supplier(supplier: dict, sync_type: str = "manual") -> dict:
    connection_type = supplier.get('connection_type', 'ftp')
    if connection_type == 'url':
        if not supplier.get('file_url'):
            return {"status": "skipped", "message": "URL no configurada"}
    else:
        if not supplier.get('ftp_host') or not supplier.get('ftp_path'):
            return {"status": "skipped", "message": "FTP no configurado"}
    
    start_time = datetime.now(timezone.utc)
    try:
        logger.info(f"Syncing supplier: {supplier['name']} (via {connection_type})")
        content = await download_file_from_url(supplier['file_url']) if connection_type == 'url' else await download_file_from_ftp(supplier)
        result = await process_supplier_file(supplier, content)
        now = datetime.now(timezone.utc)
        duration = (now - start_time).total_seconds()
        
        product_count = await db.products.count_documents({"supplier_id": supplier['id']})
        await db.suppliers.update_one({"id": supplier['id']}, {"$set": {"product_count": product_count, "last_sync": now.isoformat()}})
        
        notification = {
            "id": str(uuid.uuid4()), "type": "sync_complete",
            "message": f"Sincronización completada: {supplier['name']} - {result['imported']} nuevos, {result['updated']} actualizados",
            "product_id": None, "product_name": None,
            "user_id": supplier["user_id"], "read": False, "created_at": now.isoformat()
        }
        await db.notifications.insert_one(notification)
        await send_realtime_notification(supplier["user_id"], notification)
        
        final_result = {"status": "success", **result}
        await record_sync_history(supplier, final_result, sync_type, duration)
        logger.info(f"Sync complete for {supplier['name']}: {result}")
        return final_result
    except Exception as e:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.error(f"Error syncing supplier {supplier['name']}: {e}")
        
        notification = {
            "id": str(uuid.uuid4()), "type": "sync_error",
            "message": f"Error en sincronización: {supplier['name']} - {str(e)[:100]}",
            "product_id": None, "product_name": None,
            "user_id": supplier["user_id"], "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
        await send_realtime_notification(supplier["user_id"], notification)
        
        error_result = {"status": "error", "message": str(e), "imported": 0, "updated": 0, "errors": 1}
        await record_sync_history(supplier, error_result, sync_type, duration, str(e))
        return error_result


async def sync_all_suppliers():
    logger.info("Starting scheduled sync for all suppliers...")
    ftp_suppliers = await db.suppliers.find({
        "connection_type": {"$ne": "url"}, 
        "ftp_host": {"$nin": [None, ""]}
    }).to_list(1000)
    url_suppliers = await db.suppliers.find({
        "connection_type": "url", 
        "file_url": {"$nin": [None, ""]}
    }).to_list(1000)
    all_suppliers = ftp_suppliers + url_suppliers
    logger.info(f"Found {len(all_suppliers)} suppliers to sync")
    for supplier in all_suppliers:
        if supplier.get('ftp_paths'):
            await sync_supplier_multifile(supplier, sync_type="scheduled")
        else:
            await sync_supplier(supplier, sync_type="scheduled")
        await asyncio.sleep(2)
    logger.info("Scheduled sync completed")



# ==================== FTP BROWSER ====================

def browse_ftp_sync(config: dict, path: str = "/") -> dict:
    """
    Navega por el servidor FTP/SFTP y lista archivos y carpetas.
    Soporta: FTP, FTPS, SFTP
    """
    schema = config.get('ftp_schema', 'ftp').lower()
    host = config.get('ftp_host')
    port = config.get('ftp_port', 21)
    user = config.get('ftp_user', '')
    password = config.get('ftp_password', '')
    mode = config.get('ftp_mode', 'passive')

    if not host:
        return {"status": "error", "message": "FTP host is required", "files": [], "path": path}

    files = []
    error_message = None
    
    try:
        if schema == 'sftp':
            port = port or 22
            transport = paramiko.Transport((host, port))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            try:
                for attr in sftp.listdir_attr(path):
                    is_dir = attr.st_mode and (attr.st_mode & 0o170000 == 0o040000)
                    file_ext = attr.filename.rsplit('.', 1)[-1].lower() if '.' in attr.filename else ''
                    files.append({
                        "name": attr.filename,
                        "path": f"{path.rstrip('/')}/{attr.filename}",
                        "size": attr.st_size,
                        "size_formatted": format_file_size(attr.st_size),
                        "is_dir": is_dir,
                        "is_supported": file_ext in ['csv', 'xlsx', 'xls', 'xml', 'zip', 'txt'],
                        "extension": file_ext,
                        "modified": str(datetime.fromtimestamp(attr.st_mtime)) if attr.st_mtime else None
                    })
            finally:
                sftp.close()
                transport.close()
        else:
            port = port or 21
            ftp = ftplib.FTP_TLS() if schema == 'ftps' else ftplib.FTP()
            try:
                ftp.connect(host, port, timeout=15)
                ftp.login(user or 'anonymous', password or '')
                if schema == 'ftps':
                    ftp.prot_p()
                ftp.set_pasv(mode == 'passive')
                
                # Intentar usar MLSD primero (más información)
                try:
                    for name, facts in ftp.mlsd(path):
                        if name in ['.', '..']:
                            continue
                        is_dir = facts.get('type') == 'dir'
                        size = int(facts.get('size', 0)) if not is_dir else 0
                        file_ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
                        modified = facts.get('modify', '')
                        if modified and len(modified) >= 14:
                            modified = f"{modified[:4]}-{modified[4:6]}-{modified[6:8]} {modified[8:10]}:{modified[10:12]}"
                        files.append({
                            "name": name,
                            "path": f"{path.rstrip('/')}/{name}",
                            "size": size,
                            "size_formatted": format_file_size(size),
                            "is_dir": is_dir,
                            "is_supported": file_ext in ['csv', 'xlsx', 'xls', 'xml', 'zip', 'txt'],
                            "extension": file_ext,
                            "modified": modified
                        })
                except Exception:
                    # Fallback a DIR si MLSD no está soportado
                    raw_lines = []
                    ftp.dir(path, raw_lines.append)
                    for line in raw_lines:
                        parts = line.split(None, 8)
                        if len(parts) >= 9:
                            name = parts[8]
                            if name in ['.', '..']:
                                continue
                            is_dir = line.startswith('d')
                            size = int(parts[4]) if not is_dir else 0
                            date_str = f"{parts[5]} {parts[6]} {parts[7]}"
                            file_ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
                            files.append({
                                "name": name,
                                "path": f"{path.rstrip('/')}/{name}",
                                "size": size,
                                "size_formatted": format_file_size(size),
                                "is_dir": is_dir,
                                "is_supported": file_ext in ['csv', 'xlsx', 'xls', 'xml', 'zip', 'txt'],
                                "extension": file_ext,
                                "modified": date_str
                            })
            finally:
                try:
                    ftp.quit()
                except Exception:
                    pass
    except ftplib.error_perm as e:
        error_message = f"Error de permisos FTP: {str(e)}"
        logger.error(f"FTP permission error browsing {path}: {e}")
    except Exception as e:
        error_message = f"Error de conexión: {str(e)}"
        logger.error(f"FTP browse error for {path}: {e}")

    # Ordenar: carpetas primero, luego archivos por nombre
    files.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    
    # Calcular estadísticas
    total_files = len([f for f in files if not f["is_dir"]])
    supported_files = len([f for f in files if f.get("is_supported")])
    total_dirs = len([f for f in files if f["is_dir"]])
    
    return {
        "status": "ok" if not error_message else "error",
        "message": error_message,
        "path": path,
        "files": files,
        "stats": {
            "total_files": total_files,
            "supported_files": supported_files,
            "total_dirs": total_dirs
        }
    }


def format_file_size(size: int) -> str:
    """Formatea el tamaño de archivo en formato legible"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


async def browse_ftp_directory(config: dict, path: str = "/") -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, browse_ftp_sync, config, path)


# ==================== MULTI-FILE SYNC ====================

def parse_text_file(content: bytes, separator: str = ";", header_row: int = 1) -> list:
    """Parse a semicolon-delimited text file. header_row=0 means no header (positional col names)."""
    try:
        decoded = content.decode('utf-8-sig', errors='replace')
    except Exception:
        try:
            decoded = content.decode('utf-8', errors='replace')
        except Exception:
            decoded = content.decode('latin-1', errors='replace')
    lines = decoded.strip().split('\n')
    if header_row > 1:
        lines = lines[header_row - 1:]
    if not lines:
        return []
    if separator == '\\t':
        separator = '\t'
    if header_row == 0:
        first_line = lines[0].rstrip('\r') if lines else ''
        first_row_parsed = list(csv.reader([first_line], delimiter=separator, quotechar='"'))
        num_cols = len(first_row_parsed[0]) if first_row_parsed else 0
        fieldnames = [f'col_{i}' for i in range(num_cols)]
        reader = csv.DictReader(lines, fieldnames=fieldnames, delimiter=separator, quotechar='"')
    else:
        reader = csv.DictReader(lines, delimiter=separator, quotechar='"')
    return list(reader)


def extract_zip_files(content: bytes) -> dict:
    """Extract all files from a ZIP archive, returns {filename: bytes}"""
    result = {}
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for info in zf.infolist():
            if not info.is_dir():
                with zf.open(info.filename) as f:
                    result[info.filename] = f.read()
    return result


async def resolve_latest_file(supplier: dict, file_config: dict) -> str:
    """If auto_latest is set, find the latest matching file (e.g. latest ZIP)"""
    file_path = file_config.get('path', '')
    if not file_config.get('auto_latest'):
        return file_path
    
    # Get the directory of the file
    dir_path = '/'.join(file_path.split('/')[:-1]) or '/'
    filename = file_path.split('/')[-1]
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    try:
        result = await browse_ftp_directory(supplier, dir_path)
        if result.get('status') != 'ok':
            return file_path
        
        # Filter files with same extension
        candidates = [f for f in result['files'] if not f['is_dir'] and f['name'].lower().endswith(f'.{ext}')]
        if not candidates:
            return file_path
        
        # Sort by name descending (works for date-based naming like _20260223)
        candidates.sort(key=lambda x: x['name'], reverse=True)
        latest = candidates[0]
        
        if latest['path'] != file_path:
            logger.info(f"Auto-latest: resolved {file_path} -> {latest['path']}")
        
        return latest['path']
    except Exception as e:
        logger.warning(f"Could not resolve latest file for {file_path}: {e}")
        return file_path


async def sync_supplier_multifile(supplier: dict, sync_type: str = "manual") -> dict:
    """Sync supplier with multiple file paths - downloads all, merges by key"""
    ftp_paths = supplier.get('ftp_paths', [])
    if not ftp_paths:
        return await sync_supplier(supplier, sync_type)

    start_time = datetime.now(timezone.utc)
    logger.info(f"Multi-file sync for {supplier['name']}: {len(ftp_paths)} files configured")
    all_file_data = {}
    all_detected_columns = {}

    # Use supplier-level csv_header_row (set by preset) for all file parsing.
    # Per-file header_row in ftp_paths entries is a UI default and may not reflect
    # the actual file format; the preset sets the authoritative value.
    _sup_hdr_raw = supplier.get('csv_header_row', 1)
    supplier_hdr = 1 if _sup_hdr_raw is None else int(_sup_hdr_raw)

    for file_config in ftp_paths:
        file_path = await resolve_latest_file(supplier, file_config)
        role = file_config.get('role', 'products')
        sep = file_config.get('separator', ';')
        label = file_config.get('label', file_path)

        if not file_path:
            continue

        try:
            logger.info(f"  Downloading: {file_path} (role: {role})")
            content = await download_file_from_ftp({**supplier, 'ftp_path': file_path})

            if file_path.lower().endswith('.zip') or (len(content) >= 2 and content[:2] == b'PK'):
                extracted = extract_zip_files(content)
                logger.info(f"  ZIP contains {len(extracted)} files: {list(extracted.keys())}, header_row={supplier_hdr}")
                for fname, fcontent in extracted.items():
                    rows = parse_text_file(fcontent, sep, supplier_hdr)
                    sub_role = role
                    fname_lower = fname.lower()
                    if 'stock' in fname_lower:
                        sub_role = 'stock'
                    elif 'price' in fname_lower and 'qb' not in fname_lower:
                        sub_role = 'prices'
                    elif 'qb' in fname_lower:
                        sub_role = 'prices_qb'
                    elif 'product' in fname_lower:
                        sub_role = 'products'
                    elif 'kit' in fname_lower:
                        sub_role = 'kit'
                    elif 'minqty' in fname_lower:
                        sub_role = 'min_qty'

                    # Keep the file with most rows for each role
                    if sub_role not in all_file_data or len(rows) > len(all_file_data[sub_role]):
                        all_file_data[sub_role] = rows
                        if rows:
                            all_detected_columns[sub_role] = list(rows[0].keys())
                    logger.info(f"    {fname}: {len(rows)} rows, role={sub_role}")
            else:
                rows = parse_text_file(content, sep, supplier_hdr)
                all_file_data[role] = rows
                if rows:
                    all_detected_columns[role] = list(rows[0].keys())
                logger.info(f"  {label}: {len(rows)} rows")

        except Exception as e:
            logger.error(f"  Error downloading {file_path}: {e}")
            continue

    if not all_file_data:
        return {"status": "error", "message": "No se pudo descargar ningún archivo"}

    products_data = all_file_data.get('products', [])
    prices_data = all_file_data.get('prices', [])
    stock_data = all_file_data.get('stock', [])

    if not products_data and prices_data:
        products_data = prices_data

    if not products_data:
        return {"status": "error", "message": "No se encontraron datos de productos"}

    # Detect merge key from products (first column is usually the ID)
    first_row = products_data[0] if products_data else {}
    product_keys = list(first_row.keys())
    merge_key = product_keys[0] if product_keys else None

    # For the merge prefix strategy, reuse the already-computed supplier_hdr.
    multifile_header_row = supplier_hdr

    # Build lookup dictionaries
    prices_lookup = {}
    price_merge_key = None
    if prices_data:
        price_keys = list(prices_data[0].keys()) if prices_data else []
        price_merge_key = price_keys[0] if price_keys else None
        if price_merge_key:
            for row in prices_data:
                key = str(row.get(price_merge_key, '')).strip()
                if key:
                    prices_lookup[key] = row

    stock_lookup = {}
    stock_merge_key = None
    if stock_data:
        stock_keys = list(stock_data[0].keys()) if stock_data else []
        stock_merge_key = stock_keys[0] if stock_keys else None
        if stock_merge_key:
            for row in stock_data:
                key = str(row.get(stock_merge_key, '')).strip()
                if key:
                    stock_lookup[key] = row

    logger.info(f"Merging: {len(products_data)} products, {len(prices_lookup)} prices, {len(stock_lookup)} stock entries")

    now = datetime.now(timezone.utc).isoformat()
    imported = 0
    updated = 0
    errors = 0

    for raw_product in products_data:
        try:
            prod_id = str(raw_product.get(merge_key, '')).strip()
            if not prod_id:
                errors += 1
                continue

            merged = dict(raw_product)
            if prod_id in prices_lookup:
                for k, v in prices_lookup[prod_id].items():
                    if multifile_header_row == 0:
                        if k != price_merge_key:
                            merged[f"prices_{k}"] = v
                    elif k not in merged or not merged[k]:
                        merged[k] = v
            if prod_id in stock_lookup:
                for k, v in stock_lookup[prod_id].items():
                    if multifile_header_row == 0:
                        if k != stock_merge_key:
                            merged[f"stock_{k}"] = v
                    elif k not in merged or not merged[k]:
                        merged[k] = v

            column_mapping = supplier.get('column_mapping')
            if column_mapping:
                normalized = apply_column_mapping(merged, column_mapping)
            else:
                normalized = normalize_product_data(merged)

            sku = normalized.get('sku') or prod_id
            name = normalized.get('name', '')
            if not name:
                errors += 1
                continue

            existing = await db.products.find_one({"sku": sku, "supplier_id": supplier['id']})
            product_doc = {
                "sku": sku, "name": name,
                "description": normalized.get('description'),
                "price": normalized.get('price', 0),
                "stock": normalized.get('stock', 0),
                "category": normalized.get('category'),
                "brand": normalized.get('brand'),
                "ean": normalized.get('ean'),
                "weight": normalized.get('weight'),
                "image_url": normalized.get('image_url'),
                "supplier_id": supplier['id'],
                "supplier_name": supplier["name"],
                "user_id": supplier["user_id"],
                "updated_at": now
            }

            if existing:
                old_price = existing.get('price', 0)
                new_price = product_doc['price']
                if old_price != new_price and old_price > 0:
                    change_pct = ((new_price - old_price) / old_price) * 100
                    await db.price_history.insert_one({
                        "id": str(uuid.uuid4()), "product_id": existing["id"],
                        "product_name": name, "old_price": old_price,
                        "new_price": new_price, "change_percentage": change_pct,
                        "user_id": supplier["user_id"], "created_at": now
                    })
                    # Notificar si el cambio de precio supera el umbral configurado
                    if abs(change_pct) >= PRICE_CHANGE_THRESHOLD_PERCENT:
                        direction = "subido" if change_pct > 0 else "bajado"
                        await db.notifications.insert_one({
                            "id": str(uuid.uuid4()), "type": "price_change",
                            "message": f"Precio de '{name[:40]}' ha {direction} {abs(change_pct):.1f}% ({old_price:.2f}€ → {new_price:.2f}€)",
                            "product_id": existing["id"], "product_name": name,
                            "user_id": supplier["user_id"], "read": False, "created_at": now
                        })
                old_stock = existing.get('stock', 0)
                new_stock = product_doc['stock']
                if old_stock > 0 and new_stock == 0:
                    await db.notifications.insert_one({
                        "id": str(uuid.uuid4()), "type": "stock_out",
                        "message": f"Producto '{name[:40]}' sin stock",
                        "product_id": existing["id"], "product_name": name,
                        "user_id": supplier["user_id"], "read": False, "created_at": now
                    })
                elif old_stock > LOW_STOCK_THRESHOLD and 0 < new_stock <= LOW_STOCK_THRESHOLD:
                    await db.notifications.insert_one({
                        "id": str(uuid.uuid4()), "type": "stock_low",
                        "message": f"Producto '{name[:40]}' con stock bajo ({new_stock} uds)",
                        "product_id": existing["id"], "product_name": name,
                        "user_id": supplier["user_id"], "read": False, "created_at": now
                    })
                await db.products.update_one({"id": existing["id"]}, {"$set": product_doc})
                updated += 1
            else:
                product_doc["id"] = str(uuid.uuid4())
                product_doc["created_at"] = now
                await db.products.insert_one(product_doc)
                imported += 1

        except Exception as e:
            logger.error(f"Error processing multi-file product: {e}")
            errors += 1

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    product_count = await db.products.count_documents({"supplier_id": supplier['id']})

    # Build flat detected_columns list (products + prefixed prices/stock) for the mapping UI
    flat_detected = []
    prod_cols = all_detected_columns.get('products', [])
    flat_detected.extend(prod_cols)
    price_cols = all_detected_columns.get('prices', [])
    if price_cols and multifile_header_row == 0:
        price_key = price_cols[0] if price_cols else None
        flat_detected.extend([f"prices_{c}" for c in price_cols if c != price_key])
    elif price_cols:
        flat_detected.extend([c for c in price_cols if c not in flat_detected])
    stock_cols = all_detected_columns.get('stock', [])
    if stock_cols and multifile_header_row == 0:
        stock_key = stock_cols[0] if stock_cols else None
        flat_detected.extend([f"stock_{c}" for c in stock_cols if c != stock_key])
    elif stock_cols:
        flat_detected.extend([c for c in stock_cols if c not in flat_detected])

    await db.suppliers.update_one({"id": supplier['id']}, {"$set": {
        "product_count": product_count, "last_sync": now,
        "detected_columns": flat_detected if flat_detected else list(all_detected_columns.keys())
    }})

    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "type": "sync_complete",
        "message": f"Sincronización multi-archivo: {supplier['name']} - {imported} nuevos, {updated} actualizados ({len(ftp_paths)} archivos)",
        "product_id": None, "product_name": None,
        "user_id": supplier["user_id"], "read": False, "created_at": now
    })

    final_result = {
        "status": "success", "imported": imported, "updated": updated,
        "errors": errors, "files_processed": len(all_file_data),
        "detected_columns": flat_detected
    }
    await record_sync_history(supplier, final_result, sync_type, duration)
    
    logger.info(f"Multi-file sync complete: {imported} imported, {updated} updated, {errors} errors")
    return final_result


# ==================== WOOCOMMERCE SYNC ====================

def get_woocommerce_client(config: dict) -> WooCommerceAPI:
    return WooCommerceAPI(url=config['store_url'], consumer_key=config['consumer_key'], consumer_secret=config['consumer_secret'], version="wc/v3", timeout=30)


def mask_key(key: str) -> str:
    if len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


def calculate_final_price(base_price: float, product: dict, rules: list) -> float:
    final_price = base_price
    for rule in rules:
        applies = False
        if rule["apply_to"] == "all":
            applies = True
        elif rule["apply_to"] == "category" and product.get("category") == rule.get("apply_to_value"):
            applies = True
        elif rule["apply_to"] == "supplier" and product.get("supplier_id") == rule.get("apply_to_value"):
            applies = True
        elif rule["apply_to"] == "product" and product.get("id") == rule.get("apply_to_value"):
            applies = True
        if applies:
            if rule.get("min_price") and base_price < rule["min_price"]:
                continue
            if rule.get("max_price") and base_price > rule["max_price"]:
                continue
            if rule["rule_type"] == "percentage":
                final_price = base_price * (1 + rule["value"] / 100)
            elif rule["rule_type"] == "fixed":
                final_price = base_price + rule["value"]
            break
    return final_price


async def sync_woocommerce_store_price_stock(config: dict):
    store_name = config.get("name", "Unknown")
    catalog_id = config.get("catalog_id")
    if not catalog_id:
        logger.warning(f"No catalog associated with WooCommerce store {store_name}")
        return
    logger.info(f"Starting price/stock sync for WooCommerce store: {store_name}")
    try:
        wcapi = get_woocommerce_client(config)
        catalog_items = await db.catalog_items.find({"catalog_id": catalog_id, "active": True}).to_list(10000)
        if not catalog_items:
            logger.info(f"No active products in catalog for store {store_name}")
            return
        margin_rules = await db.catalog_margin_rules.find({"catalog_id": catalog_id}).to_list(100)
        wc_products_by_ean = {}
        wc_products_by_sku = {}
        page = 1
        while True:
            response = await asyncio.to_thread(wcapi.get, "products", params={"per_page": 100, "page": page})
            if response.status_code == 200:
                products_batch = response.json()
                if not products_batch:
                    break
                for p in products_batch:
                    for meta in p.get("meta_data", []):
                        if meta.get("key") in ["_global_unique_id", "_gtin", "_ean", "gtin"]:
                            ean_value = meta.get("value")
                            if ean_value:
                                wc_products_by_ean[ean_value] = p["id"]
                                break
                    if p.get("sku"):
                        wc_products_by_sku[p["sku"]] = p["id"]
                page += 1
                if len(products_batch) < 100:
                    break
            else:
                logger.error(f"Error fetching WooCommerce products: {response.text}")
                break
        logger.info(f"Found {len(wc_products_by_ean)} products by EAN, {len(wc_products_by_sku)} by SKU")
        updated = 0
        failed = 0
        for item in catalog_items:
            try:
                product = await db.products.find_one({"id": item["product_id"]})
                if not product:
                    continue
                base_price = item.get("custom_price") or product.get("price", 0)
                final_price = base_price
                for rule in margin_rules:
                    if rule.get("applies_to") == "all":
                        if rule.get("margin_type") == "percentage":
                            final_price = base_price * (1 + rule.get("margin_value", 0) / 100)
                        else:
                            final_price = base_price + rule.get("margin_value", 0)
                        break
                    elif rule.get("applies_to") == "category" and rule.get("category") == product.get("category"):
                        if rule.get("margin_type") == "percentage":
                            final_price = base_price * (1 + rule.get("margin_value", 0) / 100)
                        else:
                            final_price = base_price + rule.get("margin_value", 0)
                        break
                ean = product.get("ean", "")
                sku = product.get("sku", "")
                wc_product_id = wc_products_by_ean.get(ean) if ean else None
                if not wc_product_id and sku:
                    wc_product_id = wc_products_by_sku.get(sku)
                if wc_product_id:
                    update_data = {"regular_price": str(round(final_price, 2)), "stock_quantity": product.get("stock", 0)}
                    response = await asyncio.to_thread(wcapi.put, f"products/{wc_product_id}", update_data)
                    if response.status_code in [200, 201]:
                        updated += 1
                    else:
                        failed += 1
                        logger.warning(f"Failed to update product {ean or sku}: {response.text[:100]}")
            except Exception as e:
                failed += 1
                logger.error(f"Error processing catalog item: {e}")
        now = datetime.now(timezone.utc).isoformat()
        await db.woocommerce_configs.update_one({"id": config["id"]}, {"$set": {"last_sync": now, "products_synced": updated}})
        logger.info(f"WooCommerce sync completed for {store_name}: {updated} updated, {failed} failed")
    except Exception as e:
        logger.error(f"Error syncing WooCommerce store {store_name}: {e}")


async def sync_all_woocommerce_stores():
    logger.info("Starting scheduled WooCommerce sync for all stores...")
    configs = await db.woocommerce_configs.find({
        "auto_sync_enabled": True, 
        "catalog_id": {"$nin": [None, ""]}
    }).to_list(1000)
    logger.info(f"Found {len(configs)} WooCommerce stores with auto-sync enabled")
    for config in configs:
        try:
            await sync_woocommerce_store_price_stock(config)
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error syncing WooCommerce store {config.get('name', config['id'])}: {e}")
    logger.info("Scheduled WooCommerce sync completed")


# ==================== WOOCOMMERCE CATEGORY FUNCTIONS ====================

def get_woocommerce_categories_sync(config: dict) -> list:
    """Get all categories from WooCommerce"""
    wcapi = get_woocommerce_client(config)
    categories = []
    page = 1
    try:
        while True:
            response = wcapi.get("products/categories", params={"per_page": 100, "page": page})
            if response.status_code == 200:
                batch = response.json()
                if not batch:
                    break
                categories.extend(batch)
                page += 1
                if len(batch) < 100:
                    break
            else:
                logger.error(f"Error fetching WooCommerce categories: {response.text[:200]}")
                break
    except Exception as e:
        logger.error(f"WooCommerce get_categories error: {e}")
    return categories


async def get_woocommerce_categories(config: dict) -> list:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_woocommerce_categories_sync, config)


def create_woocommerce_category_sync(config: dict, category_data: dict) -> dict:
    """Create a category in WooCommerce"""
    wcapi = get_woocommerce_client(config)
    try:
        payload = {
            "name": category_data.get("name", ""),
            "parent": category_data.get("parent_id", 0),
            "description": category_data.get("description", "")
        }
        response = wcapi.post("products/categories", payload)
        if response.status_code in [200, 201]:
            cat = response.json()
            return {"status": "success", "category_id": cat.get("id"), "message": "Categoría creada"}
        else:
            return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}


async def create_woocommerce_category(config: dict, category_data: dict) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, create_woocommerce_category_sync, config, category_data)


async def find_or_create_woocommerce_category(config: dict, name: str, parent_id: int = 0, existing_categories: list = None) -> int:
    """Find existing category by name or create it"""
    if existing_categories is None:
        existing_categories = await get_woocommerce_categories(config)
    
    # Search for existing category
    for cat in existing_categories:
        if cat.get("name", "").lower() == name.lower() and cat.get("parent", 0) == parent_id:
            return cat.get("id")
    
    # Create new category
    result = await create_woocommerce_category(config, {"name": name, "parent_id": parent_id})
    if result.get("status") == "success":
        return result.get("category_id")
    return None


async def export_catalog_categories_to_woocommerce(config: dict, catalog_id: str, user_id: str) -> dict:
    """Export catalog categories to WooCommerce store"""
    from services.database import db
    
    # Get catalog categories
    categories = await db.catalog_categories.find(
        {"catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
    ).sort("position", 1).to_list(500)
    
    if not categories:
        return {"status": "warning", "created": 0, "message": "No hay categorías para exportar"}
    
    # Get existing WooCommerce categories
    wc_categories = await get_woocommerce_categories(config)
    
    # Build mapping of our category IDs to WooCommerce category IDs
    category_mapping = {}  # local_id -> wc_id
    created = 0
    errors = []
    
    # Process categories level by level
    max_level = max(cat.get("level", 0) for cat in categories)
    for level in range(max_level + 1):
        level_cats = [c for c in categories if c.get("level", 0) == level]
        for cat in level_cats:
            try:
                wc_parent_id = 0
                if cat.get("parent_id") and cat["parent_id"] in category_mapping:
                    wc_parent_id = category_mapping[cat["parent_id"]]
                
                wc_id = await find_or_create_woocommerce_category(
                    config, cat["name"], wc_parent_id, wc_categories
                )
                
                if wc_id:
                    category_mapping[cat["id"]] = wc_id
                    # Check if it was created (not found in existing)
                    was_existing = any(
                        wc.get("name", "").lower() == cat["name"].lower() and wc.get("parent", 0) == wc_parent_id
                        for wc in wc_categories
                    )
                    if not was_existing:
                        created += 1
                        # Add to existing list to avoid duplicates
                        wc_categories.append({"id": wc_id, "name": cat["name"], "parent": wc_parent_id})
                else:
                    errors.append(f"Error creando categoría: {cat['name']}")
            except Exception as e:
                errors.append(f"Error procesando {cat['name']}: {str(e)[:50]}")
    
    return {
        "status": "success" if not errors else "partial",
        "created": created,
        "total": len(categories),
        "mapped": len(category_mapping),
        "category_mapping": category_mapping,
        "errors": errors[:10]
    }
