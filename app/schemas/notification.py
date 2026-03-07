from pydantic import BaseModel


class SendNotificationRequest(BaseModel):
    MobileNo: str
    Message: str


class RegisterPushRequest(BaseModel):
    MobileRegistrationToken: str
    DeviceId: str
    UCode: str


class NotificationResponse(BaseModel):
    status: str
    message: str | None = None
