import asyncio
import ftplib
import io
import ipaddress
import logging
import random
import socket
from datetime import datetime
from urllib.parse import urlparse

import paramiko
import requests

from config import (
    FTP_CONNECTION_TIMEOUT,
    FTP_DOWNLOAD_TIMEOUT,
    MAX_DOWNLOAD_SIZE,
    SOCKET_CONNECTION_TIMEOUT,
    URL_DOWNLOAD_TIMEOUT,
    URL_REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Hostnames bloqueados explícitamente por string antes de resolución DNS (anti-SSRF)
_BLOCKED_HOSTNAMES = frozenset({
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
})


def download_file_from_ftp_sync(supplier: dict) -> bytes:
    schema = supplier.get('ftp_schema', 'ftp').lower()
    host = supplier.get('ftp_host')
    port = supplier.get('ftp_port', 21)
    user = supplier.get('ftp_user', '')
    password = supplier.get('ftp_password', '')
    file_path = supplier.get('ftp_path', '')
    mode = supplier.get('ftp_mode', 'passive')
    if not host or not file_path:
        raise ValueError("FTP host and path are required")
    logger.info(f"Connecting to {schema.upper()}://{host}:{port}{file_path}")
    content = io.BytesIO()
    if schema == 'sftp':
        port = port or 22
        sock = socket.create_connection((host, port), timeout=SOCKET_CONNECTION_TIMEOUT)
        transport = paramiko.Transport(sock)
        transport.connect(username=user, password=password)
        transport.set_keepalive(30)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get_channel().settimeout(120)
        try:
            sftp.getfo(file_path, content)
            logger.info(f"SFTP download completed: {content.tell()} bytes")
        finally:
            sftp.close()
            transport.close()
    else:
        port = port or 21
        ftp = ftplib.FTP_TLS() if schema == 'ftps' else ftplib.FTP()
        try:
            ftp.connect(host, port, timeout=FTP_CONNECTION_TIMEOUT)
            ftp.login(user or 'anonymous', password or '')
            if schema == 'ftps':
                ftp.prot_p()
            ftp.set_pasv(mode == 'passive')
            logger.info(f"FTP connected, downloading {file_path}")
            ftp.retrbinary(f'RETR {file_path}', content.write)
            logger.info(f"FTP download completed: {content.tell()} bytes")
        finally:
            try:
                ftp.quit()
            except Exception:
                pass
    content.seek(0)
    return content.read()


async def download_file_from_ftp(supplier: dict) -> bytes:
    """Download file from FTP/SFTP with retry logic and exponential backoff."""
    loop = asyncio.get_running_loop()
    max_retries = 3
    timeout = FTP_DOWNLOAD_TIMEOUT  # Configurable via environment variable

    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, download_file_from_ftp_sync, supplier),
                timeout=timeout,
            )
        except TimeoutError:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)  # Exponential backoff: 2s, 4s
                logger.warning(f"FTP/SFTP timeout para '{supplier.get('name', '?')}' (intento {attempt + 1}/{max_retries}), esperando {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise Exception(f"Timeout descargando fichero FTP/SFTP del proveedor '{supplier.get('name', '?')}' tras {max_retries} intentos (límite: {timeout/60:.0f} minutos)")
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                logger.warning(f"Error FTP/SFTP para '{supplier.get('name', '?')}': {e} (intento {attempt + 1}/{max_retries}), reintentando en {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise


def _build_browser_session(url: str, auth=None) -> tuple:
    """Build a requests Session with realistic browser headers to avoid 403 blocks."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    # Realistic User-Agents (same as in http_client.py)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]

    session = requests.Session()
    session.headers.update({
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Referer': origin,
        'Cache-Control': 'max-age=0',
    })
    if auth:
        session.auth = auth
    return session


def _validate_url_ssrf(url: str) -> None:
    """Valida que la URL no apunte a IPs privadas/internas (prevención SSRF)."""
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https', 'ftp', 'sftp'):
        raise ValueError(f"Esquema de URL no permitido: {parsed.scheme}")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL sin hostname válido")
    # Bloqueo explícito por nombre de host antes de resolución DNS
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise ValueError(
            f"URL apunta a hostname interno bloqueado ({hostname}). "
            f"No se permiten conexiones a redes internas."
        )
    if '@' in (parsed.netloc.split(':')[0] if ':' in parsed.netloc else parsed.netloc):
        raise ValueError("URLs con @ en el host no están permitidas")
    try:
        resolved_ips = socket.getaddrinfo(hostname, parsed.port or 443)
        for family, _type, _proto, _canonname, sockaddr in resolved_ips:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                raise ValueError(
                    f"URL apunta a IP privada/reservada ({ip}). "
                    f"No se permiten conexiones a redes internas."
                )
    except socket.gaierror:
        raise ValueError(f"No se pudo resolver el hostname: {hostname}")


def download_file_from_url_sync(url: str, username: str = None, password: str = None) -> bytes:
    _validate_url_ssrf(url)
    logger.info(f"Downloading from URL: {url}")
    auth = (username, password) if username and password else None
    session = _build_browser_session(url, auth)

    def _do_request(verify_ssl: bool) -> bytes:
        response = session.get(url, timeout=URL_REQUEST_TIMEOUT, stream=True, verify=verify_ssl)
        response.raise_for_status()

        # Verificar Content-Length antes de descargar si está disponible
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_DOWNLOAD_SIZE:
            raise ValueError(
                f"Archivo demasiado grande: {int(content_length):,} bytes "
                f"(máximo permitido: {MAX_DOWNLOAD_SIZE:,} bytes / 500 MB)"
            )

        # Descargar en chunks con límite acumulado
        chunks = []
        downloaded = 0
        for chunk in response.iter_content(chunk_size=65536):
            downloaded += len(chunk)
            if downloaded > MAX_DOWNLOAD_SIZE:
                raise ValueError(
                    f"Descarga superó el límite de {MAX_DOWNLOAD_SIZE:,} bytes (500 MB). "
                    f"Verifica el archivo del proveedor."
                )
            chunks.append(chunk)

        content = b"".join(chunks)
        ssl_note = "" if verify_ssl else " (SSL verification skipped)"
        logger.info(f"URL download completed{ssl_note}: {len(content):,} bytes")
        return content

    try:
        return _do_request(verify_ssl=True)
    except requests.exceptions.SSLError as ssl_err:
        logger.warning(f"SSL verification failed for {url}: {ssl_err}")
        # SECURITY FIX: Don't automatically disable SSL - this is a MITM vector
        # Instead, log the error and fail - the user must explicitly configure self-signed certificates
        logger.error(f"SSL verification failed for supplier URL: {url}")
        logger.error("To use this URL, one of the following is required:")
        logger.error("1. Use a valid SSL certificate signed by a trusted CA")
        logger.error("2. Configure certificate pinning in supplier settings")
        logger.error("3. Contact administrator to add exception for this domain")
        raise Exception(
            f"SSL verification failed para {url}. Requiere certificado SSL válido. "
            f"Contacta al administrador para configurar excepciones."
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"URL download failed: {e}")
        raise Exception(f"Error descargando desde URL: {str(e)}")


async def download_file_from_url(url: str, username: str = None, password: str = None) -> bytes:
    """Download file from URL with retry logic and exponential backoff."""
    loop = asyncio.get_running_loop()
    max_retries = 3
    timeout = URL_DOWNLOAD_TIMEOUT  # Configurable via environment variable

    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, download_file_from_url_sync, url, username, password),
                timeout=timeout,
            )
        except TimeoutError:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)  # Exponential backoff: 2s, 4s
                logger.warning(f"Timeout descargando URL {url[:50]}... (intento {attempt + 1}/{max_retries}), esperando {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise Exception(f"Timeout descargando desde URL tras {max_retries} intentos (límite: {timeout/60:.0f} minutos): {url[:100]}")
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                logger.warning(f"Error descargando URL {url[:50]}...: {e} (intento {attempt + 1}/{max_retries}), reintentando en {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise


def browse_ftp_sync(config: dict, path: str = "/") -> dict:
    """
    Navega por el servidor FTP/SFTP y lista archivos y carpetas.
    Soporta: FTP, FTPS, SFTP
    """
    schema = config.get('ftp_schema', 'ftp').lower()
    host = config.get('ftp_host')
    port = config.get('ftp_port', 21)
    user = config.get('ftp_user', '')
    password = config.get('ftp_password', '')
    mode = config.get('ftp_mode', 'passive')

    if not host:
        return {"status": "error", "message": "FTP host is required", "files": [], "path": path}

    files = []
    error_message = None

    try:
        if schema == 'sftp':
            port = port or 22
            transport = paramiko.Transport((host, port))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            try:
                for attr in sftp.listdir_attr(path):
                    is_dir = attr.st_mode and (attr.st_mode & 0o170000 == 0o040000)
                    file_ext = attr.filename.rsplit('.', 1)[-1].lower() if '.' in attr.filename else ''
                    files.append({
                        "name": attr.filename,
                        "path": f"{path.rstrip('/')}/{attr.filename}",
                        "size": attr.st_size,
                        "size_formatted": format_file_size(attr.st_size),
                        "is_dir": is_dir,
                        "is_supported": file_ext in ['csv', 'xlsx', 'xls', 'xml', 'zip', 'txt'],
                        "extension": file_ext,
                        "modified": str(datetime.fromtimestamp(attr.st_mtime)) if attr.st_mtime else None
                    })
            finally:
                sftp.close()
                transport.close()
        else:
            port = port or 21
            ftp = ftplib.FTP_TLS() if schema == 'ftps' else ftplib.FTP()
            try:
                ftp.connect(host, port, timeout=FTP_CONNECTION_TIMEOUT)
                ftp.login(user or 'anonymous', password or '')
                if schema == 'ftps':
                    ftp.prot_p()
                ftp.set_pasv(mode == 'passive')

                # Intentar usar MLSD primero (más información)
                try:
                    for name, facts in ftp.mlsd(path):
                        if name in ['.', '..']:
                            continue
                        is_dir = facts.get('type') == 'dir'
                        size = int(facts.get('size', 0)) if not is_dir else 0
                        file_ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
                        modified = facts.get('modify', '')
                        if modified and len(modified) >= 14:
                            modified = f"{modified[:4]}-{modified[4:6]}-{modified[6:8]} {modified[8:10]}:{modified[10:12]}"
                        files.append({
                            "name": name,
                            "path": f"{path.rstrip('/')}/{name}",
                            "size": size,
                            "size_formatted": format_file_size(size),
                            "is_dir": is_dir,
                            "is_supported": file_ext in ['csv', 'xlsx', 'xls', 'xml', 'zip', 'txt'],
                            "extension": file_ext,
                            "modified": modified
                        })
                except Exception:
                    # Fallback a DIR si MLSD no está soportado
                    raw_lines = []
                    ftp.dir(path, raw_lines.append)
                    for line in raw_lines:
                        parts = line.split(None, 8)
                        if len(parts) >= 9:
                            name = parts[8]
                            if name in ['.', '..']:
                                continue
                            is_dir = line.startswith('d')
                            size = int(parts[4]) if not is_dir else 0
                            date_str = f"{parts[5]} {parts[6]} {parts[7]}"
                            file_ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
                            files.append({
                                "name": name,
                                "path": f"{path.rstrip('/')}/{name}",
                                "size": size,
                                "size_formatted": format_file_size(size),
                                "is_dir": is_dir,
                                "is_supported": file_ext in ['csv', 'xlsx', 'xls', 'xml', 'zip', 'txt'],
                                "extension": file_ext,
                                "modified": date_str
                            })
            finally:
                try:
                    ftp.quit()
                except Exception:
                    pass
    except ftplib.error_perm as e:
        error_message = f"Error de permisos FTP: {str(e)}"
        logger.error(f"FTP permission error browsing {path}: {e}")
    except Exception as e:
        error_message = f"Error de conexión: {str(e)}"
        logger.error(f"FTP browse error for {path}: {e}")

    # Ordenar: carpetas primero, luego archivos por nombre
    files.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

    # Calcular estadísticas
    total_files = len([f for f in files if not f["is_dir"]])
    supported_files = len([f for f in files if f.get("is_supported")])
    total_dirs = len([f for f in files if f["is_dir"]])

    return {
        "status": "ok" if not error_message else "error",
        "message": error_message,
        "path": path,
        "files": files,
        "stats": {
            "total_files": total_files,
            "supported_files": supported_files,
            "total_dirs": total_dirs
        }
    }


def format_file_size(size: int) -> str:
    """Formatea el tamaño de archivo en formato legible"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


async def browse_ftp_directory(config: dict, path: str = "/") -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, browse_ftp_sync, config, path)
