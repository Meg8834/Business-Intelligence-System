from fastapi import FastAPI
from sqlalchemy import text
from database.db_config import engine
from fastapi.middleware.cors import CORSMiddleware

# ── Import all routers ──────────────────────────────────────────
from routes.upload_routes import router as upload_router
from routes.forecast_routes import router as forecast_router
from routes.anomaly_routes import router as anomaly_router
from routes.simulation_routes import router as simulation_router
from routes.health_routes import router as health_router

app = FastAPI(title="Business Decision Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────────────
app.include_router(upload_router, tags=["Upload"])
app.include_router(forecast_router, tags=["Forecast"])
app.include_router(anomaly_router, tags=["Anomaly"])
app.include_router(simulation_router, tags=["Simulation"])
app.include_router(health_router, tags=["Health"])


# ── Existing endpoints ───────────────────────────────────────────
@app.get("/", tags=["Root"])
def home():
    return {"message": "Business Intelligence System API Running"}


@app.get("/business-data", tags=["Data"])
def get_business_data():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM business_data ORDER BY id ASC"))
        rows = [dict(row._mapping) for row in result]
    return rows