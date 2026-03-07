"""
Orders router
Endpoints: create, status change, delete, list pending/completed, start/end processing
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.equipment import AgricultureEquipment
from app.models.order import Orders, OrderStatus
from app.models.user import Users
from app.schemas.order import (
    ChangeOrderStatusRequest,
    CreateOrderRequest,
    DeleteOrderRequest,
    GetOrdersRequest,
    OrderDetail,
    OrderProcessingDetail,
    OrderProcessingRequest,
    OrderStartStatus,
    OrdersResponse,
)
from app.services.fcm import send_notification_by_mobile

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# Status constants
STATUS_CREATED = 0
STATUS_ACCEPTED = 1
STATUS_CANCELLED = 2
STATUS_COMPLETED = 3


# ── POST /api/orders/create ───────────────────────────────────────────────────
@router.post("/create", summary="Create a new order (fan-out to multiple owners)")
async def create_order(body: CreateOrderRequest, db: AsyncSession = Depends(get_db)):
    """
    Creates an order row + an OrderStatus row for each owner in OwnerIds.
    Sends a push notification to each owner.
    """
    now = datetime.now(timezone.utc)

    for owner in body.OwnerIds:
        order = Orders(
            OrderID=body.OrderID,
            UserId=body.UserId,
            OwnerId=owner.OwnerID,
            EquipmentId=body.EquipmentId,
            SubEquipmentId=body.SubEquipmentId,
            OrderCreatedOn=now,
            OrderRequiredOn=body.OrderRequiredOn,
            OrderRequiredLocation=body.OrderRequiredLocation,
            Lat=body.Latitude,
            Long=body.Longitude,
            Quantity=body.Quantity,
            RequiredTime=body.RequiredTime,
            EstimatedAmount=body.EstimatedAmount,
            AmountPaid=body.AmountPaid,
            MinimumAmountToPay=body.MinimumAmountToPay,
            PaymentMode=body.PaymentMode,
            TransactionID=body.TransactionID,
            ContactNumber=body.ContactNumber,
            ContactNanme=body.ContactNanme,
            ApprovedBy=body.ApprovedBy,
            Comments=body.Comments,
            CreatedBy=body.CreatedBy or "Admin",
            CreatedOn=now,
            IsDeleted=False,
        )
        db.add(order)

        order_status = OrderStatus(
            OrderID=body.OrderID,
            UserId=body.UserId,
            OwnerId=owner.OwnerID,
            StatusID=STATUS_CREATED,
            CreatedBy=body.CreatedBy or "Admin",
            CreatedOn=now,
            IsDeleted=False,
        )
        db.add(order_status)

    await db.commit()

    # Notify each owner asynchronously (fire & forget style)
    for owner in body.OwnerIds:
        result = await db.execute(
            select(Users.MobileNo).where(Users.UCode == owner.OwnerID)
        )
        mobile = result.scalar_one_or_none()
        if mobile:
            await send_notification_by_mobile(
                mobile, f"New order {body.OrderID} received!", db
            )

    return {"status": "success", "message": f"Order {body.OrderID} created for {len(body.OwnerIds)} owner(s)"}


# ── POST /api/orders/status ───────────────────────────────────────────────────
@router.post("/status", summary="Accept / Cancel / Complete an order")
async def change_order_status(body: ChangeOrderStatusRequest, db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(OrderStatus)
        .where(
            OrderStatus.OrderID == body.OrderID,
            OrderStatus.UserId == body.UserId,
        )
        .values(StatusID=body.StatusID, OwnerId=body.OwnerId, ApprovedBy=body.ApprovedBy)
    )
    await db.commit()
    return {"status": "success", "message": "Order status updated"}


# ── POST /api/orders/delete ───────────────────────────────────────────────────
@router.post("/delete", summary="Delete an order")
async def delete_order(body: DeleteOrderRequest, db: AsyncSession = Depends(get_db)):
    # Find the owner for this order
    result = await db.execute(
        select(OrderStatus.OwnerId).where(
            OrderStatus.OrderID == body.OrderID,
            OrderStatus.UserId == body.UserId,
        )
    )
    owner_id = result.scalar_one_or_none()
    if not owner_id:
        raise HTTPException(status_code=404, detail="Order not found")

    await db.execute(
        update(Orders)
        .where(Orders.OrderID == body.OrderID, Orders.OwnerId == owner_id)
        .values(IsDeleted=True)
    )
    await db.execute(
        update(OrderStatus)
        .where(OrderStatus.OrderID == body.OrderID, OrderStatus.UserId == body.UserId)
        .values(IsDeleted=True)
    )
    await db.commit()
    return {"status": "success", "message": "Order deleted"}


# ── POST /api/orders/pending ──────────────────────────────────────────────────
@router.post("/pending", response_model=OrdersResponse, summary="Get pending/active orders for a user")
async def get_orders(body: GetOrdersRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Orders.OrderID,
            Orders.OwnerId,
            Orders.UserId,
            Orders.EquipmentId,
            Orders.SubEquipmentId,
            Orders.OrderRequiredOn,
            Orders.OrderRequiredLocation,
            Orders.EstimatedAmount,
            Orders.AmountPaid,
            Orders.MinimumAmountToPay,
            Orders.Lat,
            Orders.Long,
            OrderStatus.StatusID,
            Users.MobileNo,
            AgricultureEquipment.Image.label("ImageURL"),
            AgricultureEquipment.Equipment.label("EquipmentName"),
        )
        .join(OrderStatus, Orders.OrderID == OrderStatus.OrderID)
        .join(Users, Orders.UserId == Users.UCode)
        .outerjoin(
            AgricultureEquipment,
            (AgricultureEquipment.EquipmentID == Orders.EquipmentId)
            & (AgricultureEquipment.SubEquipmentID == Orders.SubEquipmentId),
        )
        .where(
            Orders.UserId == body.UserID,
            Orders.IsDeleted == False,
            OrderStatus.StatusID.in_([STATUS_CREATED, STATUS_ACCEPTED]),
        )
    )
    rows = result.all()
    details = [
        OrderDetail(
            OrderID=r.OrderID,
            OwnerId=r.OwnerId,
            UserId=r.UserId,
            EquipmentId=r.EquipmentId,
            SubEquipmentId=r.SubEquipmentId,
            OrderRequiredOn=r.OrderRequiredOn,
            OrderRequiredLocation=r.OrderRequiredLocation,
            EstimatedAmount=float(r.EstimatedAmount) if r.EstimatedAmount else None,
            AmountPaid=float(r.AmountPaid) if r.AmountPaid else None,
            MinimumAmountToPay=float(r.MinimumAmountToPay) if r.MinimumAmountToPay else None,
            StatusID=r.StatusID,
            MobileNo=r.MobileNo,
            Lat=float(r.Lat) if r.Lat else None,
            Long=float(r.Long) if r.Long else None,
            ImageURL=r.ImageURL,
            EquipmentName=r.EquipmentName,
        )
        for r in rows
    ]
    return OrdersResponse(status="success", value=details)


# ── POST /api/orders/completed ────────────────────────────────────────────────
@router.post("/completed", response_model=OrdersResponse, summary="Get completed orders for a user")
async def get_completed_orders(body: GetOrdersRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Orders.OrderID,
            Orders.OwnerId,
            Orders.UserId,
            Orders.EquipmentId,
            Orders.SubEquipmentId,
            Orders.OrderRequiredOn,
            Orders.OrderRequiredLocation,
            Orders.EstimatedAmount,
            Orders.AmountPaid,
            Orders.MinimumAmountToPay,
            Orders.Lat,
            Orders.Long,
            OrderStatus.StatusID,
            Users.MobileNo,
            AgricultureEquipment.Image.label("ImageURL"),
            AgricultureEquipment.Equipment.label("EquipmentName"),
        )
        .join(OrderStatus, Orders.OrderID == OrderStatus.OrderID)
        .join(Users, Orders.UserId == Users.UCode)
        .outerjoin(
            AgricultureEquipment,
            (AgricultureEquipment.EquipmentID == Orders.EquipmentId)
            & (AgricultureEquipment.SubEquipmentID == Orders.SubEquipmentId),
        )
        .where(
            Orders.UserId == body.UserID,
            Orders.IsDeleted == False,
            OrderStatus.StatusID == STATUS_COMPLETED,
        )
    )
    rows = result.all()
    details = [
        OrderDetail(
            OrderID=r.OrderID,
            OwnerId=r.OwnerId,
            UserId=r.UserId,
            EquipmentId=r.EquipmentId,
            SubEquipmentId=r.SubEquipmentId,
            OrderRequiredOn=r.OrderRequiredOn,
            OrderRequiredLocation=r.OrderRequiredLocation,
            EstimatedAmount=float(r.EstimatedAmount) if r.EstimatedAmount else None,
            StatusID=r.StatusID,
            MobileNo=r.MobileNo,
            Lat=float(r.Lat) if r.Lat else None,
            Long=float(r.Long) if r.Long else None,
            ImageURL=r.ImageURL,
            EquipmentName=r.EquipmentName,
        )
        for r in rows
    ]
    return OrdersResponse(status="success", value=details)


# ── POST /api/orders/start ────────────────────────────────────────────────────
@router.post("/start", summary="Mark order processing as started")
async def order_started(body: OrderProcessingRequest, db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Orders)
        .where(Orders.OrderID == body.OrderID)
        .values(ProcessingDate=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"status": "success", "message": "Order processing started"}


# ── POST /api/orders/end ──────────────────────────────────────────────────────
@router.post("/end", summary="Mark order processing as ended (completed)")
async def order_ended(body: OrderProcessingRequest, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Orders)
        .where(Orders.OrderID == body.OrderID)
        .values(CompletedDate=now)
    )
    await db.execute(
        update(OrderStatus)
        .where(OrderStatus.OrderID == body.OrderID)
        .values(StatusID=STATUS_COMPLETED)
    )
    await db.commit()
    return {"status": "success", "message": "Order completed"}


# ── POST /api/orders/processing-status ────────────────────────────────────────
@router.post("/processing-status", response_model=OrderStartStatus, summary="Check if order has started/ended")
async def is_order_started(body: OrderProcessingRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Orders.ProcessingDate, Orders.CompletedDate).where(Orders.OrderID == body.OrderID)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderStartStatus(
        IsOrderStarted=row.ProcessingDate is not None,
        IsOrderEnded=row.CompletedDate is not None,
    )
