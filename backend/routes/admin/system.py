"""
Rutas de reinicio del sistema para SuperAdmin.
"""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.auth import get_superadmin_user
from services.database import db

sub_router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== SYSTEM RESET ====================

class ResetConfirmation(BaseModel):
    confirmation_text: str = Field(..., description="Debe ser 'RESET' para confirmar")

@sub_router.post("/admin/system/reset")
async def reset_application(confirmation: ResetConfirmation, user: dict = Depends(get_superadmin_user)):
    """
    Reset the entire application, deleting all data EXCEPT users.
    Requires confirmation_text = "RESET" to execute.
    """
    if confirmation.confirmation_text != "RESET":
        raise HTTPException(
            status_code=400,
            detail="Confirmación incorrecta. Escriba 'RESET' para confirmar."
        )

    try:
        # List of collections to preserve (users-related)
        preserved_collections = ["users"]

        # Get all collection names
        database = db.client.get_database(db.name)
        all_collections = await database.list_collection_names()

        deleted_stats = {}

        for collection_name in all_collections:
            if collection_name in preserved_collections:
                # Count but don't delete users
                count = await database[collection_name].count_documents({})
                deleted_stats[collection_name] = {"preserved": True, "count": count}
                continue

            # Count documents before deletion
            count = await database[collection_name].count_documents({})

            # Delete all documents in this collection
            if count > 0:
                result = await database[collection_name].delete_many({})
                deleted_stats[collection_name] = {
                    "deleted": result.deleted_count,
                    "preserved": False
                }
            else:
                deleted_stats[collection_name] = {"deleted": 0, "preserved": False}

        logger.warning(f"SYSTEM RESET executed by SuperAdmin {user.get('email')} - Stats: {deleted_stats}")

        return {
            "success": True,
            "message": "Aplicación reiniciada correctamente. Todos los datos han sido eliminados excepto los usuarios.",
            "stats": deleted_stats,
            "executed_by": user.get("email"),
            "executed_at": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"Error during system reset: {e}")
        raise HTTPException(status_code=500, detail=f"Error al reiniciar la aplicación: {str(e)}")
