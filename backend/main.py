from contextlib import asynccontextmanager
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.market_stream import market_stream
from services.daily_report import daily_report_scheduler
from services.metrics import MetricsMiddleware
from routers import market, options, brain, backtest, signals, paper, auth, broker, misc, ws, ops, report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await market_stream.start()
    await daily_report_scheduler.start()
    yield
    market_stream.stop()
    daily_report_scheduler.stop()


app = FastAPI(title="QUANTUM NEXUS API", version="2.0.0", lifespan=lifespan)

# Enable CORS for live Vercel & local connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(MetricsMiddleware)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}


for _router in (
    market.router,
    options.router,
    brain.router,
    backtest.router,
    signals.router,
    paper.router,
    auth.router,
    broker.router,
    misc.router,
    ws.router,
    ops.router,
    report.router,
):
    app.include_router(_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
