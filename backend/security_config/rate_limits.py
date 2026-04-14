"""
Rate Limiting Configuration for SyncStock API
Implements OWASP A08:2021 – Software and Data Integrity Failures
"""

# Default rate limits per endpoint category
RATE_LIMITS = {
    # Authentication & Security (CRITICAL)
    "auth_register": "5/minute",        # Sign-up: 5 attempts per minute
    "auth_login": "10/minute",          # Login: 10 attempts per minute
    "auth_forgot_password": "3/minute", # Forgot password: 3 attempts per minute
    "auth_reset_password": "5/minute",  # Reset password: 5 attempts per minute
    "auth_change_password": "10/minute",# Change password: 10 attempts per minute

    # Write Operations (HIGH)
    "write_slow": "30/minute",          # Slow write operations (create, update)
    "write_fast": "60/minute",          # Fast write operations (toggle, soft ops)

    # Read Operations (MODERATE)
    "read_expensive": "100/minute",     # Complex queries (search, reports)
    "read_fast": "200/minute",          # Simple reads (list, get)

    # Sync & Background Jobs (HIGH - prevent abuse)
    "sync_trigger": "10/minute",        # Trigger sync manually
    "export": "5/minute",               # Export operations
    "import": "5/minute",               # Import operations

    # Admin Operations (CRITICAL)
    "admin_system": "5/minute",         # System operations
    "admin_user_management": "30/minute", # User CRUD

    # External Integrations (MODERATE)
    "woocommerce_sync": "20/minute",    # WooCommerce sync trigger
    "stripe_webhook": "200/minute",     # Stripe webhooks (high volume expected)
    "crm_sync": "20/minute",            # CRM sync trigger

    # Public/Unauthenticated (LOW)
    "public_health": "1000/minute",     # Health check
    "public_webhook": "500/minute",     # Generic webhooks
}

# Endpoint to rate limit mapping
ENDPOINT_LIMITS = {
    # Auth
    "/auth/register": "auth_register",
    "/auth/login": "auth_login",
    "/auth/forgot-password": "auth_forgot_password",
    "/auth/reset-password": "auth_reset_password",
    "/auth/change-password": "auth_change_password",

    # Products - Write
    "POST:/products": "write_slow",
    "PUT:/products/*": "write_slow",
    "DELETE:/products/*": "write_slow",

    # Products - Read
    "GET:/products": "read_fast",
    "GET:/products/*": "read_fast",
    "GET:/products/search/*": "read_expensive",

    # Suppliers - Write
    "POST:/suppliers": "write_slow",
    "PUT:/suppliers/*": "write_slow",
    "DELETE:/suppliers/*": "write_slow",

    # Sync Operations
    "POST:/suppliers/*/sync": "sync_trigger",
    "POST:/products/sync": "sync_trigger",

    # Catalogs - Write
    "POST:/catalogs": "write_slow",
    "PUT:/catalogs/*": "write_slow",
    "DELETE:/catalogs/*": "write_slow",
    "POST:/catalogs/*/products": "write_slow",

    # Catalogs - Read
    "GET:/catalogs": "read_fast",
    "GET:/catalogs/*": "read_fast",

    # Admin
    "POST:/admin/system/*": "admin_system",
    "PUT:/admin/users/*": "admin_user_management",

    # WooCommerce
    "POST:/woocommerce/*/sync": "woocommerce_sync",

    # Export/Import
    "POST:/products/export": "export",
    "POST:/products/import": "import",

    # Health
    "GET:/health": "public_health",

    # Webhooks
    "POST:/webhooks/stripe": "stripe_webhook",
    "POST:/webhooks/*": "public_webhook",
}

def get_rate_limit(method: str, path: str) -> str:
    """
    Get rate limit for a specific endpoint.

    Returns the rate limit string (e.g., "100/minute")
    or default "60/minute" if not specified.
    """
    # Try exact match first
    key = f"{method}:{path}"
    if key in ENDPOINT_LIMITS:
        limit_key = ENDPOINT_LIMITS[key]
        return RATE_LIMITS.get(limit_key, "60/minute")

    # Try path-only match
    if path in ENDPOINT_LIMITS:
        limit_key = ENDPOINT_LIMITS[path]
        return RATE_LIMITS.get(limit_key, "60/minute")

    # Default: 60 requests per minute
    return "60/minute"
