# Re-exporta todos los símbolos del módulo principal de sincronización.
# Los sub-módulos (notifications, downloaders, parsers, normalizer) contienen
# versiones extraídas de las funciones correspondientes para uso futuro.
# La lógica completa vive en _sync_original.py mientras la migración avanza.
from services.sync._sync_original import *  # noqa: F401, F403
from services.sync._sync_original import (  # noqa: F401
    SKUCache,
    BULK_BATCH_SIZE,
    PROGRESS_REPORT_INTERVAL,
    sanitize_ean_quotes,
    send_realtime_notification,
    bulk_upsert_products,
    prefetch_existing_products,
    download_file_from_ftp_sync,
    download_file_from_ftp,
    download_file_from_url_sync,
    download_file_from_url,
    parse_csv_content,
    parse_xlsx_content,
    parse_xls_content,
    parse_xml_content,
    normalize_product_data,
    apply_column_mapping,
    process_supplier_file,
    record_sync_history,
    sync_supplier,
    sync_all_suppliers,
    browse_ftp_sync,
    format_file_size,
    browse_ftp_directory,
    parse_text_file,
    extract_zip_files,
    resolve_latest_file,
    sync_supplier_multifile,
    get_woocommerce_client,
    mask_key,
    calculate_final_price,
    sync_woocommerce_store_price_stock,
    sync_all_woocommerce_stores,
    get_woocommerce_categories_sync,
    get_woocommerce_categories,
    create_woocommerce_category_sync,
    create_woocommerce_category,
    find_or_create_woocommerce_category,
    export_catalog_categories_to_woocommerce,
    fetch_all_store_products,
    extract_store_product_info,
    create_catalog_from_store_products,
)

# Versiones con soporte de operation_id (sobreescriben las del original)
from services.sync.notifications import (  # noqa: F401
    send_sync_progress,
    send_sync_complete,
    send_sync_error,
)
