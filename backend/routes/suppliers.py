from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging

from services.database import db
from services.auth import get_current_user
from services.sync import (
    sync_supplier, sync_supplier_multifile,
    parse_csv_content, parse_xlsx_content,
    parse_xls_content, parse_xml_content, normalize_product_data,
    browse_ftp_directory
)
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
    supplier_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    supplier_doc = {
        "id": supplier_id, "user_id": user["id"],
        "name": supplier.name, "description": supplier.description,
        "connection_type": supplier.connection_type or "ftp",
        "file_url": supplier.file_url,
        "ftp_schema": supplier.ftp_schema, "ftp_host": supplier.ftp_host,
        "ftp_user": supplier.ftp_user, "ftp_password": supplier.ftp_password,
        "ftp_port": supplier.ftp_port, "ftp_path": supplier.ftp_path,
        "ftp_mode": supplier.ftp_mode,
        "file_format": supplier.file_format,
        "csv_separator": supplier.csv_separator, "csv_enclosure": supplier.csv_enclosure,
        "csv_line_break": supplier.csv_line_break, "csv_header_row": supplier.csv_header_row,
        "column_mapping": supplier.column_mapping,
        "product_count": 0, "last_sync": None, "created_at": now
    }
    await db.suppliers.insert_one(supplier_doc)
    supplier_doc.pop("ftp_password", None)
    supplier_doc.pop("user_id", None)
    supplier_doc.pop("_id", None)
    return SupplierResponse(**supplier_doc)


@router.get("/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(user: dict = Depends(get_current_user)):
    suppliers = await db.suppliers.find({"user_id": user["id"]}, {"_id": 0, "ftp_password": 0, "user_id": 0}).to_list(1000)
    return [SupplierResponse(**s) for s in suppliers]


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str, user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]}, {"_id": 0, "ftp_password": 0, "user_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return SupplierResponse(**supplier)


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: str, supplier: SupplierUpdate, user: dict = Depends(get_current_user)):
    existing = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    update_data = {k: v for k, v in supplier.model_dump().items() if v is not None}
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
    connection_type = supplier.get('connection_type', 'ftp')
    if connection_type == 'url':
        if not supplier.get('file_url'):
            raise HTTPException(status_code=400, detail="URL del archivo no configurada.")
    else:
        if not supplier.get('ftp_host') or not supplier.get('ftp_path'):
            raise HTTPException(status_code=400, detail="Configuración FTP incompleta.")
    try:
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
    return {
        "last_sync": supplier.get('last_sync'),
        "ftp_configured": bool(supplier.get('ftp_host') and supplier.get('ftp_path')),
        "product_count": supplier.get('product_count', 0)
    }


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
