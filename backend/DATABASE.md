# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS - SyncStock
# ============================================================================
#
# Este archivo documenta la estructura completa de MongoDB para la aplicación.
# Úsalo como referencia para configurar, migrar o restaurar la base de datos.
#
# Conexión por defecto (ver .env):
#   MONGO_URL = mongodb://localhost:27017
#   DB_NAME   = test_database
#
# ============================================================================


# ============================================================================
# COLECCIONES Y SUS CAMPOS
# ============================================================================


# --- users -------------------------------------------------------------------
# Usuarios registrados en la aplicación.
# Se usa autenticación JWT con hash bcrypt para contraseñas.
#
# Campos:
#   id                                (str)  UUID v4 - Identificador único del usuario
#   email                             (str)  Email del usuario (único, se usa para login)
#   password                          (str)  Hash bcrypt de la contraseña
#   name                              (str)  Nombre del usuario
#   company                           (str)  Nombre de la empresa (opcional)
#   competitor_monitoring_catalog_id  (str)  ID del catálogo usado para monitoreo de precios (opcional)
#   created_at                        (str)  Fecha ISO 8601 de creación
#
# Índices recomendados:
#   { "email": 1 }           único
#   { "id": 1 }              único


# --- suppliers ---------------------------------------------------------------
# Proveedores configurados. Cada uno tiene su conexión FTP/URL y mapeo.
#
# Campos:
#   id               (str)   UUID v4
#   user_id          (str)   ID del usuario propietario
#   name             (str)   Nombre del proveedor
#   description      (str)   Descripción (opcional)
#   connection_type  (str)   "ftp" | "url"
#   file_url         (str)   URL de descarga directa (si connection_type = "url")
#   ftp_schema       (str)   "ftp" | "ftps" | "sftp"
#   ftp_host         (str)   Host del servidor FTP
#   ftp_user         (str)   Usuario FTP
#   ftp_password     (str)   Contraseña FTP (almacenada en texto plano)
#   ftp_port         (int)   Puerto (21 por defecto, 22 para SFTP)
#   ftp_path         (str)   Ruta al archivo único en el FTP
#   ftp_paths        (list)  Lista de archivos múltiples para sincronización
#                            Cada elemento: {
#                              path:        (str) Ruta del archivo en el FTP
#                              role:        (str) "products" | "prices" | "stock" | "prices_qb" | "kit" | "min_qty" | "other"
#                              label:       (str) Nombre descriptivo del archivo
#                              separator:   (str) Separador CSV (";" por defecto)
#                              header_row:  (int) Fila de cabecera (1 por defecto)
#                              merge_key:   (str) Columna para fusionar datos entre archivos
#                              auto_latest: (bool) Si true, busca automáticamente el archivo más reciente
#                            }
#   ftp_mode         (str)   "passive" | "active"
#   file_format      (str)   "csv" | "xlsx" | "xls" | "xml"
#   csv_separator    (str)   Separador de columnas (";" por defecto)
#   csv_enclosure    (str)   Carácter de entrecomillado ('"' por defecto)
#   csv_line_break   (str)   Salto de línea ("\n" por defecto)
#   csv_header_row   (int)   Fila donde empieza la cabecera (1 por defecto)
#   column_mapping   (dict)  Mapeo personalizado de columnas del archivo a campos del sistema
#                            Ejemplo: { "sku": "Referencia", "name": "Nombre", "price": "PVP" }
#   detected_columns (list)  Columnas detectadas en la última sincronización
#   product_count    (int)   Número total de productos del proveedor
#   last_sync        (str)   Fecha ISO 8601 de la última sincronización
#   created_at       (str)   Fecha ISO 8601 de creación
#
# Índices recomendados:
#   { "id": 1 }              único
#   { "user_id": 1 }


# --- products ----------------------------------------------------------------
# Productos importados desde los proveedores. Un producto pertenece a un
# proveedor. La unificación por EAN se hace a nivel de consulta (aggregation).
#
# Campos:
#   id               (str)    UUID v4
#   user_id          (str)    ID del usuario propietario
#   supplier_id      (str)    ID del proveedor que lo suministra
#   supplier_name    (str)    Nombre del proveedor (desnormalizado para agilizar)
#   sku              (str)    Código SKU del proveedor
#   name             (str)    Nombre del producto
#   description      (str)    Descripción larga (opcional)
#   price            (float)  Precio de coste del proveedor
#   stock            (int)    Stock disponible del proveedor
#   category         (str)    Categoría (opcional)
#   brand            (str)    Marca (opcional)
#   ean              (str)    Código EAN/GTIN - CLAVE para unificación entre proveedores
#   weight           (float)  Peso en kg (opcional)
#   image_url        (str)    URL de la imagen principal (opcional)
#   attributes       (dict)   Atributos adicionales libres (opcional)
#   created_at       (str)    Fecha ISO 8601 de creación
#   updated_at       (str)    Fecha ISO 8601 de última actualización
#
#   --- Campos extendidos (editables desde la ficha de producto) ---
#   referencia             (str)   Referencia interna
#   part_number            (str)   Número de parte del fabricante
#   asin                   (str)   ASIN de Amazon
#   upc                    (str)   Código UPC
#   gtin                   (str)   Código GTIN
#   oem                    (str)   Código OEM
#   id_erp                 (str)   ID en el ERP externo
#   activado               (bool)  Producto activo para venta (true por defecto)
#   descatalogado          (bool)  Producto descatalogado (false por defecto)
#   condicion              (str)   "Nuevo" | "Usado" | "Reacondicionado"
#   activar_pos            (bool)  Visible en punto de venta
#   tipo_pack              (bool)  Es un pack de productos
#   vender_sin_stock       (bool)  Permitir venta sin stock
#   nuevo                  (str)   Indicador de novedad
#   fecha_disponibilidad   (str)   Fecha de disponibilidad (ISO 8601)
#   stock_disponible       (int)   Stock disponible propio
#   stock_fantasma         (int)   Stock virtual/fantasma
#   stock_market           (int)   Stock en marketplace
#   unid_caja              (int)   Unidades por caja
#   cantidad_minima        (int)   Cantidad mínima de compra
#   dias_entrega           (int)   Días estimados de entrega
#   cantidad_maxima_carrito (int)  Cantidad máxima permitida en carrito
#   resto_stock            (bool)  Mostrar resto de stock (true por defecto)
#   requiere_envio         (bool)  Requiere envío físico (true por defecto)
#   envio_gratis           (bool)  Envío gratuito
#   gastos_envio           (float) Coste de envío específico
#   largo                  (float) Largo en cm
#   ancho                  (float) Ancho en cm
#   alto                   (float) Alto en cm
#   tipo_peso              (str)   "gram" | "kilogram" | "ounce" | "pound"
#   formas_pago            (str)   "todas" | "especificas"
#   formas_envio           (str)   "todas" | "especificas"
#   permite_actualizar_coste (bool) Permitir que el proveedor actualice el precio
#   permite_actualizar_stock (bool) Permitir que el proveedor actualice el stock
#   tipo_cheque_regalo     (bool)  Es un cheque regalo
#
# Índices recomendados:
#   { "id": 1 }                           único
#   { "user_id": 1, "ean": 1 }            para unificación por EAN
#   { "supplier_id": 1, "sku": 1 }        único - evita duplicados por proveedor
#   { "user_id": 1, "stock": 1 }          para alertas de stock
#   { "user_id": 1, "category": 1 }       para filtrado por categoría


# --- catalogs ----------------------------------------------------------------
# Catálogos personalizados. Cada usuario puede tener varios catálogos,
# uno de ellos marcado como predeterminado.
#
# Campos:
#   id          (str)   UUID v4
#   user_id     (str)   ID del usuario propietario
#   name        (str)   Nombre del catálogo
#   description (str)   Descripción (opcional)
#   is_default  (bool)  Si es el catálogo predeterminado (solo uno por usuario)
#   created_at  (str)   Fecha ISO 8601 de creación
#
# Índices recomendados:
#   { "id": 1 }              único
#   { "user_id": 1 }


# --- catalog_items -----------------------------------------------------------
# Asociación de productos a catálogos. Un producto puede estar en
# múltiples catálogos con precio y nombre personalizados.
#
# Campos:
#   id           (str)    UUID v4
#   catalog_id   (str)    ID del catálogo
#   product_id   (str)    ID del producto
#   user_id      (str)    ID del usuario
#   custom_price (float)  Precio personalizado (null = usar precio del proveedor)
#   custom_name  (str)    Nombre personalizado (null = usar nombre original)
#   active       (bool)   Si el producto está activo en este catálogo
#   created_at   (str)    Fecha ISO 8601
#
# Índices recomendados:
#   { "id": 1 }                              único
#   { "catalog_id": 1, "product_id": 1 }     único - evita duplicados
#   { "catalog_id": 1, "active": 1 }         para listar productos activos


# --- catalog_margin_rules ----------------------------------------------------
# Reglas de margen de beneficio por catálogo.
# Se aplican en orden de prioridad al calcular el precio final.
#
# Campos:
#   id             (str)    UUID v4
#   catalog_id     (str)    ID del catálogo al que pertenece
#   user_id        (str)    ID del usuario
#   name           (str)    Nombre descriptivo de la regla
#   rule_type      (str)    "percentage" | "fixed"
#   value          (float)  Valor del margen (% o importe fijo)
#   apply_to       (str)    "all" | "category" | "supplier" | "product"
#   apply_to_value (str)    Valor del filtro (nombre categoría, ID proveedor, etc.)
#   priority       (int)    Prioridad (mayor = se aplica primero)
#   created_at     (str)    Fecha ISO 8601
#
# Índices recomendados:
#   { "id": 1 }              único
#   { "catalog_id": 1 }


# --- margin_rules ------------------------------------------------------------
# Reglas de margen globales (legacy, del catálogo único original).
# Misma estructura que catalog_margin_rules pero sin catalog_id.
#
# Campos:
#   id             (str)    UUID v4
#   user_id        (str)    ID del usuario
#   name           (str)    Nombre de la regla
#   rule_type      (str)    "percentage" | "fixed"
#   value          (float)  Valor del margen
#   apply_to       (str)    "all" | "category" | "supplier" | "product"
#   apply_to_value (str)    Valor del filtro
#   min_price      (float)  Precio mínimo para aplicar (opcional)
#   max_price      (float)  Precio máximo para aplicar (opcional)
#   priority       (int)    Prioridad
#   created_at     (str)    Fecha ISO 8601
#
# Índices recomendados:
#   { "id": 1 }              único
#   { "user_id": 1 }


# --- catalog (legacy) --------------------------------------------------------
# Catálogo único original (antes de la funcionalidad multi-catálogo).
# Se mantiene por compatibilidad. Usar catalog_items para nuevos datos.
#
# Campos:
#   id           (str)    UUID v4
#   product_id   (str)    ID del producto
#   user_id      (str)    ID del usuario
#   custom_price (float)  Precio personalizado
#   custom_name  (str)    Nombre personalizado
#   active       (bool)   Activo para exportación
#   created_at   (str)    Fecha ISO 8601
#
# Índices recomendados:
#   { "id": 1 }                          único
#   { "user_id": 1, "product_id": 1 }    único


# --- woocommerce_configs ----------------------------------------------------
# Configuraciones de tiendas WooCommerce para exportación y sincronización.
#
# Campos:
#   id                (str)   UUID v4
#   user_id           (str)   ID del usuario
#   name              (str)   Nombre descriptivo de la tienda
#   store_url         (str)   URL de la tienda WooCommerce (sin / final)
#   consumer_key      (str)   Consumer Key de la API REST de WooCommerce
#   consumer_secret   (str)   Consumer Secret de la API REST de WooCommerce
#   catalog_id        (str)   ID del catálogo asociado para sincronización
#   auto_sync_enabled (bool)  Si la sincronización automática está activa
#   is_connected      (bool)  Si la última prueba de conexión fue exitosa
#   last_sync         (str)   Fecha ISO 8601 de la última sincronización
#   products_synced   (int)   Número de productos sincronizados en la última sync
#   sync_status       (str)   "idle" | "syncing" | "success" | "error"
#   created_at        (str)   Fecha ISO 8601
#
# Índices recomendados:
#   { "id": 1 }                          único
#   { "user_id": 1 }
#   { "auto_sync_enabled": 1 }           para tareas programadas


# --- notifications -----------------------------------------------------------
# Notificaciones del sistema: alertas de stock, sincronización, exportación.
#
# Campos:
#   id           (str)   UUID v4
#   user_id      (str)   ID del usuario destinatario
#   type         (str)   "sync_complete" | "sync_error" | "stock_out" | "stock_low"
#                        | "woocommerce_export" | "price_change"
#   message      (str)   Mensaje descriptivo de la notificación
#   product_id   (str)   ID del producto relacionado (opcional)
#   product_name (str)   Nombre del producto (opcional, desnormalizado)
#   read         (bool)  Si la notificación ha sido leída
#   created_at   (str)   Fecha ISO 8601
#
# Índices recomendados:
#   { "id": 1 }                          único
#   { "user_id": 1, "read": 1 }          para contar no leídas
#   { "user_id": 1, "created_at": -1 }   para listar por fecha


# --- price_history -----------------------------------------------------------
# Historial de cambios de precio. Se crea automáticamente al sincronizar
# cuando el precio de un producto cambia respecto al valor anterior.
#
# Campos:
#   id                (str)    UUID v4
#   user_id           (str)    ID del usuario
#   product_id        (str)    ID del producto
#   product_name      (str)    Nombre del producto (desnormalizado)
#   old_price         (float)  Precio anterior
#   new_price         (float)  Precio nuevo
#   change_percentage (float)  Porcentaje de cambio ((new - old) / old * 100)
#   created_at        (str)    Fecha ISO 8601
#
# Índices recomendados:
#   { "id": 1 }                          único
#   { "user_id": 1, "created_at": -1 }
#   { "product_id": 1 }


# ============================================================================
# SCRIPT PARA CREAR ÍNDICES RECOMENDADOS
# ============================================================================
#
# Ejecutar en mongo shell o con pymongo para optimizar rendimiento:
#
#   mongosh test_database --eval '
#     db.users.createIndex({ "id": 1 }, { unique: true });
#     db.users.createIndex({ "email": 1 }, { unique: true });
#
#     db.suppliers.createIndex({ "id": 1 }, { unique: true });
#     db.suppliers.createIndex({ "user_id": 1 });
#
#     db.products.createIndex({ "id": 1 }, { unique: true });
#     db.products.createIndex({ "user_id": 1, "ean": 1 });
#     db.products.createIndex({ "supplier_id": 1, "sku": 1 }, { unique: true });
#     db.products.createIndex({ "user_id": 1, "stock": 1 });
#     db.products.createIndex({ "user_id": 1, "category": 1 });
#
#     db.catalogs.createIndex({ "id": 1 }, { unique: true });
#     db.catalogs.createIndex({ "user_id": 1 });
#
#     db.catalog_items.createIndex({ "id": 1 }, { unique: true });
#     db.catalog_items.createIndex({ "catalog_id": 1, "product_id": 1 }, { unique: true });
#     db.catalog_items.createIndex({ "catalog_id": 1, "active": 1 });
#
#     db.catalog_margin_rules.createIndex({ "id": 1 }, { unique: true });
#     db.catalog_margin_rules.createIndex({ "catalog_id": 1 });
#
#     db.margin_rules.createIndex({ "id": 1 }, { unique: true });
#     db.margin_rules.createIndex({ "user_id": 1 });
#
#     db.catalog.createIndex({ "id": 1 }, { unique: true });
#     db.catalog.createIndex({ "user_id": 1, "product_id": 1 }, { unique: true });
#
#     db.woocommerce_configs.createIndex({ "id": 1 }, { unique: true });
#     db.woocommerce_configs.createIndex({ "user_id": 1 });
#     db.woocommerce_configs.createIndex({ "auto_sync_enabled": 1 });
#
#     db.notifications.createIndex({ "id": 1 }, { unique: true });
#     db.notifications.createIndex({ "user_id": 1, "read": 1 });
#     db.notifications.createIndex({ "user_id": 1, "created_at": -1 });
#
#     db.price_history.createIndex({ "id": 1 }, { unique: true });
#     db.price_history.createIndex({ "user_id": 1, "created_at": -1 });
#     db.price_history.createIndex({ "product_id": 1 });
#   '
#
# ============================================================================


# --- competitors ---------------------------------------------------------------
# Competidores monitorizados para comparación de precios.
# Cada usuario puede registrar múltiples competidores (tiendas online).
#
# Campos:
#   id                (str)   UUID v4
#   user_id           (str)   ID del usuario propietario
#   name              (str)   Nombre del competidor (ej: "Amazon España")
#   base_url          (str)   URL base del competidor (ej: "https://www.amazon.es")
#   channel           (str)   Canal: amazon_es, pccomponentes, mediamarkt, fnac,
#                              el_corte_ingles, worten, coolmod, ldlc, alternate,
#                              web_directa, otro
#   country           (str)   Código de país ISO 3166-1 alpha-2 (ej: "ES")
#   active            (bool)  Si el competidor está activo para scraping
#   last_crawl_at     (str)   Fecha ISO 8601 del último crawl
#   last_crawl_status (str)   "success" | "error" | "partial"
#   created_at        (str)   Fecha ISO 8601 de creación
#
# Índices recomendados:
#   { "user_id": 1, "id": 1 }        único
#   { "user_id": 1, "active": 1 }


# --- price_snapshots -----------------------------------------------------------
# Capturas de precios de productos en tiendas de competidores.
# Cada snapshot es un registro inmutable de un precio en un momento dado.
#
# Campos:
#   id               (str)    UUID v4
#   user_id          (str)    ID del usuario propietario
#   competitor_id    (str)    ID del competidor
#   sku              (str)    SKU del producto (opcional)
#   ean              (str)    EAN/GTIN del producto (opcional)
#   product_name     (str)    Nombre del producto en la tienda del competidor
#   price            (float)  Precio actual del producto
#   original_price   (float)  Precio original / tachado (antes de descuento)
#   currency         (str)    Moneda ISO 4217 (ej: "EUR")
#   url              (str)    URL directa al producto en la tienda del competidor
#   seller           (str)    Vendedor (relevante en marketplaces como Amazon)
#   availability     (str)    "in_stock" | "out_of_stock" | "limited"
#   match_confidence (float)  Confianza del matching 0.0 - 1.0
#   matched_by       (str)    Método de matching: "ean", "sku", "fuzzy_name"
#   scraped_at       (str)    Fecha ISO 8601 del momento del scraping
#
# Índices recomendados:
#   { "sku": 1, "competitor_id": 1, "scraped_at": -1 }   consulta principal
#   { "ean": 1, "competitor_id": 1, "scraped_at": -1 }   consulta por EAN
#   { "competitor_id": 1, "scraped_at": -1 }              por competidor
#   { "user_id": 1, "scraped_at": -1 }                    por usuario


# --- price_alerts --------------------------------------------------------------
# Alertas de precio configuradas por el usuario.
# Se evalúan tras cada batch de scraping.
#
# Campos:
#   id                (str)    UUID v4
#   user_id           (str)    ID del usuario propietario
#   sku               (str)    SKU del producto (opcional, al menos uno de sku/ean)
#   ean               (str)    EAN del producto (opcional)
#   alert_type        (str)    "price_drop" | "price_below" | "competitor_cheaper" | "any_change"
#   threshold         (float)  Umbral en % o precio absoluto (según tipo)
#   channel           (str)    "app" | "email" | "webhook"
#   webhook_url       (str)    URL del webhook (solo si channel = "webhook")
#   active            (bool)   Si la alerta está activa
#   last_triggered_at (str)    Fecha ISO 8601 de la última vez que se disparó
#   trigger_count     (int)    Número de veces que se ha disparado
#   created_at        (str)    Fecha ISO 8601 de creación
#
# Índices recomendados:
#   { "user_id": 1, "id": 1 }        único
#   { "user_id": 1, "active": 1 }
#   { "sku": 1, "active": 1 }
#   { "ean": 1, "active": 1 }


# --- pending_matches -----------------------------------------------------------
# Matches de baja confianza pendientes de revisión manual.
# Se crean cuando el matching automático tiene un score < 0.85.
#
# Campos:
#   id                (str)    UUID v4
#   user_id           (str)    ID del usuario propietario
#   sku               (str)    SKU del producto propio
#   ean               (str)    EAN del producto propio
#   product_name      (str)    Nombre del producto propio
#   competitor_id     (str)    ID del competidor
#   snapshot_id       (str)    ID del snapshot candidato
#   candidate_name    (str)    Nombre del producto del competidor
#   candidate_url     (str)    URL del producto del competidor
#   match_score       (float)  Score de similitud 0.0 - 1.0
#   status            (str)    "pending" | "confirmed" | "rejected"
#   reviewed_at       (str)    Fecha ISO 8601 de revisión (null si pendiente)
#   created_at        (str)    Fecha ISO 8601 de creación
#
# Índices recomendados:
#   { "user_id": 1, "status": 1 }
#   { "sku": 1 }


# --- price_automation_rules ----------------------------------------------------
# Reglas de automatización inteligente de precios basadas en datos de competidores.
# Permiten ajustar precios automáticamente según diferentes estrategias.
#
# Campos:
#   id                (str)    UUID v4
#   user_id           (str)    ID del usuario propietario
#   name              (str)    Nombre descriptivo de la regla
#   strategy          (str)    "match_cheapest" | "undercut_by_amount" | "undercut_by_percent" |
#                              "margin_above_cost" | "price_cap"
#   value             (float)  Importe o porcentaje según la estrategia
#   apply_to          (str)    "all" | "category" | "supplier" | "competitor" | "product"
#   apply_to_value    (str)    ID o nombre del target (según apply_to)
#   min_price         (float)  Precio mínimo resultante (floor). Default 0
#   max_price         (float)  Precio máximo resultante (ceiling). Null = sin límite
#   catalog_id        (str)    Catálogo donde aplicar (null = precio base del producto)
#   priority          (int)    Mayor = se evalúa primero (como margin_rules)
#   active            (bool)   Si la regla está habilitada
#   last_applied_at   (str)    Fecha ISO 8601 de última aplicación
#   products_affected (int)    Número de productos afectados en última ejecución
#   created_at        (str)    Fecha ISO 8601 de creación
#
# Índices recomendados:
#   { "user_id": 1, "active": 1, "priority": -1 }
#   { "id": 1 }   único


# ============================================================================
# TAREAS PROGRAMADAS (APScheduler)
# ============================================================================
#
# 1. sync_all_suppliers
#    - Frecuencia: Cada 6 horas
#    - Acción: Sincroniza todos los proveedores configurados (FTP/URL).
#              Si el proveedor tiene ftp_paths (multi-archivo), usa
#              sync_supplier_multifile que además resuelve auto_latest.
#
# 2. sync_all_woocommerce_stores
#    - Frecuencia: Cada 12 horas
#    - Acción: Sincroniza precio y stock con todas las tiendas WooCommerce
#              que tengan auto_sync_enabled = true y un catálogo asociado.
#
# ============================================================================


# ============================================================================
# NOTAS IMPORTANTES
# ============================================================================
#
# 1. Todos los IDs son UUID v4 almacenados como string (no ObjectId de MongoDB).
#    El campo _id de MongoDB se excluye siempre de las respuestas de la API.
#
# 2. Las fechas se almacenan como string ISO 8601 con timezone UTC.
#    Ejemplo: "2026-02-23T15:30:00.000000+00:00"
#
# 3. Las contraseñas de usuario se hashean con bcrypt antes de almacenar.
#    Las contraseñas FTP se almacenan en texto plano (considerar cifrado).
#
# 4. La unificación de productos por EAN se hace mediante aggregation pipeline
#    en la consulta, no existe una colección separada de productos unificados.
#
# 5. El campo supplier_name en products está desnormalizado para evitar
#    joins en cada consulta. Se actualiza al sincronizar.
#
# 6. La colección "catalog" (singular) es legacy del catálogo único original.
#    La colección "catalogs" + "catalog_items" es el sistema multi-catálogo actual.
#
# ============================================================================
