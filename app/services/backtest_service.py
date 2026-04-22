import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Any


def _format_ticker(stock_code: str) -> str:
    """台股代號加上 .TW 後綴，美股直接使用原代號"""
    if stock_code.isdigit():
        return f"{stock_code}.TW"
    return stock_code.upper()


def _calc_score(row: pd.Series) -> float:
    """計算單日技術指標評分（最高10分）"""
    score = 0.0

    # 均線得分（0~3）：股價 vs 20日均線
    if pd.notna(row["ma20"]) and row["ma20"] > 0:
        ma_pct = (row["Close"] - row["ma20"]) / row["ma20"] * 100
        if ma_pct > 3:
            score += 3
        elif ma_pct > 0:
            score += 2
        elif ma_pct > -3:
            score += 1

    # 成交量得分（0~3）：今日量 vs 5日均量
    if pd.notna(row["vol_ma5"]) and row["vol_ma5"] > 0:
        vol_ratio = row["Volume"] / row["vol_ma5"]
        if vol_ratio > 2:
            score += 3
        elif vol_ratio > 1.5:
            score += 2
        elif vol_ratio > 1:
            score += 1

    # 殖利率得分（0~4）：用 yfinance 殖利率換算
    if pd.notna(row.get("div_yield", None)):
        dy = row["div_yield"] * 100
        if dy >= 6:
            score += 4
        elif dy >= 5:
            score += 3
        elif dy >= 4:
            score += 2
        elif dy >= 3:
            score += 1

    # 法人得分：歷史數據難取得，固定 0
    return score


def run_backtest(
    stock_code: str,
    start_date: str,
    end_date: str,
    buy_threshold: float,
    stop_loss: float,
    take_profit: float,
    initial_capital: float,
) -> dict[str, Any]:
    ticker_symbol = _format_ticker(stock_code)
    ticker = yf.Ticker(ticker_symbol)

    # 多抓 60 天確保 MA20 有足夠數據
    fetch_start = pd.Timestamp(start_date) - pd.DateOffset(days=60)
    df = ticker.history(start=fetch_start.strftime("%Y-%m-%d"), end=end_date)

    if df.empty:
        raise ValueError(f"無法取得 {stock_code} 的歷史數據，請確認股票代號與日期範圍")

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)

    # 技術指標
    df["ma20"] = df["Close"].rolling(20).mean()
    df["vol_ma5"] = df["Volume"].rolling(5).mean()

    # 殖利率（靜態，取自 ticker info）
    try:
        info = ticker.info
        div_yield = info.get("dividendYield", 0) or 0
    except Exception:
        div_yield = 0
    df["div_yield"] = div_yield

    # 計算每日評分
    df["score"] = df.apply(_calc_score, axis=1)

    # 只保留目標區間
    df = df[df.index >= pd.Timestamp(start_date)]

    # ── 模擬買賣 ──────────────────────────────────────────────
    capital = initial_capital
    position = None   # {"buy_date", "buy_price", "shares"}
    trades: list[dict] = []
    equity_curve: list[dict] = []

    for date, row in df.iterrows():
        date_str = date.strftime("%Y-%m-%d")
        price = row["Close"]

        if position is not None:
            pct_chg = (price - position["buy_price"]) / position["buy_price"] * 100

            # 停損或獲利了結
            if pct_chg <= stop_loss or pct_chg >= take_profit:
                sell_value = position["shares"] * price
                capital = sell_value
                result = "profit" if pct_chg > 0 else "loss"
                trades.append({
                    "buy_date": position["buy_date"],
                    "buy_price": round(position["buy_price"], 4),
                    "sell_date": date_str,
                    "sell_price": round(price, 4),
                    "return_pct": round(pct_chg, 2),
                    "result": result,
                })
                position = None

        # 沒有持倉且評分達標 → 買進
        if position is None and row["score"] >= buy_threshold:
            shares = capital / price
            position = {
                "buy_date": date_str,
                "buy_price": price,
                "shares": shares,
            }
            capital = 0  # 全倉買入

        # 計算當日帳戶淨值
        if position is not None:
            equity = position["shares"] * price
        else:
            equity = capital
        equity_curve.append({"date": date_str, "value": round(equity, 2)})

    # 若結束時仍持倉，以最後收盤強制平倉（不計入交易統計）
    if position is not None:
        last_price = df.iloc[-1]["Close"]
        capital = position["shares"] * last_price

    final_equity = capital if position is None else position["shares"] * df.iloc[-1]["Close"]

    # ── 統計 ──────────────────────────────────────────────────
    total_return = (final_equity - initial_capital) / initial_capital * 100

    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)
    years = max((end_dt - start_dt).days / 365.25, 1 / 365.25)
    annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100

    wins = sum(1 for t in trades if t["result"] == "profit")
    win_rate = (wins / len(trades) * 100) if trades else 0.0

    # 最大回撤
    equity_values = [e["value"] for e in equity_curve]
    max_drawdown = 0.0
    if equity_values:
        peak = equity_values[0]
        for v in equity_values:
            if v > peak:
                peak = v
            dd = (v - peak) / peak * 100
            if dd < max_drawdown:
                max_drawdown = dd

    return {
        "summary": {
            "total_return": round(total_return, 2),
            "annual_return": round(annual_return, 2),
            "win_rate": round(win_rate, 2),
            "max_drawdown": round(max_drawdown, 2),
            "total_trades": len(trades),
        },
        "equity_curve": equity_curve,
        "trades": trades,
    }
