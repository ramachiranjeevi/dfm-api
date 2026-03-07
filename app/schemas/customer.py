from pydantic import BaseModel


class CreateCustomerRequest(BaseModel):
    # User fields
    RoleCode: int | None = 3
    UCode: str | None = None
    UserName: str | None = None
    Firstname: str | None = None
    Lastname: str | None = None
    DateOfBirth: str | None = None
    Language: str | None = None
    Gender: str | None = None
    MaritialStatus: str | None = None
    Address: str | None = None
    Address2: str | None = None
    Area: str | None = None
    City: str | None = None
    State: str | None = None
    Country: str | None = None
    PinCode: str | None = None
    MobileNo: str | None = None
    Email: str | None = None
    Lat: float | None = None
    Long: float | None = None

    # Customer-specific fields
    CustomerID: str | None = None
    MotherName: str | None = None
    FatherName: str | None = None
    BloodGroup: str | None = None
    EmergencyContactNumber: str | None = None
    EmergencyContactName: str | None = None
    AddhaarNumber: str | None = None
    PassportNumber: str | None = None
    EmailNumber: str | None = None
    Description: str | None = None
    DateOfJoining: str | None = None
    DateOfRelieving: str | None = None
    MartialStatus: str | None = None
    Year: str | None = None
    Month: str | None = None
    SerialNo: str | None = None
    IsRegistered: bool | None = False

    CreatedBy: str | None = "Admin"


class CustomerResponse(BaseModel):
    status: str
    message: str | None = None
