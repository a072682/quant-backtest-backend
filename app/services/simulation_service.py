import uuid
from datetime import date
from sqlalchemy.orm import Session
import yfinance as yf

from app.models.simulation import SimulationTrade
from app.services.backtest_service import _format_ticker


def create_simulation_buy(
    stock_code: str,
    stock_name: str,
    price: float,
    score: float,
    db: Session,
) -> SimulationTrade:
    shares = round(10000 / price, 4)
    trade = SimulationTrade(
        id=str(uuid.uuid4()),
        date=date.today(),
        stock_code=stock_code,
        stock_name=stock_name,
        action="buy",
        price=round(price, 4),
        shares=shares,
        total_amount=round(shares * price, 2),
        signal_score=score,
        status="open",
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


def check_and_close_positions(db: Session) -> list[SimulationTrade]:
    open_positions = (
        db.query(SimulationTrade)
        .filter(SimulationTrade.action == "buy", SimulationTrade.status == "open")
        .all()
    )

    closed: list[SimulationTrade] = []
    for pos in open_positions:
        try:
            hist = yf.Ticker(_format_ticker(pos.stock_code)).history(period="2d")
            if hist.empty:
                continue
            current_price = float(hist["Close"].iloc[-1])
        except Exception:
            continue

        pct_chg = (current_price - pos.price) / pos.price
        if -0.03 < pct_chg < 0.06:
            continue

        profit = round((current_price - pos.price) * pos.shares, 2)
        profit_pct = round(pct_chg * 100, 2)

        pos.status = "closed"

        sell = SimulationTrade(
            id=str(uuid.uuid4()),
            date=date.today(),
            stock_code=pos.stock_code,
            stock_name=pos.stock_name,
            action="sell",
            price=round(current_price, 4),
            shares=pos.shares,
            total_amount=round(current_price * pos.shares, 2),
            signal_score=pos.signal_score,
            status="closed",
            buy_price=pos.price,
            profit=profit,
            profit_pct=profit_pct,
        )
        db.add(sell)
        db.commit()
        closed.append(sell)

    return closed


def get_simulation_summary(db: Session) -> dict:
    sells = (
        db.query(SimulationTrade)
        .filter(SimulationTrade.action == "sell")
        .all()
    )
    total = len(sells)
    if total == 0:
        return {"total_trades": 0, "win_rate": 0.0, "total_profit": 0.0}

    wins = sum(1 for t in sells if t.profit and t.profit > 0)
    total_profit = sum(t.profit for t in sells if t.profit is not None)
    return {
        "total_trades": total,
        "win_rate": round(wins / total * 100, 2),
        "total_profit": round(total_profit, 2),
    }
