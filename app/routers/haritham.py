"""
HARITHAM — Public Marketplace API
Endpoints for self-registration, nearby equipment discovery,
booking lifecycle, and live GPS tracking via WebSocket.
"""
import json
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, generate_otp
from app.database import get_db
from app.models.equipment import AgricultureEquipment, EquipmentDetails
from app.models.order import Orders, OrderStatus
from app.models.user import Login, Users, VerifyOTP
from app.services.sms import send_sms

router = APIRouter(prefix="/haritham", tags=["Haritham"])

# ── Role codes ────────────────────────────────────────────────────────────────
ROLE_FARMER = 2
ROLE_OWNER  = 3
ROLE_BOTH   = 4
ROLE_ADMIN  = 1

# ── Order status codes ────────────────────────────────────────────────────────
STATUS_CREATED   = 0
STATUS_ACCEPTED  = 1
STATUS_CANCELLED = 2
STATUS_COMPLETED = 3

# ── Haversine helper ──────────────────────────────────────────────────────────
def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


# ── Schemas ───────────────────────────────────────────────────────────────────
class SendOtpRequest(BaseModel):
    mobile: str

class VerifyOtpRequest(BaseModel):
    mobile: str
    otp: str

class RegisterRequest(BaseModel):
    mobile: str
    name: str
    village: str
    role: str   # "farmer" | "owner" | "both"
    lat: float | None = None
    lng: float | None = None

class AddEquipmentRequest(BaseModel):
    ownerId: str
    equipmentId: int
    subEquipmentId: int
    price: float
    priceUnit: str = "acre"  # acre | day | hour

class CreateOrderRequest(BaseModel):
    farmerId: str
    ownerId: str
    equipmentDetailId: int
    scheduleDate: str
    notes: str | None = None
    farmerLat: float | None = None
    farmerLng: float | None = None

class UpdateStatusRequest(BaseModel):
    status: int   # 0=Created, 1=Accepted, 2=Cancelled, 3=Completed
    updatedBy: str

class UpdateLocationRequest(BaseModel):
    orderId: str
    lat: float
    lng: float


# ── OTP / Auth ────────────────────────────────────────────────────────────────

@router.post("/send-otp", summary="Send OTP (works for both new & existing users)")
async def send_otp(body: SendOtpRequest, db: AsyncSession = Depends(get_db)):
    otp = generate_otp()

    # Save to VerifyOTP (always)
    entry = VerifyOTP(
        MobileNo=body.mobile,
        OTP=otp,
        CreatedBy="haritham",
        CreatedOn=datetime.now(timezone.utc),
        IsDeleted=False,
        IsActive=True,
    )
    db.add(entry)
    await db.commit()

    await send_sms(body.mobile, f"Your Haritham OTP is {otp}. Valid for 10 minutes.")
    return {"status": "success", "message": "OTP sent"}


@router.post("/verify-otp", summary="Verify OTP — returns token if user exists, or allows registration")
async def verify_otp(body: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    # Check OTP is valid
    result = await db.execute(
        select(VerifyOTP)
        .where(VerifyOTP.MobileNo == body.mobile, VerifyOTP.OTP == body.otp, VerifyOTP.IsDeleted == False)
        .order_by(VerifyOTP.ID.desc())
        .limit(1)
    )
    otp_rec = result.scalar_one_or_none()
    if not otp_rec:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    # Mark used
    otp_rec.IsDeleted = True
    await db.commit()

    # Check if user already registered
    result2 = await db.execute(
        select(Users, Login)
        .join(Login, Login.UCode == Users.UCode)
        .where(Users.MobileNo == body.mobile, Users.IsDeleted == False)
    )
    row = result2.first()

    if row:
        user, login = row
        token = create_access_token({"sub": user.UCode, "role": user.RoleCode})
        role_map = {ROLE_FARMER: "farmer", ROLE_OWNER: "owner", ROLE_BOTH: "both", ROLE_ADMIN: "admin"}
        return {
            "status": "existing",
            "access_token": token,
            "user": {
                "id": user.UCode,
                "name": user.UserName,
                "mobile": user.MobileNo,
                "village": user.City,
                "role": role_map.get(user.RoleCode, "farmer"),
                "lat": float(user.Lat) if user.Lat else None,
                "lng": float(user.Long) if user.Long else None,
            }
        }

    return {"status": "new_user", "message": "OTP verified. Please complete registration."}


@router.post("/register", summary="Self-register as Farmer / Owner / Both")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check mobile not already registered
    existing = await db.execute(
        select(Users).where(Users.MobileNo == body.mobile, Users.IsDeleted == False)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Mobile already registered")

    role_map = {"farmer": ROLE_FARMER, "owner": ROLE_OWNER, "both": ROLE_BOTH}
    role_code = role_map.get(body.role, ROLE_FARMER)
    ucode = f"H{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    user = Users(
        RoleCode=role_code,
        UCode=ucode,
        UserName=body.name,
        Firstname=body.name.split()[0] if body.name else "",
        Lastname=body.name.split()[-1] if len(body.name.split()) > 1 else "",
        MobileNo=body.mobile,
        City=body.village,
        Lat=body.lat,
        Long=body.lng,
        CreatedBy="haritham",
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    )
    db.add(user)

    login = Login(
        RoleCode=role_code,
        UCode=ucode,
        UserName=body.name,
        CreatedBy="haritham",
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    )
    db.add(login)
    await db.commit()

    token = create_access_token({"sub": ucode, "role": role_code})
    return {
        "status": "success",
        "access_token": token,
        "user": {
            "id": ucode,
            "name": body.name,
            "mobile": body.mobile,
            "village": body.village,
            "role": body.role,
            "lat": body.lat,
            "lng": body.lng,
        }
    }


# ── Equipment ─────────────────────────────────────────────────────────────────

@router.get("/equipment/nearby", summary="Find available equipment within radius (km)")
async def nearby_equipment(lat: float, lng: float, radius: float = 5.0, db: AsyncSession = Depends(get_db)):
    """
    Uses Haversine formula to find equipment owners within `radius` km.
    Returns equipment list with distance, owner name, price.
    """
    # Get all active equipment details with owner location
    result = await db.execute(
        select(EquipmentDetails, Users, AgricultureEquipment)
        .join(Users, EquipmentDetails.OwnerID == Users.UCode)
        .join(AgricultureEquipment,
              (AgricultureEquipment.EquipmentID == EquipmentDetails.EquipmentID) &
              (AgricultureEquipment.SubEquipmentID == EquipmentDetails.SubEquipmentID))
        .where(
            EquipmentDetails.IsDeleted == False,
            EquipmentDetails.IsActive == True,
            Users.IsDeleted == False,
            Users.Lat != None,
            Users.Long != None,
        )
    )
    rows = result.all()

    nearby = []
    for eq_detail, owner, eq_catalog in rows:
        owner_lat = float(owner.Lat)
        owner_lng = float(owner.Long)
        dist = haversine_km(lat, lng, owner_lat, owner_lng)

        if dist <= radius:
            nearby.append({
                "id": eq_detail.ID,
                "equipmentId": eq_detail.EquipmentID,
                "subEquipmentId": eq_detail.SubEquipmentID,
                "type": eq_catalog.Equipment,
                "subType": eq_catalog.SubEquipment,
                "image": eq_catalog.Image,
                "ownerId": owner.UCode,
                "ownerName": owner.UserName,
                "ownerMobile": owner.MobileNo,
                "distance": round(dist, 1),
                "ownerLat": owner_lat,
                "ownerLng": owner_lng,
                "available": bool(eq_detail.IsActive),
            })

    # Sort by distance
    nearby.sort(key=lambda x: x["distance"])
    return {"status": "success", "count": len(nearby), "equipment": nearby}


@router.get("/equipment/owner/{owner_id}", summary="Get equipment listed by an owner")
async def owner_equipment(owner_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EquipmentDetails, AgricultureEquipment)
        .join(AgricultureEquipment,
              (AgricultureEquipment.EquipmentID == EquipmentDetails.EquipmentID) &
              (AgricultureEquipment.SubEquipmentID == EquipmentDetails.SubEquipmentID))
        .where(EquipmentDetails.OwnerID == owner_id, EquipmentDetails.IsDeleted == False)
    )
    rows = result.all()
    equipment = []
    for eq, catalog in rows:
        equipment.append({
            "id": eq.ID,
            "equipmentId": eq.EquipmentID,
            "subEquipmentId": eq.SubEquipmentID,
            "type": catalog.Equipment,
            "subType": catalog.SubEquipment,
            "image": catalog.Image,
            "available": bool(eq.IsActive),
            "regNo": eq.VehicleRegistrationNo,
        })
    return {"status": "success", "equipment": equipment}


@router.patch("/equipment/{equipment_id}/availability", summary="Toggle equipment availability")
async def toggle_availability(equipment_id: int, available: bool, db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(EquipmentDetails)
        .where(EquipmentDetails.ID == equipment_id)
        .values(IsActive=available)
    )
    await db.commit()
    return {"status": "success", "available": available}


@router.post("/equipment/add", summary="Owner adds equipment listing")
async def add_equipment(body: AddEquipmentRequest, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    eq = EquipmentDetails(
        OwnerID=body.ownerId,
        EquipmentID=body.equipmentId,
        SubEquipmentID=body.subEquipmentId,
        Quantity=1,
        CreatedBy=body.ownerId,
        CreatedOn=now,
        IsDeleted=False,
        IsActive=True,
    )
    db.add(eq)
    await db.commit()
    await db.refresh(eq)
    return {"status": "success", "id": eq.ID}


# ── Orders ────────────────────────────────────────────────────────────────────

@router.post("/orders/create", summary="Farmer creates a booking request")
async def create_order(body: CreateOrderRequest, db: AsyncSession = Depends(get_db)):
    order_id = f"ORD{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    order = Orders(
        OrderID=order_id,
        UserId=body.farmerId,
        OwnerId=body.ownerId,
        SubEquipmentId=body.equipmentDetailId,
        OrderCreatedOn=now,
        OrderRequiredOn=body.scheduleDate,
        Comments=body.notes,
        Lat=body.farmerLat,
        Long=body.farmerLng,
        CreatedBy=body.farmerId,
        CreatedOn=now,
        IsDeleted=False,
    )
    db.add(order)

    order_status = OrderStatus(
        OrderID=order_id,
        UserId=body.farmerId,
        OwnerId=body.ownerId,
        StatusID=STATUS_CREATED,
        CreatedBy=body.farmerId,
        CreatedOn=now,
        IsDeleted=False,
    )
    db.add(order_status)
    await db.commit()

    return {"status": "success", "orderId": order_id}


@router.get("/orders/farmer/{farmer_id}", summary="Get all orders for a farmer")
async def farmer_orders(farmer_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Orders, OrderStatus, AgricultureEquipment)
        .join(OrderStatus, OrderStatus.OrderID == Orders.OrderID)
        .outerjoin(AgricultureEquipment, AgricultureEquipment.SubEquipmentID == Orders.SubEquipmentId)
        .where(Orders.UserId == farmer_id, Orders.IsDeleted == False)
        .order_by(Orders.OrderCreatedOn.desc())
    )
    orders = []
    seen = set()
    for order, os, eq in result.all():
        if order.OrderID in seen:
            continue
        seen.add(order.OrderID)
        status_map = {0: "pending", 1: "active", 2: "cancelled", 3: "completed"}
        orders.append({
            "orderId": order.OrderID,
            "ownerId": order.OwnerId,
            "scheduleDate": order.OrderRequiredOn,
            "notes": order.Comments,
            "status": status_map.get(os.StatusID, "pending"),
            "statusId": os.StatusID,
            "equipment": eq.SubEquipment if eq else None,
            "equipmentType": eq.Equipment if eq else None,
            "image": eq.Image if eq else None,
            "createdOn": order.OrderCreatedOn.isoformat() if order.OrderCreatedOn else None,
        })
    return {"status": "success", "orders": orders}


@router.get("/orders/owner/{owner_id}", summary="Get all orders for an equipment owner")
async def owner_orders(owner_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Orders, OrderStatus, Users)
        .join(OrderStatus, OrderStatus.OrderID == Orders.OrderID)
        .join(Users, Users.UCode == Orders.UserId)
        .where(Orders.OwnerId == owner_id, Orders.IsDeleted == False)
        .order_by(Orders.OrderCreatedOn.desc())
    )
    orders = []
    seen = set()
    for order, os, farmer in result.all():
        if order.OrderID in seen:
            continue
        seen.add(order.OrderID)
        status_map = {0: "pending", 1: "active", 2: "cancelled", 3: "completed"}
        orders.append({
            "orderId": order.OrderID,
            "farmerId": order.UserId,
            "farmerName": farmer.UserName,
            "farmerMobile": farmer.MobileNo,
            "farmerVillage": farmer.City,
            "scheduleDate": order.OrderRequiredOn,
            "notes": order.Comments,
            "status": status_map.get(os.StatusID, "pending"),
            "statusId": os.StatusID,
            "farmerLat": float(order.Lat) if order.Lat else None,
            "farmerLng": float(order.Long) if order.Long else None,
            "createdOn": order.OrderCreatedOn.isoformat() if order.OrderCreatedOn else None,
        })
    return {"status": "success", "orders": orders}


@router.patch("/orders/{order_id}/status", summary="Update order status")
async def update_order_status(order_id: str, body: UpdateStatusRequest, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    await db.execute(
        update(OrderStatus)
        .where(OrderStatus.OrderID == order_id)
        .values(StatusID=body.status, ApprovedBy=body.updatedBy)
    )
    # Update timestamps on the order
    updates: dict[str, Any] = {}
    if body.status == STATUS_ACCEPTED:
        updates["ProcessingDate"] = now
        updates["ProcessingMadeBy"] = body.updatedBy
    elif body.status == STATUS_COMPLETED:
        updates["CompletedDate"] = now
        updates["CompleteMadeBy"] = body.updatedBy

    if updates:
        await db.execute(update(Orders).where(Orders.OrderID == order_id).values(**updates))

    await db.commit()
    return {"status": "success", "orderId": order_id, "newStatus": body.status}


# ── Live Tracking (WebSocket) ─────────────────────────────────────────────────
# Holds active connections per order: { order_id: [WebSocket, ...] }
tracking_rooms: dict[str, list[WebSocket]] = {}


@router.websocket("/track/{order_id}")
async def tracking_websocket(order_id: str, websocket: WebSocket):
    """
    WebSocket room per order.
    - Owner sends: {"type": "location", "lat": X, "lng": Y}
    - All connected clients (farmer) receive the same payload + distance info
    """
    await websocket.accept()
    if order_id not in tracking_rooms:
        tracking_rooms[order_id] = []
    tracking_rooms[order_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            # Broadcast to everyone else in the same room
            broadcast = json.dumps(payload)
            dead = []
            for ws in tracking_rooms[order_id]:
                if ws != websocket:
                    try:
                        await ws.send_text(broadcast)
                    except Exception:
                        dead.append(ws)

            for ws in dead:
                tracking_rooms[order_id].remove(ws)

    except WebSocketDisconnect:
        if order_id in tracking_rooms:
            tracking_rooms[order_id] = [
                ws for ws in tracking_rooms[order_id] if ws != websocket
            ]
