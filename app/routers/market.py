"""
Market Values router
Endpoint: list all market values
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.market import Market
from app.schemas.market import MarketValueItem, MarketValueResponse

router = APIRouter(prefix="/api/market", tags=["Market Values"])


# ── GET /api/market/values ────────────────────────────────────────────────────
@router.get("/values", response_model=MarketValueResponse, summary="Get all agricultural market values")
async def get_market_values(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Market).order_by(Market.ID)
    )
    items = result.scalars().all()
    return MarketValueResponse(
        status="success",
        value=[MarketValueItem.model_validate(item) for item in items],
    )
