"""
OBSOLETO — este archivo ha sido fragmentado en el paquete services/sync/.

Python carga el paquete (services/sync/__init__.py) con preferencia sobre
este módulo, por lo que este archivo nunca se importa en producción.

Conservado únicamente como referencia histórica. El original completo está en
services/sync/_sync_original.py

Módulos resultantes del refactor:
  services/sync/notifications.py  — WebSocket notifications (sin circular import)
  services/sync/downloaders.py    — Descargas FTP/SFTP/URL
  services/sync/parsers.py        — Parseo CSV/XLSX/XLS/XML/ZIP
  services/sync/normalizer.py     — Normalización de datos de producto
  services/sync/utils.py          — Helpers puros (calculate_final_price, mask_key…)
  services/sync/product_sync.py   — Orquestación sync de proveedores
  services/sync/woocommerce_sync.py — Integración WooCommerce/Shopify/PrestaShop
  services/sync/ftp_browser.py    — Navegación FTP interactiva
  services/sync/__init__.py       — Re-exporta todos los símbolos públicos
"""

# Este archivo no se carga. Cualquier 'from services.sync import X'
# resuelve al paquete services/sync/__init__.py, no a este módulo.
