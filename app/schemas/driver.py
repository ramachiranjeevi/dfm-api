from pydantic import BaseModel


class CreateDriverRequest(BaseModel):
    # User fields
    RoleCode: int | None = 2
    UCode: str | None = None
    UserName: str | None = None
    Firstname: str | None = None
    Lastname: str | None = None
    MobileNo: str | None = None
    Email: str | None = None
    Address: str | None = None
    Lat: float | None = None
    Long: float | None = None

    # Driver-specific
    DriverID: str | None = None
    LicenseNo: str | None = None
    LicenseExpiry: str | None = None
    LicenseType: str | None = None
    ExperienceYears: str | None = None
    BloodGroup: str | None = None
    EmergencyContactNumber: str | None = None
    EmergencyContactName: str | None = None
    AddhaarNumber: str | None = None
    PassportNumber: str | None = None

    CreatedBy: str | None = "Admin"


class DriverDetail(BaseModel):
    DriverID: str | None = None
    LicenseNo: str | None = None
    LicenseType: str | None = None
    ExperienceYears: str | None = None
    BloodGroup: str | None = None

    model_config = {"from_attributes": True}


class DriverResponse(BaseModel):
    status: str
    value: list[DriverDetail] = []


class DriverCreateResponse(BaseModel):
    status: str
    message: str | None = None
