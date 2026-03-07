from pydantic import BaseModel


# ── Agriculture Equipment ──────────────────────────────────────────────────────

class AgricultureEquipmentCreate(BaseModel):
    EquipmentID: int
    Equipment: str
    SubEquipmentID: int | None = None
    SubEquipment: str | None = None
    Image: str | None = None
    CreatedBy: str | None = "Admin"


class SubEquipmentDetail(BaseModel):
    SubEquipmentID: int | None = None
    SubEquipment: str | None = None
    Image: str | None = None


class AllEquipmentsResponse(BaseModel):
    EquipmentID: int | None = None
    Equipment: str | None = None
    SubEquipment: list[SubEquipmentDetail] = []


class EquipmentListResponse(BaseModel):
    status: str
    value: list[AllEquipmentsResponse] = []


# ── Owner Equipment ────────────────────────────────────────────────────────────

class OwnerEquipmentCreate(BaseModel):
    OwnerId: str
    VehicleRegistrationNo: str
    EquipmentId: int
    SubEquipmentId: int
    Quantity: int | None = 1
    CreatedBy: str | None = "Admin"
    CreatedOn: str | None = None


class SubEquipmentGet(BaseModel):
    VehicleRegistrationNo: str | None = None
    EquipmentID: int | None = None
    SubEquipmentID: int | None = None
    Quantity: int | None = None


class OwnerEquipmentGroup(BaseModel):
    OwnerId: str | None = None
    SubEquipmentAll: list[SubEquipmentGet] = []


class OwnerEquipmentResponse(BaseModel):
    status: str
    value: list[OwnerEquipmentGroup] = []


class GetOwnerEquipmentsRequest(BaseModel):
    OwnerId: str


# ── Equipment Search ───────────────────────────────────────────────────────────

class SearchEquipmentRequest(BaseModel):
    Userid: str
    SearchDistance: float = 10.0   # km radius
    Latitude: float
    Longitude: float
    EquipmentId: int
    SubEquipmentId: int


class SearchEquipmentResult(BaseModel):
    OwnerID: str | None = None
    Distance: float | None = None
    PhoneNo: str | None = None
    Name: str | None = None
    Latitude: float | None = None
    Longitude: float | None = None
    EquipmentID: int | None = None
    SubEquipmentID: int | None = None


class SearchEquipmentResponse(BaseModel):
    status: str
    value: list[SearchEquipmentResult] = []


# ── Simple Equipment list (EquipmentID + name) ─────────────────────────────────

class EquipmentSimple(BaseModel):
    EquipmentID: int | None = None
    Equipment: str | None = None
