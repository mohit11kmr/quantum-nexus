"""AI Brain routes: status, scenarios, async optimize, LSTM."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.stock_data import fetch_stock_data, generate_synthetic_stock_data, STOCK_UNIVERSE
from services.volume_analytics import compute_volume_metrics
from services.scenario_generator import evaluate_and_rank_scenarios
from services.learning_brain import (
    learning_brain,
    predict_ml_win_probability,
    train_brain_model,
    get_volume_brain_status,
    train_lstm_model,
    predict_lstm_direction,
    get_lstm_brain_status,
)
from services.task_manager import task_manager

router = APIRouter()

DEFAULT_LIGHT_SYMBOLS = 8
DEFAULT_LIGHT_EPOCHS = 12
FULL_SYMBOLS = 16
FULL_EPOCHS = 30


class OptimizeRequest(BaseModel):
    light: bool = True
    symbols: int = DEFAULT_LIGHT_SYMBOLS
    epochs: int = DEFAULT_LIGHT_EPOCHS


@router.get("/api/brain/status")
def get_brain_status():
    return learning_brain.get_brain_status()


@router.get("/api/brain/volume/status")
def get_volume_brain_status_endpoint():
    return get_volume_brain_status()


@router.post("/api/brain/volume/predict")
def predict_volume_brain(payload: Dict[str, Any] = {}):
    return predict_ml_win_probability(
        surge_ratio=float(payload.get("surge_ratio", 1.5)),
        cmf=float(payload.get("cmf", 0.1)),
        obv_trend=str(payload.get("obv_trend", "RISING")),
    )


@router.get("/api/brain/scenarios")
def get_brain_scenarios(symbol: str = "RELIANCE.NS"):
    df = fetch_stock_data(symbol, period="1y", interval="1d")
    if df.empty or len(df) < 40:
        df = generate_synthetic_stock_data(symbol, days=250)
    res = evaluate_and_rank_scenarios(df, symbol)
    res["dataSource"] = df.attrs.get("dataSource", "unknown")
    return res


def _run_optimize(light: bool, symbols: int, epochs: int) -> Dict[str, Any]:
    """Blocking training job executed inside a task_manager daemon thread."""
    n = min(max(2, int(symbols)), len(STOCK_UNIVERSE))
    stocks_dict = {}
    for item in STOCK_UNIVERSE[:n]:
        sym = item["symbol"]
        df = fetch_stock_data(sym, period="6mo", interval="1d")
        if df.empty or len(df) < 25:
            df = generate_synthetic_stock_data(sym, days=120)
        stocks_dict[sym] = compute_volume_metrics(df)
    rf_res = train_brain_model(stocks_dict)
    lstm_res = train_lstm_model(stocks_dict, epochs=max(1, int(epochs)))
    return {"randomForest": rf_res, "lstm": lstm_res}


@router.post("/api/brain/optimize")
def optimize_brain(req: Optional[OptimizeRequest] = None):
    """Submit training as a background task; returns immediately with a task_id.

    light=True (default) trains 8 symbols / 12 LSTM epochs so the Render free
    tier completes within seconds instead of hanging the single worker.
    """
    req = req or OptimizeRequest()
    symbols = req.symbols if not req.light else min(req.symbols, DEFAULT_LIGHT_SYMBOLS)
    epochs = req.epochs if not req.light else min(req.epochs, DEFAULT_LIGHT_EPOCHS)
    task_id = task_manager.submit(_run_optimize, req.light, symbols, epochs)
    return {
        "task_id": task_id,
        "status": "QUEUED",
        "light": req.light,
        "symbols": symbols,
        "epochs": epochs,
        "poll_endpoint": f"/api/brain/tasks/{task_id}",
    }


@router.get("/api/brain/tasks")
def list_tasks(limit: int = 20):
    return {"tasks": task_manager.list_tasks(limit)}


@router.get("/api/brain/tasks/{task_id}")
def get_task(task_id: str):
    task = task_manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/api/brain/lstm/status")
def get_lstm_status():
    return get_lstm_brain_status()


@router.get("/api/brain/lstm/predict")
def predict_lstm(symbol: str = "RELIANCE.NS"):
    df = fetch_stock_data(symbol, period="3mo", interval="1d")
    if df.empty or len(df) < 30:
        df = generate_synthetic_stock_data(symbol, days=90)
    df = compute_volume_metrics(df)
    res = predict_lstm_direction(df)
    res["symbol"] = symbol
    res["dataSource"] = df.attrs.get("dataSource", "unknown")
    return res


@router.post("/api/brain/predict")
def predict_brain(features: Dict[str, Any] = {}):
    return learning_brain.predict_win_probability(features)
