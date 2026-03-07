"""
Drivers router
Endpoints: create driver, list drivers, check mobile
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_otp, generate_user_code
from app.database import get_db
from app.models.driver import DriverDetails
from app.models.user import Login, Users
from app.schemas.driver import CreateDriverRequest, DriverCreateResponse, DriverDetail, DriverResponse

router = APIRouter(prefix="/api/drivers", tags=["Drivers"])


# ── POST /api/drivers/create ──────────────────────────────────────────────────
@router.post("/create", response_model=DriverCreateResponse, summary="Register a new driver")
async def create_driver(body: CreateDriverRequest, db: AsyncSession = Depends(get_db)):
    if body.MobileNo:
        count = (await db.execute(
            select(func.count()).select_from(Users).where(
                Users.MobileNo == body.MobileNo, Users.IsDeleted == False
            )
        )).scalar_one()
        if count > 0:
            raise HTTPException(status_code=409, detail="Mobile number already registered")

    ucode = body.UCode or generate_user_code()
    driver_id = body.DriverID or generate_user_code()
    otp = generate_otp()
    now = datetime.now(timezone.utc)
    role = body.RoleCode or 2  # 2 = Driver

    db.add(Login(
        RoleCode=role,
        UCode=ucode,
        UserName=body.UserName,
        OTP=otp,
        CreatedBy=body.CreatedBy,
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    ))

    db.add(Users(
        RoleCode=role,
        UCode=ucode,
        UserName=body.UserName,
        Firstname=body.Firstname,
        Lastname=body.Lastname,
        MobileNo=body.MobileNo,
        Email=body.Email,
        Address=body.Address,
        Lat=body.Lat,
        Long=body.Long,
        CreatedBy=body.CreatedBy,
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    ))

    db.add(DriverDetails(
        DriverID=driver_id,
        LicenseNo=body.LicenseNo,
        LicenseExpiry=body.LicenseExpiry,
        LicenseType=body.LicenseType,
        ExperienceYears=body.ExperienceYears,
        BloodGroup=body.BloodGroup,
        EmergencyContactNumber=body.EmergencyContactNumber,
        EmergencyContactName=body.EmergencyContactName,
        AddhaarNumber=body.AddhaarNumber,
        PassportNumber=body.PassportNumber,
        Lat=body.Lat,
        Long=body.Long,
        CreatedBy=body.CreatedBy,
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    ))

    await db.commit()
    return DriverCreateResponse(status="success", message="Driver registered successfully")


# ── GET /api/drivers/list ─────────────────────────────────────────────────────
@router.get("/list", response_model=DriverResponse, summary="List all drivers")
async def get_drivers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DriverDetails).where(DriverDetails.IsDeleted == False)
    )
    drivers = result.scalars().all()
    items = [DriverDetail.model_validate(d) for d in drivers]
    return DriverResponse(status="success", value=items)


# ── GET /api/drivers/check-mobile ─────────────────────────────────────────────
@router.get("/check-mobile", summary="Check if a mobile number is registered")
async def check_mobile(mobile: str, db: AsyncSession = Depends(get_db)):
    count = (await db.execute(
        select(func.count()).select_from(Users).where(
            Users.MobileNo == mobile, Users.IsDeleted == False
        )
    )).scalar_one()
    return {"MobileExist": count > 0}
