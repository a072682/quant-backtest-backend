from fastapi import APIRouter
from app.api.v1.endpoints import backtest, simulation

router = APIRouter()
router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
