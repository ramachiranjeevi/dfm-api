"""VAPID Web Push notification service."""
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_web_push(subscription_json: str, title: str, body: str, data: dict | None = None) -> dict:
    """
    Send a Web Push notification to a stored subscription.
    subscription_json: the raw JSON string saved from the browser's PushSubscription.toJSON()
    """
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        logger.warning("VAPID keys not configured — skipping web push")
        return {"status": "skipped", "reason": "VAPID not configured"}

    try:
        from pywebpush import webpush, WebPushException

        subscription = json.loads(subscription_json)
        payload = json.dumps({"title": title, "body": body, **(data or {})})

        webpush(
            subscription_info=subscription,
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_EMAIL},
        )
        return {"status": "success"}
    except Exception as exc:
        logger.warning("Web push failed: %s", exc)
        return {"status": "error", "error": str(exc)}


async def send_push_to_user(mobile: str, title: str, body: str, db) -> dict:
    """Look up push subscription by mobile number and send web push."""
    try:
        from sqlalchemy import select, desc
        from app.models.user import DeviceDetails

        result = await db.execute(
            select(DeviceDetails.RegistrationToken)
            .where(
                DeviceDetails.MobileNo == mobile,
                DeviceDetails.IsDeleted == False,
                DeviceDetails.DeviceType == "webpush",   # distinguish from FCM tokens
            )
            .order_by(desc(DeviceDetails.ID))
            .limit(1)
        )
        token = result.scalar_one_or_none()
        if not token:
            return {"status": "skipped", "reason": "No web push subscription found"}

        return await send_web_push(token, title, body)
    except Exception as exc:
        logger.warning("send_push_to_user failed: %s", exc)
        return {"status": "error", "error": str(exc)}
