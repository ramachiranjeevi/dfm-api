from datetime import datetime

from pydantic import BaseModel


# ── Request schemas ────────────────────────────────────────────────────────────

class OwnerRef(BaseModel):
    OwnerID: str


class CreateOrderRequest(BaseModel):
    OrderID: str
    UserId: str
    EquipmentId: int
    SubEquipmentId: int
    OrderCreatedOn: str | None = None
    OrderRequiredOn: str | None = None
    OrderRequiredLocation: str | None = None
    Latitude: float | None = None
    Longitude: float | None = None
    Quantity: int | None = 1
    RequiredTime: str | None = None
    EstimatedAmount: float | None = None
    AmountPaid: float | None = None
    MinimumAmountToPay: float | None = None
    PaymentMode: str | None = None
    TransactionID: str | None = None
    ContactNumber: str | None = None
    ContactNanme: str | None = None
    ApprovedBy: str | None = None
    Comments: str | None = None
    CreatedBy: str | None = "Admin"
    OwnerIds: list[OwnerRef] = []


class ChangeOrderStatusRequest(BaseModel):
    OrderID: str
    StatusID: int          # 0=Created 1=Accepted 2=Cancelled 3=Completed
    OwnerId: str
    UserId: str
    ApprovedBy: str | None = None
    CreatedBy: str | None = "Admin"


class DeleteOrderRequest(BaseModel):
    OrderID: str
    UserId: str


class GetOrdersRequest(BaseModel):
    OrderID: str | None = None
    UserID: str


class OrderProcessingRequest(BaseModel):
    OrderID: str


# ── Response schemas ───────────────────────────────────────────────────────────

class OrderDetail(BaseModel):
    OrderID: str | None = None
    OwnerId: str | None = None
    UserId: str | None = None
    EquipmentId: int | None = None
    SubEquipmentId: int | None = None
    OrderRequiredOn: str | None = None
    OrderRequiredLocation: str | None = None
    EstimatedAmount: float | None = None
    AmountPaid: float | None = None
    MinimumAmountToPay: float | None = None
    StatusID: int | None = None
    MobileNo: str | None = None
    Lat: float | None = None
    Long: float | None = None
    ImageURL: str | None = None
    EquipmentName: str | None = None


class OrdersResponse(BaseModel):
    status: str
    value: list[OrderDetail] = []


class OrderProcessingDetail(BaseModel):
    processingDate: datetime | None = None
    completedDate: datetime | None = None


class OrderStartStatus(BaseModel):
    IsOrderStarted: bool = False
    IsOrderEnded: bool = False
