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

logger = logging.getLogger(__name__)


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


def normalize_product_data(raw: dict) -> dict:
    mapping = {
        'sku': ['sku', 'codigo', 'code', 'ref', 'referencia', 'reference', 'id', 'product_id'],
        'name': ['name', 'nombre', 'title', 'titulo', 'product_name', 'description'],
        'price': ['price', 'precio', 'pvp', 'cost', 'coste', 'unit_price'],
        'stock': ['stock', 'quantity', 'cantidad', 'qty', 'inventory', 'disponible'],
        'category': ['category', 'categoria', 'cat', 'type', 'tipo'],
        'brand': ['brand', 'marca', 'manufacturer', 'fabricante'],
        'ean': ['ean', 'ean13', 'barcode', 'upc', 'codigo_barras'],
        'weight': ['weight', 'peso', 'kg'],
        'image_url': ['image', 'imagen', 'image_url', 'photo', 'foto', 'picture'],
        'description': ['description', 'descripcion', 'desc', 'details', 'detalles']
    }
    result = {}
    raw_lower = {str(k).lower().strip(): v for k, v in raw.items()}
    for field, aliases in mapping.items():
        for alias in aliases:
            if alias in raw_lower and raw_lower[alias]:
                value = raw_lower[alias]
                if field in ['price', 'weight']:
                    try:
                        value = float(str(value).replace(',', '.').replace('€', '').strip())
                    except Exception:
                        value = 0.0
                elif field == 'stock':
                    try:
                        value = int(float(str(value).replace(',', '.')))
                    except Exception:
                        value = 0
                result[field] = value
                break
    return result


def apply_column_mapping(raw_data: dict, column_mapping: dict) -> dict:
    if not column_mapping:
        return normalize_product_data(raw_data)
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
    header_row = supplier.get('csv_header_row', 1) or 1
    column_mapping = supplier.get('column_mapping')
    detected_columns = []
    try:
        if file_format == 'csv':
            try:
                decoded = content.decode('utf-8')
            except Exception:
                decoded = content.decode('latin-1')
            lines = decoded.split('\n')
            if header_row > 1:
                lines = lines[header_row-1:]
            if separator == '\\t':
                separator = '\t'
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
            col_names_lower = [c.lower().strip() for c in detected_columns]
            has_sku = any(x in col_names_lower for x in ['sku', 'codigo', 'referencia', 'ref', 'reference', 'id'])
            has_name = any(x in col_names_lower for x in ['name', 'nombre', 'title', 'titulo', 'product', 'producto'])
            if not has_sku or not has_name:
                needs_mapping = True
        for raw in raw_products:
            try:
                normalized = apply_column_mapping(raw, column_mapping) if column_mapping else normalize_product_data(raw)
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
                    if existing.get('price') != product_doc['price'] and existing.get('price', 0) > 0:
                        await db.price_history.insert_one({
                            "id": str(uuid.uuid4()), "product_id": existing["id"],
                            "product_name": product_doc["name"], "old_price": existing.get('price', 0),
                            "new_price": product_doc['price'],
                            "change_percentage": ((product_doc['price'] - existing.get('price', 0)) / existing.get('price', 1)) * 100,
                            "user_id": supplier["user_id"], "created_at": now
                        })
                    if existing.get('stock', 0) > 0 and product_doc['stock'] == 0:
                        await db.notifications.insert_one({
                            "id": str(uuid.uuid4()), "type": "stock_out",
                            "message": f"Producto '{product_doc['name']}' sin stock",
                            "product_id": existing["id"], "product_name": product_doc["name"],
                            "user_id": supplier["user_id"], "read": False, "created_at": now
                        })
                    elif existing.get('stock', 0) > 5 and product_doc['stock'] <= 5 and product_doc['stock'] > 0:
                        await db.notifications.insert_one({
                            "id": str(uuid.uuid4()), "type": "stock_low",
                            "message": f"Producto '{product_doc['name']}' con stock bajo ({product_doc['stock']} uds)",
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
        if needs_mapping and errors > 0 and (imported + updated) == 0:
            result["message"] = "Se detectaron columnas pero no se pudieron importar productos. Configura el mapeo de columnas."
            result["needs_mapping"] = True
        return result
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return {"imported": 0, "updated": 0, "errors": 1, "message": str(e), "detected_columns": []}


async def sync_supplier(supplier: dict) -> dict:
    connection_type = supplier.get('connection_type', 'ftp')
    if connection_type == 'url':
        if not supplier.get('file_url'):
            return {"status": "skipped", "message": "URL no configurada"}
    else:
        if not supplier.get('ftp_host') or not supplier.get('ftp_path'):
            return {"status": "skipped", "message": "FTP no configurado"}
    try:
        logger.info(f"Syncing supplier: {supplier['name']} (via {connection_type})")
        content = await download_file_from_url(supplier['file_url']) if connection_type == 'url' else await download_file_from_ftp(supplier)
        result = await process_supplier_file(supplier, content)
        now = datetime.now(timezone.utc).isoformat()
        product_count = await db.products.count_documents({"supplier_id": supplier['id']})
        await db.suppliers.update_one({"id": supplier['id']}, {"$set": {"product_count": product_count, "last_sync": now}})
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "type": "sync_complete",
            "message": f"Sincronización completada: {supplier['name']} - {result['imported']} nuevos, {result['updated']} actualizados",
            "product_id": None, "product_name": None,
            "user_id": supplier["user_id"], "read": False, "created_at": now
        })
        logger.info(f"Sync complete for {supplier['name']}: {result}")
        return {"status": "success", **result}
    except Exception as e:
        logger.error(f"Error syncing supplier {supplier['name']}: {e}")
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "type": "sync_error",
            "message": f"Error en sincronización: {supplier['name']} - {str(e)[:100]}",
            "product_id": None, "product_name": None,
            "user_id": supplier["user_id"], "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return {"status": "error", "message": str(e)}


async def sync_all_suppliers():
    logger.info("Starting scheduled sync for all suppliers...")
    ftp_suppliers = await db.suppliers.find({"connection_type": {"$ne": "url"}, "ftp_host": {"$ne": None, "$ne": ""}, "ftp_path": {"$ne": None, "$ne": ""}}).to_list(1000)
    url_suppliers = await db.suppliers.find({"connection_type": "url", "file_url": {"$ne": None, "$ne": ""}}).to_list(1000)
    all_suppliers = ftp_suppliers + url_suppliers
    logger.info(f"Found {len(all_suppliers)} suppliers to sync")
    for supplier in all_suppliers:
        await sync_supplier(supplier)
        await asyncio.sleep(2)
    logger.info("Scheduled sync completed")



# ==================== FTP BROWSER ====================

def browse_ftp_sync(config: dict, path: str = "/") -> dict:
    schema = config.get('ftp_schema', 'ftp').lower()
    host = config.get('ftp_host')
    port = config.get('ftp_port', 21)
    user = config.get('ftp_user', '')
    password = config.get('ftp_password', '')
    mode = config.get('ftp_mode', 'passive')

    if not host:
        return {"status": "error", "message": "FTP host is required", "files": []}

    files = []
    if schema == 'sftp':
        port = port or 22
        transport = paramiko.Transport((host, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            for attr in sftp.listdir_attr(path):
                is_dir = attr.st_mode and (attr.st_mode & 0o170000 == 0o040000)
                files.append({
                    "name": attr.filename,
                    "path": f"{path.rstrip('/')}/{attr.filename}",
                    "size": attr.st_size,
                    "is_dir": is_dir,
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
            raw_lines = []
            ftp.dir(path, raw_lines.append)
            for line in raw_lines:
                parts = line.split(None, 8)
                if len(parts) >= 9:
                    name = parts[8]
                    is_dir = line.startswith('d')
                    size = int(parts[4]) if not is_dir else 0
                    date_str = f"{parts[5]} {parts[6]} {parts[7]}"
                    files.append({
                        "name": name,
                        "path": f"{path.rstrip('/')}/{name}",
                        "size": size,
                        "is_dir": is_dir,
                        "modified": date_str
                    })
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    files.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return {"status": "ok", "path": path, "files": files}


async def browse_ftp_directory(config: dict, path: str = "/") -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, browse_ftp_sync, config, path)


# ==================== MULTI-FILE SYNC ====================

def parse_text_file(content: bytes, separator: str = ";", header_row: int = 1) -> list:
    """Parse a semicolon-delimited text file"""
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


async def sync_supplier_multifile(supplier: dict) -> dict:
    """Sync supplier with multiple file paths - downloads all, merges by key"""
    ftp_paths = supplier.get('ftp_paths', [])
    if not ftp_paths:
        return await sync_supplier(supplier)

    logger.info(f"Multi-file sync for {supplier['name']}: {len(ftp_paths)} files configured")
    all_file_data = {}
    all_detected_columns = {}

    for file_config in ftp_paths:
        file_path = await resolve_latest_file(supplier, file_config)
        role = file_config.get('role', 'products')
        sep = file_config.get('separator', ';')
        hdr = file_config.get('header_row', 1) or 1
        label = file_config.get('label', file_path)

        if not file_path:
            continue

        try:
            logger.info(f"  Downloading: {file_path} (role: {role})")
            content = await download_file_from_ftp({**supplier, 'ftp_path': file_path})

            if file_path.lower().endswith('.zip'):
                extracted = extract_zip_files(content)
                logger.info(f"  ZIP contains {len(extracted)} files: {list(extracted.keys())}")
                for fname, fcontent in extracted.items():
                    rows = parse_text_file(fcontent, sep, hdr)
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

                    all_file_data[sub_role] = rows
                    if rows:
                        all_detected_columns[f"{fname} ({sub_role})"] = list(rows[0].keys())
                    logger.info(f"    {fname}: {len(rows)} rows, role={sub_role}")
            else:
                rows = parse_text_file(content, sep, hdr)
                all_file_data[role] = rows
                if rows:
                    all_detected_columns[f"{label} ({role})"] = list(rows[0].keys())
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

    # Build lookup dictionaries
    prices_lookup = {}
    if prices_data:
        price_keys = list(prices_data[0].keys()) if prices_data else []
        price_merge_key = price_keys[0] if price_keys else None
        if price_merge_key:
            for row in prices_data:
                key = str(row.get(price_merge_key, '')).strip()
                if key:
                    prices_lookup[key] = row

    stock_lookup = {}
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
                    if k not in merged or not merged[k]:
                        merged[k] = v
            if prod_id in stock_lookup:
                for k, v in stock_lookup[prod_id].items():
                    if k not in merged or not merged[k]:
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
                    await db.price_history.insert_one({
                        "id": str(uuid.uuid4()), "product_id": existing["id"],
                        "product_name": name, "old_price": old_price,
                        "new_price": new_price,
                        "change_percentage": ((new_price - old_price) / old_price) * 100,
                        "user_id": supplier["user_id"], "created_at": now
                    })
                old_stock = existing.get('stock', 0)
                new_stock = product_doc['stock']
                if old_stock > 0 and new_stock == 0:
                    await db.notifications.insert_one({
                        "id": str(uuid.uuid4()), "type": "stock_out",
                        "message": f"Producto '{name}' sin stock",
                        "product_id": existing["id"], "product_name": name,
                        "user_id": supplier["user_id"], "read": False, "created_at": now
                    })
                elif old_stock > 5 and 0 < new_stock <= 5:
                    await db.notifications.insert_one({
                        "id": str(uuid.uuid4()), "type": "stock_low",
                        "message": f"Producto '{name}' con stock bajo ({new_stock} uds)",
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

    product_count = await db.products.count_documents({"supplier_id": supplier['id']})
    await db.suppliers.update_one({"id": supplier['id']}, {"$set": {
        "product_count": product_count, "last_sync": now,
        "detected_columns": all_detected_columns
    }})

    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "type": "sync_complete",
        "message": f"Sincronización multi-archivo: {supplier['name']} - {imported} nuevos, {updated} actualizados ({len(ftp_paths)} archivos)",
        "product_id": None, "product_name": None,
        "user_id": supplier["user_id"], "read": False, "created_at": now
    })

    logger.info(f"Multi-file sync complete: {imported} imported, {updated} updated, {errors} errors")
    return {
        "status": "success", "imported": imported, "updated": updated,
        "errors": errors, "files_processed": len(all_file_data),
        "detected_columns": all_detected_columns
    }


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
    configs = await db.woocommerce_configs.find({"auto_sync_enabled": True, "catalog_id": {"$ne": None, "$ne": ""}}).to_list(1000)
    logger.info(f"Found {len(configs)} WooCommerce stores with auto-sync enabled")
    for config in configs:
        try:
            await sync_woocommerce_store_price_stock(config)
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error syncing WooCommerce store {config.get('name', config['id'])}: {e}")
    logger.info("Scheduled WooCommerce sync completed")
