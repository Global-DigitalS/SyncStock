"""
Base HTTP client para scraping con rate limiting y respeto a robots.txt.
Optimizado para ser invisible: User-Agents reales, headers realistas, delays aleatorios.
"""
import asyncio
import hashlib
import logging
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import aiohttp

logger = logging.getLogger(__name__)

# User-Agents reales de navegadores (para parecer invisible)
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

def _get_random_user_agent() -> str:
    """Obtiene un User-Agent aleatorio de navegador real."""
    return random.choice(_USER_AGENTS)

# Referers realistas (simular que vienes de búsquedas, otros sitios, etc.)
_REFERERS = [
    "https://www.google.com/",
    "https://www.google.es/",
    "https://www.bing.com/",
    "https://www.duckduckgo.com/",
    "https://www.ecosia.org/",
    # Sin referer (navegación directa)
    None,
    None,  # Más probabilidad de sin referer (comportamiento real)
]

def _get_random_referer() -> Optional[str]:
    """Obtiene un Referer aleatorio realista."""
    return random.choice(_REFERERS)

# Headers realistas que imitan un navegador real
def _get_realistic_headers(user_agent: Optional[str] = None, referer: Optional[str] = None) -> dict:
    """Genera headers realistas que parecen un navegador de verdad."""
    ua = user_agent or _get_random_user_agent()
    ref = referer if referer is not None else _get_random_referer()

    # Determinar el navegador para headers más específicos
    is_firefox = "Firefox" in ua
    is_safari = "Safari" in ua and "Chrome" not in ua

    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none" if ref is None else "cross-site",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    # Añadir Referer si existe
    if ref:
        headers["Referer"] = ref

    # Headers específicos por navegador
    if is_firefox:
        headers["Sec-GPC"] = "1"

    if not is_safari:  # Chrome/Edge/Firefox
        headers["sec-ch-ua"] = '"Not_A Brand";v="8", "Chromium";v="120"'
        headers["sec-ch-ua-mobile"] = "?0"
        headers["sec-ch-ua-platform"] = '"Windows"'

    return headers

# Tiempo mínimo entre peticiones al mismo dominio (segundos)
_DEFAULT_DELAY = 2.0

# Rango de delays aleatorios (segundos) para parecer más humano
_DELAY_RANGE = (1.0, 5.0)  # Entre 1 y 5 segundos

# Timeout por petición
_REQUEST_TIMEOUT = 15

# Máximo de reintentos por petición
_MAX_RETRIES = 2

# Cache de robots.txt (TTL 1 hora)
_ROBOTS_CACHE_TTL = 3600

# Cache de ETags (para HTTP 304 Not Modified)
class CacheHeadersStore:
    """Almacena ETags y Last-Modified para caching HTTP."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, str]] = {}  # url -> {etag, last_modified}

    def get_cache_headers(self, url: str) -> Dict[str, str]:
        """Obtiene headers de caché para una URL."""
        if url in self._cache:
            headers = {}
            cache = self._cache[url]
            if "etag" in cache:
                headers["If-None-Match"] = cache["etag"]
            if "last_modified" in cache:
                headers["If-Modified-Since"] = cache["last_modified"]
            return headers
        return {}

    def store_cache_headers(self, url: str, response_headers: aiohttp.ClientResponse):
        """Almacena ETag y Last-Modified de una respuesta."""
        cache = {}
        if "etag" in response_headers:
            cache["etag"] = response_headers["etag"]
        if "last-modified" in response_headers:
            cache["last_modified"] = response_headers["last-modified"]
        if cache:
            self._cache[url] = cache


# Instancia global de caché de headers
_cache_headers_store = CacheHeadersStore()


class RobotsCache:
    """Cache en memoria de robots.txt por dominio."""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # domain -> (parser, fetched_at)
        # User-Agent genérico para robots.txt (los servidores suelen permitir */)
        self._robots_ua = "*"

    async def is_allowed(self, url: str, session: aiohttp.ClientSession) -> bool:
        """Comprueba si la URL está permitida por robots.txt."""
        parsed = urlparse(url)
        domain = parsed.netloc
        robots_url = f"{parsed.scheme}://{domain}/robots.txt"

        now = time.monotonic()

        # Comprobar cache
        if domain in self._cache:
            parser, fetched_at = self._cache[domain]
            if now - fetched_at < _ROBOTS_CACHE_TTL:
                return parser.can_fetch(self._robots_ua, url)

        # Fetch robots.txt
        parser = RobotFileParser()
        try:
            async with session.get(
                robots_url,
                timeout=aiohttp.ClientTimeout(total=5),
                headers=_get_realistic_headers(),  # Use realistic headers for robots.txt too
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    parser.parse(text.splitlines())
                else:
                    # Si no existe robots.txt, permitir todo
                    parser.parse([])
        except Exception as e:
            logger.debug(f"No se pudo obtener robots.txt de {domain}: {e}")
            # Si falla, ser conservador pero permitir
            parser.parse([])

        self._cache[domain] = (parser, now)
        return parser.can_fetch(self._robots_ua, url)

    def get_crawl_delay(self, domain: str) -> Optional[float]:
        """Obtiene el Crawl-delay definido en robots.txt."""
        if domain in self._cache:
            parser, _ = self._cache[domain]
            delay = parser.crawl_delay(self._robots_ua)
            return float(delay) if delay else None
        return None


class RateLimiter:
    """Rate limiter por dominio basado en token bucket."""

    def __init__(self, default_delay: float = _DEFAULT_DELAY):
        self._default_delay = default_delay
        self._last_request: Dict[str, float] = {}  # domain -> timestamp
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, domain: str) -> asyncio.Lock:
        if domain not in self._locks:
            self._locks[domain] = asyncio.Lock()
        return self._locks[domain]

    async def wait(self, domain: str, crawl_delay: Optional[float] = None):
        """Espera el tiempo necesario antes de hacer una petición al dominio.
        Usa delays aleatorios para parecer más humano."""
        lock = self._get_lock(domain)
        async with lock:
            # Obtener delay base
            base_delay = crawl_delay if crawl_delay else self._default_delay

            # Añadir jitter aleatorio para parecer humano
            # Si base_delay < 2, usar el rango de delays aleatorios
            if base_delay < 2:
                actual_delay = random.uniform(_DELAY_RANGE[0], _DELAY_RANGE[1])
            else:
                # Si el servidor especifica un delay, respetar + pequeño jitter
                actual_delay = base_delay + random.uniform(0, 0.5)

            now = time.monotonic()
            last = self._last_request.get(domain, 0)
            wait_time = actual_delay - (now - last)

            if wait_time > 0:
                logger.debug(f"Rate limit: esperando {wait_time:.2f}s para {domain}")
                await asyncio.sleep(wait_time)

            self._last_request[domain] = time.monotonic()


# Instancias globales
_robots_cache = RobotsCache()
_rate_limiter = RateLimiter()


class ScraperHttpClient:
    """
    Cliente HTTP async para scraping con:
    - Rate limiting por dominio
    - Respeto a robots.txt
    - Reintentos con backoff exponencial
    - Headers realistas (parecer invisible)
    - Timeout configurado
    - Cookies por sesión (comportamiento de navegador)
    - ETag caching (HTTP 304 Not Modified)
    """

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._domain_cookies: Dict[str, aiohttp.CookieJar] = {}  # Cookies por dominio

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT)
            connector = aiohttp.TCPConnector(
                limit=5,  # máx conexiones simultáneas
                limit_per_host=2,  # máx por host
                ttl_dns_cache=300,
            )
            # Usar headers realistas aleatorios para parecer invisible
            headers = _get_realistic_headers()
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=headers,
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def fetch(
        self,
        url: str,
        respect_robots: bool = True,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Obtiene el HTML de una URL respetando robots.txt y rate limiting.

        Returns:
            HTML como string, o None si la petición falla o está bloqueada.
        """
        session = await self._get_session()
        parsed = urlparse(url)
        domain = parsed.netloc

        # 1. Comprobar robots.txt
        if respect_robots:
            allowed = await _robots_cache.is_allowed(url, session)
            if not allowed:
                logger.info(f"Bloqueado por robots.txt: {url}")
                return None

        # 2. Respetar Crawl-delay
        crawl_delay = _robots_cache.get_crawl_delay(domain)
        await _rate_limiter.wait(domain, crawl_delay)

        # 3. Fetch con reintentos
        # Usar headers realistas aleatorios + referer aleatorio para cada petición
        referer = _get_random_referer()
        headers = _get_realistic_headers(referer=referer)

        # Añadir headers de caché (If-None-Match, If-Modified-Since)
        cache_headers = _cache_headers_store.get_cache_headers(url)
        headers.update(cache_headers)

        if extra_headers:
            headers.update(extra_headers)

        last_error = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                async with session.get(url, headers=headers, allow_redirects=True) as resp:
                    if resp.status == 200:
                        # Guardar caché headers para la próxima vez
                        _cache_headers_store.store_cache_headers(url, resp.headers)
                        html = await resp.text()
                        logger.debug(f"✓ Descargado {url} (200 OK)")
                        return html
                    elif resp.status == 304:
                        # Not Modified - usar caché local (aunque no lo tengamos aquí)
                        logger.debug(f"✓ {url} no modificado (304 Not Modified) - usando caché del servidor")
                        return ""  # Retornar vacío, el servidor dice que no cambió
                    elif resp.status == 429:
                        # Too Many Requests: esperar y reintentar
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        logger.warning(f"429 Too Many Requests en {domain}. Esperando {retry_after}s")
                        await asyncio.sleep(min(retry_after, 60))
                        continue
                    elif resp.status in (403, 451):
                        logger.warning(f"Acceso denegado ({resp.status}) para {url}")
                        return None
                    elif resp.status >= 500:
                        logger.warning(f"Error del servidor ({resp.status}) para {url}")
                        last_error = f"HTTP {resp.status}"
                    else:
                        logger.warning(f"HTTP {resp.status} para {url}")
                        return None
            except asyncio.TimeoutError:
                last_error = "timeout"
                logger.warning(f"Timeout para {url} (intento {attempt + 1})")
            except aiohttp.ClientError as e:
                last_error = str(e)
                logger.warning(f"Error de conexión para {url}: {e} (intento {attempt + 1})")

            # Backoff exponencial entre reintentos
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(2 ** (attempt + 1))

        logger.error(f"Fallo definitivo para {url} tras {_MAX_RETRIES + 1} intentos: {last_error}")
        return None


# Instancia global reutilizable
scraper_client = ScraperHttpClient()
