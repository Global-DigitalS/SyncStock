"""
Tests unitarios para BrandingService.
Mockea BrandingRepository para no requerir MongoDB real.
"""
import sys
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ==================== MOCK SETUP ====================

# Mock de services.database (sin Motor real)
_database_module = MagicMock()
_database_module.db = MagicMock()
sys.modules.setdefault("services.database", _database_module)

# Importar después del mock
from services.branding_service import BrandingService  # noqa: E402
from repositories.branding_repository import BrandingRepository  # noqa: E402


# ==================== FIXTURES ====================

@pytest.fixture
def user_id():
    """ID de usuario de prueba."""
    return "test_user_123"


@pytest.fixture
def sample_branding_data():
    """Datos básicos de configuración de marca."""
    return {
        "company_name": "Test Company",
        "primary_color": "#007AFF",
        "secondary_color": "#5AC8FA",
        "support_email": "support@test.com",
        "logo_url": "https://example.com/logo.png",
        "company_description": "Test company description",
    }


@pytest.fixture
def created_branding(sample_branding_data):
    """Documento de configuración de marca simulado que ya existe."""
    now = datetime.now(UTC).isoformat()
    return {
        "id": "branding_123",
        "company_name": sample_branding_data["company_name"],
        "primary_color": sample_branding_data["primary_color"],
        "secondary_color": sample_branding_data["secondary_color"],
        "support_email": sample_branding_data["support_email"],
        "logo_url": sample_branding_data["logo_url"],
        "logo_dark_url": None,
        "favicon_url": None,
        "company_description": sample_branding_data["company_description"],
        "support_phone": None,
        "social_links": {},
        "subscription_plans": [],
        "created_at": now,
        "updated_at": now,
        "created_by": "user_123",
        "updated_by": None,
    }


# ==================== TESTS: GET BRANDING ====================

class TestGetBranding:
    """Tests para BrandingService.get_branding"""

    @pytest.mark.asyncio
    async def test_get_branding_success(self, created_branding):
        """Test: Obtener configuración de marca exitosamente."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = created_branding

            result = await BrandingService.get_branding()

            assert result is not None
            assert result["id"] == created_branding["id"]
            assert result["company_name"] == created_branding["company_name"]
            mock_get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_branding_not_exists(self):
        """Test: Obtener configuración cuando no existe debería retornar None."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await BrandingService.get_branding()

            assert result is None
            mock_get.assert_awaited_once()


# ==================== TESTS: UPDATE BRANDING ====================

class TestUpdateBranding:
    """Tests para BrandingService.update_branding"""

    @pytest.mark.asyncio
    async def test_update_branding_success(self, created_branding, user_id):
        """Test: Actualizar configuración de marca exitosamente."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                updated_branding = {**created_branding, "company_name": "Updated Company"}
                mock_update.return_value = updated_branding

                result = await BrandingService.update_branding(
                    updated_by=user_id,
                    company_name="Updated Company",
                )

                assert result["company_name"] == "Updated Company"
                mock_get.assert_awaited_once()
                mock_update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_branding_not_exists(self, user_id):
        """Test: Actualizar cuando no existe debería fallar."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError, match="No existe configuración de marca"):
                await BrandingService.update_branding(
                    updated_by=user_id,
                    company_name="New Company",
                )

    @pytest.mark.asyncio
    async def test_update_branding_with_multiple_fields(self, created_branding, user_id):
        """Test: Actualizar múltiples campos de una vez."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                updated_branding = {
                    **created_branding,
                    "company_name": "New Name",
                    "primary_color": "#FF0000",
                    "support_email": "newemail@test.com",
                }
                mock_update.return_value = updated_branding

                result = await BrandingService.update_branding(
                    updated_by=user_id,
                    company_name="New Name",
                    primary_color="#FF0000",
                    support_email="newemail@test.com",
                )

                assert result["company_name"] == "New Name"
                assert result["primary_color"] == "#FF0000"
                assert result["support_email"] == "newemail@test.com"

    @pytest.mark.asyncio
    async def test_update_branding_includes_user(self, created_branding, user_id):
        """Test: Verificar que updated_by se incluye en la actualización."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                mock_update.return_value = {**created_branding, "updated_by": user_id}

                await BrandingService.update_branding(
                    updated_by=user_id,
                    company_name="New Name",
                )

                # Verificar que se pasó updated_by en los updates
                call_args = mock_update.await_args
                updates = call_args[0][0]
                assert "updated_by" in updates
                assert updates["updated_by"] == user_id


# ==================== TESTS: INITIALIZE BRANDING ====================

class TestInitializeBranding:
    """Tests para BrandingService.initialize_branding"""

    @pytest.mark.asyncio
    async def test_initialize_branding_success(self, user_id, sample_branding_data):
        """Test: Inicializar configuración de marca exitosamente."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get_current:
            with patch.object(BrandingRepository, "create_or_update", new_callable=AsyncMock) as mock_create:
                mock_get_current.return_value = None
                expected_branding = {
                    "id": "branding_456",
                    "company_name": sample_branding_data["company_name"],
                    "primary_color": sample_branding_data["primary_color"],
                    "secondary_color": sample_branding_data["secondary_color"],
                    "support_email": sample_branding_data["support_email"],
                    "created_by": user_id,
                }
                mock_create.return_value = expected_branding

                result = await BrandingService.initialize_branding(
                    company_name=sample_branding_data["company_name"],
                    primary_color=sample_branding_data["primary_color"],
                    secondary_color=sample_branding_data["secondary_color"],
                    support_email=sample_branding_data["support_email"],
                    created_by=user_id,
                )

                assert result["company_name"] == sample_branding_data["company_name"]
                assert result["primary_color"] == sample_branding_data["primary_color"]
                assert result["created_by"] == user_id
                mock_get_current.assert_awaited_once()
                mock_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_initialize_branding_already_exists(self, user_id, created_branding, sample_branding_data):
        """Test: Inicializar cuando ya existe debería fallar."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get_current:
            mock_get_current.return_value = created_branding

            with pytest.raises(ValueError, match="La configuración de marca ya existe"):
                await BrandingService.initialize_branding(
                    company_name=sample_branding_data["company_name"],
                    primary_color=sample_branding_data["primary_color"],
                    secondary_color=sample_branding_data["secondary_color"],
                    support_email=sample_branding_data["support_email"],
                    created_by=user_id,
                )

    @pytest.mark.asyncio
    async def test_initialize_branding_with_optional_fields(self, user_id, sample_branding_data):
        """Test: Inicializar con campos opcionales."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get_current:
            with patch.object(BrandingRepository, "create_or_update", new_callable=AsyncMock) as mock_create:
                mock_get_current.return_value = None
                expected_branding = {
                    "id": "branding_456",
                    "company_name": sample_branding_data["company_name"],
                    "primary_color": sample_branding_data["primary_color"],
                    "secondary_color": sample_branding_data["secondary_color"],
                    "support_email": sample_branding_data["support_email"],
                    "logo_url": sample_branding_data["logo_url"],
                    "company_description": sample_branding_data["company_description"],
                }
                mock_create.return_value = expected_branding

                result = await BrandingService.initialize_branding(
                    company_name=sample_branding_data["company_name"],
                    primary_color=sample_branding_data["primary_color"],
                    secondary_color=sample_branding_data["secondary_color"],
                    support_email=sample_branding_data["support_email"],
                    created_by=user_id,
                    logo_url=sample_branding_data["logo_url"],
                    company_description=sample_branding_data["company_description"],
                )

                assert result["logo_url"] == sample_branding_data["logo_url"]
                assert result["company_description"] == sample_branding_data["company_description"]


# ==================== TESTS: GET OR INITIALIZE BRANDING ====================

class TestGetOrInitializeBranding:
    """Tests para BrandingService.get_or_initialize_branding"""

    @pytest.mark.asyncio
    async def test_get_or_initialize_existing(self, created_branding):
        """Test: Obtener configuración existente."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = created_branding

            result = await BrandingService.get_or_initialize_branding()

            assert result == created_branding
            mock_get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_or_initialize_creates_with_defaults(self):
        """Test: Inicializar con valores por defecto si no existe."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "create_or_update", new_callable=AsyncMock) as mock_create:
                mock_get.return_value = None
                expected_branding = {
                    "id": "branding_default",
                    "company_name": "SyncStock",
                    "primary_color": "#007AFF",
                    "secondary_color": "#5AC8FA",
                    "support_email": "support@syncstock.local",
                }
                mock_create.return_value = expected_branding

                result = await BrandingService.get_or_initialize_branding()

                assert result["company_name"] == "SyncStock"
                assert result["primary_color"] == "#007AFF"
                mock_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_or_initialize_with_custom_values(self):
        """Test: Inicializar con valores personalizados."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "create_or_update", new_callable=AsyncMock) as mock_create:
                mock_get.return_value = None
                expected_branding = {
                    "id": "branding_custom",
                    "company_name": "Custom Company",
                    "primary_color": "#FF0000",
                    "secondary_color": "#00FF00",
                    "support_email": "custom@test.com",
                }
                mock_create.return_value = expected_branding

                result = await BrandingService.get_or_initialize_branding(
                    company_name="Custom Company",
                    primary_color="#FF0000",
                    secondary_color="#00FF00",
                    support_email="custom@test.com",
                )

                assert result["company_name"] == "Custom Company"


# ==================== TESTS: EXISTS ====================

class TestBrandingExists:
    """Tests para BrandingService.exists"""

    @pytest.mark.asyncio
    async def test_branding_exists_true(self):
        """Test: Verificar que configuración existe."""
        with patch.object(BrandingRepository, "exists", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = True

            result = await BrandingService.exists()

            assert result is True
            mock_exists.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_branding_exists_false(self):
        """Test: Verificar que configuración no existe."""
        with patch.object(BrandingRepository, "exists", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = False

            result = await BrandingService.exists()

            assert result is False


# ==================== TESTS: UPDATE COLORS ====================

class TestUpdateColors:
    """Tests para BrandingService.update_colors"""

    @pytest.mark.asyncio
    async def test_update_colors_success(self, created_branding, user_id):
        """Test: Actualizar colores exitosamente."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                updated_branding = {
                    **created_branding,
                    "primary_color": "#FF0000",
                    "secondary_color": "#00FF00",
                }
                mock_update.return_value = updated_branding

                result = await BrandingService.update_colors(
                    primary_color="#FF0000",
                    secondary_color="#00FF00",
                    updated_by=user_id,
                )

                assert result["primary_color"] == "#FF0000"
                assert result["secondary_color"] == "#00FF00"


# ==================== TESTS: UPDATE COMPANY INFO ====================

class TestUpdateCompanyInfo:
    """Tests para BrandingService.update_company_info"""

    @pytest.mark.asyncio
    async def test_update_company_info_all_fields(self, created_branding, user_id):
        """Test: Actualizar toda la información de la empresa."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                updated_branding = {
                    **created_branding,
                    "company_name": "New Company",
                    "company_description": "New description",
                    "support_email": "newemail@test.com",
                    "support_phone": "+1234567890",
                }
                mock_update.return_value = updated_branding

                result = await BrandingService.update_company_info(
                    company_name="New Company",
                    company_description="New description",
                    support_email="newemail@test.com",
                    support_phone="+1234567890",
                    updated_by=user_id,
                )

                assert result["company_name"] == "New Company"
                assert result["company_description"] == "New description"
                assert result["support_phone"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_update_company_info_partial_fields(self, created_branding, user_id):
        """Test: Actualizar solo algunos campos."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                updated_branding = {**created_branding, "support_email": "newemail@test.com"}
                mock_update.return_value = updated_branding

                result = await BrandingService.update_company_info(
                    support_email="newemail@test.com",
                    updated_by=user_id,
                )

                assert result["support_email"] == "newemail@test.com"


# ==================== TESTS: UPDATE LOGOS ====================

class TestUpdateLogos:
    """Tests para BrandingService.update_logos"""

    @pytest.mark.asyncio
    async def test_update_logos_success(self, created_branding, user_id):
        """Test: Actualizar logos exitosamente."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                updated_branding = {
                    **created_branding,
                    "logo_url": "https://example.com/new-logo.png",
                    "logo_dark_url": "https://example.com/new-logo-dark.png",
                    "favicon_url": "https://example.com/favicon.ico",
                }
                mock_update.return_value = updated_branding

                result = await BrandingService.update_logos(
                    logo_url="https://example.com/new-logo.png",
                    logo_dark_url="https://example.com/new-logo-dark.png",
                    favicon_url="https://example.com/favicon.ico",
                    updated_by=user_id,
                )

                assert result["logo_url"] == "https://example.com/new-logo.png"
                assert result["logo_dark_url"] == "https://example.com/new-logo-dark.png"

    @pytest.mark.asyncio
    async def test_update_logos_partial(self, created_branding, user_id):
        """Test: Actualizar solo algunos logos."""
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                updated_branding = {**created_branding, "logo_url": "https://example.com/logo.png"}
                mock_update.return_value = updated_branding

                result = await BrandingService.update_logos(
                    logo_url="https://example.com/logo.png",
                    updated_by=user_id,
                )

                assert result["logo_url"] == "https://example.com/logo.png"


# ==================== TESTS: UPDATE SOCIAL LINKS ====================

class TestUpdateSocialLinks:
    """Tests para BrandingService.update_social_links"""

    @pytest.mark.asyncio
    async def test_update_social_links_success(self, created_branding, user_id):
        """Test: Actualizar enlaces a redes sociales."""
        social_links = {
            "facebook": "https://facebook.com/company",
            "twitter": "https://twitter.com/company",
            "instagram": "https://instagram.com/company",
        }
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                updated_branding = {**created_branding, "social_links": social_links}
                mock_update.return_value = updated_branding

                result = await BrandingService.update_social_links(
                    social_links=social_links,
                    updated_by=user_id,
                )

                assert result["social_links"] == social_links


# ==================== TESTS: UPDATE SUBSCRIPTION PLANS ====================

class TestUpdateSubscriptionPlans:
    """Tests para BrandingService.update_subscription_plans"""

    @pytest.mark.asyncio
    async def test_update_subscription_plans_success(self, created_branding, user_id):
        """Test: Actualizar planes de suscripción."""
        plans = [
            {"name": "Basic", "price": 29, "features": ["Feature 1", "Feature 2"]},
            {"name": "Pro", "price": 79, "features": ["Feature 1", "Feature 2", "Feature 3"]},
        ]
        with patch.object(BrandingRepository, "get_current", new_callable=AsyncMock) as mock_get:
            with patch.object(BrandingRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_branding
                updated_branding = {**created_branding, "subscription_plans": plans}
                mock_update.return_value = updated_branding

                result = await BrandingService.update_subscription_plans(
                    subscription_plans=plans,
                    updated_by=user_id,
                )

                assert result["subscription_plans"] == plans
                assert len(result["subscription_plans"]) == 2
