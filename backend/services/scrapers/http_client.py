"""
Base HTTP client para scraping con rate limiting y respeto a robots.txt.
Diseñado para ser legal y respetuoso con los sitios objetivo.
"""
import asyncio
import hashlib
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import aiohttp

logger = logging.getLogger(__name__)

# User-Agent transparente que identifica el bot
_USER_AGENT = "SyncStockPriceBot/1.0 (+https://syncstock.app/bot; precio-comparador)"

# Headers por defecto para peticiones
_DEFAULT_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
}

# Tiempo mínimo entre peticiones al mismo dominio (segundos)
_DEFAULT_DELAY = 2.0

# Timeout por petición
_REQUEST_TIMEOUT = 15

# Máximo de reintentos por petición
_MAX_RETRIES = 2

# Cache de robots.txt (TTL 1 hora)
_ROBOTS_CACHE_TTL = 3600


class RobotsCache:
    """Cache en memoria de robots.txt por dominio."""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # domain -> (parser, fetched_at)

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
                return parser.can_fetch(_USER_AGENT, url)

        # Fetch robots.txt
        parser = RobotFileParser()
        try:
            async with session.get(
                robots_url,
                timeout=aiohttp.ClientTimeout(total=5),
                headers={"User-Agent": _USER_AGENT},
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
        return parser.can_fetch(_USER_AGENT, url)

    def get_crawl_delay(self, domain: str) -> Optional[float]:
        """Obtiene el Crawl-delay definido en robots.txt."""
        if domain in self._cache:
            parser, _ = self._cache[domain]
            delay = parser.crawl_delay(_USER_AGENT)
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
        """Espera el tiempo necesario antes de hacer una petición al dominio."""
        lock = self._get_lock(domain)
        async with lock:
            delay = crawl_delay if crawl_delay else self._default_delay
            now = time.monotonic()
            last = self._last_request.get(domain, 0)
            wait_time = delay - (now - last)
            if wait_time > 0:
                logger.debug(f"Rate limit: esperando {wait_time:.1f}s para {domain}")
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
    - Headers transparentes (identifica al bot)
    - Timeout configurado
    """

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT)
            connector = aiohttp.TCPConnector(
                limit=5,  # máx conexiones simultáneas
                limit_per_host=2,  # máx por host
                ttl_dns_cache=300,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=_DEFAULT_HEADERS,
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
        headers = dict(_DEFAULT_HEADERS)
        if extra_headers:
            headers.update(extra_headers)

        last_error = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                async with session.get(url, headers=headers, allow_redirects=True) as resp:
                    if resp.status == 200:
                        return await resp.text()
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
