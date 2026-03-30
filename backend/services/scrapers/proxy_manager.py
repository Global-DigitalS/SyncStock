"""
ProxyManager con Circuit Breaker para scraping resiliente.

Arquitectura:
- CLOSED (normal): el proxy funciona correctamente
- OPEN (bloqueado): el proxy está bloqueado, en cooldown
- HALF_OPEN (probando): probando si el proxy se recuperó

Cooldown exponencial: 1min → 5min → 30min → 1h
Detección automática de bloqueos por HTTP 429, 403, timeouts, CAPTCHAs.
"""
import asyncio
import logging
import time
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"       # Proxy operativo
    OPEN = "open"           # Proxy bloqueado, en cooldown
    HALF_OPEN = "half_open" # Probando recuperación


# Cooldowns escalonados (segundos)
COOLDOWN_LEVELS = [60, 300, 1800, 3600]  # 1min, 5min, 30min, 1h

# Umbral de fallos para abrir el circuit breaker
FAILURE_THRESHOLD = 3

# Número de éxitos en HALF_OPEN para cerrar el circuito
RECOVERY_THRESHOLD = 2

# Códigos HTTP que indican bloqueo
BLOCKED_STATUS_CODES = {403, 429, 451, 407}

# Patrones de CAPTCHA en URLs/contenido
CAPTCHA_PATTERNS = ["captcha", "cloudflare", "ddos-guard", "under-attack", "are you human"]


@dataclass
class ProxyEntry:
    """Entrada de proxy con estado de circuit breaker."""
    url: Optional[str]       # None = sin proxy (directo)
    host: str = "direct"
    port: int = 0

    # Circuit breaker
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    cooldown_level: int = 0   # índice en COOLDOWN_LEVELS
    opened_at: float = 0.0    # timestamp cuando se abrió
    half_open_at: float = 0.0

    # Estadísticas de vida
    total_requests: int = 0
    total_successes: int = 0
    total_failures: int = 0
    last_used_at: float = 0.0
    last_error: str = ""

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.total_successes / self.total_requests

    @property
    def current_cooldown(self) -> float:
        idx = min(self.cooldown_level, len(COOLDOWN_LEVELS) - 1)
        return COOLDOWN_LEVELS[idx]

    @property
    def is_available(self) -> bool:
        now = time.monotonic()
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            # Comprobar si ya pasó el cooldown
            if now - self.opened_at >= self.current_cooldown:
                self.state = CircuitState.HALF_OPEN
                self.half_open_at = now
                self.failure_count = 0  # Resetear conteo para prueba
                logger.info(f"Proxy {self.host} pasó a HALF_OPEN (cooldown completado)")
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            return True
        return False


class ProxyManager:
    """
    Gestión inteligente de proxies con circuit breaker por proxy.

    Uso básico:
        manager = ProxyManager(proxy_urls=["http://proxy1:8080", "http://proxy2:8080"])
        proxy = manager.get_proxy()
        try:
            result = await fetch(url, proxy=proxy)
            manager.record_success(proxy)
        except HTTPError as e:
            manager.record_failure(proxy, status_code=e.status)
    """

    def __init__(self, proxy_urls: Optional[List[str]] = None):
        """
        Args:
            proxy_urls: Lista de URLs de proxy. Si es None o vacía,
                        se usa una entrada "direct" (sin proxy).
        """
        self._proxies: List[ProxyEntry] = []
        self._lock = asyncio.Lock()

        if proxy_urls:
            for url in proxy_urls:
                entry = self._parse_proxy_url(url)
                self._proxies.append(entry)
            logger.info(f"ProxyManager iniciado con {len(self._proxies)} proxies")
        else:
            # Sin proxies: modo directo
            self._proxies.append(ProxyEntry(url=None, host="direct"))
            logger.info("ProxyManager iniciado en modo directo (sin proxies)")

    @staticmethod
    def _parse_proxy_url(url: str) -> ProxyEntry:
        """Parsea una URL de proxy a ProxyEntry."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or url
            port = parsed.port or 8080
            return ProxyEntry(url=url, host=host, port=port)
        except Exception:
            return ProxyEntry(url=url, host=url)

    def get_proxy(self) -> Optional[ProxyEntry]:
        """
        Devuelve el proxy disponible con mejor success rate.
        Siempre retorna un proxy (incluido 'direct' si no hay proxies).

        Returns:
            ProxyEntry con el mejor proxy disponible, o None si ninguno disponible.
        """
        available = [p for p in self._proxies if p.is_available]

        if not available:
            # Todos bloqueados: usar el que tenga el cooldown más próximo a vencer
            if self._proxies:
                now = time.monotonic()
                closest = min(
                    self._proxies,
                    key=lambda p: (now - p.opened_at) - p.current_cooldown
                )
                logger.warning(
                    f"Todos los proxies bloqueados. Usando {closest.host} (más próximo a recuperarse)"
                )
                return closest
            return None

        # Ordenar por: estado CLOSED > HALF_OPEN, luego por success rate
        def proxy_score(p: ProxyEntry) -> float:
            base = 1.0 if p.state == CircuitState.CLOSED else 0.5
            return base * p.success_rate

        best = max(available, key=proxy_score)
        best.last_used_at = time.monotonic()
        best.total_requests += 1
        return best

    def record_success(self, proxy: Optional[ProxyEntry]) -> None:
        """Registra un éxito para un proxy."""
        if proxy is None:
            return

        proxy.total_successes += 1
        proxy.success_count += 1

        if proxy.state == CircuitState.HALF_OPEN:
            if proxy.success_count >= RECOVERY_THRESHOLD:
                proxy.state = CircuitState.CLOSED
                proxy.failure_count = 0
                proxy.success_count = 0
                proxy.cooldown_level = max(0, proxy.cooldown_level - 1)  # Reducir nivel de cooldown
                logger.info(f"Proxy {proxy.host} recuperado → CLOSED (success rate: {proxy.success_rate:.1%})")

        logger.debug(f"✓ Proxy {proxy.host}: success (rate: {proxy.success_rate:.1%})")

    def record_failure(
        self,
        proxy: Optional[ProxyEntry],
        status_code: Optional[int] = None,
        error: str = "",
        html_content: str = "",
    ) -> None:
        """
        Registra un fallo para un proxy y activa el circuit breaker si necesario.

        Args:
            proxy: El proxy que falló
            status_code: Código HTTP de respuesta (429, 403, etc.)
            error: Descripción del error (timeout, connection, etc.)
            html_content: Contenido HTML para detectar CAPTCHA
        """
        if proxy is None:
            return

        proxy.total_failures += 1
        proxy.last_error = error or f"HTTP {status_code}"

        # Determinar si es un bloqueo severo
        is_hard_block = (
            status_code in BLOCKED_STATUS_CODES or
            self._detect_captcha(html_content) or
            "captcha" in error.lower() or
            "blocked" in error.lower()
        )

        if is_hard_block:
            # Bloqueo duro: abrir circuito inmediatamente
            self._open_circuit(proxy, reason=f"Hard block (HTTP {status_code})")
        else:
            # Fallo suave: incrementar contador
            proxy.failure_count += 1
            logger.debug(
                f"Proxy {proxy.host}: fallo #{proxy.failure_count}/{FAILURE_THRESHOLD} "
                f"(error: {proxy.last_error})"
            )

            if proxy.failure_count >= FAILURE_THRESHOLD:
                self._open_circuit(proxy, reason=f"Demasiados fallos ({proxy.failure_count})")

    def _open_circuit(self, proxy: ProxyEntry, reason: str = "") -> None:
        """Abre el circuit breaker para un proxy."""
        proxy.state = CircuitState.OPEN
        proxy.opened_at = time.monotonic()
        proxy.success_count = 0
        proxy.cooldown_level = min(proxy.cooldown_level + 1, len(COOLDOWN_LEVELS) - 1)

        cooldown = proxy.current_cooldown
        logger.warning(
            f"🔴 Proxy {proxy.host} → OPEN. Razón: {reason}. "
            f"Cooldown: {cooldown}s (nivel {proxy.cooldown_level})"
        )

    @staticmethod
    def _detect_captcha(content: str) -> bool:
        """Detecta si el contenido HTML contiene un CAPTCHA o bloqueo."""
        if not content:
            return False
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in CAPTCHA_PATTERNS)

    def get_stats(self) -> List[Dict]:
        """
        Devuelve estadísticas de todos los proxies.

        Returns:
            Lista de dicts con estadísticas por proxy.
        """
        stats = []
        now = time.monotonic()

        for proxy in self._proxies:
            cooldown_remaining = 0
            if proxy.state == CircuitState.OPEN:
                elapsed = now - proxy.opened_at
                cooldown_remaining = max(0, proxy.current_cooldown - elapsed)

            stats.append({
                "host": proxy.host,
                "url": proxy.url,
                "state": proxy.state.value,
                "success_rate": round(proxy.success_rate, 3),
                "total_requests": proxy.total_requests,
                "total_successes": proxy.total_successes,
                "total_failures": proxy.total_failures,
                "failure_count": proxy.failure_count,
                "cooldown_level": proxy.cooldown_level,
                "cooldown_remaining_s": round(cooldown_remaining),
                "last_error": proxy.last_error,
                "is_available": proxy.is_available,
            })

        return sorted(stats, key=lambda x: x["success_rate"], reverse=True)

    def get_best_available_count(self) -> int:
        """Número de proxies disponibles."""
        return sum(1 for p in self._proxies if p.is_available)

    def reset_proxy(self, host: str) -> bool:
        """Resetea manualmente el estado de un proxy (para administración)."""
        for proxy in self._proxies:
            if proxy.host == host:
                proxy.state = CircuitState.CLOSED
                proxy.failure_count = 0
                proxy.success_count = 0
                proxy.cooldown_level = 0
                proxy.last_error = ""
                logger.info(f"Proxy {host} reseteado manualmente")
                return True
        return False

    def add_proxy(self, url: str) -> None:
        """Agrega un proxy dinámicamente."""
        entry = self._parse_proxy_url(url)
        # Evitar duplicados
        existing_hosts = {p.host for p in self._proxies}
        if entry.host not in existing_hosts:
            self._proxies.append(entry)
            logger.info(f"Proxy {entry.host} agregado dinámicamente")

    def remove_proxy(self, host: str) -> bool:
        """Elimina un proxy dinámicamente."""
        original_count = len(self._proxies)
        self._proxies = [p for p in self._proxies if p.host != host]
        removed = len(self._proxies) < original_count
        if removed:
            logger.info(f"Proxy {host} eliminado")
        return removed


# ──────────────────────────────────────────────────────────────────────────────
# Instancia global singleton
# ──────────────────────────────────────────────────────────────────────────────

# Carga URLs de proxies desde config/env si existen
def _load_proxy_urls() -> List[str]:
    """Carga URLs de proxies desde variables de entorno."""
    import os
    proxy_env = os.environ.get("SCRAPER_PROXY_URLS", "")
    if not proxy_env:
        return []
    return [url.strip() for url in proxy_env.split(",") if url.strip()]


proxy_manager = ProxyManager(proxy_urls=_load_proxy_urls())
