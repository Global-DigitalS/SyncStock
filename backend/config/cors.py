"""
CORS Configuration for SyncStock API
Implements OWASP A01:2021 – Broken Access Control
"""

import os
from typing import List

def get_cors_origins() -> List[str]:
    """
    Get allowed CORS origins based on environment.

    Development: localhost, 127.0.0.1
    Production: configured domain only
    """
    env = os.getenv("ENVIRONMENT", "development")

    # Production: Strictly configured domain
    if env == "production":
        # IMPORTANT: Configure your actual domain
        allowed = [
            "https://yourdomain.com",
            "https://www.yourdomain.com",
            "https://app.yourdomain.com",
        ]
        return allowed

    # Development/Staging: Allow localhost development
    if env in ["development", "staging"]:
        allowed = [
            "http://localhost:3000",      # React dev server
            "http://localhost:3001",      # Alternative dev port
            "http://127.0.0.1:3000",      # Loopback
            "http://127.0.0.1:3001",      # Loopback alt
        ]

        # Allow additional origins from env var if set
        extra = os.getenv("CORS_EXTRA_ORIGINS", "")
        if extra:
            allowed.extend([origin.strip() for origin in extra.split(",")])

        return allowed

    # Default: Deny all (safe fail)
    return []


# CORS Middleware Configuration
CORS_CONFIG = {
    "allow_origins": get_cors_origins(),
    "allow_credentials": True,              # Allow credentials (cookies)
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allow_headers": [
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
    ],
    "expose_headers": [
        "X-Total-Count",                # For pagination metadata
        "X-Page",
        "X-Page-Size",
    ],
    "max_age": 600,                     # 10 minutes cache preflight
}

# Security Headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",                          # Prevent MIME sniffing
    "X-Frame-Options": "DENY",                                    # Prevent clickjacking
    "X-XSS-Protection": "1; mode=block",                          # XSS protection
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",  # HSTS
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
}

# Cookie Security Settings
COOKIE_CONFIG = {
    "httponly": True,                   # Not accessible via JavaScript
    "secure": os.getenv("ENVIRONMENT") == "production",  # Only HTTPS in prod
    "samesite": "lax",                  # CSRF protection
    "max_age": 7 * 24 * 60 * 60,       # 7 days
}
