from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging
import asyncio
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.database import db
from services.auth import get_current_user, check_user_limit
from services.sync import (
    sync_supplier, sync_supplier_multifile,
    parse_csv_content, parse_xlsx_content,
    parse_xls_content, parse_xml_content, normalize_product_data,
    browse_ftp_directory, prefetch_existing_products, bulk_upsert_products
)
from services.sanitizer import sanitize_string, sanitize_dict, sanitize_path
from services.encryption import encrypt_password, decrypt_password
from models.schemas import SupplierCreate, SupplierUpdate, SupplierResponse, ProductResponse

router = APIRouter()
_limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


class FtpBrowseRequest(BaseModel):
    ftp_schema: str = "ftp"
    ftp_host: str
    ftp_user: Optional[str] = ""
    ftp_password: Optional[str] = ""
    ftp_port: Optional[int] = 21
    ftp_mode: Optional[str] = "passive"
    path: Optional[str] = "/"
    supplier_id: Optional[str] = None  # If set, use saved password from DB


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


@router.post("/suppliers/{supplier_id}/apply-preset")
async def apply_preset_to_supplier(supplier_id: str, data: dict, user: dict = Depends(get_current_user)):
    """Aplica una plantilla predefinida a un proveedor ya existente (actualiza config de formato y mapeo)."""
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    preset_id = data.get("preset_id")
    preset = next((p for p in SUPPLIER_PRESETS if p["id"] == preset_id), None)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Plantilla '{preset_id}' no encontrada")
    config = preset["config"]
    new_separator = config.get("csv_separator")
    new_header_row = config.get("csv_header_row")
    update_fields = {
        "file_format": config.get("file_format"),
        "csv_separator": new_separator,
        "csv_enclosure": config.get("csv_enclosure"),
        "csv_line_break": config.get("csv_line_break"),
        "csv_header_row": new_header_row,
        "strip_ean_quotes": config.get("strip_ean_quotes", False),
        "column_mapping": config.get("column_mapping"),
        "preset_id": preset_id,
    }
    # Also propagate separator and header_row to ftp_paths entries so they stay consistent
    existing_ftp_paths = supplier.get("ftp_paths") or []
    if existing_ftp_paths:
        updated_ftp_paths = []
        for fp in existing_ftp_paths:
            fp_copy = dict(fp)
            if new_separator is not None:
                fp_copy["separator"] = new_separator
            if new_header_row is not None:
                fp_copy["header_row"] = new_header_row
            updated_ftp_paths.append(fp_copy)
        update_fields["ftp_paths"] = updated_ftp_paths
    await db.suppliers.update_one({"id": supplier_id}, {"$set": update_fields})
    updated = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0, "ftp_password": 0, "user_id": 0})
    return {
        "message": f"Plantilla '{preset['name']}' aplicada correctamente. Sincroniza el proveedor para importar los productos.",
        "supplier": SupplierResponse(**_normalize_supplier_data(updated))
    }


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
@_limiter.limit("10/minute")
async def sync_supplier_manual(request: Request, supplier_id: str, user: dict = Depends(get_current_user)):
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

    # Mark sync as running immediately so the UI can show progress
    await db.suppliers.update_one(
        {"id": supplier_id},
        {"$set": {"sync_status": "running", "sync_started_at": datetime.now(timezone.utc).isoformat()}}
    )

    async def _run_sync():
        try:
            if has_multifile:
                result = await sync_supplier_multifile(supplier)
            else:
                result = await sync_supplier(supplier)
            status = result.get('status', 'error')
            await db.suppliers.update_one(
                {"id": supplier_id},
                {"$set": {"sync_status": status, "sync_last_result": result.get('message', '')}}
            )
        except Exception as exc:
            logger.error(f"Background sync error for {supplier_id}: {exc}")
            await db.suppliers.update_one(
                {"id": supplier_id},
                {"$set": {"sync_status": "error", "sync_last_result": str(exc)}}
            )

    asyncio.create_task(_run_sync())
    return {
        "status": "queued",
        "message": f"Sincronización de '{supplier.get('name', supplier_id)}' iniciada en segundo plano."
    }


@router.get("/suppliers/{supplier_id}/sync-status")
async def get_sync_status(supplier_id: str, user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    has_ftp = bool(supplier.get('ftp_host') and (supplier.get('ftp_path') or supplier.get('ftp_paths')))

    def _to_str(v):
        if v is None:
            return None
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        return str(v)

    # Auto-reset sync_status if stuck in "running" for more than 30 minutes
    sync_status = supplier.get('sync_status') or 'idle'
    sync_started_at = supplier.get('sync_started_at')
    if sync_status == 'running' and sync_started_at:
        try:
            started_str = sync_started_at.isoformat() if hasattr(sync_started_at, 'isoformat') else str(sync_started_at)
            started_dt = datetime.fromisoformat(started_str)
            if started_dt.tzinfo is None:
                started_dt = started_dt.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - started_dt).total_seconds()
            if elapsed > 1800:  # 30 minutes
                sync_status = 'error'
                await db.suppliers.update_one(
                    {"id": supplier_id},
                    {"$set": {"sync_status": "error", "sync_last_result": "Sincronización interrumpida (tiempo máximo superado)"}}
                )
        except Exception:
            pass

    return {
        "last_sync": _to_str(supplier.get('last_sync')),
        "ftp_configured": has_ftp,
        "product_count": int(supplier.get('product_count') or 0),
        "ftp_paths_count": len(supplier.get('ftp_paths') or []),
        "sync_status": sync_status,
        "sync_started_at": _to_str(sync_started_at),
        "sync_last_result": str(supplier.get('sync_last_result') or ''),
    }


def _sanitize_ftp_path(path: str) -> str:
    """Normalise an FTP path and reject path-traversal sequences."""
    import posixpath
    # Resolve '..' segments without touching the filesystem
    clean = posixpath.normpath("/" + path.replace("\\", "/"))
    # After normpath a safe path always starts with '/'
    if not clean.startswith("/"):
        clean = "/"
    return clean


@router.post("/suppliers/ftp-browse")
async def ftp_browse(req: FtpBrowseRequest, user: dict = Depends(get_current_user)):
    """Navega por el servidor FTP y lista archivos/carpetas"""
    safe_path = _sanitize_ftp_path(req.path or "/")
    # Resolve password: use saved DB password if supplier_id is provided and no new password given
    password = req.ftp_password
    if req.supplier_id and not password:
        supplier = await db.suppliers.find_one({"id": req.supplier_id, "user_id": user["id"]})
        if supplier and supplier.get("ftp_password"):
            password = decrypt_password(supplier["ftp_password"])
    try:
        result = await browse_ftp_directory({
            "ftp_schema": req.ftp_schema, "ftp_host": req.ftp_host,
            "ftp_user": req.ftp_user, "ftp_password": password,
            "ftp_port": req.ftp_port, "ftp_mode": req.ftp_mode,
        }, safe_path)
        return result
    except Exception as e:
        logger.error(f"FTP browse error: {e}")
        return {"status": "error", "message": "Error al navegar el directorio FTP", "files": [], "path": safe_path}


class FtpTestRequest(BaseModel):
    ftp_schema: str = "ftp"
    ftp_host: str
    ftp_user: Optional[str] = ""
    ftp_password: Optional[str] = ""
    ftp_port: Optional[int] = 21
    ftp_mode: Optional[str] = "passive"
    supplier_id: Optional[str] = None  # If set, use saved password from DB


@router.post("/suppliers/ftp-test")
async def ftp_test_connection(req: FtpTestRequest, current_user: dict = Depends(get_current_user)):
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
    # Resolve password: use saved DB password if supplier_id is provided and no new password given
    password = req.ftp_password or ''
    if req.supplier_id and not password:
        supplier = await db.suppliers.find_one({"id": req.supplier_id, "user_id": current_user["id"]})
        if supplier and supplier.get("ftp_password"):
            password = decrypt_password(supplier["ftp_password"])
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
            "message": "Error de autenticación FTP. Verifica las credenciales.",
            "connected": False,
            "suggestion": "Verifica el usuario y contraseña"
        }
    except paramiko.AuthenticationException as e:
        return {
            "status": "error", 
            "message": "Error de autenticación SFTP. Verifica las credenciales.",
            "connected": False,
            "suggestion": "Verifica el usuario y contraseña"
        }
    except (ConnectionRefusedError, OSError) as e:
        return {
            "status": "error",
            "message": "No se puede conectar al servidor FTP/SFTP. Verifica el host y el puerto.",
            "connected": False,
            "suggestion": f"Verifica que el host {host} y puerto {port} sean correctos"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Error de conexión. Verifica los parámetros del servidor.",
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
        return {"status": "error", "message": "Error al listar el directorio FTP", "files": [], "path": path}


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
        return {"status": "error", "message": "Error al listar el directorio FTP", "files": []}


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
    # Normalize all products
    normalized_products = []
    for raw in raw_products:
        normalized = normalize_product_data(raw)
        if not normalized.get('sku') or not normalized.get('name'):
            continue
        normalized_products.append(normalized)

    # Bulk upsert with pre-fetched existing products
    supplier_doc = {"id": supplier_id, "name": supplier["name"], "user_id": user["id"]}
    existing_map = await prefetch_existing_products(supplier_id, user["id"])
    bulk_result = await bulk_upsert_products(supplier_doc, normalized_products, existing_map, now)
    imported = bulk_result["imported"]
    updated = bulk_result["updated"]

    product_count = await db.products.count_documents({"supplier_id": supplier_id})
    await db.suppliers.update_one({"id": supplier_id}, {"$set": {"product_count": product_count, "last_sync": now}})
    return {"imported": imported, "updated": updated, "total": imported + updated}


# ==================== SUPPLIER PRESETS ====================

SUPPLIER_PRESETS = [
    {
        "id": "ingram_es",
        "name": "INGRAM MICRO (España)",
        "description": "PRICE09.ZIP — ZIP con PRICE09.TXT (CSV coma, sin cabecera, 29 columnas). Ruta SFTP: /PRICE09.ZIP",
        "config": {
            "file_format": "csv",
            "csv_separator": ",",
            "csv_enclosure": '"',
            "csv_line_break": "\\n",
            "csv_header_row": 0,
            "strip_ean_quotes": False,
            "column_mapping": {
                "sku": "col_1",
                "name": "col_6",
                "description": "col_7",
                "ean": "col_4",
                "weight": "col_8",
                "brand": "col_2",
                "category": "col_5",
                "stock": "col_23",
                "price": "col_24"
            }
        }
    },
    {
        "id": "techdata_es",
        "name": "Tech Data (España)",
        "description": "ZIP con GM_ES_C_Product + GM_ES_C_Prices — CSV punto y coma, sin cabecera. Stock requiere StockFile.txt por separado.",
        "config": {
            "file_format": "zip",
            "csv_separator": ";",
            "csv_enclosure": '"',
            "csv_line_break": "\\n",
            "csv_header_row": 0,
            "strip_ean_quotes": False,
            "column_mapping": {
                "sku": "col_0",
                "name": "col_1",
                "description": "col_2",
                "brand": "col_5",
                "ean": "col_12",
                "weight": "col_13",
                "category": "col_15",
                "subcategory": "col_17",
                "subcategory2": "col_19",
                "price": "prices_col_3"
            }
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
    from services.sync import download_file_from_ftp, download_file_from_url, extract_zip_files, parse_text_file

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
            # Support both ftp_path (single file) and ftp_paths (multi-file)
            ftp_paths = supplier.get('ftp_paths') or []
            single_path = supplier.get('ftp_path', '')
            if not supplier.get('ftp_host'):
                raise HTTPException(status_code=400, detail="FTP no configurado")
            if single_path:
                content = await download_file_from_ftp(supplier)
            elif ftp_paths:
                # Download the first products-role file for preview
                preview_entry = next(
                    (e for e in ftp_paths if e.get('role', 'products') == 'products'),
                    ftp_paths[0]
                )
                from services.sync import resolve_latest_file
                preview_path = await resolve_latest_file(supplier, preview_entry)
                content = await download_file_from_ftp({**supplier, 'ftp_path': preview_path})
            else:
                raise HTTPException(status_code=400, detail="FTP no configurado")
        
        # Parse as CSV (with ZIP support)
        separator = supplier.get('csv_separator', ';') or ';'
        if separator == '\\t':
            separator = '\t'
        _header_row_raw = supplier.get('csv_header_row', 1)
        header_row = 1 if _header_row_raw is None else int(_header_row_raw)

        # If it's a ZIP, extract the products file first
        if len(content) >= 2 and content[:2] == b'PK':
            extracted = extract_zip_files(content)
            role_kws = ['product', 'catalog', 'article', 'catalogo', 'articulo', 'master', 'price', 'precio']
            # Prefer products/catalog files; fall back to any compatible file
            compatible_exts = ('.csv', '.txt', '.xlsx', '.xls')
            best = None
            best_rows = 0
            for fname, fcontent in extracted.items():
                if not fname.lower().endswith(compatible_exts):
                    continue
                fname_lower = fname.split('/')[-1].lower()
                rows = parse_text_file(fcontent, separator, header_row)
                if len(rows) > best_rows:
                    best_rows = len(rows)
                    best = fcontent
            content = best or content
            if best is None:
                return {"status": "error", "message": f"El ZIP no contiene archivos CSV/TXT compatibles", "columns": []}

        import csv
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
        return {"status": "error", "message": "Error al leer las columnas del archivo", "columns": []}


@router.post("/suppliers/{supplier_id}/diagnose")
async def diagnose_supplier_zip(supplier_id: str, user: dict = Depends(get_current_user)):
    """
    Descarga el archivo del proveedor y devuelve un diagnóstico detallado
    sin importar nada a la base de datos. Útil para depurar problemas de mapeo.
    """
    from services.sync import (
        download_file_from_ftp, download_file_from_url,
        extract_zip_files, parse_text_file, apply_column_mapping
    )
    import csv as csv_mod

    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if supplier.get("ftp_password"):
        supplier["ftp_password"] = decrypt_password(supplier["ftp_password"])

    separator = supplier.get("csv_separator", ";")
    if separator == "\\t":
        separator = "\t"
    _hdr = supplier.get("csv_header_row", 1)
    header_row = 1 if _hdr is None else int(_hdr)
    column_mapping = supplier.get("column_mapping")

    try:
        connection_type = supplier.get("connection_type", "ftp")
        if connection_type == "url":
            content = await download_file_from_url(supplier["file_url"])
        else:
            content = await download_file_from_ftp(supplier)
    except Exception as e:
        return {"status": "error", "step": "download", "message": "Error al descargar el archivo del proveedor"}

    # Is it a ZIP?
    is_zip = len(content) >= 2 and content[:2] == b'PK'
    result = {
        "status": "ok",
        "file_size_bytes": len(content),
        "is_zip": is_zip,
        "header_row": header_row,
        "separator": repr(separator),
        "column_mapping": column_mapping,
    }

    if is_zip:
        try:
            extracted = extract_zip_files(content)
        except Exception as e:
            return {**result, "status": "error", "step": "unzip", "message": "Error al descomprimir el archivo"}

        compatible_exts = ('.csv', '.txt', '.xlsx', '.xls', '.xml')
        compatible = [
            f for f in extracted
            if f.lower().endswith(compatible_exts)
            and not f.split('/')[-1].startswith('.')
            and not f.split('/')[-1].startswith('__')
        ]
        role_keywords = {
            'stock':    ['stock', 'inventory', 'disponibilidad', 'existencias', 'qty'],
            'prices':   ['price', 'precio', 'tarif', 'coste', 'cost', 'pvp', 'pvd'],
            'products': ['product', 'catalog', 'article', 'catalogo', 'articulo', 'master'],
        }
        files_info = []
        role_assignments = {}
        for fname in extracted:
            fname_base = fname.split('/')[-1].lower()
            ext = '.' + fname_base.rsplit('.', 1)[-1] if '.' in fname_base else '(sin extensión)'
            is_compat = fname in compatible
            detected_role = 'products'
            for role, kws in role_keywords.items():
                if any(kw in fname_base for kw in kws):
                    detected_role = role
                    break
            file_entry = {
                "name": fname,
                "extension": ext,
                "size_bytes": len(extracted[fname]),
                "is_compatible": is_compat,
                "detected_role": detected_role if is_compat else "skipped",
            }
            if is_compat:
                try:
                    rows = parse_text_file(extracted[fname], separator, header_row)
                    file_entry["row_count"] = len(rows)
                    file_entry["columns"] = list(rows[0].keys()) if rows else []
                    file_entry["sample_row"] = {k: str(v)[:80] for k, v in list(rows[0].items())[:10]} if rows else {}
                    # Check if this role already assigned (keep largest)
                    if detected_role not in role_assignments or len(rows) > role_assignments[detected_role]["row_count"]:
                        role_assignments[detected_role] = {"file": fname, "row_count": len(rows), "columns": file_entry["columns"]}
                except Exception as pe:
                    file_entry["parse_error"] = str(pe)
            files_info.append(file_entry)

        result["zip_files"] = files_info
        result["zip_total_files"] = len(extracted)
        result["compatible_files_count"] = len(compatible)
        result["role_assignments"] = role_assignments

        # Test column_mapping against a sample merged row
        if column_mapping and "products" in role_assignments and "prices" in role_assignments:
            prod_cols = role_assignments["products"]["columns"]
            price_cols = role_assignments["prices"]["columns"]
            # Simulate merged row (first product + prefixed prices)
            sample_merged = {c: f"<{c}_value>" for c in prod_cols}
            prices_merge_key = price_cols[0] if price_cols else None
            for c in price_cols:
                if header_row == 0 and c != prices_merge_key:
                    sample_merged[f"prices_{c}"] = f"<prices_{c}_value>"
                elif c not in sample_merged:
                    sample_merged[c] = f"<{c}_value>"
            mapping_test = {}
            for field, col in column_mapping.items():
                found = sample_merged.get(col)
                mapping_test[field] = {"maps_to": col, "found_in_merged": found is not None}
            result["mapping_test"] = mapping_test
            missing = [f for f, v in mapping_test.items() if not v["found_in_merged"]]
            result["mapping_missing_cols"] = missing
            result["mapping_ok"] = len(missing) == 0
    else:
        # Single flat file
        try:
            decoded = content.decode('utf-8-sig', errors='replace')
        except Exception:
            decoded = content.decode('latin-1', errors='replace')
        lines = decoded.split('\n')
        if header_row == 0:
            first_line = lines[0].rstrip('\r') if lines else ''
            first_parsed = list(csv_mod.reader([first_line], delimiter=separator))
            num_cols = len(first_parsed[0]) if first_parsed else 0
            fieldnames = [f'col_{i}' for i in range(num_cols)]
            reader = csv_mod.DictReader(lines, fieldnames=fieldnames, delimiter=separator)
        else:
            reader = csv_mod.DictReader(lines, delimiter=separator)
        rows = list(reader)
        result["row_count"] = len(rows)
        result["columns"] = list(rows[0].keys()) if rows else []
        result["sample_row"] = {k: str(v)[:80] for k, v in list(rows[0].items())[:10]} if rows else {}
        if column_mapping and rows:
            sample = rows[0]
            mapping_test = {}
            for field, col in column_mapping.items():
                mapping_test[field] = {"maps_to": col, "found": col in sample}
            result["mapping_test"] = mapping_test
            missing = [f for f, v in mapping_test.items() if not v["found"]]
            result["mapping_missing_cols"] = missing
            result["mapping_ok"] = len(missing) == 0

    return result

