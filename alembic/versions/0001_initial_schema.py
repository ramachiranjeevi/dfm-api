"""Initial schema — all DFM tables

Revision ID: 0001
Revises:
Create Date: 2026-03-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "Users",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("RoleCode", sa.Integer(), nullable=True),
        sa.Column("UCode", sa.String(50), nullable=True),
        sa.Column("UserName", sa.String(200), nullable=True),
        sa.Column("Firstname", sa.String(100), nullable=True),
        sa.Column("Lastname", sa.String(100), nullable=True),
        sa.Column("DateOfBirth", sa.String(50), nullable=True),
        sa.Column("Language", sa.String(50), nullable=True),
        sa.Column("Gender", sa.String(20), nullable=True),
        sa.Column("MaritialStatus", sa.String(50), nullable=True),
        sa.Column("Address", sa.Text(), nullable=True),
        sa.Column("Address2", sa.Text(), nullable=True),
        sa.Column("Area", sa.String(100), nullable=True),
        sa.Column("City", sa.String(100), nullable=True),
        sa.Column("State", sa.String(100), nullable=True),
        sa.Column("Country", sa.String(100), nullable=True),
        sa.Column("PinCode", sa.String(20), nullable=True),
        sa.Column("DoorNo", sa.String(50), nullable=True),
        sa.Column("NearestLandMark", sa.String(200), nullable=True),
        sa.Column("MobileNo", sa.String(20), nullable=True),
        sa.Column("Email", sa.String(200), nullable=True),
        sa.Column("Lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("Long", sa.Numeric(10, 7), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
        sa.Column("IsActive", sa.Boolean(), default=True),
    )

    # ── Login ──────────────────────────────────────────────────────────────────
    op.create_table(
        "Login",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("RoleCode", sa.Integer(), nullable=True),
        sa.Column("UCode", sa.String(50), nullable=True),
        sa.Column("UserName", sa.String(200), nullable=True),
        sa.Column("Pasword", sa.String(200), nullable=True),
        sa.Column("Pin", sa.String(10), nullable=True),
        sa.Column("OTP", sa.String(10), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
        sa.Column("IsActive", sa.Boolean(), default=True),
    )

    # ── DeviceDetails ──────────────────────────────────────────────────────────
    op.create_table(
        "DeviceDetails",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("UCODE", sa.String(50), nullable=True),
        sa.Column("MobileNo", sa.String(20), nullable=True),
        sa.Column("IMEI", sa.String(100), nullable=True),
        sa.Column("DeviceId", sa.String(200), nullable=True),
        sa.Column("DeviceType", sa.String(50), nullable=True),
        sa.Column("DeviceName", sa.String(100), nullable=True),
        sa.Column("RegistrationToken", sa.Text(), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("Modifiedon", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
        sa.Column("IsActive", sa.Boolean(), default=True),
    )

    # ── VerifyOTP ──────────────────────────────────────────────────────────────
    op.create_table(
        "VerifyOTP",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("MobileNo", sa.String(20), nullable=True),
        sa.Column("OTP", sa.String(10), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
        sa.Column("IsActive", sa.Boolean(), default=True),
    )

    # ── AgricultureEquipment ───────────────────────────────────────────────────
    op.create_table(
        "AgricultureEquipment",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("EquipmentID", sa.Integer(), nullable=True),
        sa.Column("Equipment", sa.String(200), nullable=True),
        sa.Column("SubEquipmentID", sa.Integer(), nullable=True),
        sa.Column("SubEquipment", sa.String(200), nullable=True),
        sa.Column("Image", sa.Text(), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
        sa.Column("IsActive", sa.Boolean(), default=True),
    )

    # ── EquipmentDetails ───────────────────────────────────────────────────────
    op.create_table(
        "EquipmentDetails",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("OwnerID", sa.String(50), nullable=True),
        sa.Column("EquipmentID", sa.Integer(), nullable=True),
        sa.Column("SubEquipmentID", sa.Integer(), nullable=True),
        sa.Column("VehicleRegistrationNo", sa.String(50), nullable=True),
        sa.Column("Quantity", sa.Integer(), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
        sa.Column("IsActive", sa.Boolean(), default=True),
    )

    # ── Orders ─────────────────────────────────────────────────────────────────
    op.create_table(
        "Orders",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("OrderID", sa.String(50), nullable=True),
        sa.Column("UserId", sa.String(50), nullable=True),
        sa.Column("OwnerId", sa.String(50), nullable=True),
        sa.Column("EquipmentId", sa.Integer(), nullable=True),
        sa.Column("SubEquipmentId", sa.Integer(), nullable=True),
        sa.Column("OrderCreatedOn", sa.DateTime(), nullable=True),
        sa.Column("OrderRequiredOn", sa.String(100), nullable=True),
        sa.Column("OrderRequiredLocation", sa.Text(), nullable=True),
        sa.Column("Lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("Long", sa.Numeric(10, 7), nullable=True),
        sa.Column("Quantity", sa.Integer(), nullable=True),
        sa.Column("RequiredTime", sa.String(100), nullable=True),
        sa.Column("EstimatedAmount", sa.Numeric(12, 2), nullable=True),
        sa.Column("AmountPaid", sa.Numeric(12, 2), nullable=True),
        sa.Column("MinimumAmountToPay", sa.Numeric(12, 2), nullable=True),
        sa.Column("PaymentMode", sa.String(50), nullable=True),
        sa.Column("TransactionID", sa.String(100), nullable=True),
        sa.Column("ContactNumber", sa.String(20), nullable=True),
        sa.Column("ContactNanme", sa.String(100), nullable=True),
        sa.Column("ApprovedBy", sa.String(100), nullable=True),
        sa.Column("Comments", sa.Text(), nullable=True),
        sa.Column("ProcessingDate", sa.DateTime(), nullable=True),
        sa.Column("CompletedDate", sa.DateTime(), nullable=True),
        sa.Column("ProcessingMadeBy", sa.String(100), nullable=True),
        sa.Column("CompleteMadeBy", sa.String(100), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
    )

    # ── OrderStatus ────────────────────────────────────────────────────────────
    op.create_table(
        "OrderStatus",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("OrderID", sa.String(50), nullable=True),
        sa.Column("UserId", sa.String(50), nullable=True),
        sa.Column("OwnerId", sa.String(50), nullable=True),
        sa.Column("StatusID", sa.Integer(), default=0),
        sa.Column("ApprovedBy", sa.String(100), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
    )

    # ── VehicleDetails ─────────────────────────────────────────────────────────
    op.create_table(
        "VehicleDetails",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("OwnerID", sa.String(50), nullable=True),
        sa.Column("VehicleNumber", sa.String(50), nullable=True),
        sa.Column("VehiclePhoto", sa.Text(), nullable=True),
        sa.Column("VehicleModel", sa.String(100), nullable=True),
        sa.Column("VehicleTankCapacity", sa.String(50), nullable=True),
        sa.Column("VehicleChassis", sa.String(100), nullable=True),
        sa.Column("VehicleRC", sa.Text(), nullable=True),
        sa.Column("VehicleInsuranceNo", sa.String(100), nullable=True),
        sa.Column("VehicleInsuranceProvider", sa.String(100), nullable=True),
        sa.Column("VehicleInsuranceStartDate", sa.String(50), nullable=True),
        sa.Column("VehicleInsuranceExpireDate", sa.String(50), nullable=True),
        sa.Column("VehicleServiceNo", sa.String(100), nullable=True),
        sa.Column("YearOfManufacture", sa.String(10), nullable=True),
        sa.Column("Image", sa.Text(), nullable=True),
        sa.Column("SpeedLimit", sa.String(20), nullable=True),
        sa.Column("Lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("Long", sa.Numeric(10, 7), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
        sa.Column("IsActive", sa.Boolean(), default=True),
    )

    # ── CustomerDetails ────────────────────────────────────────────────────────
    op.create_table(
        "CustomerDetails",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("CustomerID", sa.String(50), nullable=True),
        sa.Column("MotherName", sa.String(100), nullable=True),
        sa.Column("FatherName", sa.String(100), nullable=True),
        sa.Column("BloodGroup", sa.String(10), nullable=True),
        sa.Column("EmergencyContactNumber", sa.String(20), nullable=True),
        sa.Column("EmergencyContactName", sa.String(100), nullable=True),
        sa.Column("AddhaarNumber", sa.String(20), nullable=True),
        sa.Column("PassportNumber", sa.String(20), nullable=True),
        sa.Column("EmailNumber", sa.String(200), nullable=True),
        sa.Column("Description", sa.Text(), nullable=True),
        sa.Column("DateOfJoining", sa.String(50), nullable=True),
        sa.Column("DateOfRelieving", sa.String(50), nullable=True),
        sa.Column("MartialStatus", sa.String(50), nullable=True),
        sa.Column("Year", sa.String(10), nullable=True),
        sa.Column("Month", sa.String(20), nullable=True),
        sa.Column("SerialNo", sa.String(50), nullable=True),
        sa.Column("IsRegistered", sa.Boolean(), default=False),
        sa.Column("Lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("Long", sa.Numeric(10, 7), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
        sa.Column("IsActive", sa.Boolean(), default=True),
    )

    # ── DriverDetails ──────────────────────────────────────────────────────────
    op.create_table(
        "DriverDetails",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("DriverID", sa.String(50), nullable=True),
        sa.Column("LicenseNo", sa.String(50), nullable=True),
        sa.Column("LicenseExpiry", sa.String(50), nullable=True),
        sa.Column("LicenseType", sa.String(50), nullable=True),
        sa.Column("ExperienceYears", sa.String(10), nullable=True),
        sa.Column("BloodGroup", sa.String(10), nullable=True),
        sa.Column("EmergencyContactNumber", sa.String(20), nullable=True),
        sa.Column("EmergencyContactName", sa.String(100), nullable=True),
        sa.Column("AddhaarNumber", sa.String(20), nullable=True),
        sa.Column("PassportNumber", sa.String(20), nullable=True),
        sa.Column("Lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("Long", sa.Numeric(10, 7), nullable=True),
        sa.Column("CreatedBy", sa.String(100), nullable=True),
        sa.Column("CreatedOn", sa.DateTime(), nullable=True),
        sa.Column("IsDeleted", sa.Boolean(), default=False),
        sa.Column("IsActive", sa.Boolean(), default=True),
    )

    # ── Market ─────────────────────────────────────────────────────────────────
    op.create_table(
        "Market",
        sa.Column("ID", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ItemName", sa.String(200), nullable=True),
        sa.Column("CurrentValue", sa.Numeric(12, 2), nullable=True),
        sa.Column("ImageURL", sa.Text(), nullable=True),
        sa.Column("State", sa.String(100), nullable=True),
        sa.Column("Country", sa.String(100), nullable=True),
        sa.Column("Unit", sa.String(50), nullable=True),
    )

    # ── Indexes ────────────────────────────────────────────────────────────────
    op.create_index("ix_users_mobileno", "Users", ["MobileNo"])
    op.create_index("ix_users_ucode", "Users", ["UCode"])
    op.create_index("ix_login_ucode", "Login", ["UCode"])
    op.create_index("ix_orders_orderid", "Orders", ["OrderID"])
    op.create_index("ix_orders_userid", "Orders", ["UserId"])
    op.create_index("ix_orderstatus_orderid", "OrderStatus", ["OrderID"])
    op.create_index("ix_equipmentdetails_ownerid", "EquipmentDetails", ["OwnerID"])
    op.create_index("ix_devicedetails_mobileno", "DeviceDetails", ["MobileNo"])
    op.create_index("ix_devicedetails_ucode", "DeviceDetails", ["UCODE"])


def downgrade() -> None:
    op.drop_table("Market")
    op.drop_table("DriverDetails")
    op.drop_table("CustomerDetails")
    op.drop_table("VehicleDetails")
    op.drop_table("OrderStatus")
    op.drop_table("Orders")
    op.drop_table("EquipmentDetails")
    op.drop_table("AgricultureEquipment")
    op.drop_table("VerifyOTP")
    op.drop_table("DeviceDetails")
    op.drop_table("Login")
    op.drop_table("Users")
