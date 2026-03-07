"""
Notifications router
Endpoints: send push notification, register device push token
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import DeviceDetails
from app.schemas.notification import NotificationResponse, RegisterPushRequest, SendNotificationRequest
from app.services.fcm import send_notification_by_mobile, send_push_notification

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# ── POST /api/notifications/send ─────────────────────────────────────────────
@router.post("/send", response_model=NotificationResponse, summary="Send push notification by mobile number")
async def send_notification(body: SendNotificationRequest, db: AsyncSession = Depends(get_db)):
    result = await send_notification_by_mobile(body.MobileNo, body.Message, db)
    if result.get("success", 0) == 0:
        return NotificationResponse(status="failed", message=result.get("error", "Unknown error"))
    return NotificationResponse(status="success", message="Notification sent")


# ── POST /api/notifications/register-device ───────────────────────────────────
@router.post("/register-device", response_model=NotificationResponse, summary="Register or update device push token")
async def register_device(body: RegisterPushRequest, db: AsyncSession = Depends(get_db)):
    """
    Updates the RegistrationToken for an existing DeviceDetails record (matched by UCode).
    If no record exists, creates one.
    """
    result = await db.execute(
        select(DeviceDetails).where(DeviceDetails.UCODE == body.UCode).limit(1)
    )
    device = result.scalar_one_or_none()

    if device:
        await db.execute(
            update(DeviceDetails)
            .where(DeviceDetails.UCODE == body.UCode)
            .values(
                DeviceId=body.DeviceId,
                RegistrationToken=body.MobileRegistrationToken,
                Modifiedon=datetime.now(timezone.utc),
            )
        )
    else:
        db.add(DeviceDetails(
            UCODE=body.UCode,
            DeviceId=body.DeviceId,
            RegistrationToken=body.MobileRegistrationToken,
            CreatedBy="Admin",
            CreatedOn=datetime.now(timezone.utc),
            IsDeleted=False,
            IsActive=True,
        ))

    await db.commit()
    return NotificationResponse(status="success", message="Device registered")
