from fastapi import APIRouter
from app.api.v1.endpoints import backtest

router = APIRouter()
router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
