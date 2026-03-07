from pydantic import BaseModel


class MarketValueItem(BaseModel):
    ID: int
    ItemName: str | None = None
    CurrentValue: float | None = None
    ImageURL: str | None = None
    State: str | None = None
    Country: str | None = None
    Unit: str | None = None

    model_config = {"from_attributes": True}


class MarketValueResponse(BaseModel):
    status: str
    value: list[MarketValueItem] = []
