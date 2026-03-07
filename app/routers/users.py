"""
Users router
Endpoints: create user, get user by mobile, check mobile uniqueness
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_otp, generate_user_code
from app.database import get_db
from app.models.user import DeviceDetails, Login, Users
from app.schemas.user import CreateUserRequest, CreateUserResponse, GetUserRequest, GetUserResponse, UserDetail
from app.services.sms import send_sms

router = APIRouter(prefix="/api/users", tags=["Users"])


# ── POST /api/users/create ────────────────────────────────────────────────────
@router.post("/create", response_model=CreateUserResponse, summary="Register a new user")
async def create_user(body: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    """
    Creates a new user, login record, and device details in a single transaction.
    Also sends an OTP SMS to the mobile number.
    """
    # Check uniqueness of mobile / email
    q = select(func.count()).select_from(Users).where(
        (Users.MobileNo == body.MobileNo) | (Users.Email == body.Email),
        Users.IsDeleted == False,
    )
    count = (await db.execute(q)).scalar_one()
    if count > 0:
        raise HTTPException(status_code=409, detail="Mobile or email already registered")

    ucode = body.UserCode or generate_user_code()
    otp = generate_otp()
    now = datetime.now(timezone.utc)

    # Users table
    user = Users(
        RoleCode=body.RoleCode,
        UCode=ucode,
        UserName=body.UserName,
        MobileNo=body.MobileNo,
        Email=body.Email,
        Address=body.Address,
        PinCode=body.PinCode,
        Lat=body.Latitude,
        Long=body.Longitude,
        CreatedBy=body.CreatedBy or "Admin",
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    )
    db.add(user)

    # Login table
    login = Login(
        RoleCode=body.RoleCode,
        UCode=ucode,
        UserName=body.UserName,
        OTP=otp,
        CreatedBy=body.CreatedBy or "Admin",
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    )
    db.add(login)

    # DeviceDetails table (if device info supplied)
    if body.IMEI or body.DeviceId or body.RegistrationToken:
        device = DeviceDetails(
            UCODE=ucode,
            MobileNo=body.MobileNo,
            IMEI=body.IMEI,
            DeviceId=body.DeviceId,
            DeviceType=body.DeviceType,
            DeviceName=body.DeviceName,
            RegistrationToken=body.RegistrationToken,
            CreatedBy=body.CreatedBy or "Admin",
            CreatedOn=now,
            IsDeleted=False,
            IsActive=True,
        )
        db.add(device)

    await db.commit()

    # Send OTP SMS
    message = f"Welcome to DFM! Your OTP is {otp}."
    await send_sms(body.MobileNo, message)

    return CreateUserResponse(status="success", message=f"User created. OTP sent to {body.MobileNo}")


# ── POST /api/users/get ───────────────────────────────────────────────────────
@router.post("/get", response_model=GetUserResponse, summary="Get user details by mobile number")
async def get_user(body: GetUserRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Login.OTP, Users.RoleCode, Users.UserName, Users.Address, Users.Email)
        .join(Users, Login.UCode == Users.UCode)
        .where(Users.MobileNo == body.MobileNo, Users.IsDeleted == False)
    )
    row = result.first()
    if not row:
        return GetUserResponse(status="success", value=[])

    detail = UserDetail(
        OTP=row.OTP,
        RoleCode=row.RoleCode,
        UserName=row.UserName,
        Address=row.Address,
        Email=row.Email,
    )
    return GetUserResponse(status="success", value=[detail])


# ── GET /api/users/check-mobile ───────────────────────────────────────────────
@router.get("/check-mobile", summary="Check if mobile number is already registered")
async def check_mobile(mobile: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(func.count()).select_from(Users).where(
            Users.MobileNo == mobile, Users.IsDeleted == False
        )
    )
    count = result.scalar_one()
    return {"MobileExist": count > 0}
