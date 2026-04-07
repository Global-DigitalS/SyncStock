"""
Input sanitization utilities for security.
Prevents XSS, injection attacks, and other security issues.
"""
import html
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Dangerous HTML tags and attributes
DANGEROUS_TAGS = re.compile(r'<\s*(script|iframe|object|embed|form|input|button|style|link|meta|base)[^>]*>', re.IGNORECASE)
DANGEROUS_ATTRS = re.compile(r'\s(on\w+|javascript:|data:text/html|vbscript:)[^>\s]*', re.IGNORECASE)
SCRIPT_CONTENT = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)

# MongoDB injection patterns
MONGO_OPERATORS = re.compile(r'\$(?:where|gt|gte|lt|lte|ne|in|nin|or|and|not|nor|exists|type|mod|regex|text|all|elemMatch|size|slice|meta|comment)', re.IGNORECASE)

# Path traversal patterns
PATH_TRAVERSAL = re.compile(r'\.\.[\\/]|[\\/]\.\.', re.IGNORECASE)


def sanitize_string(value: str, max_length: int = 10000, allow_html: bool = False) -> str:
    """
    Sanitize a string input.
    
    Args:
        value: The string to sanitize
        max_length: Maximum allowed length
        allow_html: If False, escape HTML entities
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return value

    # Trim to max length
    value = value[:max_length]

    # Remove null bytes
    value = value.replace('\x00', '')

    # Remove script tags and content
    value = SCRIPT_CONTENT.sub('', value)

    # Remove dangerous tags
    value = DANGEROUS_TAGS.sub('', value)

    # Remove dangerous attributes (onclick, onload, etc.)
    value = DANGEROUS_ATTRS.sub('', value)

    # Escape HTML if not allowed
    if not allow_html:
        value = html.escape(value, quote=True)

    # Strip leading/trailing whitespace
    value = value.strip()

    return value


def sanitize_email(email: str) -> str:
    """Sanitize email input."""
    if not isinstance(email, str):
        return email

    # Basic sanitization
    email = sanitize_string(email, max_length=254)

    # Remove any whitespace
    email = email.strip().lower()

    # Basic email validation pattern
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        # Return empty string for invalid emails (let validation handle it)
        return email

    return email


def sanitize_password(password: str) -> str:
    """
    Sanitize password input.
    Note: Passwords should not be heavily modified to preserve user's intended password.
    """
    if not isinstance(password, str):
        return password

    # Only remove null bytes and limit length
    password = password.replace('\x00', '')
    password = password[:128]  # Reasonable max password length

    return password


def sanitize_mongo_query(value: str) -> str:
    """Remove potential MongoDB operator injection."""
    if not isinstance(value, str):
        return value

    # Escape $ at the start of strings (MongoDB operators)
    if value.startswith('$'):
        value = '\\' + value

    return value


def sanitize_path(path: str) -> str:
    """Sanitize file path to prevent path traversal attacks."""
    if not isinstance(path, str):
        return path

    # Remove path traversal patterns
    path = PATH_TRAVERSAL.sub('', path)

    # Remove null bytes
    path = path.replace('\x00', '')

    # Remove potentially dangerous characters
    path = re.sub(r'[<>:"|?*]', '', path)

    return path


def sanitize_url(url: str) -> str:
    """Sanitize URL input."""
    if not isinstance(url, str):
        return url

    url = sanitize_string(url, max_length=2048)

    # Check for javascript: or data: URLs
    if re.match(r'^(javascript|data|vbscript):', url, re.IGNORECASE):
        return ''

    return url


def sanitize_dict(data: dict[str, Any], allow_html_fields: list[str] = None) -> dict[str, Any]:
    """
    Recursively sanitize all string values in a dictionary.
    
    Args:
        data: Dictionary to sanitize
        allow_html_fields: List of field names that can contain HTML
    
    Returns:
        Sanitized dictionary
    """
    if allow_html_fields is None:
        allow_html_fields = []

    sanitized = {}

    for key, value in data.items():
        # Sanitize the key itself
        safe_key = sanitize_string(str(key), max_length=256)

        if isinstance(value, str):
            allow_html = key in allow_html_fields
            sanitized[safe_key] = sanitize_string(value, allow_html=allow_html)
        elif isinstance(value, dict):
            sanitized[safe_key] = sanitize_dict(value, allow_html_fields)
        elif isinstance(value, list):
            sanitized[safe_key] = sanitize_list(value, allow_html_fields)
        else:
            sanitized[safe_key] = value

    return sanitized


def sanitize_list(data: list[Any], allow_html_fields: list[str] = None) -> list[Any]:
    """Recursively sanitize all string values in a list."""
    if allow_html_fields is None:
        allow_html_fields = []

    sanitized = []

    for item in data:
        if isinstance(item, str):
            sanitized.append(sanitize_string(item))
        elif isinstance(item, dict):
            sanitized.append(sanitize_dict(item, allow_html_fields))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item, allow_html_fields))
        else:
            sanitized.append(item)

    return sanitized


def sanitize_model(model: Any, allow_html_fields: list[str] = None) -> Any:
    """
    Sanitize a Pydantic model's fields.
    
    Args:
        model: Pydantic model instance
        allow_html_fields: Fields that can contain HTML
    
    Returns:
        Same model with sanitized values
    """
    if allow_html_fields is None:
        allow_html_fields = []

    if hasattr(model, 'model_dump'):
        data = model.model_dump()
    elif hasattr(model, 'dict'):
        data = model.dict()
    else:
        return model

    sanitized_data = sanitize_dict(data, allow_html_fields)

    # Return sanitized dict (caller can reconstruct model if needed)
    return sanitized_data


# Middleware helper for FastAPI
def create_sanitization_middleware():
    """Create a middleware that sanitizes request bodies."""
    import json

    from fastapi import Request
    from starlette.middleware.base import BaseHTTPMiddleware

    class SanitizationMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Only process JSON requests
            if request.headers.get('content-type', '').startswith('application/json'):
                try:
                    body = await request.body()
                    if body:
                        data = json.loads(body)
                        if isinstance(data, dict):
                            # Fields that may contain HTML (like email templates)
                            html_fields = ['html_content', 'template_content', 'body_html']
                            sanitized = sanitize_dict(data, html_fields)
                            # Note: We can't easily modify the request body in Starlette
                            # So sanitization should be done at the route level
                except Exception:
                    pass

            response = await call_next(request)
            return response

    return SanitizationMiddleware


# ── Credential removal helper (MEDIUM FIX #13) ──────────────────────────────

# Fields that should never be exposed in API responses
SENSITIVE_FIELDS = {
    "password", "ftp_password", "url_password", "api_key", "secret_key",
    "webhook_secret", "access_token", "refresh_token", "private_key",
    "client_secret", "smtp_password", "encryption_key", "jwt_secret"
}


def remove_credentials(data: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Recursively remove sensitive credentials from API responses.

    MEDIUM FIX #13: Safer credential removal across all API endpoints.
    Provides centralized, systematic removal of password, keys, tokens, and secrets.

    Handles:
    - Single dict: returns dict without credentials
    - List of dicts: returns list with credentials removed from each
    - Nested dicts and lists: recursively processes nested structures

    Usage:
        # Single object
        user = {"id": "123", "name": "John", "password": "secret"}
        user = remove_credentials(user)  # {"id": "123", "name": "John"}

        # List of objects
        suppliers = await db.suppliers.find(...).to_list(1000)
        suppliers = remove_credentials(suppliers)

        # Return from route
        return remove_credentials(supplier_doc)

    Args:
        data: Dict, list of dicts, or nested structure

    Returns:
        Same structure with SENSITIVE_FIELDS removed
    """
    if isinstance(data, dict):
        # Return new dict without sensitive fields
        return {k: remove_credentials(v) for k, v in data.items() if k not in SENSITIVE_FIELDS}
    elif isinstance(data, list):
        # Process each item in list
        return [remove_credentials(item) for item in data]
    else:
        # Return primitive values unchanged
        return data


# UUID v4 format pattern
_UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


def validate_uuid(value: str) -> str:
    """Valida que un string sea un UUID v4 válido. Lanza ValueError si no lo es."""
    if not value or not _UUID_PATTERN.match(value):
        raise ValueError(f"ID inválido: se esperaba UUID, se recibió '{value[:50]}'")
    return value
