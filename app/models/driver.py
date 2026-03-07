from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DriverDetails(Base):
    __tablename__ = "DriverDetails"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    DriverID: Mapped[str | None] = mapped_column(String(50))
    LicenseNo: Mapped[str | None] = mapped_column(String(50))
    LicenseExpiry: Mapped[str | None] = mapped_column(String(50))
    LicenseType: Mapped[str | None] = mapped_column(String(50))
    ExperienceYears: Mapped[str | None] = mapped_column(String(10))
    BloodGroup: Mapped[str | None] = mapped_column(String(10))
    EmergencyContactNumber: Mapped[str | None] = mapped_column(String(20))
    EmergencyContactName: Mapped[str | None] = mapped_column(String(100))
    AddhaarNumber: Mapped[str | None] = mapped_column(String(20))
    PassportNumber: Mapped[str | None] = mapped_column(String(20))
    Lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    Long: Mapped[float | None] = mapped_column(Numeric(10, 7))
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    IsActive: Mapped[bool | None] = mapped_column(Boolean, default=True)
