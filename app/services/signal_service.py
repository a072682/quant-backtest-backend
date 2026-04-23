import pandas as pd
import yfinance as yf
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.backtest_service import _format_ticker, _calc_score
from app.services.simulation_service import create_simulation_buy


async def create_today_signal(stock_code: str, db: AsyncSession) -> dict:
    ticker_symbol = _format_ticker(stock_code)
    ticker = yf.Ticker(ticker_symbol)

    df = ticker.history(period="30d")
    if df.empty or len(df) < 2:
        raise ValueError(f"無法取得 {stock_code} 的數據")

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df["ma20"] = df["Close"].rolling(20).mean()
    df["vol_ma5"] = df["Volume"].rolling(5).mean()

    try:
        info = ticker.info
        div_yield = info.get("dividendYield", 0) or 0
        stock_name = info.get("shortName") or info.get("longName") or stock_code
    except Exception:
        div_yield = 0
        stock_name = stock_code

    df["div_yield"] = div_yield

    today_row = df.iloc[-1]
    score = _calc_score(today_row)
    price = float(today_row["Close"])

    if score >= 5:
        await create_simulation_buy(
            stock_code=stock_code,
            stock_name=stock_name,
            price=price,
            score=score,
            db=db,
        )

    return {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "date": date.today().isoformat(),
        "price": round(price, 4),
        "total_score": score,
        "signal": score >= 5,
    }
