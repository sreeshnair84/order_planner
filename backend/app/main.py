from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import logging
from app.database.connection import init_db
from app.api import auth, orders, tracking, files, trips, logistics, order_processing, management, manufacturers, email_management
from app.utils.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Order Management System...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Order Management System...")

app = FastAPI(
    title="Order Management System",
    description="A web-based order management system for FMCG/OEM providers",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(order_processing.router, tags=["Order Processing"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Tracking"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(trips.router, prefix="/api/trips", tags=["Trip Optimization"])
app.include_router(logistics.router, prefix="/api/logistics", tags=["Logistics & Analytics"])
app.include_router(management.router, prefix="/api/management", tags=["Management"])
app.include_router(manufacturers.router, prefix="/api", tags=["Manufacturers"])
app.include_router(email_management.router, prefix="/api", tags=["Email Management"])

@app.get("/")
async def root():
    return {"message": "Order Management System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-07-05T00:00:00Z"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
