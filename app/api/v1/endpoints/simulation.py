from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.simulation import SimulationTrade
from app.services.simulation_service import check_and_close_positions, get_simulation_summary

router = APIRouter()


@router.get("/trades")
def get_trades(db: Session = Depends(get_db)):
    return (
        db.query(SimulationTrade)
        .order_by(SimulationTrade.created_at.desc())
        .all()
    )


@router.get("/positions")
def get_positions(db: Session = Depends(get_db)):
    return (
        db.query(SimulationTrade)
        .filter(SimulationTrade.action == "buy", SimulationTrade.status == "open")
        .order_by(SimulationTrade.created_at.desc())
        .all()
    )


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return get_simulation_summary(db)
