from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.backtest_service import run_backtest

router = APIRouter()


class BacktestRequest(BaseModel):
    stock_code: str = Field(..., examples=["0056"])
    start_date: str = Field(..., examples=["2020-01-01"])
    end_date: str = Field(..., examples=["2024-12-31"])
    buy_threshold: float = Field(5, ge=0)
    stop_loss: float = Field(-3, le=0)
    take_profit: float = Field(6, ge=0)
    initial_capital: float = Field(100000, gt=0)


@router.post("/run")
async def run(body: BacktestRequest):
    try:
        result = run_backtest(
            stock_code=body.stock_code,
            start_date=body.start_date,
            end_date=body.end_date,
            buy_threshold=body.buy_threshold,
            stop_loss=body.stop_loss,
            take_profit=body.take_profit,
            initial_capital=body.initial_capital,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回測執行錯誤：{str(e)}")
