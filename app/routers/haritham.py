"""
HARITHAM — Public Marketplace API
Endpoints for self-registration, nearby equipment discovery,
booking lifecycle, and live GPS tracking via WebSocket.
"""
import json
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, generate_otp
from app.database import get_db
from app.models.equipment import AgricultureEquipment, EquipmentDetails
from app.models.order import Orders, OrderStatus
from app.models.user import DeviceDetails, Login, Users, VerifyOTP
from app.services.sms import send_sms
from app.services.webpush import send_push_to_user

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

# ── Default service radius (km) by equipment type ─────────────────────────────
TYPE_DEFAULT_RADIUS_KM: dict[str, float] = {
    "drone":       40.0,
    "harvester":   20.0,
    "sprayer":     15.0,
    "tractor":     10.0,
    "plough":       8.0,
    "water pump":   5.0,
}

def _default_radius(equipment_name: str) -> float:
    return TYPE_DEFAULT_RADIUS_KM.get((equipment_name or "").lower(), 10.0)


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
    flow: str = "login"   # "login" | "register"

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
    priceUnit: str = "acre"          # acre | day | hour
    serviceRadius: float = 10.0      # km — how far owner is willing to travel

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

class UpdateEquipmentRequest(BaseModel):
    price: float | None = None
    priceUnit: str | None = None
    serviceRadius: float | None = None
    regNo: str | None = None

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    village: str | None = None

class UpdateRoleRequest(BaseModel):
    role: str   # "owner" | "both"

class UpdateUserLocationRequest(BaseModel):
    lat: float
    lng: float

class PushSubscribeRequest(BaseModel):
    mobile: str
    subscription: dict   # browser PushSubscription.toJSON()


# ── Notification helper ────────────────────────────────────────────────────────

async def _notify(mobile: str, title: str, body: str, db: AsyncSession) -> None:
    """Fire SMS + Web Push to a user. Both are best-effort — failures are logged only."""
    sms_msg = f"{title}: {body}"
    try:
        await send_sms(mobile, sms_msg)
    except Exception as exc:
        logger.warning("SMS notify failed for %s: %s", mobile, exc)
    try:
        await send_push_to_user(mobile, title, body, db)
    except Exception as exc:
        logger.warning("Push notify failed for %s: %s", mobile, exc)


# ── OTP / Auth ────────────────────────────────────────────────────────────────

@router.post("/send-otp", summary="Send OTP (works for both new & existing users)")
async def send_otp(body: SendOtpRequest, db: AsyncSession = Depends(get_db)):

    # For login flow — reject unregistered numbers immediately
    if body.flow == "login":
        user_check = await db.execute(
            select(Users).where(
                Users.MobileNo == body.mobile,
                Users.IsDeleted == False,
                Users.CreatedBy == "haritham",
            )
        )
        if not user_check.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail="This number is not registered. Please register first."
            )

    otp = generate_otp()

    # Save to VerifyOTP (always)
    entry = VerifyOTP(
        MobileNo=body.mobile,
        OTP=otp,
        CreatedBy="haritham",
        CreatedOn=datetime.utcnow(),
        IsDeleted=False,
        IsActive=True,
    )
    db.add(entry)
    await db.commit()

    sms_result = await send_sms(body.mobile, f"Your Haritham OTP is {otp}. Valid for 10 minutes.")
    logger.info("SMS result for %s: %s", body.mobile, sms_result)
    sms_ok = sms_result.get("status") == "success"

    # TODO: set otp=None once TRAI/DLT SMS registration is approved and live
    return {
        "status": "success",
        "message": "OTP sent" if sms_ok else "OTP generated (SMS registration pending)",
        "otp": None if sms_ok else otp,
    }


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
    now = datetime.utcnow()

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


@router.patch("/users/{user_id}/role", summary="Upgrade user role (e.g. farmer → both)")
async def update_user_role(user_id: str, body: UpdateRoleRequest, db: AsyncSession = Depends(get_db)):
    role_map = {"farmer": ROLE_FARMER, "owner": ROLE_OWNER, "both": ROLE_BOTH}
    role_code = role_map.get(body.role)
    if not role_code:
        raise HTTPException(status_code=400, detail="Invalid role. Use 'farmer', 'owner', or 'both'.")

    result = await db.execute(
        select(Users).where(Users.UCode == user_id, Users.IsDeleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await db.execute(
        update(Users).where(Users.UCode == user_id).values(RoleCode=role_code)
    )
    await db.execute(
        update(Login).where(Login.UCode == user_id, Login.IsDeleted == False).values(RoleCode=role_code)
    )
    await db.commit()
    return {"status": "success", "userId": user_id, "role": body.role}


@router.patch("/users/{user_id}/location", summary="Update user GPS location (used to place equipment on map)")
async def update_user_location(user_id: str, body: UpdateUserLocationRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Users).where(Users.UCode == user_id, Users.IsDeleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await db.execute(
        update(Users).where(Users.UCode == user_id).values(Lat=body.lat, Long=body.lng)
    )
    await db.commit()
    logger.info("Location updated for user %s → %.5f, %.5f", user_id, body.lat, body.lng)
    return {"status": "success", "lat": body.lat, "lng": body.lng}


@router.patch("/users/{user_id}/profile", summary="Update user name and/or village")
async def update_user_profile(user_id: str, body: UpdateProfileRequest, db: AsyncSession = Depends(get_db)):
    updates: dict[str, Any] = {}
    if body.name is not None:
        updates["UserName"] = body.name
    if body.village is not None:
        updates["City"] = body.village
    if not updates:
        return {"status": "success"}
    await db.execute(update(Users).where(Users.UCode == user_id, Users.IsDeleted == False).values(**updates))
    if body.name is not None:
        await db.execute(update(Login).where(Login.UCode == user_id, Login.IsDeleted == False).values(UserName=body.name))
    await db.commit()
    return {"status": "success"}


@router.post("/push/subscribe", summary="Save browser Web Push subscription for a user")
async def push_subscribe(body: PushSubscribeRequest, db: AsyncSession = Depends(get_db)):
    import json as _json
    from datetime import datetime as _dt

    now = _dt.utcnow()
    sub_json = _json.dumps(body.subscription)

    # Check if subscription already stored for this mobile
    result = await db.execute(
        select(DeviceDetails)
        .where(DeviceDetails.MobileNo == body.mobile, DeviceDetails.DeviceType == "webpush",
               DeviceDetails.IsDeleted == False)
        .limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.RegistrationToken = sub_json
        existing.Modifiedon = now
    else:
        db.add(DeviceDetails(
            MobileNo=body.mobile,
            RegistrationToken=sub_json,
            DeviceType="webpush",
            CreatedBy="haritham",
            CreatedOn=now,
            IsDeleted=False,
            IsActive=True,
        ))
    await db.commit()
    return {"status": "success", "message": "Push subscription saved"}


@router.get("/push/vapid-public-key", summary="Return VAPID public key for browser subscription")
async def vapid_public_key():
    from app.config import settings as _s
    return {"publicKey": _s.VAPID_PUBLIC_KEY}


# ── Equipment helpers ─────────────────────────────────────────────────────────

_price_cols_migrated = False

async def _ensure_price_columns(db: AsyncSession) -> None:
    """Idempotent: add Price / PriceUnit to EquipmentDetails if they don't exist yet."""
    global _price_cols_migrated
    if _price_cols_migrated:
        return
    try:
        await db.execute(text("""
            ALTER TABLE "EquipmentDetails"
            ADD COLUMN IF NOT EXISTS "Price"            NUMERIC(10,2),
            ADD COLUMN IF NOT EXISTS "PriceUnit"        VARCHAR(20) DEFAULT 'acre',
            ADD COLUMN IF NOT EXISTS "ServiceRadiusKm"  NUMERIC(6,1) DEFAULT 10.0
        """))
        await db.commit()
        _price_cols_migrated = True
        logger.info("EquipmentDetails price/radius columns ensured.")
    except Exception as exc:
        logger.warning("Price column migration skipped: %s", exc)
        await db.rollback()


# ── Equipment ─────────────────────────────────────────────────────────────────

_drone_seeded = False

async def _ensure_drone_catalog(db: AsyncSession):
    """Seed Drone into AgricultureEquipment catalog if not already present."""
    global _drone_seeded
    if _drone_seeded:
        return
    try:
        exists = await db.execute(
            select(AgricultureEquipment)
            .where(AgricultureEquipment.IsDeleted == False)
            .where(AgricultureEquipment.Equipment.ilike("drone"))
        )
        if exists.scalars().first():
            _drone_seeded = True
            return

        # Find max EquipmentID to assign next id
        max_eid_res = await db.execute(
            select(AgricultureEquipment.EquipmentID)
            .where(AgricultureEquipment.IsDeleted == False)
            .order_by(AgricultureEquipment.EquipmentID.desc())
        )
        max_eid = max_eid_res.scalars().first() or 0
        drone_eid = max_eid + 1

        max_sid_res = await db.execute(
            select(AgricultureEquipment.SubEquipmentID)
            .where(AgricultureEquipment.IsDeleted == False)
            .order_by(AgricultureEquipment.SubEquipmentID.desc())
        )
        max_sid = max_sid_res.scalars().first() or 0

        drone_subtypes = [
            "Pesticide Spraying Drone",
            "Seed Sowing Drone",
            "Fertilizer Spraying Drone",
        ]
        now = datetime.utcnow()
        for i, sub in enumerate(drone_subtypes, start=1):
            db.add(AgricultureEquipment(
                EquipmentID=drone_eid,
                Equipment="Drone",
                SubEquipmentID=max_sid + i,
                SubEquipment=sub,
                CreatedBy="system",
                CreatedOn=now,
                IsDeleted=False,
                IsActive=True,
            ))
        await db.commit()
        _drone_seeded = True
        logger.info("Drone equipment seeded into catalog.")
    except Exception as exc:
        logger.warning("Drone catalog seed skipped: %s", exc)
        await db.rollback()


@router.get("/equipment/catalog", summary="Return all equipment types & sub-types from catalog")
async def equipment_catalog(db: AsyncSession = Depends(get_db)):
    await _ensure_price_columns(db)
    await _ensure_drone_catalog(db)
    result = await db.execute(
        select(AgricultureEquipment)
        .where(AgricultureEquipment.IsDeleted == False, AgricultureEquipment.IsActive == True)
        .order_by(AgricultureEquipment.EquipmentID, AgricultureEquipment.SubEquipmentID)
    )
    rows = result.scalars().all()

    types: dict[int, dict] = {}
    for row in rows:
        eid = row.EquipmentID
        if eid not in types:
            types[eid] = {"equipmentId": eid, "name": row.Equipment or "", "subTypes": []}
        types[eid]["subTypes"].append({
            "subEquipmentId": row.SubEquipmentID,
            "name": row.SubEquipment or "",
        })
    return {"status": "success", "catalog": list(types.values())}


@router.get("/equipment/nearby", summary="Find equipment that can serve the farmer's location")
async def nearby_equipment(lat: float, lng: float, radius: float = 50.0, available_date: str | None = None, db: AsyncSession = Depends(get_db)):
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

        # Use the equipment's own service radius; fall back to type default
        eq_radius = float(eq_detail.ServiceRadiusKm) if eq_detail.ServiceRadiusKm else \
                    _default_radius(eq_catalog.Equipment or "")

        # Farmer must be within the owner's declared service area
        # `radius` param acts as an upper-bound cap (default 50 km)
        if dist <= eq_radius and dist <= radius:
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
                "price": float(eq_detail.Price) if eq_detail.Price else None,
                "priceUnit": eq_detail.PriceUnit or "acre",
                "serviceRadius": eq_radius,
            })

    # Sort by distance
    nearby.sort(key=lambda x: x["distance"])

    # Filter out equipment already booked (accepted) on the requested date
    if available_date:
        try:
            booked_result = await db.execute(
                select(Orders.SubEquipmentId)
                .join(OrderStatus, OrderStatus.OrderID == Orders.OrderID)
                .where(
                    Orders.IsDeleted == False,
                    OrderStatus.StatusID == STATUS_ACCEPTED,
                    Orders.OrderRequiredOn == available_date,
                )
            )
            booked_ids = {row[0] for row in booked_result.all()}
            nearby = [e for e in nearby if e["id"] not in booked_ids]
        except Exception as exc:
            logger.warning("available_date filter failed: %s", exc)

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
            "price": float(eq.Price) if eq.Price else None,
            "priceUnit": eq.PriceUnit or "acre",
            "serviceRadius": float(eq.ServiceRadiusKm) if eq.ServiceRadiusKm else None,
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


@router.patch("/equipment/{equipment_id}", summary="Edit equipment price, radius, or reg no")
async def update_equipment(equipment_id: int, body: UpdateEquipmentRequest, db: AsyncSession = Depends(get_db)):
    updates: dict[str, Any] = {}
    if body.price is not None:
        updates["Price"] = body.price
    if body.priceUnit is not None:
        updates["PriceUnit"] = body.priceUnit
    if body.serviceRadius is not None:
        updates["ServiceRadiusKm"] = body.serviceRadius
    if body.regNo is not None:
        updates["VehicleRegistrationNo"] = body.regNo
    if updates:
        await db.execute(update(EquipmentDetails).where(EquipmentDetails.ID == equipment_id).values(**updates))
        await db.commit()
    return {"status": "success"}


@router.post("/equipment/add", summary="Owner adds equipment listing")
async def add_equipment(body: AddEquipmentRequest, db: AsyncSession = Depends(get_db)):
    await _ensure_price_columns(db)
    now = datetime.utcnow()
    eq = EquipmentDetails(
        OwnerID=body.ownerId,
        EquipmentID=body.equipmentId,
        SubEquipmentID=body.subEquipmentId,
        Quantity=1,
        Price=body.price,
        PriceUnit=body.priceUnit,
        ServiceRadiusKm=body.serviceRadius,
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
    # Prevent an owner from booking their own equipment
    if body.farmerId == body.ownerId:
        raise HTTPException(status_code=400, detail="You cannot book your own equipment.")

    # Prevent double-booking: same equipment + same date with an accepted order
    conflict_result = await db.execute(
        select(Orders)
        .join(OrderStatus, OrderStatus.OrderID == Orders.OrderID)
        .where(
            Orders.SubEquipmentId == body.equipmentDetailId,
            Orders.IsDeleted == False,
            OrderStatus.StatusID == STATUS_ACCEPTED,
            Orders.OrderRequiredOn == body.scheduleDate,
        )
    )
    if conflict_result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="This equipment is already booked for that date. Please choose a different date."
        )

    order_id = f"ORD{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()

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

    # ── Notify owner via SMS + Web Push ───────────────────────────────────────
    try:
        owner_result = await db.execute(
            select(Users).where(Users.UCode == body.ownerId, Users.IsDeleted == False)
        )
        owner = owner_result.scalar_one_or_none()
        farmer_result = await db.execute(
            select(Users).where(Users.UCode == body.farmerId, Users.IsDeleted == False)
        )
        farmer = farmer_result.scalar_one_or_none()
        if owner and farmer:
            date_str = body.scheduleDate[:10] if body.scheduleDate else "TBD"
            await _notify(
                mobile=owner.MobileNo,
                title="New Booking Request",
                body=f"{farmer.UserName} from {farmer.City or 'nearby'} needs your equipment on {date_str}. Open Haritham to accept.",
                db=db,
            )
    except Exception as exc:
        logger.warning("Order create notify failed: %s", exc)

    return {"status": "success", "orderId": order_id}


@router.get("/orders/farmer/{farmer_id}", summary="Get all orders for a farmer")
async def farmer_orders(farmer_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import aliased
    OwnerUser = aliased(Users)
    result = await db.execute(
        select(Orders, OrderStatus, AgricultureEquipment, OwnerUser)
        .join(OrderStatus, OrderStatus.OrderID == Orders.OrderID)
        .outerjoin(AgricultureEquipment, AgricultureEquipment.SubEquipmentID == Orders.SubEquipmentId)
        .outerjoin(OwnerUser, OwnerUser.UCode == Orders.OwnerId)
        .where(Orders.UserId == farmer_id, Orders.IsDeleted == False)
        .order_by(Orders.OrderCreatedOn.desc())
    )
    orders = []
    seen = set()
    for order, os, eq, owner in result.all():
        if order.OrderID in seen:
            continue
        seen.add(order.OrderID)
        status_map = {0: "pending", 1: "active", 2: "cancelled", 3: "completed"}
        orders.append({
            "orderId": order.OrderID,
            "ownerId": order.OwnerId,
            "ownerName": owner.UserName if owner else None,
            "ownerMobile": owner.MobileNo if owner else None,
            "scheduleDate": order.OrderRequiredOn,
            "notes": order.Comments,
            "status": status_map.get(os.StatusID, "pending"),
            "statusId": os.StatusID,
            "equipment": eq.SubEquipment if eq else None,
            "equipmentType": eq.Equipment if eq else None,
            "image": eq.Image if eq else None,
            "createdOn": order.OrderCreatedOn.isoformat() if order.OrderCreatedOn else None,
            "rating": getattr(order, "Rating", None),
        })
    return {"status": "success", "orders": orders}


@router.get("/orders/owner/{owner_id}", summary="Get all orders for an equipment owner")
async def owner_orders(owner_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Orders, OrderStatus, Users, AgricultureEquipment, EquipmentDetails)
        .join(OrderStatus, OrderStatus.OrderID == Orders.OrderID)
        .join(Users, Users.UCode == Orders.UserId)
        .outerjoin(EquipmentDetails, EquipmentDetails.ID == Orders.SubEquipmentId)
        .outerjoin(AgricultureEquipment,
            (AgricultureEquipment.EquipmentID == EquipmentDetails.EquipmentID) &
            (AgricultureEquipment.SubEquipmentID == EquipmentDetails.SubEquipmentID))
        .where(Orders.OwnerId == owner_id, Orders.IsDeleted == False)
        .order_by(Orders.OrderCreatedOn.desc())
    )
    orders = []
    seen = set()
    for order, os, farmer, eq, eq_detail in result.all():
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
            "equipment": eq.SubEquipment if eq else None,
            "equipmentType": eq.Equipment if eq else None,
            "price": float(eq_detail.Price) if eq_detail and eq_detail.Price else None,
            "priceUnit": eq_detail.PriceUnit if eq_detail else None,
            "createdOn": order.OrderCreatedOn.isoformat() if order.OrderCreatedOn else None,
        })
    return {"status": "success", "orders": orders}


@router.get("/orders/{order_id}", summary="Get single order details (for tracking page)")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import aliased
    OwnerUser = aliased(Users)
    FarmerUser = aliased(Users)
    result = await db.execute(
        select(Orders, OrderStatus, AgricultureEquipment, FarmerUser, OwnerUser)
        .join(OrderStatus, OrderStatus.OrderID == Orders.OrderID)
        .outerjoin(AgricultureEquipment, AgricultureEquipment.SubEquipmentID == Orders.SubEquipmentId)
        .outerjoin(FarmerUser, FarmerUser.UCode == Orders.UserId)
        .outerjoin(OwnerUser, OwnerUser.UCode == Orders.OwnerId)
        .where(Orders.OrderID == order_id, Orders.IsDeleted == False)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found.")
    order, os, eq, farmer, owner = row
    status_map = {0: "pending", 1: "active", 2: "cancelled", 3: "completed"}
    return {
        "orderId": order.OrderID,
        "status": status_map.get(os.StatusID, "pending"),
        "statusId": os.StatusID,
        "scheduleDate": order.OrderRequiredOn,
        "notes": order.Comments,
        "farmerLat": float(order.Lat) if order.Lat else None,
        "farmerLng": float(order.Long) if order.Long else None,
        "farmerName": farmer.UserName if farmer else None,
        "farmerMobile": farmer.MobileNo if farmer else None,
        "ownerId": order.OwnerId,
        "ownerName": owner.UserName if owner else None,
        "ownerMobile": owner.MobileNo if owner else None,
        "equipment": eq.SubEquipment if eq else None,
        "equipmentType": eq.Equipment if eq else None,
        "createdOn": order.OrderCreatedOn.isoformat() if order.OrderCreatedOn else None,
    }


@router.patch("/orders/{order_id}/status", summary="Update order status")
async def update_order_status(order_id: str, body: UpdateStatusRequest, db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
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

    # ── Notify relevant party via SMS + Web Push ───────────────────────────────
    try:
        order_res = await db.execute(
            select(Orders).where(Orders.OrderID == order_id)
        )
        order = order_res.scalar_one_or_none()
        if order:
            farmer_res = await db.execute(select(Users).where(Users.UCode == order.UserId))
            farmer = farmer_res.scalar_one_or_none()
            owner_res  = await db.execute(select(Users).where(Users.UCode == order.OwnerId))
            owner  = owner_res.scalar_one_or_none()

            if body.status == STATUS_ACCEPTED and farmer:
                await _notify(
                    mobile=farmer.MobileNo,
                    title="Booking Accepted! ✅",
                    body=f"Your equipment request was accepted by {owner.UserName if owner else 'the owner'}. They will arrive on the scheduled date.",
                    db=db,
                )
            elif body.status == STATUS_CANCELLED:
                # Who cancelled? Notify the other party
                if body.updatedBy == order.UserId and owner:   # farmer cancelled → notify owner
                    await _notify(
                        mobile=owner.MobileNo,
                        title="Booking Cancelled",
                        body=f"{farmer.UserName if farmer else 'The farmer'} cancelled their equipment request.",
                        db=db,
                    )
                elif farmer:  # owner cancelled → notify farmer
                    await _notify(
                        mobile=farmer.MobileNo,
                        title="Booking Cancelled",
                        body="The owner cancelled your equipment request. Please search for another equipment nearby.",
                        db=db,
                    )
            elif body.status == STATUS_COMPLETED and farmer:
                await _notify(
                    mobile=farmer.MobileNo,
                    title="Job Completed ✅",
                    body="Your equipment job is marked complete. Thank you for using Haritham!",
                    db=db,
                )
    except Exception as exc:
        logger.warning("Order status notify failed: %s", exc)

    return {"status": "success", "orderId": order_id, "newStatus": body.status}


# ── Admin Analytics ───────────────────────────────────────────────────────────

@router.get("/admin/analytics", summary="Admin analytics — users, orders, equipment, top villages")
async def admin_analytics(db: AsyncSession = Depends(get_db)):
    now      = datetime.utcnow()
    ago_7d   = now - timedelta(days=7)
    ago_30d  = now - timedelta(days=30)

    role_label = {ROLE_FARMER: "farmer", ROLE_OWNER: "owner", ROLE_BOTH: "both"}

    # Only count Haritham users — exclude admins and old DFM accounts
    HARITHAM_FILTER = (
        Users.IsDeleted == False,
        Users.CreatedBy == "haritham",
        Users.RoleCode != ROLE_ADMIN,   # hard-exclude admin role regardless of CreatedBy
    )

    # ── Users by role ─────────────────────────────────────────────────────────
    role_rows = (await db.execute(
        select(Users.RoleCode, func.count(Users.ID).label("n"))
        .where(*HARITHAM_FILTER)
        .group_by(Users.RoleCode)
    )).all()

    by_role = {"farmer": 0, "owner": 0, "both": 0}
    total_users = 0
    for rc, cnt in role_rows:
        key = role_label.get(rc)
        if key:   # skip any unknown/admin role codes entirely
            by_role[key] += cnt
            total_users += cnt

    # ── New registrations ─────────────────────────────────────────────────────
    new_7d  = (await db.execute(select(func.count(Users.ID)).where(*HARITHAM_FILTER, Users.CreatedOn >= ago_7d))).scalar() or 0
    new_30d = (await db.execute(select(func.count(Users.ID)).where(*HARITHAM_FILTER, Users.CreatedOn >= ago_30d))).scalar() or 0

    # ── Daily signups — last 14 days (raw rows, grouped in Python) ────────────
    daily_rows = (await db.execute(
        select(Users.CreatedOn)
        .where(*HARITHAM_FILTER, Users.CreatedOn >= now - timedelta(days=14))
        .order_by(Users.CreatedOn)
    )).scalars().all()

    daily_map: dict[str, int] = {}
    for ts in daily_rows:
        if ts:
            day = ts.strftime("%d %b")
            daily_map[day] = daily_map.get(day, 0) + 1
    daily_signups = [{"date": d, "count": c} for d, c in daily_map.items()]

    # ── Orders by status ──────────────────────────────────────────────────────
    status_rows = (await db.execute(
        select(OrderStatus.StatusID, func.count(Orders.OrderID).label("n"))
        .join(Orders, Orders.OrderID == OrderStatus.OrderID)
        .where(Orders.IsDeleted == False)
        .group_by(OrderStatus.StatusID)
    )).all()

    order_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for sid, cnt in status_rows:
        order_counts[sid] = cnt

    # ── Equipment ─────────────────────────────────────────────────────────────
    equip_active   = (await db.execute(select(func.count(EquipmentDetails.ID)).where(EquipmentDetails.IsDeleted == False, EquipmentDetails.IsActive == True))).scalar() or 0
    equip_inactive = (await db.execute(select(func.count(EquipmentDetails.ID)).where(EquipmentDetails.IsDeleted == False, EquipmentDetails.IsActive == False))).scalar() or 0

    # ── Top 5 villages ────────────────────────────────────────────────────────
    village_rows = (await db.execute(
        select(Users.City, func.count(Users.ID).label("n"))
        .where(*HARITHAM_FILTER, Users.City.isnot(None), Users.City != "")
        .group_by(Users.City)
        .order_by(func.count(Users.ID).desc())
        .limit(5)
    )).all()

    # ── Recent 10 registrations ───────────────────────────────────────────────
    recent_rows = (await db.execute(
        select(Users.UserName, Users.MobileNo, Users.RoleCode, Users.City, Users.CreatedOn)
        .where(*HARITHAM_FILTER)
        .order_by(Users.CreatedOn.desc())
        .limit(10)
    )).all()

    return {
        "status": "success",
        "generatedAt": now.isoformat(),
        "users": {
            "total":  total_users,
            "byRole": by_role,
            "new7d":  new_7d,
            "new30d": new_30d,
            "dailySignups": daily_signups,
        },
        "orders": {
            "total":     sum(order_counts.values()),
            "pending":   order_counts[STATUS_CREATED],
            "active":    order_counts[STATUS_ACCEPTED],
            "cancelled": order_counts[STATUS_CANCELLED],
            "completed": order_counts[STATUS_COMPLETED],
        },
        "equipment": {
            "active":   equip_active,
            "inactive": equip_inactive,
            "total":    equip_active + equip_inactive,
        },
        "topVillages": [{"village": v, "count": c} for v, c in village_rows],
        "recentUsers": [
            {
                "name":     name,
                "mobile":   mobile,
                "role":     role_label.get(rc, "unknown"),
                "village":  city or "—",
                "joinedOn": ts.strftime("%d %b %Y") if ts else "—",
            }
            for name, mobile, rc, city, ts in recent_rows
        ],
    }


# ── Rating ────────────────────────────────────────────────────────────────────

_rating_col_migrated = False

async def _ensure_rating_column(db: AsyncSession) -> None:
    """Idempotent: add Rating column to Orders if it doesn't exist."""
    global _rating_col_migrated
    if _rating_col_migrated:
        return
    try:
        await db.execute(text('ALTER TABLE "Orders" ADD COLUMN IF NOT EXISTS "Rating" INTEGER'))
        await db.commit()
        _rating_col_migrated = True
        logger.info("Orders.Rating column ensured.")
    except Exception as exc:
        logger.warning("Rating column migration skipped: %s", exc)
        await db.rollback()


class RateOrderRequest(BaseModel):
    rating: int   # 1–5
    ratedBy: str


@router.patch("/orders/{order_id}/rating", summary="Farmer rates a completed order (1–5 stars)")
async def rate_order(order_id: str, body: RateOrderRequest, db: AsyncSession = Depends(get_db)):
    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
    await _ensure_rating_column(db)
    await db.execute(
        update(Orders).where(Orders.OrderID == order_id).values(**{"Rating": body.rating})
    )
    await db.commit()
    return {"status": "success", "orderId": order_id, "rating": body.rating}


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
