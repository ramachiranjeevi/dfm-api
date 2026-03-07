"""
Authentication router
Endpoints: login (OTP + PIN), OTP generation, set PIN
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, generate_otp
from app.database import get_db
from app.models.user import Login, Users, VerifyOTP
from app.schemas.auth import (
    LoginCheckDetail,
    LoginCheckPin,
    LoginRequest,
    LoginResponse,
    OTPRequest,
    SetPinRequest,
)
from app.services.sms import send_sms

router = APIRouter(prefix="/api/login", tags=["Authentication"])


# ── POST /api/login/check ─────────────────────────────────────────────────────
@router.post("/check", response_model=LoginResponse, summary="Login with mobile + OTP/PIN")
async def login_check(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Step 1 of login flow.
    - If user has no PIN → returns OTP flag so app can prompt OTP verification.
    - If user has a PIN  → validates PIN and returns JWT token.
    """
    result = await db.execute(
        select(Login, Users)
        .join(Users, Login.UCode == Users.UCode)
        .where(Users.MobileNo == body.MobileNo, Users.IsDeleted == False)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    login_rec, user_rec = row

    # No PIN set yet — tell the mobile app to verify OTP
    if not login_rec.Pin:
        detail = LoginCheckDetail(
            userId=user_rec.UCode,
            RoleCode=user_rec.RoleCode,
            userName=user_rec.UserName,
            otp=login_rec.OTP,
            isOtpVerified=False,
        )
        return LoginResponse(status="success", value=[detail])

    # PIN is set but not provided — tell app to prompt for PIN
    if not body.Pin:
        detail = LoginCheckDetail(
            userId=user_rec.UCode,
            RoleCode=user_rec.RoleCode,
            userName=user_rec.UserName,
            otp=login_rec.OTP,
            isOtpVerified=True,
        )
        return LoginResponse(status="success", value=[detail])

    # PIN provided — validate it
    if body.Pin != login_rec.Pin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")

    token = create_access_token({"sub": user_rec.UCode, "role": user_rec.RoleCode})
    detail = LoginCheckPin(
        userId=user_rec.UCode,
        RoleCode=user_rec.RoleCode,
        userName=user_rec.UserName,
        pin=login_rec.Pin,
        isOtpVerified=True,
    )
    return LoginResponse(status="success", value=[detail], access_token=token)


# ── POST /api/login/otp ───────────────────────────────────────────────────────
@router.post("/otp", summary="Generate and send OTP via SMS")
async def generate_and_send_otp(body: OTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Generates a 4-digit OTP, persists it in VerifyOTP, and dispatches an SMS.
    """
    # Check mobile exists
    result = await db.execute(
        select(Users).where(Users.MobileNo == body.MobileNo, Users.IsDeleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Mobile number not registered")

    otp = generate_otp()
    verify = VerifyOTP(
        MobileNo=body.MobileNo,
        OTP=otp,
        CreatedBy="Admin",
        CreatedOn=datetime.now(timezone.utc),
        IsDeleted=False,
        IsActive=True,
    )
    db.add(verify)

    # Also update OTP in Login table
    await db.execute(
        update(Login).where(Login.UCode == user.UCode).values(OTP=otp)
    )
    await db.commit()

    message = f"Your DFM OTP is {otp}. Do not share it with anyone."
    await send_sms(body.MobileNo, message)

    return {"status": "success", "message": "OTP sent successfully"}


# ── POST /api/login/verify-otp ────────────────────────────────────────────────
@router.post("/verify-otp", summary="Verify OTP and get JWT token")
async def verify_otp(body: OTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Verifies OTP. On success, returns a JWT access token.
    """
    if not body.OTP:
        raise HTTPException(status_code=400, detail="OTP is required")

    result = await db.execute(
        select(Login, Users)
        .join(Users, Login.UCode == Users.UCode)
        .where(Users.MobileNo == body.MobileNo, Login.OTP == body.OTP)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    login_rec, user_rec = row
    token = create_access_token({"sub": user_rec.UCode, "role": user_rec.RoleCode})
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "userId": user_rec.UCode,
        "RoleCode": user_rec.RoleCode,
        "userName": user_rec.UserName,
    }


# ── POST /api/login/set-pin ───────────────────────────────────────────────────
@router.post("/set-pin", summary="Set or update login PIN")
async def set_pin(body: SetPinRequest, db: AsyncSession = Depends(get_db)):
    """
    Sets or updates the PIN for a user identified by mobile number.
    """
    result = await db.execute(
        select(Users).where(Users.MobileNo == body.MobileNo, Users.IsDeleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(
        update(Login).where(Login.UCode == user.UCode).values(Pin=body.Pin)
    )
    await db.commit()
    return {"status": "success", "message": "PIN updated"}
