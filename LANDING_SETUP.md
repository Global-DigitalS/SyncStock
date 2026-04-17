# SyncStock Landing Page CMS - Setup Guide

Complete setup and integration guide for the SyncStock Landing Page CMS system. This document covers architecture, setup, API endpoints, page structure, and testing.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Setup Instructions](#setup-instructions)
3. [API Endpoints](#api-endpoints)
4. [Page Content Structure](#page-content-structure)
5. [Testing Guide](#testing-guide)
6. [Database Initialization](#database-initialization)
7. [Environment Variables](#environment-variables)

---

## Architecture Overview

The SyncStock Landing Page CMS is a three-subsystem architecture:

### 1. Backend API (FastAPI + MongoDB)

The backend provides REST endpoints for:
- **Branding Management**: Centralized company branding configuration
- **Page Management**: Public page content with versioning and publishing
- **Public Endpoints**: Non-authenticated access for landing page

**Key Files:**
- `backend/routes/branding.py` - Branding endpoints
- `backend/routes/pages.py` - Page endpoints
- `backend/services/page_service.py` - Page business logic
- `backend/services/branding_service.py` - Branding business logic
- `backend/repositories/page_repository.py` - Page data access
- `backend/repositories/branding_repository.py` - Branding data access

### 2. Super Admin Dashboard (React + Axios)

Admin interface for managing:
- Page creation, editing, and publishing
- Branding configuration and logo uploads
- Content management with rich text editor

**Key Files:**
- `frontend/src/pages/PageManager.js` - Main admin page
- `frontend/src/pages/PageEditor.js` - Page editing interface
- `frontend/src/components/PageForm.js` - Form component
- `frontend/src/hooks/usePageManager.js` - Admin state management
- `frontend/src/services/pageService.js` - Admin API client

### 3. Landing Page (React 18)

Public-facing marketing website that:
- Fetches branding and pages from the backend
- Displays content dynamically based on page slug
- Supports SEO and analytics
- Uses fallback defaults if API is unavailable

**Key Files:**
- `landing/src/hooks/useLandingData.js` - Data loading hook
- `landing/src/services/landingApiService.js` - Public API client
- `landing/src/constants/defaultBranding.js` - Fallback defaults
- `landing/src/pages/Home.js` - Home page
- `landing/src/components/DynamicPage.js` - Dynamic content renderer

### Data Flow

```
Super Admin Dashboard
        ↓
   Admin Forms
        ↓
Backend API (POST/PUT/DELETE)
        ↓
   MongoDB
        ↓
Backend API (GET /api/branding, /api/pages/*)
        ↓
Landing Page (useLandingData hook)
        ↓
Rendered HTML + Fallback Defaults
```

---

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.9+
- MongoDB 5.0+
- npm or yarn
- Git

### Step 1: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration (see Environment Variables section)
nano .env

# Run database initialization (creates indexes)
python -m pytest tests/  # Verify tests pass

# Initialize branding data
python seeds/init_branding.py

# Start development server
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### Step 2: Super Admin Dashboard Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
yarn install

# Copy environment template
cp .env.example .env.local

# Configure API URL
# Edit .env.local:
# REACT_APP_BACKEND_URL=http://localhost:8000

# Start development server
npm start
# or
yarn start
```

The admin dashboard will be available at `http://localhost:3000`

### Step 3: Landing Page Setup

```bash
# Navigate to landing directory
cd landing

# Install dependencies
npm install
# or
yarn install

# Copy environment template
cp .env.example .env.local

# Configure API URL
# Edit .env.local:
# REACT_APP_API_URL=http://localhost:8000/api/v1

# Start development server
npm start
# or
yarn start
```

The landing page will be available at `http://localhost:3001`

### Step 4: Complete Verification

1. Navigate to `http://localhost:3000` (admin dashboard)
2. Create a page via the PageManager interface
3. Set it as published
4. Navigate to `http://localhost:3001` (landing page)
5. Verify the page appears dynamically

---

## API Endpoints

### Branding Endpoints (Public)

All endpoints are public and do not require authentication.

#### GET /api/branding

Retrieves the current branding configuration.

**Response:** 200 OK
```json
{
  "company_name": "SyncStock",
  "app_slogan": "Sincronización de Inventario B2B",
  "logo_url": "https://...",
  "primary_color": "#4f46e5",
  "secondary_color": "#0f172a",
  "accent_color": "#10b981",
  "support_email": "support@syncstock.com",
  "social_links": {
    "facebook": "https://facebook.com/syncstock",
    "twitter": "https://twitter.com/syncstock",
    "linkedin": "https://linkedin.com/company/syncstock"
  },
  "subscription_plans": [...]
}
```

**Error Responses:**
- 404 Not Found - Branding not configured yet

---

### Page Endpoints (Public)

All page endpoints are public and do not require authentication.

#### GET /api/pages/public

Retrieves all published pages.

**Response:** 200 OK
```json
[
  {
    "id": "home-page-uuid",
    "slug": "inicio",
    "title": "Inicio",
    "content": "Welcome to SyncStock...",
    "meta_description": "SyncStock homepage",
    "meta_keywords": ["inventory", "sync"],
    "is_published": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-04-17T10:30:00Z"
  },
  ...
]
```

**Query Parameters:**
- None

---

#### GET /api/pages/public/{slug}

Retrieves a specific published page by slug.

**Parameters:**
- `slug` (string, required) - URL-friendly identifier (e.g., "acerca-de")

**Response:** 200 OK
```json
{
  "id": "about-page-uuid",
  "slug": "nosotros",
  "title": "Acerca de Nosotros",
  "content": "SyncStock es una plataforma...",
  "meta_description": "About SyncStock",
  "meta_keywords": ["about", "team", "mission"],
  "is_published": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-04-17T10:30:00Z"
}
```

**Error Responses:**
- 404 Not Found - Page with specified slug not found or not published

---

### Admin Endpoints (Protected)

Admin endpoints require authentication and admin permissions.

#### POST /api/pages

Creates a new page.

**Request Body:**
```json
{
  "slug": "nueva-pagina",
  "title": "Nueva Página",
  "content": "Contenido de la página...",
  "meta_description": "Page description",
  "meta_keywords": ["keyword1", "keyword2"],
  "is_published": false
}
```

**Response:** 201 Created
```json
{
  "id": "new-page-uuid",
  "slug": "nueva-pagina",
  "title": "Nueva Página",
  ...
}
```

---

#### PUT /api/pages/{id}

Updates an existing page.

**Parameters:**
- `id` (string, required) - Page UUID

**Request Body:** (same as POST)

**Response:** 200 OK

---

#### DELETE /api/pages/{id}

Deletes a page.

**Parameters:**
- `id` (string, required) - Page UUID

**Response:** 204 No Content

---

#### PUT /api/branding

Creates or updates branding configuration.

**Request Body:**
```json
{
  "company_name": "SyncStock",
  "logo_url": "https://...",
  "primary_color": "#4f46e5",
  "support_email": "support@syncstock.com",
  "subscription_plans": [...]
}
```

**Response:** 200 OK

---

## Page Content Structure

### Page JSON Structure

Pages follow this structure in the database:

```python
{
    # Unique identifier
    "id": "uuid-v4-string",
    
    # URL-friendly identifier
    "slug": "acerca-de",
    
    # Page title (for browser tab and SEO)
    "title": "Acerca de Nosotros",
    
    # Main content (HTML or markdown)
    "content": "<h1>Sobre SyncStock</h1><p>...</p>",
    
    # SEO meta description
    "meta_description": "Learn about SyncStock and our mission",
    
    # SEO meta keywords
    "meta_keywords": ["about", "team", "mission"],
    
    # Publication status
    "is_published": true,
    
    # Timestamps
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-04-17T10:30:00Z"
}
```

### Content Format

The `content` field can contain:

**HTML Content:**
```html
<h1>Título</h1>
<p>Párrafo con <strong>texto en negrita</strong> y <em>cursiva</em>.</p>
<ul>
  <li>Elemento de lista</li>
  <li>Otro elemento</li>
</ul>
<img src="image.jpg" alt="Descripción" />
```

**Markdown Content:**
```markdown
# Título

Párrafo con **negrita** y *cursiva*.

- Elemento de lista
- Otro elemento

![Descripción](image.jpg)
```

### Branding Configuration Fields

```json
{
  "company_name": "String - Nombre de la empresa",
  "app_slogan": "String - Eslogan de la aplicación",
  "logo_url": "String|null - URL del logo",
  "logo_dark_url": "String|null - URL del logo versión oscura",
  "favicon_url": "String|null - URL del favicon",
  "primary_color": "String - Color primario en hex (#4f46e5)",
  "secondary_color": "String - Color secundario en hex",
  "accent_color": "String - Color de acento en hex",
  "company_description": "String - Descripción de la empresa",
  "support_email": "String - Email de soporte",
  "support_phone": "String|null - Teléfono de soporte",
  "footer_text": "String - Texto personalizado del pie de página",
  "page_title": "String - Título base de las páginas",
  "hero_title": "String - Título del hero section",
  "hero_subtitle": "String - Subtítulo del hero section",
  "social_links": {
    "facebook": "String|null - URL de Facebook",
    "twitter": "String|null - URL de Twitter",
    "linkedin": "String|null - URL de LinkedIn",
    "instagram": "String|null - URL de Instagram"
  },
  "subscription_plans": [
    {
      "id": "plan-id",
      "name": "Plan Name",
      "description": "Plan description",
      "price_monthly": 29,
      "price_yearly": 290,
      "max_suppliers": 5,
      "max_catalogs": 3,
      "features": ["Feature 1", "Feature 2"]
    }
  ]
}
```

---

## Testing Guide

### Landing Page Hook Tests

The `useLandingData` hook has comprehensive tests that cover:

**Test Suite:** `landing/src/__tests__/useLandingData.test.js`

#### Run Tests

```bash
cd landing
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test useLandingData.test.js
```

#### Test Coverage

- **Successful Data Loading**: Branding, pages, and slug-based page loading
- **Error Handling**: Fallback to defaults when API fails
- **Slug-based Navigation**: Loading specific pages by slug
- **Cleanup**: Proper unmount handling to prevent memory leaks
- **Promise Handling**: Correct Promise.allSettled behavior

#### Example Test Cases

```javascript
// Test successful data loading
it("debería cargar branding y páginas correctamente", async () => {
  const { result } = renderHook(() => useLandingData());
  await waitFor(() => {
    expect(result.current.loading).toBe(false);
  });
  expect(result.current.branding).toBeDefined();
  expect(result.current.pages).toBeDefined();
});

// Test error handling
it("debería usar defaults cuando getBranding falla", async () => {
  landingApiService.getBranding.mockRejectedValue(new Error("Network error"));
  const { result } = renderHook(() => useLandingData());
  await waitFor(() => {
    expect(result.current.loading).toBe(false);
  });
  expect(result.current.branding).toEqual(DEFAULT_BRANDING);
});
```

### Backend Tests

```bash
cd backend

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_pages.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest --cov=. tests/
```

### Integration Testing

1. **Start all services:**
   ```bash
   # Terminal 1: Backend
   cd backend && uvicorn server:app --reload

   # Terminal 2: Admin Dashboard
   cd frontend && npm start

   # Terminal 3: Landing Page
   cd landing && npm start
   ```

2. **Test workflows:**
   - Navigate to admin dashboard (http://localhost:3000)
   - Create a new page with test content
   - Publish the page
   - Navigate to landing page (http://localhost:3001)
   - Verify the page appears with correct content
   - Test error handling by stopping the backend API
   - Verify fallback defaults are used

---

## Database Initialization

### Initialize Branding Data

The `init_branding.py` script creates the default branding configuration in MongoDB.

**Features:**
- Idempotent: Safe to run multiple times
- Creates default SyncStock branding if none exists
- Includes all subscription plans
- Does not modify existing branding

**Run:**
```bash
cd backend
python seeds/init_branding.py
```

**Output:**
```
Conectando a MongoDB: mongodb://localhost:27017
Base de datos: syncstock_db
Creando documento de branding predeterminado...
Documento de branding creado exitosamente.
  ID MongoDB: 66c1a2b3c4d5e6f7g8h9i0j1
  Empresa: SyncStock
  Color primario: #4f46e5
  Planes de suscripción: 4
Conexión a MongoDB cerrada.
```

### Manual MongoDB Setup

If you prefer manual setup:

```bash
# Connect to MongoDB
mongo

# Switch to database
use syncstock_db

# Create branding document
db.branding.insertOne({
  "company_name": "SyncStock",
  "app_slogan": "Sincronización de Inventario B2B",
  "logo_url": null,
  "primary_color": "#4f46e5",
  "secondary_color": "#0f172a",
  "accent_color": "#10b981",
  "support_email": "support@syncstock.com",
  "subscription_plans": [...]
})

# Create indexes for pages
db.pages.createIndex({ "slug": 1 }, { unique: true })
db.pages.createIndex({ "is_published": 1 })
db.pages.createIndex({ "created_at": -1 })
```

---

## Environment Variables

### Backend Configuration

Create `backend/.env`:

```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=syncstock_db

# Authentication
JWT_SECRET=your-256-bit-hex-secret-key-here
JWT_EXPIRATION_HOURS=168

# API
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Landing Page
LANDING_PAGE_URL=http://localhost:3001
LANDING_CONTACT_EMAIL=contact@syncstock.com
LANDING_ENDPOINTS_ENABLED=true
```

### Landing Page Configuration

Create `landing/.env.local`:

```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ENV=development

# Analytics (optional)
# REACT_APP_POSTHOG_KEY=phc_your_key_here
```

### Admin Dashboard Configuration

Create `frontend/.env.local`:

```env
# API Configuration
REACT_APP_BACKEND_URL=http://localhost:8000

# Environment
REACT_APP_ENV=development
```

---

## Troubleshooting

### Landing Page Shows Defaults Instead of API Data

**Problem:** Landing page displays default content instead of API data

**Solutions:**
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check CORS configuration in `backend/.env`
3. Verify `REACT_APP_API_URL` in `landing/.env.local`
4. Check browser console for API errors
5. Verify branding has been initialized: `python seeds/init_branding.py`

### Pages Not Appearing

**Problem:** Pages created in admin don't appear on landing page

**Solutions:**
1. Verify page is published (`is_published: true`)
2. Check page slug is correct
3. Hard refresh landing page (Ctrl+Shift+R or Cmd+Shift+R)
4. Verify API response: `curl http://localhost:8000/api/pages/public`

### Tests Failing

**Problem:** Jest or pytest tests fail

**Solutions:**
1. Install dependencies: `npm install` or `pip install -r requirements.txt`
2. Clear cache: `npm test -- --clearCache` or `pytest --cache-clear`
3. Check mock setup in tests
4. Verify MongoDB is running for integration tests

---

## Deployment Checklist

- [ ] Database configured and verified
- [ ] Branding initialized: `python seeds/init_branding.py`
- [ ] Environment variables set for all three services
- [ ] API endpoints tested with curl or Postman
- [ ] Landing page tests pass: `npm test`
- [ ] Backend tests pass: `pytest tests/`
- [ ] CORS origins configured correctly
- [ ] SSL/TLS certificates configured for production
- [ ] Database backups enabled
- [ ] API rate limiting configured
- [ ] Monitoring and logging enabled

---

## Additional Resources

- [Backend Database Schema](../backend/DATABASE.md)
- [API Documentation](../backend/docs/)
- [React Hooks Testing](https://react-hooks-testing-library.com/)
- [MongoDB Motor Documentation](https://motor.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
