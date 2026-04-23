import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Float, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SimulationTrade(Base):
    __tablename__ = "simulation_trades"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[date] = mapped_column(Date)
    stock_code: Mapped[str] = mapped_column(String(20))
    stock_name: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(10))          # buy / sell
    price: Mapped[float] = mapped_column(Float)
    shares: Mapped[float] = mapped_column(Float)
    total_amount: Mapped[float] = mapped_column(Float)
    signal_score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(10), default="open")  # open / closed
    buy_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
