"""Repositorio para competitors, price_snapshots, price_alerts y price_automation_rules.
Incluye los pipelines de agregacion complejos del dashboard como metodos nombrados.
"""
import logging

from services.database import db

logger = logging.getLogger(__name__)


class CompetitorRepository:
    @staticmethod
    async def get_by_id(competitor_id: str, user_id: str) -> dict | None:
        return await db.competitors.find_one({"id": competitor_id, "user_id": user_id})

    @staticmethod
    async def get_all_paginated(user_id: str, query: dict, skip: int, limit: int) -> tuple[list, int]:
        full_query = {"user_id": user_id, **query}
        total = await db.competitors.count_documents(full_query)
        items = await db.competitors.find(full_query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
        return items, total

    @staticmethod
    async def create(data: dict) -> dict:
        await db.competitors.insert_one(data)
        return data

    @staticmethod
    async def update(competitor_id: str, user_id: str, updates: dict) -> dict | None:
        await db.competitors.update_one(
            {"id": competitor_id, "user_id": user_id}, {"$set": updates}
        )
        return await db.competitors.find_one({"id": competitor_id, "user_id": user_id})

    @staticmethod
    async def delete(competitor_id: str, user_id: str) -> bool:
        result = await db.competitors.delete_one({"id": competitor_id, "user_id": user_id})
        return result.deleted_count > 0

    @staticmethod
    async def count_snapshots(competitor_id: str) -> int:
        return await db.price_snapshots.count_documents({"competitor_id": competitor_id})

    @staticmethod
    async def get_price_snapshots(query: dict, limit: int = 100, sort: tuple = None) -> list:
        cursor = db.price_snapshots.find(query, {"_id": 0})
        if sort:
            cursor = cursor.sort(*sort)
        return await cursor.to_list(limit)

    @staticmethod
    async def aggregate_snapshots(pipeline: list, limit: int = 10000) -> list:
        return await db.price_snapshots.aggregate(pipeline).to_list(limit)


    @staticmethod
    async def get_all(user_id: str, query: dict = None, sort_field: str = "created_at") -> list:
        """Devuelve todos los competidores del usuario, opcionalmente filtrados."""
        full_query = {"user_id": user_id, **(query or {})}
        return await db.competitors.find(
            full_query, {"_id": 0}
        ).sort(sort_field, -1).to_list(200)

    @staticmethod
    async def count(user_id: str, query: dict = None) -> int:
        full_query = {"user_id": user_id, **(query or {})}
        return await db.competitors.count_documents(full_query)

    @staticmethod
    async def find_by_url(user_id: str, base_url: str) -> dict | None:
        return await db.competitors.find_one({"user_id": user_id, "base_url": base_url})

    @staticmethod
    async def get_by_id_clean(competitor_id: str, user_id: str) -> dict | None:
        return await db.competitors.find_one(
            {"id": competitor_id, "user_id": user_id}, {"_id": 0}
        )

    @staticmethod
    async def delete_snapshots(competitor_id: str, user_id: str) -> int:
        result = await db.price_snapshots.delete_many(
            {"competitor_id": competitor_id, "user_id": user_id}
        )
        return result.deleted_count

    @staticmethod
    async def count_snapshots_by_query(query: dict) -> int:
        return await db.price_snapshots.count_documents(query)

    @staticmethod
    async def distinct_snapshot_field(field: str, query: dict) -> list:
        return await db.price_snapshots.distinct(field, query)

    @staticmethod
    async def find_one_snapshot(query: dict, sort: list = None) -> dict | None:
        cursor = db.price_snapshots.find_one(query, {"_id": 0, "price": 1})
        if sort:
            return await db.price_snapshots.find_one(query, {"_id": 0, "price": 1}, sort=sort)
        return await cursor if cursor else None

    @staticmethod
    async def upsert_snapshot(filter_query: dict, updates: dict) -> None:
        from pymongo import UpdateOne
        await db.price_snapshots.update_one(filter_query, updates, upsert=True)

    @staticmethod
    async def update_snapshot(filter_query: dict, updates: dict) -> None:
        await db.price_snapshots.update_one(filter_query, updates)


class PriceAlertRepository:
    @staticmethod
    async def get_all(user_id: str, query: dict, limit: int = 100) -> list:
        full_query = {"user_id": user_id, **query}
        return await db.price_alerts.find(full_query, {"_id": 0}).sort("created_at", -1).to_list(limit)

    @staticmethod
    async def get_by_id(alert_id: str, user_id: str) -> dict | None:
        return await db.price_alerts.find_one({"id": alert_id, "user_id": user_id})

    @staticmethod
    async def create(data: dict) -> dict:
        await db.price_alerts.insert_one(data)
        return data

    @staticmethod
    async def update(alert_id: str, user_id: str, updates: dict) -> dict | None:
        await db.price_alerts.update_one(
            {"id": alert_id, "user_id": user_id}, {"$set": updates}
        )
        return await db.price_alerts.find_one({"id": alert_id, "user_id": user_id}, {"_id": 0})


    @staticmethod
    async def count(user_id: str, query: dict = None) -> int:
        full_query = {"user_id": user_id, **(query or {})}
        return await db.price_alerts.count_documents(full_query)

    @staticmethod
    async def delete(alert_id: str, user_id: str) -> bool:
        result = await db.price_alerts.delete_one({"id": alert_id, "user_id": user_id})
        return result.deleted_count > 0


class AutomationRuleRepository:
    @staticmethod
    async def get_all(user_id: str, query: dict) -> list:
        full_query = {"user_id": user_id, **query}
        return await db.price_automation_rules.find(full_query, {"_id": 0}).sort("priority", -1).to_list(100)

    @staticmethod
    async def get_by_id(rule_id: str, user_id: str) -> dict | None:
        return await db.price_automation_rules.find_one({"id": rule_id, "user_id": user_id})

    @staticmethod
    async def create(data: dict) -> dict:
        await db.price_automation_rules.insert_one(data)
        return data

    @staticmethod
    async def update(rule_id: str, user_id: str, updates: dict) -> dict | None:
        await db.price_automation_rules.update_one(
            {"id": rule_id, "user_id": user_id}, {"$set": updates}
        )
        return await db.price_automation_rules.find_one({"id": rule_id, "user_id": user_id}, {"_id": 0})

    @staticmethod
    async def update_by_id(rule_id: str, updates: dict) -> None:
        await db.price_automation_rules.update_one({"id": rule_id}, {"$set": updates})

    @staticmethod
    async def delete(rule_id: str, user_id: str) -> bool:
        result = await db.price_automation_rules.delete_one({"id": rule_id, "user_id": user_id})
        return result.deleted_count > 0


class CrawlJobRepository:
    @staticmethod
    async def get_paginated(user_id: str, query: dict, offset: int, limit: int) -> tuple[list, int]:
        total = await db.crawl_jobs.count_documents(query)
        jobs = await db.crawl_jobs.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        return jobs, total


class UserMonitoringConfigRepository:
    @staticmethod
    async def get_monitoring_catalog_id(user_id: str) -> str | None:
        doc = await db.users.find_one(
            {"id": user_id}, {"_id": 0, "competitor_monitoring_catalog_id": 1}
        )
        return doc.get("competitor_monitoring_catalog_id") if doc else None

    @staticmethod
    async def set_monitoring_catalog_id(user_id: str, catalog_id: str) -> bool:
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"competitor_monitoring_catalog_id": catalog_id}}
        )
        return result.matched_count > 0


class PendingMatchRepository:
    @staticmethod
    async def get_paginated(user_id: str, skip: int, limit: int, status: str = None) -> tuple[list, int]:
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        total = await db.pending_matches.count_documents(query)
        items = await db.pending_matches.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        return items, total

    @staticmethod
    async def get_by_id(match_id: str, user_id: str) -> dict | None:
        return await db.pending_matches.find_one({"id": match_id, "user_id": user_id})

    @staticmethod
    async def update(match_id: str, user_id: str, updates: dict) -> None:
        await db.pending_matches.update_one({"id": match_id, "user_id": user_id}, {"$set": updates})
