# CLAUDE.md — StockHUB3 AI Assistant Guide

This file provides context for AI assistants (Claude Code, etc.) working on the StockHUB3 codebase.

---

## Project Overview

**StockHUB3** (also called "SupplierSync Pro") is a B2B SaaS platform for supplier catalog management and synchronization. It enables businesses to:

- Aggregate product catalogs from multiple suppliers (FTP, SFTP, URL, CSV, XLSX, XML)
- Manage multi-store synchronization (WooCommerce, Shopify, PrestaShop)
- Integrate with CRM systems (Dolibarr, Odoo)
- Publish and export customized catalogs with margin rules and custom pricing
- Monitor price history, stock levels, and sync events in real time
- Process payments via Stripe

**Language note**: The application UI and internal docs are primarily in Spanish (`es`).

---

## Repository Structure

```
StockHUB3/
├── backend/                    # FastAPI REST API (Python)
│   ├── routes/                 # 14 API route modules
│   ├── services/               # Business logic & integrations
│   ├── models/                 # Pydantic schemas (schemas.py)
│   ├── tests/                  # pytest test suites
│   ├── config.py               # App settings (env vars + config.json)
│   ├── server.py               # FastAPI app entry point
│   ├── requirements.txt        # Python dependencies
│   ├── DATABASE.md             # MongoDB schema reference
│   └── uploads/                # Uploaded product images
├── frontend/                   # React 19 SPA
│   ├── src/
│   │   ├── pages/              # 20+ page components
│   │   ├── components/         # 72+ reusable components
│   │   │   ├── ui/             # Radix UI wrappers
│   │   │   ├── dialogs/        # Modal dialog components
│   │   │   └── shared/         # Common shared components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # Utilities
│   │   ├── utils/              # Helper functions
│   │   ├── App.js              # Router + Auth Context + WebSocket Context
│   │   └── index.js            # Entry point
│   ├── package.json
│   └── build/                  # Production build output (gitignored)
├── landing/                    # Marketing landing page (React 18)
├── backend_test.py             # API integration test runner
├── install.sh                  # Automated Plesk installation script
├── update.sh                   # Zero-downtime update script
├── design_guidelines.json      # UI/UX design system specification
├── ODOO_INTEGRATION.md         # Odoo CRM integration docs
└── README-DEPLOY-PLESK.md      # Plesk deployment guide
```

---

## Technology Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.110+ |
| Server | Uvicorn |
| Database | MongoDB (Motor async driver 3.3+) |
| Auth | JWT (PyJWT), bcrypt |
| Scheduler | APScheduler 3.11 |
| Validation | Pydantic v2 |
| Rate Limiting | SlowAPI |
| Data Processing | Pandas, OpenPyXL, XlRd, xmltodict |
| FTP/SFTP | ftplib (stdlib), Paramiko |
| E-commerce | WooCommerce API, Shopify API |
| Payments | Stripe |
| Email | SMTP + Jinja2 templates |
| HTTP Client | Requests, aiohttp |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | React 19.0.0 |
| Routing | React Router DOM 7 |
| UI Components | Radix UI (20+ packages) |
| Styling | Tailwind CSS 3.4 |
| Forms | React Hook Form + Zod |
| Charts | Recharts |
| HTTP Client | Axios |
| Date Utils | date-fns |
| Excel Export | XLSX |
| Toasts | Sonner |
| Icons | Lucide React |
| Build Tool | CRACO (CRA override) |
| Drag & Drop | DND Kit |

---

## Architecture

### System Overview
```
React SPA (frontend)
    ↕ HTTPS + WebSocket
FastAPI (backend, port 8001)
    ↕ Motor (async)
MongoDB
```

### Backend Route Modules (`backend/routes/`)

| Module | Prefix | Key Responsibility |
|--------|--------|--------------------|
| `auth.py` | `/auth` | Register, login, logout, JWT, password reset |
| `suppliers.py` | `/suppliers` | CRUD, FTP/URL sync, column mapping |
| `products.py` | `/products` | Product inventory, search, filtering, image upload |
| `catalogs.py` | `/catalogs` | Multi-catalog CRUD, items, margin rules |
| `woocommerce.py` | `/woocommerce` | WooCommerce store connections and sync |
| `stores.py` | `/stores` | Multi-platform store configuration |
| `dashboard.py` | `/dashboard` | Analytics, metrics, recent activity |
| `subscriptions.py` | `/subscriptions` | Plans, billing, limits enforcement |
| `crm.py` | `/crm` | Dolibarr & Odoo integration, sync |
| `email.py` | `/email` | SMTP config, templates, test send |
| `stripe.py` | `/stripe` | Checkout sessions, webhooks |
| `admin.py` | `/admin` | Superadmin user/plan management |
| `webhooks.py` | `/webhooks` | Third-party webhook receivers |
| `setup.py` | `/setup` | Initial setup wizard, config management |

**Special endpoints:**
- `GET /health` — Root health check
- `GET /api/health` — API health check
- `WebSocket /ws/notifications/{user_id}` — Real-time notifications

### Backend Services (`backend/services/`)

| Service | Responsibility |
|---------|---------------|
| `auth.py` | JWT creation/validation, bcrypt hashing, RBAC permission check |
| `database.py` | MongoDB connection pooling, index creation |
| `sync.py` | FTP/URL downloads, CSV/XLSX/XML parsing, product upsert, notification triggers |
| `email_service.py` | SMTP integration, Jinja2 email templates |
| `config_manager.py` | Persistent config at `/etc/suppliersync/config.json` |
| `platforms.py` | E-commerce platform API integrations |
| `crm_scheduler.py` | Scheduled CRM sync jobs (Dolibarr, Odoo) |
| `unified_sync.py` | User-configured supplier sync scheduling |

### Frontend State Management

- **Auth Context** (`App.js`) — Global user object, login/logout, token state
- **WebSocket Context** (`App.js`) — Real-time notification connection
- **Local Storage** — Session persistence (`localStorage.user`)
- **Component State** — `useState` for forms, modals, tables
- **Axios Interceptors** — Automatic JWT cookie handling

---

## MongoDB Collections

See `backend/DATABASE.md` for full schema details.

| Collection | Purpose |
|------------|---------|
| `users` | User accounts with roles |
| `suppliers` | FTP/SFTP/URL data sources |
| `products` | Imported product inventory |
| `catalogs` | Multi-catalog definitions |
| `catalog_items` | Products in catalogs with custom pricing |
| `catalog_margin_rules` | Profit margin configurations per catalog |
| `woocommerce_configs` | WooCommerce store connections |
| `notifications` | System alerts (sync, stock, price) |
| `price_history` | Price change audit trail |
| `subscription_plans` | Plan tier definitions |
| `subscriptions` | User subscription assignments |
| `crm_connections` | Dolibarr/Odoo connection configs |

**ID convention**: All records use `id` as a UUID v4 string. The MongoDB `_id` field is always excluded from API responses. Never use MongoDB ObjectId for application-level IDs.

---

## Authentication & Authorization

### JWT Flow
1. User logs in → password verified with bcrypt
2. JWT token created containing `user_id`, `role`, expiry (default 7 days)
3. Token stored in **httpOnly, Secure, SameSite=Lax** cookie
4. Backend validates token via `get_current_user()` FastAPI dependency

### Role-Based Access Control

| Role | Suppliers | Catalogs | WooCommerce | Special Permissions |
|------|-----------|----------|-------------|---------------------|
| `superadmin` | Unlimited | Unlimited | Unlimited | manage_users, manage_limits, manage_settings, unlimited |
| `admin` | 50 | 20 | 10 | manage_settings |
| `user` | 10 | 5 | 2 | Standard CRUD + sync + export |
| `viewer` | 0 | 0 | 0 | Read-only |

### Security Patterns
- Rate limit: 5 requests/minute on `/auth/register`
- Per-endpoint rate limiting via `SlowAPI`
- Passwords: minimum validation + bcrypt hashing
- Input sanitization on all user inputs
- CORS: configurable origins (defaults to `*` in dev)

---

## Environment Variables

### Backend
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=supplier_sync_db
JWT_SECRET=<128-char hex string>
JWT_EXPIRATION_HOURS=168
CORS_ORIGINS=*
PRICE_CHANGE_THRESHOLD_PERCENT=10
LOW_STOCK_THRESHOLD=5
SUPPLIER_SYNC_INTERVAL_HOURS=6
WOOCOMMERCE_SYNC_INTERVAL_HOURS=12
MONGO_CONNECT_TIMEOUT_MS=5000
MONGO_SERVER_SELECTION_TIMEOUT_MS=5000
MONGO_MAX_POOL_SIZE=10
```

### Frontend
```env
REACT_APP_BACKEND_URL=https://yourdomain.com
```

### Persistent Configuration
Stored at `/etc/suppliersync/config.json` (outside app directory, survives updates).
Contains: `mongo_url`, `db_name`, `jwt_secret`, `cors_origins`, SMTP credentials.

---

## Development Commands

### Backend

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run development server
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Run tests
cd backend
pytest tests/

# Run API integration tests
python backend_test.py
```

### Frontend

```bash
# Install dependencies
cd frontend
yarn install   # or: npm install

# Development server
yarn start     # or: npm start

# Production build
yarn build     # or: npm build

# Run tests
yarn test      # or: npm test
```

### Production (systemd)

```bash
# Service management
sudo systemctl start suppliersync-backend
sudo systemctl stop suppliersync-backend
sudo systemctl restart suppliersync-backend
sudo systemctl status suppliersync-backend

# Logs
sudo journalctl -u suppliersync-backend -f

# Health checks
curl http://localhost:8001/health
curl http://localhost:8001/api/health
```

---

## Code Conventions

### Python (Backend)

- **Style**: snake_case for functions, variables, module names
- **Models**: Pydantic v2 `BaseModel` in `backend/models/schemas.py`
- **Routes**: One file per feature domain in `backend/routes/`
- **Dependencies**: Use FastAPI `Depends()` for auth (`get_current_user`), DB, services
- **IDs**: Always UUID v4 strings, never MongoDB ObjectId
- **API responses**: Exclude `_id`, always return `id`
- **Error handling**: `raise HTTPException(status_code=..., detail="...")`
- **Async**: All database operations use `await` with Motor async driver
- **Field exclusion**: Use `response_model_exclude` or manual dict cleanup to hide `_id`

```python
# Example: standard route pattern
@router.get("/{item_id}")
async def get_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    item = await db.collection.find_one({"id": item_id, "user_id": current_user["id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.pop("_id", None)  # Always remove MongoDB _id
    return item
```

### JavaScript/React (Frontend)

- **Style**: camelCase for variables/functions, PascalCase for components
- **File naming**: PascalCase for components (`ProductCard.js`), camelCase for hooks (`useProducts.js`)
- **API calls**: Axios with `withCredentials: true` for cookie-based auth
- **Forms**: React Hook Form + Zod schema validation
- **Toasts**: `import { toast } from "sonner"` — use `toast.success()`, `toast.error()`
- **Icons**: Lucide React (`import { IconName } from "lucide-react"`)
- **Styling**: Tailwind CSS utility classes; use `cn()` from `lib/utils` for conditional classes
- **UI components**: Prefer existing Radix UI wrappers in `components/ui/`

```javascript
// Example: standard API call pattern
const fetchData = async () => {
  try {
    const response = await axios.get(`${backendUrl}/api/resource`, {
      withCredentials: true,
    });
    setData(response.data);
  } catch (error) {
    toast.error("Error al cargar los datos");
    console.error(error);
  }
};
```

### API Design Patterns

- REST conventions: `GET` list, `POST` create, `GET /{id}` single, `PUT /{id}` update, `DELETE /{id}` delete
- All routes prefixed with `/api/` (mounted in `server.py`)
- Pagination: `skip` and `limit` query params (not cursor-based)
- Filtering: query params (`?search=`, `?category=`, `?supplier_id=`)
- Sorting: `?sort_by=field&sort_order=asc|desc`

---

## Testing

### Backend Tests (`backend/tests/`)

```bash
cd backend
pytest tests/
pytest tests/test_catalogs.py        # Specific module
pytest tests/ -v                     # Verbose
pytest tests/ -k "test_auth"         # Filter by name
```

Test files cover:
- `test_admin_panel.py` — Admin user management
- `test_catalogs.py` — Catalog CRUD and items
- `test_crm_dolibarr.py` — CRM integration
- `test_product_detail.py` — Product operations
- `test_products_sorting_price_history.py` — Sorting and price history
- `test_roles_users_websocket.py` — RBAC and WebSocket
- `test_stripe_checkout_sftp.py` — Stripe and SFTP
- `test_stores_multiplatform.py` — Multi-store sync
- `test_url_connection.py` — URL-based supplier connections
- And more...

Test results are archived in `test_reports/` as JSON files.

### Integration Tests

```bash
# Full API integration test suite
python backend_test.py
```

---

## Deployment

### Target Environments
- Plesk Obsidian 18.0+ (primary)
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / Rocky Linux 8+
- Minimum: 1 GB RAM, 10 GB disk, ports 80/443/8001 open

### Installation
```bash
sudo bash install.sh   # Full automated setup
```

### Updates (zero-downtime)
```bash
sudo bash update.sh    # Preserves /etc/suppliersync/config.json
```

### Nginx Configuration
- Frontend static files served from Nginx
- Backend proxied at `/api/` → `http://127.0.0.1:8001`
- WebSocket proxied at `/ws/` → `http://127.0.0.1:8001`

### No Docker
The project is not containerized. It deploys directly to the host OS with Nginx + systemd + MongoDB.

---

## Key Files for Common Tasks

| Task | Key Files |
|------|-----------|
| Add a new API route | `backend/routes/<new>.py`, register in `backend/server.py` |
| Add a Pydantic model | `backend/models/schemas.py` |
| Add a new page | `frontend/src/pages/<NewPage>.js`, add route in `frontend/src/App.js` |
| Add a UI component | `frontend/src/components/ui/<Component>.js` |
| Modify DB schema | Update collection + document `backend/DATABASE.md` |
| Add env variable | `backend/config.py` + deployment docs |
| Add email template | `backend/services/email_service.py` |
| Add a cron job | `backend/services/unified_sync.py` or `crm_scheduler.py` |
| Modify auth/RBAC | `backend/services/auth.py` |
| Add a new test | `backend/tests/test_<feature>.py` |

---

## Design System

See `design_guidelines.json` for the full specification. Key points:

- **Primary font**: System/Tailwind default
- **UI language**: Spanish (all labels, messages, buttons in `es`)
- **Component library**: Radix UI primitives wrapped in `components/ui/`
- **Color approach**: Tailwind semantic colors (no hardcoded hex in JSX)
- **Icons**: Lucide React exclusively
- **Toast notifications**: Sonner (`toast.success`, `toast.error`, `toast.warning`, `toast.info`)
- **Empty states**: Use `<EmptyState />` from `components/shared/`
- **Modals**: Use `<Dialog>` from `components/ui/dialog`

---

## Common Pitfalls to Avoid

1. **Never use MongoDB ObjectId** as an application ID — always use UUID v4 strings
2. **Always remove `_id`** from MongoDB documents before returning in API responses
3. **Use `withCredentials: true`** on all Axios calls — auth is cookie-based, not header-based
4. **Spanish UI text** — all user-facing strings must be in Spanish
5. **Check subscription limits** before creating resources (suppliers, catalogs, WooCommerce stores)
6. **Use async/await** consistently in Python routes — never use sync blocking calls with Motor
7. **Do not modify `/etc/suppliersync/config.json`** path — it's the persistent config location
8. **Run `item.pop("_id", None)`** on every MongoDB document returned to the API client
9. **Rate limiting** — be aware of SlowAPI decorators when testing endpoints rapidly
10. **Frontend build** is not checked in — run `yarn build` before deployment

---

## WebSocket Real-Time Notifications

The backend maintains a `ConnectionManager` that broadcasts notifications to connected users.

- Endpoint: `ws://<host>/ws/notifications/{user_id}`
- Events: sync completion, price changes, low stock alerts, import errors
- Frontend connection managed in `App.js` WebSocket Context
- Reconnection: handled automatically by the frontend

---

## CRM Integrations

### Dolibarr
- REST API v1 integration
- Syncs: products, customers, orders
- Config stored in `crm_connections` collection
- Routes: `backend/routes/crm.py`

### Odoo
- XML-RPC protocol
- Syncs: products, partners, invoices
- Detailed docs: `ODOO_INTEGRATION.md`
- Config stored in `crm_connections` collection

---

## Subscription / Limits System

Enforce limits before creating resources:

```python
# Pattern used throughout routes
subscription = await get_user_subscription(user_id, db)
current_count = await db.suppliers.count_documents({"user_id": user_id})
if current_count >= subscription["max_suppliers"]:
    raise HTTPException(status_code=403, detail="Has alcanzado el límite de proveedores")
```

Plans are stored in `subscription_plans` collection and assigned via `subscriptions` collection.

---

## Git Workflow

- Primary branch: `master`
- Feature/AI branches: `claude/<description>-<session-id>`
- Commit messages: descriptive, may be in Spanish
- No CI/CD pipeline — manual deployment via scripts
