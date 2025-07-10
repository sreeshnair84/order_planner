import logging

# Configure logging FIRST, before any other imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Disable SQLAlchemy info logging by setting to ERROR level
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.orm').setLevel(logging.ERROR)

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from app.database.connection import init_db
from app.api import auth, orders, tracking, files, trips, logistics, management, manufacturers, email_management, ai_agent, enhanced_order_processing
from app.utils.config import settings
import os

logger = logging.getLogger(__name__)

# HTTPS Redirect Middleware
class HTTPSRedirectMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Check if we're running in Azure Container Apps and request is HTTP
            if (
                request.url.scheme == "http" 
                and request.headers.get("host", "").endswith(".azurecontainerapps.io")
                and os.getenv("ENVIRONMENT", "development") == "production"
            ):
                # Redirect to HTTPS version
                https_url = str(request.url).replace("http://", "https://", 1)
                response = RedirectResponse(url=https_url, status_code=307)
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)

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

# Add HTTPS redirect middleware first (only in production)
if os.getenv("ENVIRONMENT", "development") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

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
app.include_router(orders.router, prefix="/api/requestedorders", tags=["Orders & Order Processing"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Tracking"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(trips.router, prefix="/api/trips", tags=["Trip Optimization"])
app.include_router(logistics.router, prefix="/api/logistics", tags=["Logistics & Analytics"])
app.include_router(management.router, prefix="/api/management", tags=["Management"])
app.include_router(manufacturers.router, prefix="/api", tags=["Manufacturers"])
app.include_router(email_management.router, prefix="/api", tags=["Email Management"])
app.include_router(ai_agent.router, tags=["AI Agent"])
app.include_router(enhanced_order_processing.router, tags=["Enhanced Order Processing"])

# Import and include analytics router
from app.api import analytics
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

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
