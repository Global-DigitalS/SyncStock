"""
Tests unitarios para los repositorios del backend.
Mockean motor y services.database para no requerir MongoDB real.
"""
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# ==================== MOCK SETUP (antes de importar repositorios) ====================

_motor_mock = MagicMock()
sys.modules.setdefault("motor", _motor_mock)
sys.modules.setdefault("motor.motor_asyncio", _motor_mock)

# Mock de services.database con db vacío (se sobreescribe en cada test con patch)
_database_module = MagicMock()
_database_module.db = MagicMock()
sys.modules.setdefault("services", MagicMock())
sys.modules.setdefault("services.database", _database_module)
for _svc in ["services.auth", "services.sync", "services.config_manager",
             "services.platforms", "services.email_service", "services.encryption"]:
    sys.modules.setdefault(_svc, MagicMock())

# Ahora los imports de repositorios funcionan sin MongoDB
from repositories.catalog_repository import (  # noqa: E402
    CatalogRepository, CatalogItemRepository, MarginRuleRepository
)
from repositories.competitor_repository import (  # noqa: E402
    CompetitorRepository, PendingMatchRepository, PriceAlertRepository
)
from repositories.notification_repository import NotificationRepository  # noqa: E402
from repositories.product_repository import ProductRepository  # noqa: E402


# ==================== HELPERS ====================

def make_cursor(data: list):
    """Mock de cursor Motor: soporta .skip/.limit/.sort/.to_list."""
    cur = MagicMock()
    cur.skip.return_value = cur
    cur.limit.return_value = cur
    cur.sort.return_value = cur
    cur.to_list = AsyncMock(return_value=data)
    return cur


def make_col(*, find_one=None, find_data=None, agg_data=None,
             modified=1, deleted=1, count=0, distinct=None):
    """Mock de colección MongoDB con retornos configurables."""
    col = MagicMock()
    col.find_one = AsyncMock(return_value=find_one)
    col.find = MagicMock(return_value=make_cursor(find_data or []))
    col.aggregate = MagicMock(return_value=make_cursor(agg_data or []))

    col.insert_one = AsyncMock(return_value=MagicMock())
    col.insert_many = AsyncMock(return_value=MagicMock())

    upd = MagicMock()
    upd.modified_count = modified
    upd.matched_count = 1
    col.update_one = AsyncMock(return_value=upd)
    col.update_many = AsyncMock(return_value=upd)

    del_res = MagicMock()
    del_res.deleted_count = deleted
    col.delete_one = AsyncMock(return_value=del_res)
    col.delete_many = AsyncMock(return_value=del_res)

    col.count_documents = AsyncMock(return_value=count)
    col.distinct = AsyncMock(return_value=distinct or [])
    return col


# ==================== CatalogRepository ====================

class TestCatalogRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        doc = {"id": "cat1", "user_id": "u1", "name": "Test"}
        with patch("repositories.catalog_repository.db") as db:
            db.catalogs = make_col(find_one=doc)
            result = await CatalogRepository.get_by_id("cat1", "u1")
        assert result == doc
        db.catalogs.find_one.assert_awaited_once_with({"id": "cat1", "user_id": "u1"}, {"_id": 0})

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        with patch("repositories.catalog_repository.db") as db:
            db.catalogs = make_col(find_one=None)
            result = await CatalogRepository.get_by_id("missing", "u1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_default(self):
        doc = {"id": "cat1", "name": "Principal"}
        with patch("repositories.catalog_repository.db") as db:
            db.catalogs = make_col(find_one=doc)
            result = await CatalogRepository.get_default("u1")
        assert result == doc
        db.catalogs.find_one.assert_awaited_once_with(
            {"user_id": "u1", "is_default": True}, {"_id": 0, "id": 1, "name": 1}
        )

    @pytest.mark.asyncio
    async def test_get_first(self):
        doc = {"id": "cat2", "name": "Primero"}
        with patch("repositories.catalog_repository.db") as db:
            db.catalogs = make_col(find_one=doc)
            result = await CatalogRepository.get_first("u1")
        assert result == doc
        db.catalogs.find_one.assert_awaited_once_with(
            {"user_id": "u1"}, {"_id": 0, "id": 1, "name": 1}
        )

    @pytest.mark.asyncio
    async def test_count(self):
        with patch("repositories.catalog_repository.db") as db:
            db.catalogs = make_col(count=5)
            result = await CatalogRepository.count("u1")
        assert result == 5

    @pytest.mark.asyncio
    async def test_delete_with_cascade_not_found(self):
        with patch("repositories.catalog_repository.db") as db:
            db.catalogs = make_col(find_one=None)
            db.catalog_items = make_col()
            db.catalog_margin_rules = make_col()
            result = await CatalogRepository.delete_with_cascade("cat1", "u1")
        assert result is False
        db.catalog_items.delete_many.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_with_cascade_found(self):
        doc = {"id": "cat1", "user_id": "u1"}
        with patch("repositories.catalog_repository.db") as db:
            db.catalogs = make_col(find_one=doc)
            db.catalog_items = make_col()
            db.catalog_margin_rules = make_col()
            result = await CatalogRepository.delete_with_cascade("cat1", "u1")
        assert result is True
        db.catalog_items.delete_many.assert_awaited_once()
        db.catalog_margin_rules.delete_many.assert_awaited_once()


# ==================== CatalogItemRepository ====================

class TestCatalogItemRepository:
    @pytest.mark.asyncio
    async def test_get_by_user_paginated(self):
        docs = [{"id": "i1"}, {"id": "i2"}]
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_items = make_col(find_data=docs)
            result = await CatalogItemRepository.get_by_user_paginated("u1", {"active": True}, 0, 10)
        assert result == docs
        db.catalog_items.find.assert_called_once_with(
            {"user_id": "u1", "active": True}, {"_id": 0, "user_id": 0}
        )

    @pytest.mark.asyncio
    async def test_aggregate_returns_list(self):
        agg = [{"_id": "cat1", "count": 3}]
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_items = make_col(agg_data=agg)
            result = await CatalogItemRepository.aggregate([{"$match": {"catalog_id": "cat1"}}])
        assert result == agg

    @pytest.mark.asyncio
    async def test_update_many_returns_modified_count(self):
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_items = make_col(modified=3)
            count = await CatalogItemRepository.update_many(
                {"catalog_id": "cat1"}, {"$set": {"category_ids": []}}
            )
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_by_id_no_catalog(self):
        doc = {"id": "item1", "catalog_id": "cat1", "user_id": "u1"}
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_items = make_col(find_one=doc)
            result = await CatalogItemRepository.get_by_id_no_catalog("item1")
        assert result == doc
        db.catalog_items.find_one.assert_awaited_once_with({"id": "item1"})

    @pytest.mark.asyncio
    async def test_delete_item_by_id_success(self):
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_items = make_col(deleted=1)
            result = await CatalogItemRepository.delete_item_by_id("item1", "u1")
        assert result is True
        db.catalog_items.delete_one.assert_awaited_once_with({"id": "item1", "user_id": "u1"})

    @pytest.mark.asyncio
    async def test_delete_item_by_id_not_found(self):
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_items = make_col(deleted=0)
            result = await CatalogItemRepository.delete_item_by_id("missing", "u1")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_existing_product_ids(self):
        docs = [{"product_id": "p1"}, {"product_id": "p2"}]
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_items = make_col(find_data=docs)
            result = await CatalogItemRepository.get_existing_product_ids("cat1")
        assert result == {"p1", "p2"}


# ==================== MarginRuleRepository ====================

class TestMarginRuleRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_no_catalog(self):
        doc = {"id": "rule1", "name": "Margen 10%"}
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_margin_rules = make_col(find_one=doc)
            result = await MarginRuleRepository.get_by_id_no_catalog("rule1", "u1")
        assert result == doc
        db.catalog_margin_rules.find_one.assert_awaited_once_with(
            {"id": "rule1", "user_id": "u1"}, {"_id": 0, "user_id": 0}
        )

    @pytest.mark.asyncio
    async def test_delete_by_user_success(self):
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_margin_rules = make_col(deleted=1)
            result = await MarginRuleRepository.delete_by_user("rule1", "u1")
        assert result is True
        db.catalog_margin_rules.delete_one.assert_awaited_once_with({"id": "rule1", "user_id": "u1"})

    @pytest.mark.asyncio
    async def test_delete_by_user_not_found(self):
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_margin_rules = make_col(deleted=0)
            result = await MarginRuleRepository.delete_by_user("missing", "u1")
        assert result is False

    @pytest.mark.asyncio
    async def test_count(self):
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_margin_rules = make_col(count=4)
            result = await MarginRuleRepository.count("cat1")
        assert result == 4

    @pytest.mark.asyncio
    async def test_get_all_sorts_by_priority(self):
        """get_all debe ordenar por prioridad descendente."""
        with patch("repositories.catalog_repository.db") as db:
            db.catalog_margin_rules = make_col(find_data=[])
            await MarginRuleRepository.get_all("cat1")
        cursor = db.catalog_margin_rules.find.return_value
        cursor.sort.assert_called_once_with("priority", -1)


# ==================== ProductRepository ====================

class TestProductRepository:
    @pytest.mark.asyncio
    async def test_find_one_with_query(self):
        doc = {"id": "p1", "sku": "ABC", "price": 10.0}
        with patch("repositories.product_repository.db") as db:
            db.products = make_col(find_one=doc)
            result = await ProductRepository.find_one({"user_id": "u1", "sku": "ABC"})
        assert result == doc

    @pytest.mark.asyncio
    async def test_find_by_sku(self):
        doc = {"price": 25.0}
        with patch("repositories.product_repository.db") as db:
            db.products = make_col(find_one=doc)
            result = await ProductRepository.find_by_sku("u1", "SKU001", {"_id": 0, "price": 1})
        assert result == doc
        db.products.find_one.assert_awaited_once_with(
            {"user_id": "u1", "sku": "SKU001"}, {"_id": 0, "price": 1}
        )

    @pytest.mark.asyncio
    async def test_find_paginated_with_projection(self):
        docs = [{"id": "p1", "name": "Prod A"}, {"id": "p2", "name": "Prod B"}]
        with patch("repositories.product_repository.db") as db:
            db.products = make_col(find_data=docs)
            result = await ProductRepository.find_paginated(
                {"user_id": "u1"}, 0, 10, {"_id": 0, "id": 1, "name": 1}
            )
        assert result == docs
        db.products.find.assert_called_once_with({"user_id": "u1"}, {"_id": 0, "id": 1, "name": 1})

    @pytest.mark.asyncio
    async def test_count(self):
        with patch("repositories.product_repository.db") as db:
            db.products = make_col(count=42)
            result = await ProductRepository.count({"user_id": "u1"})
        assert result == 42

    @pytest.mark.asyncio
    async def test_delete_success(self):
        with patch("repositories.product_repository.db") as db:
            db.products = make_col(deleted=1)
            result = await ProductRepository.delete("p1", "u1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_many(self):
        with patch("repositories.product_repository.db") as db:
            db.products = make_col(deleted=5)
            count = await ProductRepository.delete_many(["p1", "p2", "p3", "p4", "p5"], "u1")
        assert count == 5


# ==================== CompetitorRepository ====================

class TestCompetitorRepository:
    @pytest.mark.asyncio
    async def test_find_by_url(self):
        doc = {"id": "comp1", "base_url": "https://rival.com"}
        with patch("repositories.competitor_repository.db") as db:
            db.competitors = make_col(find_one=doc)
            result = await CompetitorRepository.find_by_url("u1", "https://rival.com")
        assert result == doc
        db.competitors.find_one.assert_awaited_once_with(
            {"user_id": "u1", "base_url": "https://rival.com"}
        )

    @pytest.mark.asyncio
    async def test_aggregate_snapshots(self):
        agg = [{"_id": "comp1", "count": 10}]
        with patch("repositories.competitor_repository.db") as db:
            db.price_snapshots = make_col(agg_data=agg)
            result = await CompetitorRepository.aggregate_snapshots(
                [{"$group": {"_id": "$competitor_id", "count": {"$sum": 1}}}]
            )
        assert result == agg

    @pytest.mark.asyncio
    async def test_delete_snapshots_returns_count(self):
        with patch("repositories.competitor_repository.db") as db:
            db.price_snapshots = make_col(deleted=7)
            result = await CompetitorRepository.delete_snapshots("comp1", "u1")
        assert result == 7
        db.price_snapshots.delete_many.assert_awaited_once_with(
            {"competitor_id": "comp1", "user_id": "u1"}
        )

    @pytest.mark.asyncio
    async def test_count_with_extra_query(self):
        with patch("repositories.competitor_repository.db") as db:
            db.competitors = make_col(count=3)
            result = await CompetitorRepository.count("u1", {"active": True})
        assert result == 3
        db.competitors.count_documents.assert_awaited_once_with({"user_id": "u1", "active": True})

    @pytest.mark.asyncio
    async def test_count_no_extra_query(self):
        with patch("repositories.competitor_repository.db") as db:
            db.competitors = make_col(count=10)
            result = await CompetitorRepository.count("u1")
        assert result == 10
        db.competitors.count_documents.assert_awaited_once_with({"user_id": "u1"})

    @pytest.mark.asyncio
    async def test_update_snapshot(self):
        with patch("repositories.competitor_repository.db") as db:
            db.price_snapshots = make_col()
            await CompetitorRepository.update_snapshot(
                {"id": "snap1", "user_id": "u1"},
                {"$set": {"match_confidence": 1.0}},
            )
        db.price_snapshots.update_one.assert_awaited_once_with(
            {"id": "snap1", "user_id": "u1"},
            {"$set": {"match_confidence": 1.0}},
        )

    @pytest.mark.asyncio
    async def test_distinct_snapshot_field(self):
        with patch("repositories.competitor_repository.db") as db:
            db.price_snapshots = make_col(distinct=["SKU1", "SKU2", None])
            result = await CompetitorRepository.distinct_snapshot_field("sku", {"user_id": "u1"})
        assert result == ["SKU1", "SKU2", None]

    @pytest.mark.asyncio
    async def test_count_snapshots_by_query(self):
        with patch("repositories.competitor_repository.db") as db:
            db.price_snapshots = make_col(count=15)
            result = await CompetitorRepository.count_snapshots_by_query(
                {"user_id": "u1", "scraped_at": {"$gte": "2026-01-01"}}
            )
        assert result == 15


# ==================== NotificationRepository ====================

class TestNotificationRepository:
    @pytest.mark.asyncio
    async def test_create(self):
        notification = {"id": "n1", "user_id": "u1", "message": "Test"}
        with patch("repositories.notification_repository.db") as db:
            db.notifications = make_col()
            result = await NotificationRepository.create(notification)
        assert result == notification
        db.notifications.insert_one.assert_awaited_once_with(notification)

    @pytest.mark.asyncio
    async def test_find_by_query(self):
        docs = [{"id": "n1", "type": "competitor_price"}]
        with patch("repositories.notification_repository.db") as db:
            db.notifications = make_col(find_data=docs)
            result = await NotificationRepository.find_by_query(
                "u1", {"type": "competitor_price"}, limit=20
            )
        assert result == docs
        db.notifications.find.assert_called_once_with(
            {"user_id": "u1", "type": "competitor_price"}, {"_id": 0}
        )

    @pytest.mark.asyncio
    async def test_mark_all_read(self):
        with patch("repositories.notification_repository.db") as db:
            db.notifications = make_col()
            await NotificationRepository.mark_all_read("u1")
        db.notifications.update_many.assert_awaited_once_with(
            {"user_id": "u1"}, {"$set": {"read": True}}
        )

    @pytest.mark.asyncio
    async def test_delete_success(self):
        with patch("repositories.notification_repository.db") as db:
            db.notifications = make_col(deleted=1)
            result = await NotificationRepository.delete("n1", "u1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        with patch("repositories.notification_repository.db") as db:
            db.notifications = make_col(deleted=0)
            result = await NotificationRepository.delete("missing", "u1")
        assert result is False


# ==================== PendingMatchRepository ====================

class TestPendingMatchRepository:
    @pytest.mark.asyncio
    async def test_get_paginated_with_status(self):
        docs = [{"id": "m1", "status": "pending"}]
        with patch("repositories.competitor_repository.db") as db:
            db.pending_matches = make_col(find_data=docs, count=1)
            items, total = await PendingMatchRepository.get_paginated("u1", 0, 10, status="pending")
        assert items == docs
        assert total == 1
        db.pending_matches.count_documents.assert_awaited_once_with(
            {"user_id": "u1", "status": "pending"}
        )

    @pytest.mark.asyncio
    async def test_get_paginated_no_status(self):
        with patch("repositories.competitor_repository.db") as db:
            db.pending_matches = make_col(find_data=[], count=0)
            items, total = await PendingMatchRepository.get_paginated("u1", 0, 10)
        assert items == []
        assert total == 0
        db.pending_matches.count_documents.assert_awaited_once_with({"user_id": "u1"})


# ==================== PriceAlertRepository ====================

class TestPriceAlertRepository:
    @pytest.mark.asyncio
    async def test_count_with_query(self):
        with patch("repositories.competitor_repository.db") as db:
            db.price_alerts = make_col(count=6)
            result = await PriceAlertRepository.count("u1", {"active": True})
        assert result == 6
        db.price_alerts.count_documents.assert_awaited_once_with(
            {"user_id": "u1", "active": True}
        )

    @pytest.mark.asyncio
    async def test_delete_success(self):
        with patch("repositories.competitor_repository.db") as db:
            db.price_alerts = make_col(deleted=1)
            result = await PriceAlertRepository.delete("alert1", "u1")
        assert result is True
