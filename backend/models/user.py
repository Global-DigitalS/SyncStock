from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: str | None = None
    role: str | None = "user"
    plan_id: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = {"extra": "ignore"}

    id: str
    email: str
    name: str = ""
    company: str | None = None
    role: str = "user"
    max_suppliers: int = 10
    max_catalogs: int = 5
    max_woocommerce_stores: int = 2
    max_marketplace_connections: int = 1
    max_products: int | None = None
    is_active: bool | None = None
    plan_id: str | None = None
    plan_name: str | None = None
    subscription_plan_id: str | None = None
    subscription_plan_name: str | None = None
    subscription_status: str | None = None
    trial_end: str | None = None
    created_at: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    role: str | None = None
    max_suppliers: int | None = None
    max_catalogs: int | None = None
    max_woocommerce_stores: int | None = None
    max_marketplace_connections: int | None = None


class UserLimits(BaseModel):
    max_suppliers: int = 10
    max_catalogs: int = 5
    max_woocommerce_stores: int = 2
    max_marketplace_connections: int = 1
    max_products: int | None = 1000


class UserFullUpdate(BaseModel):
    """Model for full user update by SuperAdmin"""
    name: str | None = None
    email: EmailStr | None = None
    company: str | None = None
    role: str | None = None
    max_suppliers: int | None = None
    max_catalogs: int | None = None
    max_woocommerce_stores: int | None = None
    max_marketplace_connections: int | None = None
    max_products: int | None = None
    subscription_plan_id: str | None = None
    subscription_plan_name: str | None = None
    subscription_status: str | None = None
    is_active: bool | None = None
