from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Market(Base):
    __tablename__ = "Market"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ItemName: Mapped[str | None] = mapped_column(String(200))
    CurrentValue: Mapped[float | None] = mapped_column(Numeric(12, 2))
    ImageURL: Mapped[str | None] = mapped_column(Text)
    State: Mapped[str | None] = mapped_column(String(100))
    Country: Mapped[str | None] = mapped_column(String(100))
    Unit: Mapped[str | None] = mapped_column(String(50))
