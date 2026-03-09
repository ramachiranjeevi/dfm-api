from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgricultureEquipment(Base):
    __tablename__ = "AgricultureEquipment"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EquipmentID: Mapped[int | None] = mapped_column(Integer)
    Equipment: Mapped[str | None] = mapped_column(String(200))
    SubEquipmentID: Mapped[int | None] = mapped_column(Integer)
    SubEquipment: Mapped[str | None] = mapped_column(String(200))
    Image: Mapped[str | None] = mapped_column(Text)
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    IsActive: Mapped[bool | None] = mapped_column(Boolean, default=True)


class EquipmentDetails(Base):
    __tablename__ = "EquipmentDetails"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    OwnerID: Mapped[str | None] = mapped_column(String(50))
    EquipmentID: Mapped[int | None] = mapped_column(Integer)
    SubEquipmentID: Mapped[int | None] = mapped_column(Integer)
    VehicleRegistrationNo: Mapped[str | None] = mapped_column(String(50))
    Quantity: Mapped[int | None] = mapped_column(Integer)
    Price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    PriceUnit: Mapped[str | None] = mapped_column(String(20), default="acre")
    ServiceRadiusKm: Mapped[float | None] = mapped_column(Numeric(6, 1), default=10.0)
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    IsActive: Mapped[bool | None] = mapped_column(Boolean, default=True)
