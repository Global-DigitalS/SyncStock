import logging
import uuid

logger = logging.getLogger(__name__)


async def send_realtime_notification(user_id: str, notification: dict):
    """Send notification via WebSocket if user is connected"""
    try:
        from websocket.manager import ws_manager
        await ws_manager.send_to_user(user_id, {
            "type": "notification",
            "data": notification
        })
    except Exception as e:
        logger.debug(f"Could not send realtime notification: {e}")


async def send_sync_progress(user_id: str, supplier_name: str, processed: int, total: int):
    """Send sync progress update via WebSocket"""
    pct = int((processed / total) * 100) if total > 0 else 0
    await send_realtime_notification(user_id, {
        "id": str(uuid.uuid4()),
        "type": "sync_progress",
        "message": f"Sincronizando '{supplier_name}': {processed:,}/{total:,} productos ({pct}%)",
        "progress": pct,
        "processed": processed,
        "total": total,
    })
