"""Repositorios para catalogs, catalog_items, catalog_margin_rules y catalog_categories."""
import logging

from services.database import db

logger = logging.getLogger(__name__)

MAX_MARGIN_RULES = 50


class CatalogRepository:
    @staticmethod
    async def get_by_id(catalog_id: str, user_id: str) -> dict | None:
        return await db.catalogs.find_one({"id": catalog_id, "user_id": user_id}, {"_id": 0})

    @staticmethod
    async def get_all(user_id: str) -> list:
        return await db.catalogs.find({"user_id": user_id}, {"_id": 0}).to_list(100)

    @staticmethod
    async def create(data: dict) -> dict:
        await db.catalogs.insert_one(data)
        return data

    @staticmethod
    async def count(user_id: str) -> int:
        return await db.catalogs.count_documents({"user_id": user_id})

    @staticmethod
    async def set_all_non_default(user_id: str) -> None:
        await db.catalogs.update_many({"user_id": user_id}, {"$set": {"is_default": False}})

    @staticmethod
    async def set_others_non_default(user_id: str, catalog_id: str) -> None:
        await db.catalogs.update_many(
            {"user_id": user_id, "id": {"$ne": catalog_id}},
            {"$set": {"is_default": False}}
        )

    @staticmethod
    async def update(catalog_id: str, user_id: str, updates: dict) -> dict | None:
        existing = await db.catalogs.find_one({"id": catalog_id, "user_id": user_id})
        if not existing:
            return None
        await db.catalogs.update_one({"id": catalog_id}, {"$set": updates})
        return await db.catalogs.find_one({"id": catalog_id}, {"_id": 0})


    @staticmethod
    async def update_by_id(catalog_id: str, updates: dict) -> dict | None:
        """Actualiza un catálogo por ID (sin validar user_id, asumido ya verificado)."""
        await db.catalogs.update_one({"id": catalog_id}, {"$set": updates})
        return await db.catalogs.find_one({"id": catalog_id}, {"_id": 0})

    @staticmethod
    async def get_by_id_no_auth(catalog_id: str) -> dict | None:
        """Obtiene un catálogo por ID sin filtro de usuario."""
        return await db.catalogs.find_one({"id": catalog_id}, {"_id": 0})

    @staticmethod
    async def delete_with_cascade(catalog_id: str, user_id: str) -> bool:
        existing = await db.catalogs.find_one({"id": catalog_id, "user_id": user_id})
        if not existing:
            return False
        await db.catalog_items.delete_many({"catalog_id": catalog_id, "user_id": user_id})
        await db.catalog_margin_rules.delete_many({"catalog_id": catalog_id, "user_id": user_id})
        await db.catalogs.delete_one({"id": catalog_id, "user_id": user_id})
        return True

    @staticmethod
    async def get_many_by_ids(catalog_ids: list, user_id: str) -> list:
        """Devuelve los catálogos cuyos IDs estén en la lista y pertenezcan al usuario."""
        return await db.catalogs.find(
            {"id": {"$in": catalog_ids}, "user_id": user_id}, {"_id": 0}
        ).to_list(100)

    @staticmethod
    async def get_by_ids(catalog_ids: list) -> list:
        """Devuelve catálogos por IDs sin filtro de usuario (para IDs ya validados)."""
        return await db.catalogs.find(
            {"id": {"$in": catalog_ids}}, {"_id": 0}
        ).to_list(100)

    @staticmethod
    async def get_default(user_id: str) -> dict | None:
        """Devuelve el catálogo predeterminado del usuario."""
        return await db.catalogs.find_one(
            {"user_id": user_id, "is_default": True}, {"_id": 0, "id": 1, "name": 1}
        )

    @staticmethod
    async def get_first(user_id: str) -> dict | None:
        """Devuelve el primer catálogo del usuario (sin orden garantizado)."""
        return await db.catalogs.find_one(
            {"user_id": user_id}, {"_id": 0, "id": 1, "name": 1}
        )

    @staticmethod
    async def get_item_counts(catalog_ids: list) -> dict:
        """Devuelve {catalog_id: count} para una lista de IDs."""
        pipeline = [
            {"$match": {"catalog_id": {"$in": catalog_ids}}},
            {"$group": {"_id": "$catalog_id", "count": {"$sum": 1}}}
        ]
        results = await db.catalog_items.aggregate(pipeline).to_list(100)
        return {r["_id"]: r["count"] for r in results}

    @staticmethod
    async def get_rule_counts(catalog_ids: list) -> dict:
        pipeline = [
            {"$match": {"catalog_id": {"$in": catalog_ids}}},
            {"$group": {"_id": "$catalog_id", "count": {"$sum": 1}}}
        ]
        results = await db.catalog_margin_rules.aggregate(pipeline).to_list(100)
        return {r["_id"]: r["count"] for r in results}

    @staticmethod
    async def get_category_counts(catalog_ids: list) -> dict:
        pipeline = [
            {"$match": {"catalog_id": {"$in": catalog_ids}}},
            {"$group": {"_id": "$catalog_id", "count": {"$sum": 1}}}
        ]
        results = await db.catalog_categories.aggregate(pipeline).to_list(100)
        return {r["_id"]: r["count"] for r in results}


class CatalogItemRepository:
    @staticmethod
    async def count(catalog_id: str) -> int:
        return await db.catalog_items.count_documents({"catalog_id": catalog_id})

    @staticmethod
    async def get_paginated(catalog_id: str, query: dict, skip: int, limit: int) -> list:
        full_query = {"catalog_id": catalog_id, **query}
        return await db.catalog_items.find(full_query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)

    @staticmethod
    async def get_active(catalog_id: str) -> list:
        return await db.catalog_items.find(
            {"catalog_id": catalog_id, "active": True}, {"_id": 0}
        ).to_list(10000)

    @staticmethod
    async def get_existing_product_ids(catalog_id: str) -> set:
        existing = await db.catalog_items.find(
            {"catalog_id": catalog_id}, {"product_id": 1}
        ).to_list(None)
        return {item["product_id"] for item in existing}

    @staticmethod
    async def insert_many(items: list) -> None:
        if items:
            await db.catalog_items.insert_many(items, ordered=False)

    @staticmethod
    async def delete_item(item_id: str, catalog_id: str, user_id: str) -> bool:
        result = await db.catalog_items.delete_one(
            {"id": item_id, "catalog_id": catalog_id, "user_id": user_id}
        )
        return result.deleted_count > 0

    @staticmethod
    async def delete_by_product(product_id: str, user_id: str) -> None:
        await db.catalog_items.delete_many({"product_id": product_id, "user_id": user_id})

    @staticmethod
    async def delete_by_products(product_ids: list, user_id: str) -> None:
        await db.catalog_items.delete_many({"product_id": {"$in": product_ids}, "user_id": user_id})

    @staticmethod
    async def update_many(filter_query: dict, updates: dict) -> int:
        result = await db.catalog_items.update_many(filter_query, updates)
        return result.modified_count


    @staticmethod
    async def insert_one(data: dict) -> dict:
        await db.catalog_items.insert_one(data)
        return data

    @staticmethod
    async def get_by_item_id(item_id: str, catalog_id: str) -> dict | None:
        """Busca un ítem por su ID de ítem y catalog_id."""
        return await db.catalog_items.find_one({"id": item_id, "catalog_id": catalog_id})

    @staticmethod
    async def get_by_product_user(product_id: str, user_id: str) -> dict | None:
        return await db.catalog_items.find_one({"product_id": product_id, "user_id": user_id})

    @staticmethod
    async def update_by_id(item_id: str, updates: dict) -> None:
        await db.catalog_items.update_one({"id": item_id}, {"$set": updates})

    @staticmethod
    async def count_by_category(catalog_id: str, category_id: str) -> int:
        return await db.catalog_items.count_documents({"catalog_id": catalog_id, "category_ids": category_id})

    @staticmethod
    async def find_by_category(catalog_id: str, category_id: str) -> list:
        return await db.catalog_items.find(
            {"catalog_id": catalog_id, "category_ids": category_id}, {"_id": 0}
        ).to_list(500)

    @staticmethod
    async def remove_category_refs(catalog_id: str, category_ids: list) -> None:
        """Elimina referencias a categorías eliminadas de los ítems del catálogo."""
        await db.catalog_items.update_many(
            {"catalog_id": catalog_id, "category_ids": {"$in": category_ids}},
            {"$pull": {"category_ids": {"$in": category_ids}}}
        )

    @staticmethod
    async def find_valid_ids(catalog_id: str, product_ids: list, user_id: str) -> set:
        """Valida que los product_ids existen y pertenecen al usuario."""
        docs = await db.catalog_items.find(
            {"catalog_id": catalog_id, "product_id": {"$in": product_ids}},
            {"product_id": 1}
        ).to_list(len(product_ids))
        return {d["product_id"] for d in docs}

    @staticmethod
    async def get_by_user_paginated(user_id: str, extra_query: dict, skip: int, limit: int) -> list:
        """Lista ítems filtrados por user_id sin requerir catalog_id (endpoints legacy)."""
        full_query = {"user_id": user_id, **extra_query}
        return await db.catalog_items.find(
            full_query, {"_id": 0, "user_id": 0}
        ).skip(skip).limit(limit).to_list(limit)

    @staticmethod
    async def aggregate(pipeline: list, limit: int = 1000) -> list:
        return await db.catalog_items.aggregate(pipeline).to_list(limit)

    @staticmethod
    async def get_by_id_no_catalog(item_id: str) -> dict | None:
        """Busca un ítem por ID sin filtrar por catalog_id (endpoints legacy)."""
        return await db.catalog_items.find_one({"id": item_id})

    @staticmethod
    async def delete_item_by_id(item_id: str, user_id: str) -> bool:
        """Elimina un ítem por ID y user_id sin requerir catalog_id (endpoints legacy)."""
        result = await db.catalog_items.delete_one({"id": item_id, "user_id": user_id})
        return result.deleted_count > 0

    @staticmethod
    async def find_pairs(catalog_ids: list, product_ids: list) -> set:
        """Devuelve el conjunto de pares (catalog_id, product_id) ya existentes."""
        existing = await db.catalog_items.find(
            {"catalog_id": {"$in": catalog_ids}, "product_id": {"$in": product_ids}},
            {"catalog_id": 1, "product_id": 1}
        ).to_list(10000)
        return {(item["catalog_id"], item["product_id"]) for item in existing}


class CatalogCategoryRepository:

    @staticmethod
    async def get_by_id(category_id: str, catalog_id: str) -> dict | None:
        """Obtiene una categoría por ID sin exponer _id ni user_id."""
        return await db.catalog_categories.find_one(
            {"id": category_id, "catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
        )

    @staticmethod
    async def get_by_id_raw(category_id: str, catalog_id: str) -> dict | None:
        """Obtiene una categoría incluyendo todos los campos (para checks internos)."""
        return await db.catalog_categories.find_one({"id": category_id, "catalog_id": catalog_id})

    @staticmethod
    async def get_all_by_position(catalog_id: str) -> list:
        """Devuelve categorías ordenadas por posición (para árbol plano)."""
        return await db.catalog_categories.find(
            {"catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
        ).sort("position", 1).to_list(500)

    @staticmethod
    async def get_max_position(catalog_id: str, parent_id) -> dict | None:
        """Obtiene la categoría con mayor posición bajo el mismo padre."""
        return await db.catalog_categories.find_one(
            {"catalog_id": catalog_id, "parent_id": parent_id},
            sort=[("position", -1)]
        )

    @staticmethod
    async def update_by_id(category_id: str, updates: dict) -> None:
        await db.catalog_categories.update_one({"id": category_id}, {"$set": updates})

    @staticmethod
    async def update_by_id_in_catalog(category_id: str, catalog_id: str, updates: dict) -> None:
        await db.catalog_categories.update_one(
            {"id": category_id, "catalog_id": catalog_id}, {"$set": updates}
        )

    @staticmethod
    async def find_children(catalog_id: str, parent_id: str) -> list:
        return await db.catalog_categories.find(
            {"catalog_id": catalog_id, "parent_id": parent_id}
        ).to_list(100)

    @staticmethod
    async def get_in_catalog(catalog_id: str, category_ids: list) -> list:
        """Obtiene categorías por IDs dentro de un catálogo (para validación)."""
        return await db.catalog_categories.find(
            {"catalog_id": catalog_id, "id": {"$in": category_ids}}
        ).to_list(100)

    @staticmethod
    async def delete_by_ids(ids: list) -> None:
        await db.catalog_categories.delete_many({"id": {"$in": ids}})

    @staticmethod
    async def count(catalog_id: str) -> int:
        return await db.catalog_categories.count_documents({"catalog_id": catalog_id})

    @staticmethod
    async def get_sorted(catalog_id: str) -> list:
        """Devuelve las categorías de un catálogo ordenadas por nivel y posición."""
        return await db.catalog_categories.find(
            {"catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
        ).sort([("level", 1), ("position", 1)]).to_list(500)

    @staticmethod
    async def get_all(catalog_id: str) -> list:
        return await db.catalog_categories.find(
            {"catalog_id": catalog_id}, {"_id": 0}
        ).to_list(500)

    @staticmethod
    async def create(data: dict) -> dict:
        await db.catalog_categories.insert_one(data)
        return data

    @staticmethod
    async def delete_by_catalog(catalog_id: str, user_id: str) -> None:
        await db.catalog_categories.delete_many({"catalog_id": catalog_id, "user_id": user_id})


class MarginRuleRepository:
    @staticmethod
    async def get_all(catalog_id: str) -> list:
        return await db.catalog_margin_rules.find(
            {"catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
        ).sort("priority", -1).to_list(MAX_MARGIN_RULES)

    @staticmethod
    async def get_for_sync(catalog_id: str) -> list:
        return await db.catalog_margin_rules.find(
            {"catalog_id": catalog_id}, {"_id": 0}
        ).sort("priority", -1).to_list(100)

    @staticmethod
    async def create(data: dict) -> dict:
        await db.catalog_margin_rules.insert_one(data)
        return data

    @staticmethod
    async def count(catalog_id: str) -> int:
        return await db.catalog_margin_rules.count_documents({"catalog_id": catalog_id})

    @staticmethod
    async def get_by_user(user_id: str) -> list:
        """Obtiene todas las reglas de margen de un usuario (sin catalog_id)."""
        return await db.catalog_margin_rules.find(
            {"user_id": user_id}, {"_id": 0}
        ).sort("priority", -1).to_list(50)

    @staticmethod
    async def get_by_id(rule_id: str, catalog_id: str, user_id: str) -> dict | None:
        return await db.catalog_margin_rules.find_one(
            {"id": rule_id, "catalog_id": catalog_id, "user_id": user_id}, {"_id": 0, "user_id": 0}
        )

    @staticmethod
    async def update(rule_id: str, user_id: str, updates: dict) -> dict | None:
        await db.catalog_margin_rules.update_one(
            {"id": rule_id, "user_id": user_id}, {"$set": updates}
        )
        return await db.catalog_margin_rules.find_one({"id": rule_id}, {"_id": 0, "user_id": 0})

    @staticmethod
    async def delete(rule_id: str, catalog_id: str, user_id: str) -> bool:
        result = await db.catalog_margin_rules.delete_one(
            {"id": rule_id, "catalog_id": catalog_id, "user_id": user_id}
        )
        return result.deleted_count > 0

    @staticmethod
    async def delete_by_catalog(catalog_id: str, user_id: str) -> None:
        await db.catalog_margin_rules.delete_many({"catalog_id": catalog_id, "user_id": user_id})

    @staticmethod
    async def get_by_id_no_catalog(rule_id: str, user_id: str) -> dict | None:
        """Busca una regla por ID sin filtrar por catalog_id (endpoints legacy)."""
        return await db.catalog_margin_rules.find_one(
            {"id": rule_id, "user_id": user_id}, {"_id": 0, "user_id": 0}
        )

    @staticmethod
    async def delete_by_user(rule_id: str, user_id: str) -> bool:
        """Elimina una regla por ID y user_id sin requerir catalog_id (endpoints legacy)."""
        result = await db.catalog_margin_rules.delete_one({"id": rule_id, "user_id": user_id})
        return result.deleted_count > 0


