import json
import re

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


class UUIDValidationMiddleware(BaseHTTPMiddleware):
    """Valida que path params terminados en _id sean UUIDs v4 válidos."""

    async def dispatch(self, request: Request, call_next):
        path_params = request.path_params
        if path_params:
            for key, value in path_params.items():
                if key.endswith("_id") and isinstance(value, str) and not _UUID_RE.match(value):
                    return Response(
                        content=json.dumps({"detail": f"Parámetro '{key}' debe ser un UUID válido"}),
                        status_code=400,
                        media_type="application/json",
                    )
        return await call_next(request)
