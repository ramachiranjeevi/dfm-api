"""
Customers router
Endpoint: create customer (Login + Users + CustomerDetails in one transaction)
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_otp, generate_user_code
from app.database import get_db
from app.models.customer import CustomerDetails
from app.models.user import Login, Users
from app.schemas.customer import CreateCustomerRequest, CustomerResponse

router = APIRouter(prefix="/api/customers", tags=["Customers"])


# ── POST /api/customers/create ────────────────────────────────────────────────
@router.post("/create", response_model=CustomerResponse, summary="Register a new customer")
async def create_customer(body: CreateCustomerRequest, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    if body.MobileNo:
        count = (await db.execute(
            select(func.count()).select_from(Users).where(
                Users.MobileNo == body.MobileNo, Users.IsDeleted == False
            )
        )).scalar_one()
        if count > 0:
            raise HTTPException(status_code=409, detail="Mobile number already registered")

    ucode = body.UCode or generate_user_code()
    customer_id = body.CustomerID or generate_user_code()
    otp = generate_otp()
    now = datetime.now(timezone.utc)
    role = body.RoleCode or 3  # 3 = Customer

    # Login
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

    # Users
    db.add(Users(
        RoleCode=role,
        UCode=ucode,
        UserName=body.UserName,
        Firstname=body.Firstname,
        Lastname=body.Lastname,
        DateOfBirth=body.DateOfBirth,
        Language=body.Language,
        Gender=body.Gender,
        MaritialStatus=body.MaritialStatus,
        Address=body.Address,
        Address2=body.Address2,
        Area=body.Area,
        City=body.City,
        State=body.State,
        Country=body.Country,
        PinCode=body.PinCode,
        MobileNo=body.MobileNo,
        Email=body.Email,
        Lat=body.Lat,
        Long=body.Long,
        CreatedBy=body.CreatedBy,
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    ))

    # CustomerDetails
    db.add(CustomerDetails(
        CustomerID=customer_id,
        MotherName=body.MotherName,
        FatherName=body.FatherName,
        BloodGroup=body.BloodGroup,
        EmergencyContactNumber=body.EmergencyContactNumber,
        EmergencyContactName=body.EmergencyContactName,
        AddhaarNumber=body.AddhaarNumber,
        PassportNumber=body.PassportNumber,
        EmailNumber=body.EmailNumber,
        Description=body.Description,
        DateOfJoining=body.DateOfJoining,
        DateOfRelieving=body.DateOfRelieving,
        MartialStatus=body.MartialStatus,
        Year=body.Year,
        Month=body.Month,
        SerialNo=body.SerialNo,
        IsRegistered=body.IsRegistered,
        Lat=body.Lat,
        Long=body.Long,
        CreatedBy=body.CreatedBy,
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    ))

    await db.commit()
    return CustomerResponse(status="success", message="Customer registered successfully")
