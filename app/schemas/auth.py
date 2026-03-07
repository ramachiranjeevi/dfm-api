from pydantic import BaseModel


# ── Request schemas ────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    MobileNo: str
    Pin: str | None = None


class OTPRequest(BaseModel):
    MobileNo: str
    OTP: str | None = None


class SetPinRequest(BaseModel):
    MobileNo: str
    Pin: str


# ── Response schemas ───────────────────────────────────────────────────────────

class LoginCheckDetail(BaseModel):
    userId: str | None = None
    RoleCode: int | None = None
    userName: str | None = None
    otp: str | None = None
    isOtpVerified: bool = False


class LoginCheckPin(BaseModel):
    userId: str | None = None
    RoleCode: int | None = None
    userName: str | None = None
    pin: str | None = None
    isOtpVerified: bool = True


class LoginResponse(BaseModel):
    status: str
    value: list[LoginCheckDetail] | list[LoginCheckPin] | list = []
    access_token: str | None = None
    token_type: str = "bearer"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
