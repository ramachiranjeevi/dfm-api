"""
Vehicles router
Endpoints: create vehicle, list all vehicles
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.vehicle import VehicleDetails
from app.schemas.vehicle import CreateVehicleRequest, VehicleDetail, VehicleResponse

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])


# ── POST /api/vehicles/create ─────────────────────────────────────────────────
@router.post("/create", summary="Register a new vehicle")
async def create_vehicle(body: CreateVehicleRequest, db: AsyncSession = Depends(get_db)):
    vehicle = VehicleDetails(
        OwnerID=body.OwnerID,
        VehicleNumber=body.VehicleNumber,
        VehiclePhoto=body.VehiclePhoto,
        VehicleModel=body.VehicleModel,
        VehicleTankCapacity=body.VehicleTankCapacity,
        VehicleChassis=body.VehicleChassis,
        VehicleRC=body.VehicleRC,
        VehicleInsuranceNo=body.VehicleInsuranceNo,
        VehicleInsuranceProvider=body.VehicleInsuranceProvider,
        VehicleInsuranceStartDate=body.VehicleInsuranceStartDate,
        VehicleInsuranceExpireDate=body.VehicleInsuranceExpireDate,
        VehicleServiceNo=body.VehicleServiceNo,
        YearOfManufacture=body.YearOfManufacture,
        Image=body.Image,
        SpeedLimit=body.SpeedLimit,
        Lat=body.Lat,
        Long=body.Long,
        CreatedBy=body.CreatedBy or "Admin",
        CreatedOn=datetime.now(timezone.utc),
        IsDeleted=False,
        IsActive=True,
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return {"status": "success", "message": "Vehicle registered", "id": vehicle.ID}


# ── GET /api/vehicles/list ────────────────────────────────────────────────────
@router.get("/list", response_model=VehicleResponse, summary="List all vehicles")
async def get_vehicles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VehicleDetails).where(VehicleDetails.IsDeleted == False)
    )
    vehicles = result.scalars().all()
    items = [VehicleDetail.model_validate(v) for v in vehicles]
    return VehicleResponse(status="success", value=items)
