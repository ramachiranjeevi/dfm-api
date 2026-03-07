from pydantic import BaseModel, EmailStr


# ── Request schemas ────────────────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    RoleCode: int | None = None
    UserName: str | None = None
    UserCode: str | None = None
    MobileNo: str
    Email: str | None = None
    Address: str | None = None
    PinCode: str | None = None
    Latitude: float | None = None
    Longitude: float | None = None
    CreatedBy: str | None = "Admin"
    Pin: str | None = None
    # Device info
    IMEI: str | None = None
    DeviceId: str | None = None
    DeviceType: str | None = None
    DeviceName: str | None = None
    RegistrationToken: str | None = None


class GetUserRequest(BaseModel):
    MobileNo: str


# ── Response schemas ───────────────────────────────────────────────────────────

class UserDetail(BaseModel):
    OTP: str | None = None
    RoleCode: int | None = None
    UserName: str | None = None
    Address: str | None = None
    Email: str | None = None


class GetUserResponse(BaseModel):
    status: str
    value: list[UserDetail] = []


class CreateUserResponse(BaseModel):
    status: str
    message: str | None = None
