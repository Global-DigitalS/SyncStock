"""
Rutas de soporte al usuario — tickets de incidencias y contacto.
Permite a los usuarios crear y gestionar tickets de soporte.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import logging

from services.database import db
from services.auth import get_current_user

router = APIRouter(prefix="/support", tags=["support"])
logger = logging.getLogger(__name__)

TICKET_TYPES = ["technical", "usage", "billing", "feedback", "other"]
TICKET_PRIORITIES = ["urgent", "normal", "low"]
TICKET_STATUSES = ["received", "reviewing", "replied", "resolved", "closed"]


# ==================== PYDANTIC MODELS ====================

class TicketCreate(BaseModel):
    type: str  # technical, usage, billing, feedback, other
    subject: str
    description: str
    priority: Optional[str] = "normal"
    section: Optional[str] = None
    # Technical specific fields
    what_tried: Optional[str] = None
    what_happened: Optional[str] = None
    when_started: Optional[str] = None
    is_recurring: Optional[bool] = None


class TicketMessageCreate(BaseModel):
    content: str


class TicketRating(BaseModel):
    rating: int  # 1-5
    comment: Optional[str] = None


class TicketStatusUpdate(BaseModel):
    status: str
    internal_note: Optional[str] = None


# ==================== HELPERS ====================

async def _generate_ticket_number() -> str:
    count = await db.support_tickets.count_documents({})
    return f"SUP-{(count + 1):04d}"


def _clean_ticket(ticket: dict) -> dict:
    ticket.pop("_id", None)
    return ticket


# ==================== USER ENDPOINTS ====================

@router.post("/tickets")
async def create_ticket(
    ticket: TicketCreate,
    current_user: dict = Depends(get_current_user),
):
    if ticket.type not in TICKET_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo de ticket inválido. Valores permitidos: {TICKET_TYPES}")
    if ticket.priority and ticket.priority not in TICKET_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Prioridad inválida. Valores permitidos: {TICKET_PRIORITIES}")
    if not ticket.subject.strip() or not ticket.description.strip():
        raise HTTPException(status_code=400, detail="El asunto y la descripción son obligatorios")

    ticket_number = await _generate_ticket_number()
    now = datetime.now(timezone.utc).isoformat()

    # Get user subscription info
    plan_name = "Free"
    try:
        sub = await db.user_subscriptions.find_one({"user_id": current_user["id"], "status": "active"})
        if sub:
            plan_name = sub.get("plan_name", "Free")
    except Exception:
        pass

    ticket_doc = {
        "id": str(uuid.uuid4()),
        "ticket_number": ticket_number,
        "user_id": current_user["id"],
        "user_name": current_user.get("name", ""),
        "user_email": current_user.get("email", ""),
        "company": current_user.get("company", ""),
        "plan_name": plan_name,
        "type": ticket.type,
        "subject": ticket.subject.strip()[:200],
        "description": ticket.description.strip()[:5000],
        "priority": ticket.priority or "normal",
        "section": ticket.section,
        "what_tried": ticket.what_tried,
        "what_happened": ticket.what_happened,
        "when_started": ticket.when_started,
        "is_recurring": ticket.is_recurring,
        "status": "received",
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "author": current_user.get("name", "Usuario"),
                "author_role": "user",
                "content": ticket.description.strip(),
                "created_at": now,
            }
        ],
        "rating": None,
        "rating_comment": None,
        "created_at": now,
        "updated_at": now,
    }

    await db.support_tickets.insert_one(ticket_doc)
    logger.info(f"Ticket {ticket_number} creado por usuario {current_user['id']}")

    return _clean_ticket(ticket_doc)


@router.get("/tickets")
async def list_tickets(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    query = {"user_id": current_user["id"]}
    if status and status in TICKET_STATUSES:
        query["status"] = status

    cursor = db.support_tickets.find(query).sort("created_at", -1)
    tickets = await cursor.to_list(length=100)
    return [_clean_ticket(t) for t in tickets]


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
):
    ticket = await db.support_tickets.find_one({"id": ticket_id, "user_id": current_user["id"]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return _clean_ticket(ticket)


@router.post("/tickets/{ticket_id}/messages")
async def add_message(
    ticket_id: str,
    message: TicketMessageCreate,
    current_user: dict = Depends(get_current_user),
):
    ticket = await db.support_tickets.find_one({"id": ticket_id, "user_id": current_user["id"]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket["status"] == "closed":
        raise HTTPException(status_code=400, detail="No se puede responder a un ticket cerrado")
    if not message.content.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")

    now = datetime.now(timezone.utc).isoformat()
    new_message = {
        "id": str(uuid.uuid4()),
        "author": current_user.get("name", "Usuario"),
        "author_role": "user",
        "content": message.content.strip()[:5000],
        "created_at": now,
    }

    await db.support_tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"messages": new_message},
            "$set": {"updated_at": now, "status": "received"},
        },
    )

    updated = await db.support_tickets.find_one({"id": ticket_id})
    return _clean_ticket(updated)


@router.post("/tickets/{ticket_id}/rate")
async def rate_ticket(
    ticket_id: str,
    rating: TicketRating,
    current_user: dict = Depends(get_current_user),
):
    ticket = await db.support_tickets.find_one({"id": ticket_id, "user_id": current_user["id"]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket["status"] not in ("resolved", "closed"):
        raise HTTPException(status_code=400, detail="Solo se pueden valorar tickets resueltos o cerrados")
    if not (1 <= rating.rating <= 5):
        raise HTTPException(status_code=400, detail="La valoración debe ser entre 1 y 5")

    now = datetime.now(timezone.utc).isoformat()
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {"$set": {"rating": rating.rating, "rating_comment": rating.comment, "updated_at": now}},
    )

    updated = await db.support_tickets.find_one({"id": ticket_id})
    return _clean_ticket(updated)


@router.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
):
    ticket = await db.support_tickets.find_one({"id": ticket_id, "user_id": current_user["id"]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket["status"] not in ("resolved", "closed"):
        raise HTTPException(status_code=400, detail="Solo se pueden reabrir tickets resueltos o cerrados")

    now = datetime.now(timezone.utc).isoformat()
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {"$set": {"status": "received", "updated_at": now}},
    )

    updated = await db.support_tickets.find_one({"id": ticket_id})
    return _clean_ticket(updated)


# ==================== ADMIN ENDPOINTS ====================

def _require_admin(user: dict):
    if user.get("role") not in ("superadmin", "admin"):
        raise HTTPException(status_code=403, detail="Acceso denegado")


@router.get("/admin/tickets")
async def admin_list_tickets(
    status: Optional[str] = None,
    type: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    _require_admin(current_user)

    query = {}
    if status and status in TICKET_STATUSES:
        query["status"] = status
    if type and type in TICKET_TYPES:
        query["type"] = type
    if priority and priority in TICKET_PRIORITIES:
        query["priority"] = priority

    cursor = db.support_tickets.find(query).sort("created_at", -1)
    tickets = await cursor.to_list(length=500)
    return [_clean_ticket(t) for t in tickets]


@router.get("/admin/tickets/{ticket_id}")
async def admin_get_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
):
    _require_admin(current_user)
    ticket = await db.support_tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return _clean_ticket(ticket)


@router.put("/admin/tickets/{ticket_id}")
async def admin_update_ticket(
    ticket_id: str,
    update: TicketStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    _require_admin(current_user)

    if update.status not in TICKET_STATUSES:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Valores permitidos: {TICKET_STATUSES}")

    ticket = await db.support_tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    now = datetime.now(timezone.utc).isoformat()
    set_fields = {"status": update.status, "updated_at": now}

    await db.support_tickets.update_one({"id": ticket_id}, {"$set": set_fields})

    updated = await db.support_tickets.find_one({"id": ticket_id})
    return _clean_ticket(updated)


@router.post("/admin/tickets/{ticket_id}/messages")
async def admin_add_message(
    ticket_id: str,
    message: TicketMessageCreate,
    current_user: dict = Depends(get_current_user),
):
    _require_admin(current_user)

    ticket = await db.support_tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if not message.content.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")

    now = datetime.now(timezone.utc).isoformat()
    new_message = {
        "id": str(uuid.uuid4()),
        "author": current_user.get("name", "Soporte"),
        "author_role": "support",
        "content": message.content.strip()[:5000],
        "created_at": now,
    }

    await db.support_tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"messages": new_message},
            "$set": {"updated_at": now, "status": "replied"},
        },
    )

    updated = await db.support_tickets.find_one({"id": ticket_id})
    return _clean_ticket(updated)


@router.get("/admin/stats")
async def admin_ticket_stats(
    current_user: dict = Depends(get_current_user),
):
    _require_admin(current_user)

    total = await db.support_tickets.count_documents({})
    by_status = {}
    for status in TICKET_STATUSES:
        by_status[status] = await db.support_tickets.count_documents({"status": status})

    by_priority = {}
    for priority in TICKET_PRIORITIES:
        by_priority[priority] = await db.support_tickets.count_documents({"priority": priority})

    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
    }
