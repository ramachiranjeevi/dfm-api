from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VehicleDetails(Base):
    __tablename__ = "VehicleDetails"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    OwnerID: Mapped[str | None] = mapped_column(String(50))
    VehicleNumber: Mapped[str | None] = mapped_column(String(50))
    VehiclePhoto: Mapped[str | None] = mapped_column(Text)
    VehicleModel: Mapped[str | None] = mapped_column(String(100))
    VehicleTankCapacity: Mapped[str | None] = mapped_column(String(50))
    VehicleChassis: Mapped[str | None] = mapped_column(String(100))
    VehicleRC: Mapped[str | None] = mapped_column(Text)
    VehicleInsuranceNo: Mapped[str | None] = mapped_column(String(100))
    VehicleInsuranceProvider: Mapped[str | None] = mapped_column(String(100))
    VehicleInsuranceStartDate: Mapped[str | None] = mapped_column(String(50))
    VehicleInsuranceExpireDate: Mapped[str | None] = mapped_column(String(50))
    VehicleServiceNo: Mapped[str | None] = mapped_column(String(100))
    YearOfManufacture: Mapped[str | None] = mapped_column(String(10))
    Image: Mapped[str | None] = mapped_column(Text)
    SpeedLimit: Mapped[str | None] = mapped_column(String(20))
    Lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    Long: Mapped[float | None] = mapped_column(Numeric(10, 7))
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
    IsActive: Mapped[bool | None] = mapped_column(Boolean, default=True)
