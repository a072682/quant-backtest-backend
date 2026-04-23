from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.simulation import SimulationTrade
from app.services.simulation_service import check_and_close_positions, get_simulation_summary

router = APIRouter()


@router.get("/trades")
async def get_trades(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SimulationTrade).order_by(SimulationTrade.created_at.desc())
    )
    return result.scalars().all()


@router.get("/positions")
async def get_positions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SimulationTrade)
        .where(SimulationTrade.action == "buy", SimulationTrade.status == "open")
        .order_by(SimulationTrade.created_at.desc())
    )
    return result.scalars().all()


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    return await get_simulation_summary(db)
