"""
DFM Seed Script — inserts realistic sample data into every table.
Run: python seed.py
"""
import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.customer import CustomerDetails
from app.models.driver import DriverDetails
from app.models.equipment import AgricultureEquipment, EquipmentDetails
from app.models.market import Market
from app.models.order import OrderStatus, Orders
from app.models.user import DeviceDetails, Login, Users

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

NOW = datetime.utcnow()   # naive UTC — matches DateTime columns in models


async def seed():
    async with SessionLocal() as db:

        # ── 1. Agriculture Equipment catalog ──────────────────────────────────
        print("🌾 Seeding agriculture equipment...")
        equipment_catalog = [
            (1, "Tractor",       1, "Mini Tractor",          "tractor_mini.jpg"),
            (1, "Tractor",       2, "Heavy Tractor",         "tractor_heavy.jpg"),
            (1, "Tractor",       3, "Power Tiller",          "power_tiller.jpg"),
            (2, "Harvester",     1, "Paddy Harvester",       "paddy_harvester.jpg"),
            (2, "Harvester",     2, "Wheat Harvester",       "wheat_harvester.jpg"),
            (2, "Harvester",     3, "Maize Harvester",       "maize_harvester.jpg"),
            (3, "Sprayer",       1, "Boom Sprayer",          "boom_sprayer.jpg"),
            (3, "Sprayer",       2, "Mist Blower",           "mist_blower.jpg"),
            (4, "Plough",        1, "Disc Plough",           "disc_plough.jpg"),
            (4, "Plough",        2, "Mould Board Plough",    "mould_plough.jpg"),
            (5, "Water Pump",    1, "Diesel Pump",           "diesel_pump.jpg"),
            (5, "Water Pump",    2, "Electric Pump",         "electric_pump.jpg"),
        ]
        for eq_id, eq_name, sub_id, sub_name, img in equipment_catalog:
            db.add(AgricultureEquipment(
                EquipmentID=eq_id, Equipment=eq_name,
                SubEquipmentID=sub_id, SubEquipment=sub_name,
                Image=img, CreatedBy="seed", CreatedOn=NOW,
                IsDeleted=False, IsActive=True,
            ))

        # ── 2. Market Values ──────────────────────────────────────────────────
        print("📈 Seeding market values...")
        market_items = [
            ("Rice",        2200.00, "rice.jpg",        "Tamil Nadu",  "India", "per quintal"),
            ("Wheat",       2015.00, "wheat.jpg",       "Punjab",      "India", "per quintal"),
            ("Maize",       1870.00, "maize.jpg",       "Karnataka",   "India", "per quintal"),
            ("Cotton",      6380.00, "cotton.jpg",      "Andhra Pradesh", "India", "per quintal"),
            ("Sugarcane",    315.00, "sugarcane.jpg",   "Uttar Pradesh","India", "per quintal"),
            ("Soybean",     4300.00, "soybean.jpg",     "Madhya Pradesh","India","per quintal"),
            ("Groundnut",   5850.00, "groundnut.jpg",   "Gujarat",     "India", "per quintal"),
            ("Turmeric",    7200.00, "turmeric.jpg",    "Telangana",   "India", "per quintal"),
        ]
        for name, val, img, state, country, unit in market_items:
            db.add(Market(
                ItemName=name, CurrentValue=val, ImageURL=img,
                State=state, Country=country, Unit=unit,
            ))

        # ── 3. Users ──────────────────────────────────────────────────────────
        print("👥 Seeding users...")

        # RoleCode: 0=Admin, 1=Owner, 2=Driver, 3=Customer
        users = [
            # UCode,  Role, Name,              Mobile,       Email
            ("ADM01", 0, "Admin User",         "9000000001", "admin@dfm.com"),
            ("OWN01", 1, "Rajan Krishnamurthy","9000000002", "rajan@dfm.com"),
            ("OWN02", 1, "Suresh Patel",       "9000000003", "suresh@dfm.com"),
            ("DRV01", 2, "Murugan Selvam",     "9000000004", "murugan@dfm.com"),
            ("DRV02", 2, "Anbu Arasan",        "9000000005", "anbu@dfm.com"),
            ("CST01", 3, "Priya Sharma",       "9000000006", "priya@dfm.com"),
            ("CST02", 3, "Venkat Reddy",       "9000000007", "venkat@dfm.com"),
        ]
        for ucode, role, name, mobile, email in users:
            db.add(Users(
                UCode=ucode, RoleCode=role, UserName=name,
                MobileNo=mobile, Email=email,
                Address="123 Farm Road, Coimbatore",
                City="Coimbatore", State="Tamil Nadu", Country="India",
                Lat=11.0168, Long=76.9558,
                CreatedBy="seed", CreatedOn=NOW,
                IsDeleted=False, IsActive=True,
            ))
            db.add(Login(
                UCode=ucode, RoleCode=role, UserName=name,
                OTP="1234", Pin="5678",
                CreatedBy="seed", CreatedOn=NOW,
                IsDeleted=False, IsActive=True,
            ))

        # ── 4. Driver Details ─────────────────────────────────────────────────
        print("🚗 Seeding driver details...")
        drivers = [
            ("DRV01", "TN0120230001", "2027-12-31", "LMV", "5"),
            ("DRV02", "TN0120230002", "2026-08-15", "HTV", "8"),
        ]
        for drv_id, lic, exp, typ, yrs in drivers:
            db.add(DriverDetails(
                DriverID=drv_id, LicenseNo=lic, LicenseExpiry=exp,
                LicenseType=typ, ExperienceYears=yrs,
                BloodGroup="O+", EmergencyContactNumber="9999999999",
                EmergencyContactName="Family",
                Lat=11.0168, Long=76.9558,
                CreatedBy="seed", CreatedOn=NOW,
                IsDeleted=False, IsActive=True,
            ))

        # ── 5. Customer Details ───────────────────────────────────────────────
        print("🧑‍🌾 Seeding customer details...")
        customers = [
            ("CST01", "Sharma", "Ramesh Sharma"),
            ("CST02", "Reddy",  "Gopal Reddy"),
        ]
        for cst_id, father, emergency_name in customers:
            db.add(CustomerDetails(
                CustomerID=cst_id, FatherName=father,
                BloodGroup="A+",
                EmergencyContactNumber="9888888888",
                EmergencyContactName=emergency_name,
                IsRegistered=True,
                Lat=11.0168, Long=76.9558,
                CreatedBy="seed", CreatedOn=NOW,
                IsDeleted=False, IsActive=True,
            ))

        # ── 6. Equipment Details (Owner → Equipment mapping) ──────────────────
        print("🔧 Seeding equipment details...")
        eq_details = [
            ("OWN01", 1, 1, "TN39AB1234"),   # Owner1 → Mini Tractor
            ("OWN01", 2, 1, "TN39AB1235"),   # Owner1 → Paddy Harvester
            ("OWN01", 3, 1, "TN39AB1236"),   # Owner1 → Boom Sprayer
            ("OWN02", 1, 2, "TN39CD5678"),   # Owner2 → Heavy Tractor
            ("OWN02", 4, 1, "TN39CD5679"),   # Owner2 → Disc Plough
            ("OWN02", 5, 1, "TN39CD5680"),   # Owner2 → Diesel Pump
        ]
        for owner, eq_id, sub_id, veh_no in eq_details:
            db.add(EquipmentDetails(
                OwnerID=owner, EquipmentID=eq_id, SubEquipmentID=sub_id,
                VehicleRegistrationNo=veh_no, Quantity=1,
                CreatedBy="seed", CreatedOn=NOW,
                IsDeleted=False, IsActive=True,
            ))

        # ── 7. Device Details ─────────────────────────────────────────────────
        print("📱 Seeding device details...")
        for ucode, mobile in [("CST01","9000000006"), ("CST02","9000000007"),
                               ("OWN01","9000000002"), ("OWN02","9000000003")]:
            db.add(DeviceDetails(
                UCODE=ucode, MobileNo=mobile,
                DeviceType="Android", DeviceName="Sample Device",
                RegistrationToken=f"fcm_token_{ucode.lower()}",
                CreatedBy="seed", CreatedOn=NOW,
                IsDeleted=False, IsActive=True,
            ))

        # ── 8. Orders ─────────────────────────────────────────────────────────
        print("📦 Seeding orders...")
        orders_data = [
            # OrderID,    UserID, OwnerID, EqID, SubID, Status, Location
            ("ORD20240001","CST01","OWN01", 1, 1, 1, "Thanjavur Fields"),
            ("ORD20240002","CST01","OWN01", 2, 1, 3, "Trichy Farm Block A"),
            ("ORD20240003","CST02","OWN02", 1, 2, 0, "Salem Agricultural Zone"),
            ("ORD20240004","CST02","OWN02", 4, 1, 2, "Erode District Farm"),
            ("ORD20240005","CST01","OWN02", 5, 1, 3, "Pollachi Village"),
        ]
        for ord_id, user, owner, eq_id, sub_id, status, location in orders_data:
            db.add(Orders(
                OrderID=ord_id, UserId=user, OwnerId=owner,
                EquipmentId=eq_id, SubEquipmentId=sub_id,
                OrderCreatedOn=NOW, OrderRequiredOn="2024-12-01",
                OrderRequiredLocation=location,
                Lat=11.0168, Long=76.9558,
                Quantity=1, RequiredTime="8 hours",
                EstimatedAmount=2500.00, AmountPaid=0.00,
                MinimumAmountToPay=500.00,
                PaymentMode="Cash", ContactNumber="9000000099",
                ContactNanme="Farm Manager",
                CreatedBy="seed", CreatedOn=NOW, IsDeleted=False,
            ))
            db.add(OrderStatus(
                OrderID=ord_id, UserId=user, OwnerId=owner,
                StatusID=status,   # 0=Created,1=Accepted,2=Cancelled,3=Completed
                CreatedBy="seed", CreatedOn=NOW, IsDeleted=False,
            ))

        await db.commit()
        print("\n✅ Seed complete!")
        print("   Users    : 7  (1 admin, 2 owners, 2 drivers, 2 customers)")
        print("   Equipment: 12 types across 5 categories")
        print("   Market   : 8 commodity prices")
        print("   Orders   : 5 orders (mixed statuses)")
        print("\n   Login credentials for all users:")
        print("   OTP: 1234  |  PIN: 5678")


if __name__ == "__main__":
    asyncio.run(seed())
