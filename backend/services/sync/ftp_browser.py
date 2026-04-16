"""
Navegación de directorios FTP/SFTP y resolución de archivos dinámicos.
Las funciones de listado (browse_ftp_sync, browse_ftp_directory) viven en downloaders.py
por conveniencia; este módulo añade la lógica de resolución de última versión.
"""
import logging

from services.sync.downloaders import browse_ftp_directory, browse_ftp_sync  # noqa: F401
from services.sync.utils import format_file_size  # noqa: F401

logger = logging.getLogger(__name__)


async def resolve_latest_file(supplier: dict, file_config: dict) -> str:
    """Si auto_latest está activado, busca el archivo más reciente con la misma extensión."""
    file_path = file_config.get('path', '')
    if not file_config.get('auto_latest'):
        return file_path

    dir_path = '/'.join(file_path.split('/')[:-1]) or '/'
    filename = file_path.split('/')[-1]
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    try:
        result = await browse_ftp_directory(supplier, dir_path)
        if result.get('status') != 'ok':
            return file_path

        candidates = [f for f in result['files'] if not f['is_dir'] and f['name'].lower().endswith(f'.{ext}')]
        if not candidates:
            return file_path

        # Ordenar por nombre descendente (funciona para nombres con fechas como _20260223)
        candidates.sort(key=lambda x: x['name'], reverse=True)
        latest = candidates[0]

        if latest['path'] != file_path:
            logger.info(f"Auto-latest: resuelto {file_path} -> {latest['path']}")

        return latest['path']
    except Exception as e:
        logger.warning(f"No se pudo resolver el archivo más reciente para {file_path}: {e}")
        return file_path
