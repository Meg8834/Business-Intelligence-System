from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── All routers ───────────────────────────────────────────────────
from routes.auth_routes       import router as auth_router
from routes.upload_routes     import router as upload_router
from routes.forecast_routes   import router as forecast_router
from routes.anomaly_routes    import router as anomaly_router
from routes.simulation_routes import router as simulation_router
from routes.health_routes     import router as health_router
from routes.chat_routes       import router as chat_router
from routes.report_routes     import router as report_router
from routes.email_routes      import router as email_router
from routes.tips_routes       import router as tips_router
from routes.sample_routes     import router as sample_router
from routes.admin_routes      import router as admin_router

app = FastAPI(
    title="Business Decision Intelligence API",
    version="2.0.0",
    description="ML-powered business analytics with multi-user support."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all routers ──────────────────────────────────────────
app.include_router(auth_router,       tags=["Authentication"])
app.include_router(upload_router,     tags=["Upload"])
app.include_router(forecast_router,   tags=["Forecast"])
app.include_router(anomaly_router,    tags=["Anomaly"])
app.include_router(simulation_router, tags=["Simulation"])
app.include_router(health_router,     tags=["Health"])
app.include_router(chat_router,       tags=["AI Chat"])
app.include_router(report_router,     tags=["Report"])
app.include_router(email_router,      tags=["Email"])
app.include_router(tips_router,       tags=["Tips"])
app.include_router(sample_router,     tags=["Sample"])
app.include_router(admin_router,      tags=["Admin"])


@app.get("/", tags=["Root"])
def home():
    return {
        "message": "Business Decision Intelligence System API v2.0",
        "status": "running",
        "endpoints": {
            "auth":       ["/auth/register", "/auth/login", "/auth/me"],
            "data":       ["/business-data", "/upload", "/sample-csv"],
            "ml":         ["/forecast", "/anomaly", "/simulate", "/health", "/tips"],
            "ai":         ["/chat"],
            "reports":    ["/report/download", "/email/alert"],
            "admin":      ["/admin/users", "/admin/overview"],
        }
    }