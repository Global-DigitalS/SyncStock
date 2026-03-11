from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging

from services.database import db
from services.auth import get_current_user, check_user_limit
from services.sync import (
    sync_supplier, sync_supplier_multifile,
    parse_csv_content, parse_xlsx_content,
    parse_xls_content, parse_xml_content, normalize_product_data,
    browse_ftp_directory
)
from services.sanitizer import sanitize_string, sanitize_dict, sanitize_path
from services.encryption import encrypt_password, decrypt_password
from models.schemas import SupplierCreate, SupplierUpdate, SupplierResponse, ProductResponse

router = APIRouter()
logger = logging.getLogger(__name__)


class FtpBrowseRequest(BaseModel):
    ftp_schema: str = "ftp"
    ftp_host: str
    ftp_user: Optional[str] = ""
    ftp_password: Optional[str] = ""
    ftp_port: Optional[int] = 21
    ftp_mode: Optional[str] = "passive"
    path: Optional[str] = "/"


@router.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(supplier: SupplierCreate, user: dict = Depends(get_current_user)):
    # Check user limit
    can_create = await check_user_limit(user, "suppliers")
    if not can_create:
        raise HTTPException(
            status_code=403, 
            detail=f"Has alcanzado el límite de proveedores. Máximo: {user.get('max_suppliers', 10)}"
        )
    
    supplier_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    supplier_doc = {
        "id": supplier_id, "user_id": user["id"],
        "name": supplier.name, "description": supplier.description,
        "connection_type": supplier.connection_type or "ftp",
        "file_url": supplier.file_url,
        "ftp_schema": supplier.ftp_schema, "ftp_host": supplier.ftp_host,
        "ftp_user": supplier.ftp_user, "ftp_password": encrypt_password(supplier.ftp_password) if supplier.ftp_password else None,
        "ftp_port": supplier.ftp_port, "ftp_path": supplier.ftp_path,
        "ftp_paths": [p if isinstance(p, dict) else p.model_dump() for p in (supplier.ftp_paths or [])],
        "ftp_mode": supplier.ftp_mode,
        "file_format": supplier.file_format,
        "csv_separator": supplier.csv_separator, "csv_enclosure": supplier.csv_enclosure,
        "csv_line_break": supplier.csv_line_break, "csv_header_row": supplier.csv_header_row,
        "column_mapping": supplier.column_mapping,
        "strip_ean_quotes": supplier.strip_ean_quotes or False,
        "preset_id": supplier.preset_id,
        "product_count": 0, "last_sync": None, "created_at": now
    }
    await db.suppliers.insert_one(supplier_doc)
    supplier_doc.pop("ftp_password", None)
    supplier_doc.pop("user_id", None)
    supplier_doc.pop("_id", None)
    return SupplierResponse(**supplier_doc)


def _normalize_supplier_data(supplier: dict) -> dict:
    """Normalize supplier data to handle both single-file and multi-file formats."""
    # Fix detected_columns if it's a dict (multi-file suppliers)
    if isinstance(supplier.get("detected_columns"), dict):
        all_columns = []
        for cols in supplier["detected_columns"].values():
            if isinstance(cols, list):
                all_columns.extend(cols)
        supplier["detected_columns"] = list(set(all_columns))
    return supplier


@router.get("/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(user: dict = Depends(get_current_user)):
    suppliers = await db.suppliers.find({"user_id": user["id"]}, {"_id": 0, "ftp_password": 0, "user_id": 0}).to_list(1000)
    return [SupplierResponse(**_normalize_supplier_data(s)) for s in suppliers]


@router.get("/suppliers/presets")
async def get_supplier_presets_route(user: dict = Depends(get_current_user)):
    """Devuelve la lista de plantillas predefinidas para proveedores conocidos"""
    return SUPPLIER_PRESETS


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str, user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]}, {"_id": 0, "ftp_password": 0, "user_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return SupplierResponse(**_normalize_supplier_data(supplier))


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: str, supplier: SupplierUpdate, user: dict = Depends(get_current_user)):
    existing = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    raw = supplier.model_dump()
    # Keep fields that were explicitly sent: exclude None only for optional connection fields
    # but allow None for column_mapping (to clear it when switching presets)
    always_allow_none = {"column_mapping", "preset_id", "ftp_path", "ftp_paths", "file_url", "description"}
    update_data = {
        k: v for k, v in raw.items()
        if v is not None or k in always_allow_none
    }
    if "ftp_password" in update_data and update_data["ftp_password"]:
        update_data["ftp_password"] = encrypt_password(update_data["ftp_password"])
    elif "ftp_password" in update_data and not update_data["ftp_password"]:
        update_data.pop("ftp_password")  # don't overwrite with empty string
    if update_data:
        await db.suppliers.update_one({"id": supplier_id}, {"$set": update_data})
    updated = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0, "ftp_password": 0, "user_id": 0})
    return SupplierResponse(**updated)


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, user: dict = Depends(get_current_user)):
    result = await db.suppliers.delete_one({"id": supplier_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    await db.products.delete_many({"supplier_id": supplier_id})
    return {"message": "Proveedor eliminado"}


@router.post("/suppliers/{supplier_id}/sync")
async def sync_supplier_manual(supplier_id: str, user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    # Desencriptar contraseña FTP antes de usar
    if supplier.get("ftp_password"):
        supplier["ftp_password"] = decrypt_password(supplier["ftp_password"])
    connection_type = supplier.get('connection_type', 'ftp')
    has_multifile = bool(supplier.get('ftp_paths'))
    if connection_type == 'url':
        if not supplier.get('file_url'):
            raise HTTPException(status_code=400, detail="URL del archivo no configurada.")
    else:
        if not has_multifile and (not supplier.get('ftp_host') or not supplier.get('ftp_path')):
            raise HTTPException(status_code=400, detail="Configuración FTP incompleta.")
    try:
        if has_multifile:
            result = await sync_supplier_multifile(supplier)
        else:
            result = await sync_supplier(supplier)
        if result.get('status') == 'error':
            return {"status": "error", "message": result.get('message', 'Error en sincronización')}
        return result
    except Exception as e:
        logger.error(f"Exception in sync_supplier_manual: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/suppliers/{supplier_id}/sync-status")
async def get_sync_status(supplier_id: str, user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    has_ftp = bool(supplier.get('ftp_host') and (supplier.get('ftp_path') or supplier.get('ftp_paths')))
    return {
        "last_sync": supplier.get('last_sync'),
        "ftp_configured": has_ftp,
        "product_count": supplier.get('product_count', 0),
        "ftp_paths_count": len(supplier.get('ftp_paths', []))
    }


@router.post("/suppliers/ftp-browse")
async def ftp_browse(req: FtpBrowseRequest, user: dict = Depends(get_current_user)):
    """Navega por el servidor FTP y lista archivos/carpetas"""
    try:
        result = await browse_ftp_directory({
            "ftp_schema": req.ftp_schema, "ftp_host": req.ftp_host,
            "ftp_user": req.ftp_user, "ftp_password": req.ftp_password,
            "ftp_port": req.ftp_port, "ftp_mode": req.ftp_mode,
        }, req.path)
        return result
    except Exception as e:
        logger.error(f"FTP browse error: {e}")
        return {"status": "error", "message": str(e), "files": [], "path": req.path}


class FtpTestRequest(BaseModel):
    ftp_schema: str = "ftp"
    ftp_host: str
    ftp_user: Optional[str] = ""
    ftp_password: Optional[str] = ""
    ftp_port: Optional[int] = 21
    ftp_mode: Optional[str] = "passive"


@router.post("/suppliers/ftp-test")
async def ftp_test_connection(req: FtpTestRequest, user: dict = Depends(get_current_user)):
    """
    Prueba la conexión FTP sin descargar archivos.
    Útil para verificar credenciales antes de configurar el proveedor.
    """
    import ftplib
    import paramiko
    
    schema = req.ftp_schema.lower()
    host = req.ftp_host
    port = req.ftp_port or (22 if schema == 'sftp' else 21)
    user = req.ftp_user or ''
    password = req.ftp_password or ''
    mode = req.ftp_mode or 'passive'
    
    if not host:
        return {"status": "error", "message": "Host FTP requerido", "connected": False}
    
    try:
        if schema == 'sftp':
            transport = paramiko.Transport((host, port))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Obtener directorio actual
            current_dir = sftp.getcwd() or "/"
            files_count = len(sftp.listdir(current_dir))
            
            sftp.close()
            transport.close()
            
            return {
                "status": "ok",
                "message": f"Conexión SFTP exitosa a {host}:{port}",
                "connected": True,
                "protocol": "SFTP",
                "current_dir": current_dir,
                "files_in_root": files_count
            }
        else:
            ftp = ftplib.FTP_TLS() if schema == 'ftps' else ftplib.FTP()
            ftp.connect(host, port, timeout=10)
            ftp.login(user or 'anonymous', password or '')
            
            if schema == 'ftps':
                ftp.prot_p()
            ftp.set_pasv(mode == 'passive')
            
            # Obtener información del servidor
            current_dir = ftp.pwd()
            files = []
            ftp.dir(current_dir, files.append)
            
            # Obtener mensaje de bienvenida si está disponible
            welcome = getattr(ftp, 'welcome', '')
            
            ftp.quit()
            
            return {
                "status": "ok",
                "message": f"Conexión {'FTPS' if schema == 'ftps' else 'FTP'} exitosa a {host}:{port}",
                "connected": True,
                "protocol": "FTPS" if schema == 'ftps' else "FTP",
                "mode": "Pasivo" if mode == 'passive' else "Activo",
                "current_dir": current_dir,
                "files_in_root": len(files),
                "welcome": welcome[:200] if welcome else None
            }
            
    except ftplib.error_perm as e:
        return {
            "status": "error",
            "message": f"Error de autenticación: {str(e)}",
            "connected": False,
            "suggestion": "Verifica el usuario y contraseña"
        }
    except paramiko.AuthenticationException as e:
        return {
            "status": "error", 
            "message": f"Error de autenticación SFTP: {str(e)}",
            "connected": False,
            "suggestion": "Verifica el usuario y contraseña"
        }
    except (ConnectionRefusedError, OSError) as e:
        return {
            "status": "error",
            "message": f"No se puede conectar al servidor: {str(e)}",
            "connected": False,
            "suggestion": f"Verifica que el host {host} y puerto {port} sean correctos"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error de conexión: {str(e)}",
            "connected": False
        }


@router.post("/suppliers/{supplier_id}/ftp-browse")
async def ftp_browse_supplier(supplier_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Navega por el FTP del proveedor específico"""
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if supplier.get("ftp_password"):
        supplier["ftp_password"] = decrypt_password(supplier["ftp_password"])
    path = data.get("path", "/")
    try:
        result = await browse_ftp_directory(supplier, path)
        return result
    except Exception as e:
        logger.error(f"FTP browse error: {e}")
        return {"status": "error", "message": str(e), "files": [], "path": path}


@router.post("/suppliers/{supplier_id}/ftp-list-all")
async def ftp_list_all_files(supplier_id: str, data: dict, user: dict = Depends(get_current_user)):
    """
    Lista todos los archivos soportados en una carpeta y subcarpetas (máximo 2 niveles).
    Útil para ver todos los archivos disponibles del proveedor.
    """
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if supplier.get("ftp_password"):
        supplier["ftp_password"] = decrypt_password(supplier["ftp_password"])

    base_path = data.get("path", "/")
    max_depth = min(data.get("max_depth", 2), 3)  # Máximo 3 niveles para evitar timeout
    
    all_files = []
    dirs_to_scan = [(base_path, 0)]
    
    try:
        while dirs_to_scan:
            current_path, depth = dirs_to_scan.pop(0)
            
            result = await browse_ftp_directory(supplier, current_path)
            
            if result.get("status") != "ok":
                continue
            
            for item in result.get("files", []):
                if item["is_dir"]:
                    if depth < max_depth:
                        dirs_to_scan.append((item["path"], depth + 1))
                elif item.get("is_supported"):
                    item["relative_path"] = item["path"].replace(base_path, "").lstrip("/")
                    item["depth"] = depth
                    all_files.append(item)
        
        # Agrupar por extensión
        by_extension = {}
        for f in all_files:
            ext = f.get("extension", "other")
            if ext not in by_extension:
                by_extension[ext] = []
            by_extension[ext].append(f)
        
        return {
            "status": "ok",
            "base_path": base_path,
            "total_files": len(all_files),
            "files": all_files,
            "by_extension": by_extension,
            "extensions_found": list(by_extension.keys())
        }
        
    except Exception as e:
        logger.error(f"FTP list all error: {e}")
        return {"status": "error", "message": str(e), "files": []}


@router.post("/products/import/{supplier_id}")
async def import_products(supplier_id: str, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    content = await file.read()
    filename = file.filename.lower()
    try:
        if filename.endswith('.csv'):
            raw_products = parse_csv_content(content)
        elif filename.endswith('.xlsx'):
            raw_products = parse_xlsx_content(content)
        elif filename.endswith('.xls'):
            raw_products = parse_xls_content(content)
        elif filename.endswith('.xml'):
            raw_products = parse_xml_content(content)
        else:
            raise HTTPException(status_code=400, detail="Formato no soportado. Use CSV, XLSX, XLS o XML")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando archivo: {str(e)}")
    now = datetime.now(timezone.utc).isoformat()
    imported = 0
    updated = 0
    for raw in raw_products:
        normalized = normalize_product_data(raw)
        if not normalized.get('sku') or not normalized.get('name'):
            continue
        existing = await db.products.find_one({"sku": normalized['sku'], "supplier_id": supplier_id})
        product_doc = {
            "sku": normalized.get('sku'), "name": normalized.get('name'),
            "description": normalized.get('description'), "price": normalized.get('price', 0),
            "stock": normalized.get('stock', 0), "category": normalized.get('category'),
            "brand": normalized.get('brand'), "ean": normalized.get('ean'),
            "weight": normalized.get('weight'), "image_url": normalized.get('image_url'),
            "supplier_id": supplier_id, "supplier_name": supplier["name"],
            "user_id": user["id"], "updated_at": now
        }
        if existing:
            if existing.get('price') != product_doc['price']:
                await db.price_history.insert_one({
                    "id": str(uuid.uuid4()), "product_id": existing["id"],
                    "product_name": product_doc["name"],
                    "old_price": existing.get('price', 0), "new_price": product_doc['price'],
                    "change_percentage": ((product_doc['price'] - existing.get('price', 0)) / existing.get('price', 1)) * 100 if existing.get('price', 0) > 0 else 0,
                    "user_id": user["id"], "created_at": now
                })
            if existing.get('stock', 0) > 0 and product_doc['stock'] == 0:
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()), "type": "stock_out",
                    "message": f"Producto '{product_doc['name']}' sin stock",
                    "product_id": existing["id"], "product_name": product_doc["name"],
                    "user_id": user["id"], "read": False, "created_at": now
                })
            elif existing.get('stock', 0) > 5 and product_doc['stock'] <= 5 and product_doc['stock'] > 0:
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()), "type": "stock_low",
                    "message": f"Producto '{product_doc['name']}' con stock bajo ({product_doc['stock']} uds)",
                    "product_id": existing["id"], "product_name": product_doc["name"],
                    "user_id": user["id"], "read": False, "created_at": now
                })
            await db.products.update_one({"id": existing["id"]}, {"$set": product_doc})
            updated += 1
        else:
            product_doc["id"] = str(uuid.uuid4())
            product_doc["created_at"] = now
            await db.products.insert_one(product_doc)
            imported += 1
    product_count = await db.products.count_documents({"supplier_id": supplier_id})
    await db.suppliers.update_one({"id": supplier_id}, {"$set": {"product_count": product_count, "last_sync": now}})
    return {"imported": imported, "updated": updated, "total": imported + updated}


# ==================== SUPPLIER PRESETS ====================

SUPPLIER_PRESETS = [
    {
        "id": "ingram_es",
        "name": "INGRAM MICRO (España)",
        "description": "PRICE09.TXT — CSV coma, sin cabecera, Latin-1. Mapeo posicional automático.",
        "config": {
            "file_format": "csv",
            "csv_separator": ",",
            "csv_enclosure": '"',
            "csv_line_break": "\\n",
            "csv_header_row": 0,
            "strip_ean_quotes": False,
            "column_mapping": {
                "sku": "col_0",
                "name": "col_2",
                "ean": "col_3",
                "weight": "col_4",
                "brand": "col_5",
                "category": "col_6",
                "stock": "col_7",
                "price": "col_8"
            }
        }
    },
    {
        "id": "techdata_es",
        "name": "Tech Data (España)",
        "description": "ZIP con múltiples archivos — CSV punto y coma, sin cabecera.",
        "config": {
            "file_format": "zip",
            "csv_separator": ";",
            "csv_enclosure": '"',
            "csv_line_break": "\\n",
            "csv_header_row": 0,
            "strip_ean_quotes": False,
            "column_mapping": None
        }
    },
    {
        "id": "mcr_es",
        "name": "MCR (España)",
        "description": "CSV único — punto y coma, con cabecera, UTF-8 BOM.",
        "config": {
            "file_format": "csv",
            "csv_separator": ";",
            "csv_enclosure": '"',
            "csv_line_break": "\\n",
            "csv_header_row": 1,
            "strip_ean_quotes": False,
            "column_mapping": None
        }
    },
    {
        "id": "esprinet_es",
        "name": "Esprinet (España)",
        "description": "CSV estándar — punto y coma, con cabecera.",
        "config": {
            "file_format": "csv",
            "csv_separator": ";",
            "csv_enclosure": '"',
            "csv_line_break": "\\n",
            "csv_header_row": 1,
            "strip_ean_quotes": False,
            "column_mapping": None
        }
    },
    {
        "id": "binary_es",
        "name": "Binary (España)",
        "description": "CSV estándar — punto y coma, con cabecera.",
        "config": {
            "file_format": "csv",
            "csv_separator": ";",
            "csv_enclosure": '"',
            "csv_line_break": "\\n",
            "csv_header_row": 1,
            "strip_ean_quotes": False,
            "column_mapping": None
        }
    },
    {
        "id": "infortisa_es",
        "name": "Infortisa (España)",
        "description": "CSV estándar — punto y coma, con cabecera.",
        "config": {
            "file_format": "csv",
            "csv_separator": ";",
            "csv_enclosure": '"',
            "csv_line_break": "\\n",
            "csv_header_row": 1,
            "strip_ean_quotes": False,
            "column_mapping": None
        }
    }
]


# Standard field aliases for auto-detection
FIELD_ALIASES = {
    'sku': ['sku', 'codigo', 'code', 'ref', 'referencia', 'reference', 'id', 'product_id', 'partnumber', 'part_number', 'articulo', 'codigo_articulo', 'cod', 'item_code'],
    'name': ['name', 'nombre', 'title', 'titulo', 'product_name', 'descripcion', 'description', 'producto', 'articulo_nombre', 'item_name'],
    'price': ['price', 'precio', 'pvp', 'cost', 'coste', 'unit_price', 'tarifa', 'importe', 'pricen', 'precio_neto', 'net_price'],
    'stock': ['stock', 'quantity', 'cantidad', 'qty', 'inventory', 'disponible', 'existencias', 'unidades', 'disponibilidad', 'units'],
    'category': ['category', 'categoria', 'cat', 'type', 'tipo', 'familia', 'family', 'grupo', 'group'],
    'brand': ['brand', 'marca', 'manufacturer', 'fabricante', 'vendor', 'proveedor'],
    'ean': ['ean', 'ean13', 'barcode', 'upc', 'codigo_barras', 'gtin', 'ean_code'],
    'weight': ['weight', 'peso', 'kg', 'mass'],
    'image_url': ['image', 'imagen', 'image_url', 'photo', 'foto', 'picture', 'url_imagen', 'img'],
    'description': ['description', 'descripcion', 'desc', 'details', 'detalles', 'long_description', 'short_description']
}


def suggest_column_mapping(columns: list) -> dict:
    """Auto-suggest column mappings based on column names"""
    suggestions = {}
    columns_lower = {c.lower().strip(): c for c in columns}
    
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in columns_lower:
                suggestions[field] = columns_lower[alias]
                break
    
    return suggestions


@router.post("/suppliers/{supplier_id}/preview-file")
async def preview_supplier_file(supplier_id: str, user: dict = Depends(get_current_user)):
    """Previsualiza el archivo del proveedor y muestra las columnas detectadas con sugerencias de mapeo"""
    from services.sync import download_file_from_ftp, download_file_from_url
    
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if supplier.get("ftp_password"):
        supplier["ftp_password"] = decrypt_password(supplier["ftp_password"])

    connection_type = supplier.get('connection_type', 'ftp')
    try:
        if connection_type == 'url':
            if not supplier.get('file_url'):
                raise HTTPException(status_code=400, detail="URL no configurada")
            content = await download_file_from_url(supplier['file_url'])
        else:
            if not supplier.get('ftp_host') or not supplier.get('ftp_path'):
                raise HTTPException(status_code=400, detail="FTP no configurado")
            content = await download_file_from_ftp(supplier)
        
        # Parse as CSV
        separator = supplier.get('csv_separator', ';')
        if separator == '\\t':
            separator = '\t'
        _header_row_raw = supplier.get('csv_header_row', 1)
        header_row = 1 if _header_row_raw is None else int(_header_row_raw)

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

        import csv
        if header_row == 0:
            first_line = lines[0].rstrip('\r') if lines else ''
            first_row_parsed = list(csv.reader([first_line], delimiter=separator))
            num_cols = len(first_row_parsed[0]) if first_row_parsed else 0
            fieldnames = [f'col_{i}' for i in range(num_cols)]
            reader = csv.DictReader(lines, fieldnames=fieldnames, delimiter=separator)
        else:
            reader = csv.DictReader(lines, delimiter=separator)
        raw_products = list(reader)[:10]  # First 10 for preview
        
        columns = list(raw_products[0].keys()) if raw_products else []
        
        # Auto-suggest mappings
        suggested_mapping = suggest_column_mapping(columns)
        
        # Show sample data
        samples = []
        for row in raw_products[:5]:
            samples.append({k: str(v)[:100] for k, v in row.items()})
        
        # Calculate mapping coverage
        required_fields = ['sku', 'name', 'price']
        optional_fields = ['stock', 'category', 'brand', 'ean', 'weight', 'image_url', 'description']
        missing_required = [f for f in required_fields if f not in suggested_mapping]
        mapped_optional = [f for f in optional_fields if f in suggested_mapping]
        
        return {
            "status": "success",
            "columns": columns,
            "sample_data": samples,
            "total_rows": len(lines) - 1,
            "suggested_mapping": suggested_mapping,
            "missing_required": missing_required,
            "mapped_optional": mapped_optional,
            "mapping_coverage": f"{len(suggested_mapping)}/{len(FIELD_ALIASES)} campos detectados",
            "message": f"Archivo con {len(columns)} columnas. {len(suggested_mapping)} campos auto-detectados."
        }
    except Exception as e:
        logger.error(f"Error previewing file: {e}")
        return {"status": "error", "message": str(e), "columns": []}
