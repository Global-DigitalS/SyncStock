# SyncStock Landing Page

Landing page de ventas independiente para SyncStock. Diseñada para desplegarse en un dominio separado de la aplicación principal.

## Configuración

1. Copia `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configura las variables de entorno:
   ```env
   # URL del backend (API)
   REACT_APP_API_URL=https://api.sync-stock.com
   
   # URL de la aplicación principal (para botones de registro/login)
   REACT_APP_APP_URL=https://app.sync-stock.com
   ```

## Desarrollo Local

```bash
# Instalar dependencias
yarn install

# Iniciar servidor de desarrollo
yarn start
```

La aplicación estará disponible en `http://localhost:3000`

## Compilación para Producción

```bash
# Compilar
yarn build

# Los archivos estarán en la carpeta /build
```

## Despliegue

### Opción 1: Hosting estático (Recomendado)

La landing page es una SPA estática que puede desplegarse en cualquier servicio de hosting:

- **Vercel**: `vercel --prod`
- **Netlify**: Arrastra la carpeta `/build`
- **Cloudflare Pages**: Conecta el repositorio
- **GitHub Pages**: Usa el workflow incluido
- **AWS S3 + CloudFront**: Sube los archivos a S3

### Opción 2: Servidor web tradicional

Configura tu servidor (Nginx/Apache) para servir la carpeta `/build` y redirigir todas las rutas a `index.html`:

**Nginx:**
```nginx
server {
    listen 80;
    server_name landing.sync-stock.com;
    root /var/www/landing/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## Personalización del Contenido

El contenido de la landing page se gestiona desde el panel de administración de SyncStock:

1. Accede a la app principal
2. Ve a **Admin > Landing Page**
3. Edita textos, características, testimonios, FAQ, etc.

Los cambios se reflejan automáticamente en la landing sin necesidad de redesplegar.

## Estructura

```
/landing
├── public/
│   └── index.html        # Template HTML
├── src/
│   ├── App.js            # Componente principal
│   ├── index.js          # Entry point
│   └── index.css         # Estilos globales
├── .env.example          # Variables de entorno
├── package.json          # Dependencias
├── tailwind.config.js    # Configuración Tailwind
└── README.md            # Este archivo
```

## Notas

- La landing consume la API del backend para obtener el contenido dinámico
- Si la API no está disponible, se muestra contenido por defecto
- Los botones de "Iniciar Sesión" y "Empezar Gratis" redirigen a la app principal
