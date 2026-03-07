"""Firebase Cloud Messaging service."""
import httpx

from app.config import settings

FCM_URL = "https://fcm.googleapis.com/fcm/send"


async def send_push_notification(
    registration_token: str,
    title: str = "DFM",
    body: str = "",
    data: dict | None = None,
) -> dict:
    """
    Send a FCM push notification to a single device token.
    """
    headers = {
        "Authorization": f"key={settings.FCM_SERVER_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "to": registration_token,
        "notification": {"title": title, "body": body},
    }
    if data:
        payload["data"] = data

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(FCM_URL, json=payload, headers=headers)
            return response.json()
        except Exception as exc:
            return {"success": 0, "error": str(exc)}


async def send_notification_by_mobile(mobile_no: str, message: str, db_session) -> dict:
    """
    Look up the device registration token for a mobile number
    and send a push notification.
    """
    from sqlalchemy import select, desc
    from app.models.user import DeviceDetails

    result = await db_session.execute(
        select(DeviceDetails.RegistrationToken)
        .where(DeviceDetails.MobileNo == mobile_no, DeviceDetails.IsDeleted == False)
        .order_by(desc(DeviceDetails.ID))
        .limit(1)
    )
    token = result.scalar_one_or_none()
    if not token:
        return {"success": 0, "error": "Device token not found"}

    return await send_push_notification(token, body=message)
