from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Users(Base):
    __tablename__ = "Users"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RoleCode: Mapped[int | None] = mapped_column(Integer)
    UCode: Mapped[str | None] = mapped_column(String(50))
    UserName: Mapped[str | None] = mapped_column(String(200))
    Firstname: Mapped[str | None] = mapped_column(String(100))
    Lastname: Mapped[str | None] = mapped_column(String(100))
    DateOfBirth: Mapped[str | None] = mapped_column(String(50))
    Language: Mapped[str | None] = mapped_column(String(50))
    Gender: Mapped[str | None] = mapped_column(String(20))
    MaritialStatus: Mapped[str | None] = mapped_column(String(50))
    Address: Mapped[str | None] = mapped_column(Text)
    Address2: Mapped[str | None] = mapped_column(Text)
    Area: Mapped[str | None] = mapped_column(String(100))
    City: Mapped[str | None] = mapped_column(String(100))
    State: Mapped[str | None] = mapped_column(String(100))
    Country: Mapped[str | None] = mapped_column(String(100))
    PinCode: Mapped[str | None] = mapped_column(String(20))
    DoorNo: Mapped[str | None] = mapped_column(String(50))
    NearestLandMark: Mapped[str | None] = mapped_column(String(200))
    MobileNo: Mapped[str | None] = mapped_column(String(20))
    Email: Mapped[str | None] = mapped_column(String(200))
    Lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    Long: Mapped[float | None] = mapped_column(Numeric(10, 7))
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    IsActive: Mapped[bool | None] = mapped_column(Boolean, default=True)


class Login(Base):
    __tablename__ = "Login"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RoleCode: Mapped[int | None] = mapped_column(Integer)
    UCode: Mapped[str | None] = mapped_column(String(50))
    UserName: Mapped[str | None] = mapped_column(String(200))
    Pasword: Mapped[str | None] = mapped_column(String(200))
    Pin: Mapped[str | None] = mapped_column(String(10))
    OTP: Mapped[str | None] = mapped_column(String(10))
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    IsActive: Mapped[bool | None] = mapped_column(Boolean, default=True)


class DeviceDetails(Base):
    __tablename__ = "DeviceDetails"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UCODE: Mapped[str | None] = mapped_column(String(50))
    MobileNo: Mapped[str | None] = mapped_column(String(20))
    IMEI: Mapped[str | None] = mapped_column(String(100))
    DeviceId: Mapped[str | None] = mapped_column(String(200))
    DeviceType: Mapped[str | None] = mapped_column(String(50))
    DeviceName: Mapped[str | None] = mapped_column(String(100))
    RegistrationToken: Mapped[str | None] = mapped_column(Text)
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    Modifiedon: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    IsActive: Mapped[bool | None] = mapped_column(Boolean, default=True)


class VerifyOTP(Base):
    __tablename__ = "VerifyOTP"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    MobileNo: Mapped[str | None] = mapped_column(String(20))
    OTP: Mapped[str | None] = mapped_column(String(10))
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    IsActive: Mapped[bool | None] = mapped_column(Boolean, default=True)
