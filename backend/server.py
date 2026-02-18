from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.responses import StreamingResponse
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import io
import csv
import json
import xmltodict
from openpyxl import load_workbook
import xlrd
import ftplib
import paramiko
import asyncio
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'stockhub-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Scheduler for automatic sync
scheduler = AsyncIOScheduler()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.add_job(sync_all_suppliers, 'interval', hours=12, id='sync_suppliers', replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started - FTP sync every 12 hours")
    yield
    # Shutdown
    scheduler.shutdown()
    client.close()

app = FastAPI(title="StockHub SaaS API", lifespan=lifespan)
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    company: Optional[str] = None
    created_at: str

class SupplierCreate(BaseModel):
    name: str
    description: Optional[str] = None
    # Conexión FTP
    ftp_schema: Optional[str] = "ftp"  # ftp, sftp
    ftp_host: Optional[str] = None
    ftp_user: Optional[str] = None
    ftp_password: Optional[str] = None
    ftp_port: Optional[int] = 21
    ftp_path: Optional[str] = None
    ftp_mode: Optional[str] = "passive"  # passive, active
    # Configuración CSV
    file_format: Optional[str] = "csv"  # csv, xlsx, xls, xml
    csv_separator: Optional[str] = ";"
    csv_enclosure: Optional[str] = '"'
    csv_line_break: Optional[str] = "\\n"
    csv_header_row: Optional[int] = 1
    # Mapeo de campos CSV
    csv_field_mapping: Optional[Dict[str, str]] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    # Conexión FTP
    ftp_schema: Optional[str] = None
    ftp_host: Optional[str] = None
    ftp_user: Optional[str] = None
    ftp_password: Optional[str] = None
    ftp_port: Optional[int] = None
    ftp_path: Optional[str] = None
    ftp_mode: Optional[str] = None
    # Configuración CSV
    file_format: Optional[str] = None
    csv_separator: Optional[str] = None
    csv_enclosure: Optional[str] = None
    csv_line_break: Optional[str] = None
    csv_header_row: Optional[int] = None
    # Mapeo de campos CSV
    csv_field_mapping: Optional[Dict[str, str]] = None

class SupplierResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    # Conexión FTP
    ftp_schema: Optional[str] = None
    ftp_host: Optional[str] = None
    ftp_user: Optional[str] = None
    ftp_port: Optional[int] = None
    ftp_path: Optional[str] = None
    ftp_mode: Optional[str] = None
    # Configuración CSV
    file_format: Optional[str] = None
    csv_separator: Optional[str] = None
    csv_enclosure: Optional[str] = None
    csv_line_break: Optional[str] = None
    csv_header_row: Optional[int] = None
    csv_field_mapping: Optional[Dict[str, str]] = None
    # Stats
    product_count: int = 0
    last_sync: Optional[str] = None
    created_at: str
    product_count: int = 0
    last_sync: Optional[str] = None
    created_at: str

class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: Optional[str] = None
    brand: Optional[str] = None
    ean: Optional[str] = None
    weight: Optional[float] = None
    image_url: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class ProductResponse(ProductBase):
    id: str
    supplier_id: str
    supplier_name: str
    created_at: str
    updated_at: str

class CatalogItemCreate(BaseModel):
    product_id: str
    custom_price: Optional[float] = None
    custom_name: Optional[str] = None
    active: bool = True

class CatalogItemResponse(BaseModel):
    id: str
    product_id: str
    product: ProductResponse
    custom_price: Optional[float] = None
    custom_name: Optional[str] = None
    final_price: float
    active: bool
    created_at: str

class MarginRuleCreate(BaseModel):
    name: str
    rule_type: str  # percentage, fixed, tiered
    value: float  # percentage or fixed amount
    apply_to: str  # all, category, supplier, product
    apply_to_value: Optional[str] = None  # category name, supplier id, product id
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    priority: int = 0

class MarginRuleResponse(MarginRuleCreate):
    id: str
    user_id: str
    created_at: str

class NotificationResponse(BaseModel):
    id: str
    type: str  # stock_low, stock_out, price_change
    message: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    read: bool
    created_at: str

class PriceHistoryResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    old_price: float
    new_price: float
    change_percentage: float
    created_at: str

class ExportRequest(BaseModel):
    platform: str  # prestashop, woocommerce, shopify
    catalog_ids: Optional[List[str]] = None

class DashboardStats(BaseModel):
    total_suppliers: int
    total_products: int
    total_catalog_items: int
    low_stock_count: int
    out_of_stock_count: int
    unread_notifications: int
    recent_price_changes: int

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password": hash_password(user.password),
        "name": user.name,
        "company": user.company,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id)
    return {"token": token, "user": {"id": user_id, "email": user.email, "name": user.name, "company": user.company}}

@api_router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    token = create_token(user["id"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "company": user.get("company")}}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**user)

# ==================== SUPPLIERS ENDPOINTS ====================

@api_router.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(supplier: SupplierCreate, user: dict = Depends(get_current_user)):
    supplier_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    supplier_doc = {
        "id": supplier_id,
        "user_id": user["id"],
        "name": supplier.name,
        "description": supplier.description,
        # Conexión FTP
        "ftp_schema": supplier.ftp_schema,
        "ftp_host": supplier.ftp_host,
        "ftp_user": supplier.ftp_user,
        "ftp_password": supplier.ftp_password,
        "ftp_port": supplier.ftp_port,
        "ftp_path": supplier.ftp_path,
        "ftp_mode": supplier.ftp_mode,
        # Configuración CSV
        "file_format": supplier.file_format,
        "csv_separator": supplier.csv_separator,
        "csv_enclosure": supplier.csv_enclosure,
        "csv_line_break": supplier.csv_line_break,
        "csv_header_row": supplier.csv_header_row,
        "csv_field_mapping": supplier.csv_field_mapping,
        # Stats
        "product_count": 0,
        "last_sync": None,
        "created_at": now
    }
    await db.suppliers.insert_one(supplier_doc)
    supplier_doc.pop("ftp_password", None)
    supplier_doc.pop("user_id", None)
    supplier_doc.pop("_id", None)
    return SupplierResponse(**supplier_doc)

@api_router.get("/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(user: dict = Depends(get_current_user)):
    suppliers = await db.suppliers.find({"user_id": user["id"]}, {"_id": 0, "ftp_password": 0, "user_id": 0}).to_list(1000)
    return [SupplierResponse(**s) for s in suppliers]

@api_router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str, user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]}, {"_id": 0, "ftp_password": 0, "user_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return SupplierResponse(**supplier)

@api_router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: str, supplier: SupplierUpdate, user: dict = Depends(get_current_user)):
    existing = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    update_data = {k: v for k, v in supplier.model_dump().items() if v is not None}
    if update_data:
        await db.suppliers.update_one({"id": supplier_id}, {"$set": update_data})
    
    updated = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0, "ftp_password": 0, "user_id": 0})
    return SupplierResponse(**updated)

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, user: dict = Depends(get_current_user)):
    result = await db.suppliers.delete_one({"id": supplier_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    await db.products.delete_many({"supplier_id": supplier_id})
    return {"message": "Proveedor eliminado"}

# ==================== FILE PARSING HELPERS ====================

def parse_csv_content(content: bytes) -> List[dict]:
    try:
        decoded = content.decode('utf-8')
    except:
        decoded = content.decode('latin-1')
    reader = csv.DictReader(io.StringIO(decoded))
    return list(reader)

def parse_xlsx_content(content: bytes) -> List[dict]:
    wb = load_workbook(filename=io.BytesIO(content), read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).lower().strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
    return [dict(zip(headers, row)) for row in rows[1:] if any(row)]

def parse_xls_content(content: bytes) -> List[dict]:
    wb = xlrd.open_workbook(file_contents=content)
    ws = wb.sheet_by_index(0)
    headers = [str(ws.cell_value(0, c)).lower().strip() for c in range(ws.ncols)]
    result = []
    for r in range(1, ws.nrows):
        row = {headers[c]: ws.cell_value(r, c) for c in range(ws.ncols)}
        result.append(row)
    return result

def parse_xml_content(content: bytes) -> List[dict]:
    try:
        decoded = content.decode('utf-8')
    except:
        decoded = content.decode('latin-1')
    data = xmltodict.parse(decoded)
    # Try to find the products list
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
    """Normalize different field names to our standard format"""
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
                    except:
                        value = 0.0
                elif field == 'stock':
                    try:
                        value = int(float(str(value).replace(',', '.')))
                    except:
                        value = 0
                result[field] = value
                break
    
    return result

# ==================== PRODUCTS ENDPOINTS ====================

@api_router.post("/products/import/{supplier_id}")
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
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado. Use CSV, XLSX, XLS o XML")
    except Exception as e:
        logger.error(f"Error parsing file: {e}")
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
            "sku": normalized.get('sku'),
            "name": normalized.get('name'),
            "description": normalized.get('description'),
            "price": normalized.get('price', 0),
            "stock": normalized.get('stock', 0),
            "category": normalized.get('category'),
            "brand": normalized.get('brand'),
            "ean": normalized.get('ean'),
            "weight": normalized.get('weight'),
            "image_url": normalized.get('image_url'),
            "supplier_id": supplier_id,
            "supplier_name": supplier["name"],
            "user_id": user["id"],
            "updated_at": now
        }
        
        if existing:
            # Track price changes
            if existing.get('price') != product_doc['price']:
                await db.price_history.insert_one({
                    "id": str(uuid.uuid4()),
                    "product_id": existing["id"],
                    "product_name": product_doc["name"],
                    "old_price": existing.get('price', 0),
                    "new_price": product_doc['price'],
                    "change_percentage": ((product_doc['price'] - existing.get('price', 0)) / existing.get('price', 1)) * 100 if existing.get('price', 0) > 0 else 0,
                    "user_id": user["id"],
                    "created_at": now
                })
            
            # Track stock changes
            if existing.get('stock', 0) > 0 and product_doc['stock'] == 0:
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()),
                    "type": "stock_out",
                    "message": f"Producto '{product_doc['name']}' sin stock",
                    "product_id": existing["id"],
                    "product_name": product_doc["name"],
                    "user_id": user["id"],
                    "read": False,
                    "created_at": now
                })
            elif existing.get('stock', 0) > 5 and product_doc['stock'] <= 5 and product_doc['stock'] > 0:
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()),
                    "type": "stock_low",
                    "message": f"Producto '{product_doc['name']}' con stock bajo ({product_doc['stock']} unidades)",
                    "product_id": existing["id"],
                    "product_name": product_doc["name"],
                    "user_id": user["id"],
                    "read": False,
                    "created_at": now
                })
            
            await db.products.update_one({"id": existing["id"]}, {"$set": product_doc})
            updated += 1
        else:
            product_doc["id"] = str(uuid.uuid4())
            product_doc["created_at"] = now
            await db.products.insert_one(product_doc)
            imported += 1
    
    # Update supplier stats
    product_count = await db.products.count_documents({"supplier_id": supplier_id})
    await db.suppliers.update_one({"id": supplier_id}, {"$set": {"product_count": product_count, "last_sync": now}})
    
    return {"imported": imported, "updated": updated, "total": imported + updated}

@api_router.get("/products", response_model=List[ProductResponse])
async def get_products(
    supplier_id: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_stock: Optional[int] = None,
    max_stock: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    query = {"user_id": user["id"]}
    if supplier_id:
        query["supplier_id"] = supplier_id
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"ean": {"$regex": search, "$options": "i"}}
        ]
    if min_stock is not None:
        query["stock"] = {"$gte": min_stock}
    if max_stock is not None:
        query.setdefault("stock", {})["$lte"] = max_stock
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    
    products = await db.products.find(query, {"_id": 0, "user_id": 0}).skip(skip).limit(limit).to_list(limit)
    return [ProductResponse(**p) for p in products]

@api_router.get("/products/categories")
async def get_categories(user: dict = Depends(get_current_user)):
    categories = await db.products.distinct("category", {"user_id": user["id"], "category": {"$ne": None}})
    return categories

@api_router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, user: dict = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": user["id"]}, {"_id": 0, "user_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductResponse(**product)

# ==================== CATALOG ENDPOINTS ====================

@api_router.post("/catalog")
async def add_to_catalog(item: CatalogItemCreate, user: dict = Depends(get_current_user)):
    product = await db.products.find_one({"id": item.product_id, "user_id": user["id"]})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    existing = await db.catalog.find_one({"product_id": item.product_id, "user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Producto ya está en el catálogo")
    
    catalog_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    catalog_doc = {
        "id": catalog_id,
        "product_id": item.product_id,
        "user_id": user["id"],
        "custom_price": item.custom_price,
        "custom_name": item.custom_name,
        "active": item.active,
        "created_at": now
    }
    await db.catalog.insert_one(catalog_doc)
    return {"id": catalog_id, "message": "Producto añadido al catálogo"}

@api_router.get("/catalog")
async def get_catalog(
    active_only: bool = False,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    query = {"user_id": user["id"]}
    if active_only:
        query["active"] = True
    
    catalog_items = await db.catalog.find(query, {"_id": 0, "user_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Get margin rules for price calculation
    margin_rules = await db.margin_rules.find({"user_id": user["id"]}, {"_id": 0}).sort("priority", -1).to_list(100)
    
    result = []
    for item in catalog_items:
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0, "user_id": 0})
        if not product:
            continue
        
        if search and search.lower() not in product.get("name", "").lower() and search.lower() not in product.get("sku", "").lower():
            continue
        
        # Calculate final price
        base_price = item.get("custom_price") or product.get("price", 0)
        final_price = calculate_final_price(base_price, product, margin_rules)
        
        result.append({
            "id": item["id"],
            "product_id": item["product_id"],
            "product": ProductResponse(**product),
            "custom_price": item.get("custom_price"),
            "custom_name": item.get("custom_name"),
            "final_price": round(final_price, 2),
            "active": item.get("active", True),
            "created_at": item.get("created_at")
        })
    
    return result

def calculate_final_price(base_price: float, product: dict, rules: List[dict]) -> float:
    """Calculate final price applying margin rules"""
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
            break  # Apply first matching rule
    
    return final_price

@api_router.put("/catalog/{catalog_id}")
async def update_catalog_item(catalog_id: str, item: CatalogItemCreate, user: dict = Depends(get_current_user)):
    existing = await db.catalog.find_one({"id": catalog_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    
    update_data = {
        "custom_price": item.custom_price,
        "custom_name": item.custom_name,
        "active": item.active
    }
    await db.catalog.update_one({"id": catalog_id}, {"$set": update_data})
    return {"message": "Item actualizado"}

@api_router.delete("/catalog/{catalog_id}")
async def remove_from_catalog(catalog_id: str, user: dict = Depends(get_current_user)):
    result = await db.catalog.delete_one({"id": catalog_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return {"message": "Item eliminado del catálogo"}

# ==================== MARGIN RULES ENDPOINTS ====================

@api_router.post("/margin-rules", response_model=MarginRuleResponse)
async def create_margin_rule(rule: MarginRuleCreate, user: dict = Depends(get_current_user)):
    rule_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    rule_doc = {
        "id": rule_id,
        "user_id": user["id"],
        **rule.model_dump(),
        "created_at": now
    }
    await db.margin_rules.insert_one(rule_doc)
    rule_doc.pop("_id", None)
    return MarginRuleResponse(**rule_doc)

@api_router.get("/margin-rules", response_model=List[MarginRuleResponse])
async def get_margin_rules(user: dict = Depends(get_current_user)):
    rules = await db.margin_rules.find({"user_id": user["id"]}, {"_id": 0}).sort("priority", -1).to_list(100)
    return [MarginRuleResponse(**r) for r in rules]

@api_router.put("/margin-rules/{rule_id}", response_model=MarginRuleResponse)
async def update_margin_rule(rule_id: str, rule: MarginRuleCreate, user: dict = Depends(get_current_user)):
    existing = await db.margin_rules.find_one({"id": rule_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    
    await db.margin_rules.update_one({"id": rule_id}, {"$set": rule.model_dump()})
    updated = await db.margin_rules.find_one({"id": rule_id}, {"_id": 0})
    return MarginRuleResponse(**updated)

@api_router.delete("/margin-rules/{rule_id}")
async def delete_margin_rule(rule_id: str, user: dict = Depends(get_current_user)):
    result = await db.margin_rules.delete_one({"id": rule_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"message": "Regla eliminada"}

# ==================== EXPORT ENDPOINTS ====================

@api_router.post("/export")
async def export_catalog(request: ExportRequest, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"], "active": True}
    if request.catalog_ids:
        query["id"] = {"$in": request.catalog_ids}
    
    catalog_items = await db.catalog.find(query, {"_id": 0}).to_list(10000)
    margin_rules = await db.margin_rules.find({"user_id": user["id"]}, {"_id": 0}).sort("priority", -1).to_list(100)
    
    rows = []
    for item in catalog_items:
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0, "user_id": 0})
        if not product:
            continue
        
        base_price = item.get("custom_price") or product.get("price", 0)
        final_price = calculate_final_price(base_price, product, margin_rules)
        
        name = item.get("custom_name") or product.get("name", "")
        
        if request.platform == "prestashop":
            rows.append({
                "ID": product.get("id"),
                "Active (0/1)": "1",
                "Name*": name,
                "Categories (x,y,z...)": product.get("category", ""),
                "Price tax excl.": round(final_price, 2),
                "Tax rules ID": "1",
                "Wholesale price": product.get("price", 0),
                "On sale (0/1)": "0",
                "Discount amount": "0",
                "Discount percent": "0",
                "Discount from (yyyy-mm-dd)": "",
                "Discount to (yyyy-mm-dd)": "",
                "Reference #": product.get("sku", ""),
                "Supplier reference #": product.get("sku", ""),
                "Supplier": product.get("supplier_name", ""),
                "Manufacturer": product.get("brand", ""),
                "EAN13": product.get("ean", ""),
                "UPC": "",
                "Ecotax": "0",
                "Width": "",
                "Height": "",
                "Depth": "",
                "Weight": product.get("weight", ""),
                "Quantity": product.get("stock", 0),
                "Minimal quantity": "1",
                "Visibility": "both",
                "Additional shipping cost": "0",
                "Unity": "",
                "Unit price": "",
                "Short description": "",
                "Description": product.get("description", ""),
                "Tags (x,y,z...)": "",
                "Meta title": name,
                "Meta keywords": "",
                "Meta description": "",
                "URL rewritten": "",
                "Text when in stock": "En stock",
                "Text when backorder allowed": "",
                "Available for order (0 = No, 1 = Yes)": "1",
                "Product available date": "",
                "Product creation date": "",
                "Show price (0 = No, 1 = Yes)": "1",
                "Image URLs (x,y,z...)": product.get("image_url", ""),
                "Delete existing images (0 = No, 1 = Yes)": "0"
            })
        elif request.platform == "woocommerce":
            rows.append({
                "ID": "",
                "Type": "simple",
                "SKU": product.get("sku", ""),
                "Name": name,
                "Published": "1",
                "Is featured?": "0",
                "Visibility in catalog": "visible",
                "Short description": "",
                "Description": product.get("description", ""),
                "Date sale price starts": "",
                "Date sale price ends": "",
                "Tax status": "taxable",
                "Tax class": "",
                "In stock?": "1" if product.get("stock", 0) > 0 else "0",
                "Stock": product.get("stock", 0),
                "Backorders allowed?": "0",
                "Sold individually?": "0",
                "Weight (kg)": product.get("weight", ""),
                "Length (cm)": "",
                "Width (cm)": "",
                "Height (cm)": "",
                "Allow customer reviews?": "1",
                "Purchase note": "",
                "Sale price": "",
                "Regular price": round(final_price, 2),
                "Categories": product.get("category", ""),
                "Tags": "",
                "Shipping class": "",
                "Images": product.get("image_url", ""),
                "Download limit": "",
                "Download expiry days": "",
                "Parent": "",
                "Grouped products": "",
                "Upsells": "",
                "Cross-sells": "",
                "External URL": "",
                "Button text": "",
                "Position": "0",
                "Brands": product.get("brand", "")
            })
        elif request.platform == "shopify":
            rows.append({
                "Handle": product.get("sku", "").lower().replace(" ", "-"),
                "Title": name,
                "Body (HTML)": product.get("description", ""),
                "Vendor": product.get("brand", ""),
                "Product Category": product.get("category", ""),
                "Type": product.get("category", ""),
                "Tags": "",
                "Published": "TRUE",
                "Option1 Name": "Title",
                "Option1 Value": "Default Title",
                "Option2 Name": "",
                "Option2 Value": "",
                "Option3 Name": "",
                "Option3 Value": "",
                "Variant SKU": product.get("sku", ""),
                "Variant Grams": int(float(product.get("weight", 0) or 0) * 1000),
                "Variant Inventory Tracker": "shopify",
                "Variant Inventory Qty": product.get("stock", 0),
                "Variant Inventory Policy": "deny",
                "Variant Fulfillment Service": "manual",
                "Variant Price": round(final_price, 2),
                "Variant Compare At Price": "",
                "Variant Requires Shipping": "TRUE",
                "Variant Taxable": "TRUE",
                "Variant Barcode": product.get("ean", ""),
                "Image Src": product.get("image_url", ""),
                "Image Position": "1",
                "Image Alt Text": name,
                "Gift Card": "FALSE",
                "SEO Title": name,
                "SEO Description": product.get("description", "")[:160] if product.get("description") else "",
                "Google Shopping / Google Product Category": "",
                "Google Shopping / Gender": "",
                "Google Shopping / Age Group": "",
                "Google Shopping / MPN": product.get("sku", ""),
                "Google Shopping / AdWords Grouping": "",
                "Google Shopping / AdWords Labels": "",
                "Google Shopping / Condition": "new",
                "Google Shopping / Custom Product": "",
                "Google Shopping / Custom Label 0": "",
                "Google Shopping / Custom Label 1": "",
                "Google Shopping / Custom Label 2": "",
                "Google Shopping / Custom Label 3": "",
                "Google Shopping / Custom Label 4": "",
                "Variant Image": product.get("image_url", ""),
                "Variant Weight Unit": "kg",
                "Variant Tax Code": "",
                "Cost per item": product.get("price", 0),
                "Status": "active"
            })
    
    if not rows:
        raise HTTPException(status_code=400, detail="No hay productos para exportar")
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    
    output.seek(0)
    filename = f"catalog_{request.platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================== DASHBOARD ENDPOINTS ====================

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    total_suppliers = await db.suppliers.count_documents({"user_id": user["id"]})
    total_products = await db.products.count_documents({"user_id": user["id"]})
    total_catalog_items = await db.catalog.count_documents({"user_id": user["id"]})
    low_stock_count = await db.products.count_documents({"user_id": user["id"], "stock": {"$gt": 0, "$lte": 5}})
    out_of_stock_count = await db.products.count_documents({"user_id": user["id"], "stock": 0})
    unread_notifications = await db.notifications.count_documents({"user_id": user["id"], "read": False})
    
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_price_changes = await db.price_history.count_documents({"user_id": user["id"], "created_at": {"$gte": week_ago}})
    
    return DashboardStats(
        total_suppliers=total_suppliers,
        total_products=total_products,
        total_catalog_items=total_catalog_items,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        unread_notifications=unread_notifications,
        recent_price_changes=recent_price_changes
    )

@api_router.get("/dashboard/stock-alerts")
async def get_stock_alerts(user: dict = Depends(get_current_user)):
    low_stock = await db.products.find(
        {"user_id": user["id"], "stock": {"$gt": 0, "$lte": 5}},
        {"_id": 0, "user_id": 0}
    ).limit(10).to_list(10)
    
    out_of_stock = await db.products.find(
        {"user_id": user["id"], "stock": 0},
        {"_id": 0, "user_id": 0}
    ).limit(10).to_list(10)
    
    return {"low_stock": low_stock, "out_of_stock": out_of_stock}

# ==================== NOTIFICATIONS ENDPOINTS ====================

@api_router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    query = {"user_id": user["id"]}
    if unread_only:
        query["read"] = False
    
    notifications = await db.notifications.find(query, {"_id": 0, "user_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [NotificationResponse(**n) for n in notifications]

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": user["id"]},
        {"$set": {"read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return {"message": "Notificación marcada como leída"}

@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(get_current_user)):
    await db.notifications.update_many({"user_id": user["id"]}, {"$set": {"read": True}})
    return {"message": "Todas las notificaciones marcadas como leídas"}

# ==================== PRICE HISTORY ENDPOINTS ====================

@api_router.get("/price-history", response_model=List[PriceHistoryResponse])
async def get_price_history(
    product_id: Optional[str] = None,
    days: int = 30,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query = {"user_id": user["id"], "created_at": {"$gte": start_date}}
    if product_id:
        query["product_id"] = product_id
    
    history = await db.price_history.find(query, {"_id": 0, "user_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [PriceHistoryResponse(**h) for h in history]

# ==================== HEALTH CHECK ====================

@api_router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router and configure app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
