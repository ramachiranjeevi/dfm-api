from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CustomerDetails(Base):
    __tablename__ = "CustomerDetails"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CustomerID: Mapped[str | None] = mapped_column(String(50))
    MotherName: Mapped[str | None] = mapped_column(String(100))
    FatherName: Mapped[str | None] = mapped_column(String(100))
    BloodGroup: Mapped[str | None] = mapped_column(String(10))
    EmergencyContactNumber: Mapped[str | None] = mapped_column(String(20))
    EmergencyContactName: Mapped[str | None] = mapped_column(String(100))
    AddhaarNumber: Mapped[str | None] = mapped_column(String(20))
    PassportNumber: Mapped[str | None] = mapped_column(String(20))
    EmailNumber: Mapped[str | None] = mapped_column(String(200))
    Description: Mapped[str | None] = mapped_column(Text)
    DateOfJoining: Mapped[str | None] = mapped_column(String(50))
    DateOfRelieving: Mapped[str | None] = mapped_column(String(50))
    MartialStatus: Mapped[str | None] = mapped_column(String(50))
    Year: Mapped[str | None] = mapped_column(String(10))
    Month: Mapped[str | None] = mapped_column(String(20))
    SerialNo: Mapped[str | None] = mapped_column(String(50))
    IsRegistered: Mapped[bool | None] = mapped_column(Boolean, default=False)
    Lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    Long: Mapped[float | None] = mapped_column(Numeric(10, 7))
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    IsActive: Mapped[bool | None] = mapped_column(Boolean, default=True)
