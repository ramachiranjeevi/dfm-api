from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Orders(Base):
    __tablename__ = "Orders"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    OrderID: Mapped[str | None] = mapped_column(String(50))
    UserId: Mapped[str | None] = mapped_column(String(50))
    OwnerId: Mapped[str | None] = mapped_column(String(50))
    EquipmentId: Mapped[int | None] = mapped_column(Integer)
    SubEquipmentId: Mapped[int | None] = mapped_column(Integer)
    OrderCreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    OrderRequiredOn: Mapped[str | None] = mapped_column(String(100))
    OrderRequiredLocation: Mapped[str | None] = mapped_column(Text)
    Lat: Mapped[float | None] = mapped_column(Numeric(10, 7))
    Long: Mapped[float | None] = mapped_column(Numeric(10, 7))
    Quantity: Mapped[int | None] = mapped_column(Integer)
    RequiredTime: Mapped[str | None] = mapped_column(String(100))
    EstimatedAmount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    AmountPaid: Mapped[float | None] = mapped_column(Numeric(12, 2))
    MinimumAmountToPay: Mapped[float | None] = mapped_column(Numeric(12, 2))
    PaymentMode: Mapped[str | None] = mapped_column(String(50))
    TransactionID: Mapped[str | None] = mapped_column(String(100))
    ContactNumber: Mapped[str | None] = mapped_column(String(20))
    ContactNanme: Mapped[str | None] = mapped_column(String(100))
    ApprovedBy: Mapped[str | None] = mapped_column(String(100))
    Comments: Mapped[str | None] = mapped_column(Text)
    ProcessingDate: Mapped[datetime | None] = mapped_column(DateTime)
    CompletedDate: Mapped[datetime | None] = mapped_column(DateTime)
    ProcessingMadeBy: Mapped[str | None] = mapped_column(String(100))
    CompleteMadeBy: Mapped[str | None] = mapped_column(String(100))
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)


class OrderStatus(Base):
    __tablename__ = "OrderStatus"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    OrderID: Mapped[str | None] = mapped_column(String(50))
    UserId: Mapped[str | None] = mapped_column(String(50))
    OwnerId: Mapped[str | None] = mapped_column(String(50))
    # 0=Created, 1=Accepted, 2=Cancelled, 3=Completed
    StatusID: Mapped[int | None] = mapped_column(Integer, default=0)
    ApprovedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedBy: Mapped[str | None] = mapped_column(String(100))
    CreatedOn: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool | None] = mapped_column(Boolean, default=False)
