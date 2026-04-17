"""
Tests unitarios para PageService.
Mockea PageRepository para no requerir MongoDB real.
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
from services.page_service import PageService  # noqa: E402
from repositories.page_repository import PageRepository  # noqa: E402


# ==================== FIXTURES ====================

@pytest.fixture
def user_id():
    """ID de usuario de prueba."""
    return "test_user_123"


@pytest.fixture
def sample_page_data():
    """Datos básicos de una página de prueba."""
    return {
        "slug": "test-page",
        "title": "Test Page",
        "page_type": "CUSTOM",
        "hero_section": {"title": "Hero Title", "subtitle": "Hero Subtitle"},
        "content": "<p>Test content</p>",
        "meta_description": "Test meta description",
        "meta_keywords": "test, keywords",
    }


@pytest.fixture
def created_page(sample_page_data):
    """Documento de página simulado que ya existe."""
    now = datetime.now(UTC).isoformat()
    return {
        "id": "page_123",
        "slug": sample_page_data["slug"],
        "title": sample_page_data["title"],
        "page_type": sample_page_data["page_type"],
        "hero_section": sample_page_data["hero_section"],
        "content": sample_page_data["content"],
        "meta_description": sample_page_data["meta_description"],
        "meta_keywords": sample_page_data["meta_keywords"],
        "is_published": False,
        "is_public": True,
        "created_at": now,
        "updated_at": now,
        "created_by": "user_123",
        "updated_by": None,
    }


# ==================== TESTS: CREATE PAGE ====================

class TestCreatePage:
    """Tests para PageService.create_page"""

    @pytest.mark.asyncio
    async def test_create_page_success(self, user_id, sample_page_data):
        """Test: Crear una página con datos válidos."""
        with patch.object(PageRepository, "exists_slug", new_callable=AsyncMock) as mock_exists:
            with patch.object(PageRepository, "create", new_callable=AsyncMock) as mock_create:
                mock_exists.return_value = False
                expected_page = {
                    "id": "page_123",
                    "slug": sample_page_data["slug"],
                    "title": sample_page_data["title"],
                    "page_type": sample_page_data["page_type"],
                    "hero_section": sample_page_data["hero_section"],
                    "content": sample_page_data["content"],
                    "meta_description": sample_page_data["meta_description"],
                    "meta_keywords": sample_page_data["meta_keywords"],
                    "is_published": False,
                    "is_public": True,
                    "created_by": user_id,
                    "updated_by": None,
                }
                mock_create.return_value = expected_page

                result = await PageService.create_page(
                    slug=sample_page_data["slug"],
                    title=sample_page_data["title"],
                    page_type=sample_page_data["page_type"],
                    created_by=user_id,
                    hero_section=sample_page_data["hero_section"],
                    content=sample_page_data["content"],
                    meta_description=sample_page_data["meta_description"],
                    meta_keywords=sample_page_data["meta_keywords"],
                )

                assert result["id"] == "page_123"
                assert result["slug"] == sample_page_data["slug"]
                assert result["title"] == sample_page_data["title"]
                assert result["page_type"] == sample_page_data["page_type"]
                assert result["is_published"] is False
                assert result["is_public"] is True
                assert result["created_by"] == user_id
                mock_exists.assert_awaited_once_with(sample_page_data["slug"])
                mock_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_page_missing_slug(self, user_id, sample_page_data):
        """Test: Crear página sin slug debería fallar."""
        with pytest.raises(ValueError, match="El slug y el título son requeridos"):
            await PageService.create_page(
                slug="",
                title=sample_page_data["title"],
                page_type=sample_page_data["page_type"],
                created_by=user_id,
            )

    @pytest.mark.asyncio
    async def test_create_page_missing_title(self, user_id, sample_page_data):
        """Test: Crear página sin título debería fallar."""
        with pytest.raises(ValueError, match="El slug y el título son requeridos"):
            await PageService.create_page(
                slug=sample_page_data["slug"],
                title="",
                page_type=sample_page_data["page_type"],
                created_by=user_id,
            )

    @pytest.mark.asyncio
    async def test_create_duplicate_slug_raises_error(self, user_id, sample_page_data):
        """Test: Crear página con slug duplicado debería lanzar error."""
        with patch.object(PageRepository, "exists_slug", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = True

            with pytest.raises(ValueError, match=f"El slug '{sample_page_data['slug']}' ya existe"):
                await PageService.create_page(
                    slug=sample_page_data["slug"],
                    title=sample_page_data["title"],
                    page_type=sample_page_data["page_type"],
                    created_by=user_id,
                )

            mock_exists.assert_awaited_once_with(sample_page_data["slug"])

    @pytest.mark.asyncio
    async def test_create_page_with_optional_fields(self, user_id):
        """Test: Crear página con solo campos requeridos."""
        with patch.object(PageRepository, "exists_slug", new_callable=AsyncMock) as mock_exists:
            with patch.object(PageRepository, "create", new_callable=AsyncMock) as mock_create:
                mock_exists.return_value = False
                expected_page = {
                    "id": "page_456",
                    "slug": "minimal-page",
                    "title": "Minimal Page",
                    "page_type": "HOME",
                    "is_published": False,
                    "is_public": True,
                    "created_by": user_id,
                    "updated_by": None,
                }
                mock_create.return_value = expected_page

                result = await PageService.create_page(
                    slug="minimal-page",
                    title="Minimal Page",
                    page_type="HOME",
                    created_by=user_id,
                )

                assert result["id"] == "page_456"
                assert result["slug"] == "minimal-page"
                assert result["title"] == "Minimal Page"
                assert "hero_section" not in result
                assert "content" not in result


# ==================== TESTS: GET PAGE ====================

class TestGetPage:
    """Tests para PageService.get_page"""

    @pytest.mark.asyncio
    async def test_get_page_by_id_success(self, created_page):
        """Test: Obtener página por ID exitosamente."""
        with patch.object(PageRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = created_page

            result = await PageService.get_page(created_page["id"])

            assert result is not None
            assert result["id"] == created_page["id"]
            assert result["slug"] == created_page["slug"]
            mock_get.assert_awaited_once_with(created_page["id"])

    @pytest.mark.asyncio
    async def test_get_page_by_id_not_found(self):
        """Test: Obtener página no existente debería retornar None."""
        with patch.object(PageRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await PageService.get_page("nonexistent_id")

            assert result is None
            mock_get.assert_awaited_once_with("nonexistent_id")


class TestGetPageBySlug:
    """Tests para PageService.get_page_by_slug"""

    @pytest.mark.asyncio
    async def test_get_page_by_slug_success(self, created_page):
        """Test: Obtener página por slug exitosamente."""
        with patch.object(PageRepository, "get_by_slug", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = created_page

            result = await PageService.get_page_by_slug(created_page["slug"])

            assert result is not None
            assert result["slug"] == created_page["slug"]
            assert result["id"] == created_page["id"]
            mock_get.assert_awaited_once_with(created_page["slug"])

    @pytest.mark.asyncio
    async def test_get_page_by_slug_not_found(self):
        """Test: Obtener página por slug no existente debería retornar None."""
        with patch.object(PageRepository, "get_by_slug", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await PageService.get_page_by_slug("nonexistent-slug")

            assert result is None
            mock_get.assert_awaited_once_with("nonexistent-slug")


# ==================== TESTS: LIST PAGES ====================

class TestListPages:
    """Tests para PageService.list_pages"""

    @pytest.mark.asyncio
    async def test_list_pages_all(self, created_page):
        """Test: Listar todas las páginas."""
        with patch.object(PageRepository, "get_all", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [created_page]

            result = await PageService.list_pages(skip=0, limit=100)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == created_page["id"]
            mock_list.assert_awaited_once_with(0, 100)

    @pytest.mark.asyncio
    async def test_list_pages_with_search_query(self, created_page):
        """Test: Listar páginas con búsqueda."""
        with patch.object(PageRepository, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [created_page]

            result = await PageService.list_pages(skip=0, limit=100, search_query="test")

            assert isinstance(result, list)
            assert len(result) == 1
            mock_search.assert_awaited_once_with("test", 0, 100)

    @pytest.mark.asyncio
    async def test_list_pages_by_page_type(self, created_page):
        """Test: Listar páginas filtradas por tipo."""
        with patch.object(PageRepository, "get_by_page_type", new_callable=AsyncMock) as mock_get_type:
            mock_get_type.return_value = [created_page]

            result = await PageService.list_pages(skip=0, limit=100, page_type="CUSTOM")

            assert isinstance(result, list)
            assert len(result) == 1
            mock_get_type.assert_awaited_once_with("CUSTOM", 0, 100)

    @pytest.mark.asyncio
    async def test_list_pages_empty(self):
        """Test: Listar páginas cuando no hay datos."""
        with patch.object(PageRepository, "get_all", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []

            result = await PageService.list_pages(skip=0, limit=100)

            assert isinstance(result, list)
            assert len(result) == 0
            mock_list.assert_awaited_once()


class TestListPublicPages:
    """Tests para PageService.list_public_pages"""

    @pytest.mark.asyncio
    async def test_list_public_pages_success(self, created_page):
        """Test: Listar páginas públicas y publicadas."""
        public_page = {**created_page, "is_published": True, "is_public": True}
        with patch.object(PageRepository, "get_public_published", new_callable=AsyncMock) as mock_public:
            mock_public.return_value = [public_page]

            result = await PageService.list_public_pages()

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["is_published"] is True
            assert result[0]["is_public"] is True
            mock_public.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_public_pages_empty(self):
        """Test: Listar páginas públicas cuando no hay."""
        with patch.object(PageRepository, "get_public_published", new_callable=AsyncMock) as mock_public:
            mock_public.return_value = []

            result = await PageService.list_public_pages()

            assert isinstance(result, list)
            assert len(result) == 0


# ==================== TESTS: UPDATE PAGE ====================

class TestUpdatePage:
    """Tests para PageService.update_page"""

    @pytest.mark.asyncio
    async def test_update_page_success(self, created_page, user_id):
        """Test: Actualizar página exitosamente."""
        with patch.object(PageRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            with patch.object(PageRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_page
                updated_page = {**created_page, "title": "Updated Title"}
                mock_update.return_value = updated_page

                result = await PageService.update_page(
                    created_page["id"],
                    updated_by=user_id,
                    title="Updated Title",
                )

                assert result["title"] == "Updated Title"
                mock_get.assert_awaited_once_with(created_page["id"])
                mock_update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_page_not_found(self, user_id):
        """Test: Actualizar página no existente debería retornar None."""
        with patch.object(PageRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await PageService.update_page("nonexistent_id", updated_by=user_id, title="New")

            assert result is None
            mock_get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_page_slug_conflict(self, created_page, user_id):
        """Test: Cambiar slug a uno duplicado debería fallar."""
        with patch.object(PageRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            with patch.object(PageRepository, "exists_slug", new_callable=AsyncMock) as mock_exists:
                mock_get.return_value = created_page
                mock_exists.return_value = True

                with pytest.raises(ValueError, match="El slug 'duplicate-slug' ya existe"):
                    await PageService.update_page(
                        created_page["id"],
                        updated_by=user_id,
                        slug="duplicate-slug",
                    )

                mock_exists.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_page_slug_same_allowed(self, created_page, user_id):
        """Test: Actualizar página con el mismo slug debería permitirse."""
        with patch.object(PageRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            with patch.object(PageRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_page
                updated_page = {**created_page, "title": "New Title"}
                mock_update.return_value = updated_page

                result = await PageService.update_page(
                    created_page["id"],
                    updated_by=user_id,
                    slug=created_page["slug"],
                    title="New Title",
                )

                assert result["title"] == "New Title"
                mock_update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_page_partial_fields(self, created_page, user_id):
        """Test: Actualizar solo algunos campos de la página."""
        with patch.object(PageRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            with patch.object(PageRepository, "update", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = created_page
                updated_page = {**created_page, "content": "<p>New content</p>"}
                mock_update.return_value = updated_page

                result = await PageService.update_page(
                    created_page["id"],
                    updated_by=user_id,
                    content="<p>New content</p>",
                )

                assert result["content"] == "<p>New content</p>"
                mock_update.assert_awaited_once()


# ==================== TESTS: DELETE PAGE ====================

class TestDeletePage:
    """Tests para PageService.delete_page"""

    @pytest.mark.asyncio
    async def test_delete_page_success(self, created_page):
        """Test: Eliminar página exitosamente."""
        with patch.object(PageRepository, "delete", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            result = await PageService.delete_page(created_page["id"])

            assert result is True
            mock_delete.assert_awaited_once_with(created_page["id"])

    @pytest.mark.asyncio
    async def test_delete_page_not_found(self):
        """Test: Eliminar página no existente debería retornar False."""
        with patch.object(PageRepository, "delete", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False

            result = await PageService.delete_page("nonexistent_id")

            assert result is False
            mock_delete.assert_awaited_once()


# ==================== TESTS: PUBLISH/UNPUBLISH PAGE ====================

class TestPublishPage:
    """Tests para PageService.publish_page"""

    @pytest.mark.asyncio
    async def test_publish_page_success(self, created_page):
        """Test: Publicar página exitosamente."""
        published_page = {**created_page, "is_published": True}
        with patch.object(PageRepository, "update_publication_status", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = published_page

            result = await PageService.publish_page(created_page["id"], published=True)

            assert result["is_published"] is True
            mock_update.assert_awaited_once_with(created_page["id"], True)

    @pytest.mark.asyncio
    async def test_unpublish_page_success(self, created_page):
        """Test: Despublicar página exitosamente."""
        unpublished_page = {**created_page, "is_published": False}
        with patch.object(PageRepository, "update_publication_status", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = unpublished_page

            result = await PageService.publish_page(created_page["id"], published=False)

            assert result["is_published"] is False
            mock_update.assert_awaited_once_with(created_page["id"], False)

    @pytest.mark.asyncio
    async def test_publish_page_not_found(self):
        """Test: Publicar página no existente debería retornar None."""
        with patch.object(PageRepository, "update_publication_status", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = None

            result = await PageService.publish_page("nonexistent_id", published=True)

            assert result is None


class TestBulkPublish:
    """Tests para PageService.bulk_publish"""

    @pytest.mark.asyncio
    async def test_bulk_publish_success(self, created_page):
        """Test: Publicar múltiples páginas exitosamente."""
        with patch.object(PageRepository, "bulk_update_status", new_callable=AsyncMock) as mock_bulk:
            mock_bulk.return_value = 2

            result = await PageService.bulk_publish([created_page["id"], "page_456"], published=True)

            assert result == 2
            mock_bulk.assert_awaited_once_with([created_page["id"], "page_456"], True)

    @pytest.mark.asyncio
    async def test_bulk_unpublish_success(self, created_page):
        """Test: Despublicar múltiples páginas."""
        with patch.object(PageRepository, "bulk_update_status", new_callable=AsyncMock) as mock_bulk:
            mock_bulk.return_value = 3

            result = await PageService.bulk_publish([created_page["id"], "page_456", "page_789"], published=False)

            assert result == 3

    @pytest.mark.asyncio
    async def test_bulk_publish_empty_list(self):
        """Test: Publicar lista vacía debería retornar 0."""
        with patch.object(PageRepository, "bulk_update_status", new_callable=AsyncMock) as mock_bulk:
            mock_bulk.return_value = 0

            result = await PageService.bulk_publish([], published=True)

            assert result == 0


# ==================== TESTS: COUNT PAGES ====================

class TestCountPages:
    """Tests para PageService.count_pages"""

    @pytest.mark.asyncio
    async def test_count_pages_all(self):
        """Test: Contar todas las páginas."""
        with patch.object(PageRepository, "count", new_callable=AsyncMock) as mock_count:
            mock_count.return_value = 5

            result = await PageService.count_pages()

            assert result == 5
            mock_count.assert_awaited_once_with(None)

    @pytest.mark.asyncio
    async def test_count_pages_by_type(self):
        """Test: Contar páginas por tipo."""
        with patch.object(PageRepository, "count", new_callable=AsyncMock) as mock_count:
            mock_count.return_value = 2

            result = await PageService.count_pages(page_type="CUSTOM")

            assert result == 2

    @pytest.mark.asyncio
    async def test_count_pages_empty(self):
        """Test: Contar páginas cuando no hay."""
        with patch.object(PageRepository, "count", new_callable=AsyncMock) as mock_count:
            mock_count.return_value = 0

            result = await PageService.count_pages()

            assert result == 0


# ==================== TESTS: SLUG UNIQUENESS VALIDATION ====================

class TestSlugUniquenessValidation:
    """Tests para validación de slug único"""

    @pytest.mark.asyncio
    async def test_slug_uniqueness_on_create(self, user_id):
        """Test: Validar slug único en creación."""
        with patch.object(PageRepository, "exists_slug", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = True

            with pytest.raises(ValueError, match="El slug 'duplicate' ya existe"):
                await PageService.create_page(
                    slug="duplicate",
                    title="Test",
                    page_type="CUSTOM",
                    created_by=user_id,
                )

    @pytest.mark.asyncio
    async def test_slug_uniqueness_on_update(self, created_page, user_id):
        """Test: Validar slug único en actualización."""
        with patch.object(PageRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            with patch.object(PageRepository, "exists_slug", new_callable=AsyncMock) as mock_exists:
                mock_get.return_value = created_page
                mock_exists.return_value = True

                with pytest.raises(ValueError, match="El slug 'another-page' ya existe"):
                    await PageService.update_page(
                        created_page["id"],
                        updated_by=user_id,
                        slug="another-page",
                    )

                # Verificar que se excluyó el ID actual en la búsqueda
                mock_exists.assert_awaited_once()
                call_args = mock_exists.await_args
                assert created_page["id"] in call_args[1].values()

    @pytest.mark.asyncio
    async def test_slug_case_sensitive_search(self, user_id):
        """Test: Búsqueda de slug debe ser sensible a mayúsculas."""
        with patch.object(PageRepository, "exists_slug", new_callable=AsyncMock) as mock_exists:
            with patch.object(PageRepository, "create", new_callable=AsyncMock) as mock_create:
                mock_exists.return_value = False
                mock_create.return_value = {
                    "id": "page_123",
                    "slug": "Test-Page",
                    "title": "Test",
                    "page_type": "CUSTOM",
                    "created_by": user_id,
                }

                await PageService.create_page(
                    slug="Test-Page",
                    title="Test",
                    page_type="CUSTOM",
                    created_by=user_id,
                )

                # Verificar que se buscó con el slug exacto
                mock_exists.assert_awaited_once()
