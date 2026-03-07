from pydantic import BaseModel


class CreateVehicleRequest(BaseModel):
    OwnerID: str
    VehicleNumber: str
    VehiclePhoto: str | None = None
    VehicleModel: str | None = None
    VehicleTankCapacity: str | None = None
    VehicleChassis: str | None = None
    VehicleRC: str | None = None
    VehicleInsuranceNo: str | None = None
    VehicleInsuranceProvider: str | None = None
    VehicleInsuranceStartDate: str | None = None
    VehicleInsuranceExpireDate: str | None = None
    VehicleServiceNo: str | None = None
    YearOfManufacture: str | None = None
    Image: str | None = None
    SpeedLimit: str | None = None
    Lat: float | None = None
    Long: float | None = None
    CreatedBy: str | None = "Admin"


class VehicleDetail(BaseModel):
    ID: int
    OwnerID: str | None = None
    VehicleNumber: str | None = None
    VehicleModel: str | None = None
    VehicleTankCapacity: str | None = None
    VehicleChassis: str | None = None
    VehicleInsuranceNo: str | None = None
    VehicleInsuranceProvider: str | None = None
    VehicleInsuranceExpireDate: str | None = None
    YearOfManufacture: str | None = None
    SpeedLimit: str | None = None
    Lat: float | None = None
    Long: float | None = None

    model_config = {"from_attributes": True}


class VehicleResponse(BaseModel):
    status: str
    value: list[VehicleDetail] = []
