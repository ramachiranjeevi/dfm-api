"""
Equipment router
Endpoints: agriculture equipment CRUD, owner equipment mapping, proximity search
"""
import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.equipment import AgricultureEquipment, EquipmentDetails
from app.models.user import Users
from app.schemas.equipment import (
    AgricultureEquipmentCreate,
    AllEquipmentsResponse,
    EquipmentListResponse,
    EquipmentSimple,
    GetOwnerEquipmentsRequest,
    OwnerEquipmentCreate,
    OwnerEquipmentGroup,
    OwnerEquipmentResponse,
    SearchEquipmentRequest,
    SearchEquipmentResponse,
    SearchEquipmentResult,
    SubEquipmentDetail,
    SubEquipmentGet,
)

router = APIRouter(prefix="/api/equipment", tags=["Equipment"])


# ── POST /api/equipment/agriculture/create ────────────────────────────────────
@router.post("/agriculture/create", summary="Create agriculture equipment record(s)")
async def create_agriculture_equipment(
    items: list[AgricultureEquipmentCreate],
    db: AsyncSession = Depends(get_db),
):
    created = []
    for item in items:
        # Skip duplicates
        exists = (await db.execute(
            select(func.count()).select_from(AgricultureEquipment).where(
                AgricultureEquipment.EquipmentID == item.EquipmentID,
                AgricultureEquipment.SubEquipment == item.SubEquipment,
            )
        )).scalar_one()
        if exists:
            continue

        record = AgricultureEquipment(
            EquipmentID=item.EquipmentID,
            Equipment=item.Equipment,
            SubEquipmentID=item.SubEquipmentID,
            SubEquipment=item.SubEquipment,
            Image=item.Image,
            CreatedBy=item.CreatedBy or "Admin",
            CreatedOn=datetime.now(timezone.utc),
            IsDeleted=False,
            IsActive=True,
        )
        db.add(record)
        created.append(item.SubEquipment)

    await db.commit()
    return {"status": "success", "created": created}


# ── GET /api/equipment/agriculture/list ───────────────────────────────────────
@router.get("/agriculture/list", response_model=EquipmentListResponse, summary="Get all equipment with sub-equipment")
async def get_all_agriculture(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgricultureEquipment)
        .where(AgricultureEquipment.IsDeleted == False)
        .order_by(AgricultureEquipment.EquipmentID, AgricultureEquipment.SubEquipmentID)
    )
    rows = result.scalars().all()

    grouped: dict[int, AllEquipmentsResponse] = {}
    for row in rows:
        if row.EquipmentID not in grouped:
            grouped[row.EquipmentID] = AllEquipmentsResponse(
                EquipmentID=row.EquipmentID,
                Equipment=row.Equipment,
                SubEquipment=[],
            )
        if row.SubEquipmentID:
            grouped[row.EquipmentID].SubEquipment.append(
                SubEquipmentDetail(
                    SubEquipmentID=row.SubEquipmentID,
                    SubEquipment=row.SubEquipment,
                    Image=row.Image,
                )
            )
    return EquipmentListResponse(status="success", value=list(grouped.values()))


# ── GET /api/equipment/agriculture/types ──────────────────────────────────────
@router.get("/agriculture/types", summary="Get distinct equipment types (ID + name)")
async def get_equipment_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgricultureEquipment.EquipmentID, AgricultureEquipment.Equipment)
        .distinct()
        .where(AgricultureEquipment.IsDeleted == False)
        .order_by(AgricultureEquipment.EquipmentID)
    )
    rows = result.all()
    return {
        "status": "success",
        "value": [EquipmentSimple(EquipmentID=r.EquipmentID, Equipment=r.Equipment) for r in rows],
    }


# ── POST /api/equipment/owner/create ─────────────────────────────────────────
@router.post("/owner/create", summary="Assign equipment to owner")
async def create_owner_equipment(
    items: list[OwnerEquipmentCreate],
    db: AsyncSession = Depends(get_db),
):
    created = []
    for item in items:
        exists = (await db.execute(
            select(func.count()).select_from(EquipmentDetails).where(
                EquipmentDetails.EquipmentID == item.EquipmentId,
                EquipmentDetails.SubEquipmentID == item.SubEquipmentId,
                EquipmentDetails.VehicleRegistrationNo == item.VehicleRegistrationNo,
                EquipmentDetails.OwnerID == item.OwnerId,
            )
        )).scalar_one()
        if exists:
            continue

        record = EquipmentDetails(
            OwnerID=item.OwnerId,
            EquipmentID=item.EquipmentId,
            SubEquipmentID=item.SubEquipmentId,
            VehicleRegistrationNo=item.VehicleRegistrationNo,
            Quantity=item.Quantity,
            CreatedBy=item.CreatedBy or "Admin",
            CreatedOn=datetime.now(timezone.utc),
            IsDeleted=False,
            IsActive=True,
        )
        db.add(record)
        created.append(item.VehicleRegistrationNo)

    await db.commit()
    return {"status": "success", "created": created}


# ── GET /api/equipment/owner/list ─────────────────────────────────────────────
@router.get("/owner/list", response_model=OwnerEquipmentResponse, summary="List all owner-equipment mappings")
async def get_owner_equipment_list(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EquipmentDetails).where(EquipmentDetails.IsDeleted == False)
    )
    rows = result.scalars().all()

    grouped: dict[str, OwnerEquipmentGroup] = {}
    for row in rows:
        key = row.OwnerID or ""
        if key not in grouped:
            grouped[key] = OwnerEquipmentGroup(OwnerId=row.OwnerID, SubEquipmentAll=[])
        grouped[key].SubEquipmentAll.append(
            SubEquipmentGet(
                VehicleRegistrationNo=row.VehicleRegistrationNo,
                EquipmentID=row.EquipmentID,
                SubEquipmentID=row.SubEquipmentID,
                Quantity=row.Quantity,
            )
        )
    return OwnerEquipmentResponse(status="success", value=list(grouped.values()))


# ── POST /api/equipment/owner/by-owner ────────────────────────────────────────
@router.post("/owner/by-owner", summary="Get equipment list for a specific owner")
async def get_owner_equipments(body: GetOwnerEquipmentsRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            EquipmentDetails.VehicleRegistrationNo,
            EquipmentDetails.EquipmentID,
            EquipmentDetails.SubEquipmentID,
        )
        .distinct()
        .where(
            EquipmentDetails.OwnerID == body.OwnerId,
            EquipmentDetails.IsDeleted == False,
        )
    )
    rows = result.all()
    items = [
        SubEquipmentGet(
            VehicleRegistrationNo=r.VehicleRegistrationNo,
            EquipmentID=r.EquipmentID,
            SubEquipmentID=r.SubEquipmentID,
        )
        for r in rows
    ]
    return {"status": "success", "value": items}


# ── POST /api/equipment/search ─────────────────────────────────────────────────
@router.post("/search", response_model=SearchEquipmentResponse, summary="Search nearby equipment owners")
async def search_equipment(body: SearchEquipmentRequest, db: AsyncSession = Depends(get_db)):
    """
    Haversine-based proximity search.  Returns owners within SearchDistance km
    who own the requested equipment/sub-equipment type.
    """
    result = await db.execute(
        select(
            Users.UCode,
            Users.UserName,
            Users.MobileNo,
            Users.Lat,
            Users.Long,
            EquipmentDetails.EquipmentID,
            EquipmentDetails.SubEquipmentID,
        )
        .join(EquipmentDetails, Users.UCode == EquipmentDetails.OwnerID)
        .where(
            EquipmentDetails.EquipmentID == body.EquipmentId,
            EquipmentDetails.SubEquipmentID == body.SubEquipmentId,
            Users.RoleCode == 1,  # RoleCode 1 = Owner
            Users.IsDeleted == False,
            EquipmentDetails.IsDeleted == False,
        )
    )
    rows = result.all()

    search_results: list[SearchEquipmentResult] = []
    for row in rows:
        if row.Lat is None or row.Long is None:
            continue

        # Haversine distance (km)
        lat1, lon1 = math.radians(body.Latitude), math.radians(body.Longitude)
        lat2, lon2 = math.radians(float(row.Lat)), math.radians(float(row.Long))
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        distance = 6371 * 2 * math.asin(math.sqrt(a))

        if distance <= body.SearchDistance:
            search_results.append(
                SearchEquipmentResult(
                    OwnerID=row.UCode,
                    Distance=round(distance, 2),
                    PhoneNo=row.MobileNo,
                    Name=row.UserName,
                    Latitude=float(row.Lat),
                    Longitude=float(row.Long),
                    EquipmentID=row.EquipmentID,
                    SubEquipmentID=row.SubEquipmentID,
                )
            )

    search_results.sort(key=lambda x: x.Distance or 0)
    return SearchEquipmentResponse(status="success", value=search_results)
