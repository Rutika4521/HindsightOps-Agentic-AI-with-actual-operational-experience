"""
FastAPI main application — Incident Memory Commander backend.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Import routers
from backend.api.incidents import router as incidents_router
from backend.api.memory import router as memory_router
from backend.api.demo import router as demo_router
from backend.api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Incident Memory Commander starting up...")
    logger.info(f"  HINDSIGHT_BASE_URL: {os.getenv('HINDSIGHT_BASE_URL', 'NOT SET')}")
    logger.info(f"  HINDSIGHT_BANK_ID:  {os.getenv('HINDSIGHT_BANK_ID', 'NOT SET')}")
    logger.info(f"  LLM_MODEL:          {os.getenv('LLM_MODEL', 'NOT SET')}")

    # Auto-create the Hindsight memory bank if it doesn't exist
    try:
        from backend.api.deps import get_hindsight_client
        client = get_hindsight_client()
        result = await client.ensure_bank_exists()
        if result.get("success"):
            logger.info(f"✓ Hindsight bank ready: {result.get('bank_id')}")
        else:
            logger.warning(f"Bank setup warning: {result.get('error')}")
    except Exception as e:
        logger.warning(f"Could not auto-create Hindsight bank (may already exist): {e}")

    yield
    logger.info("Incident Memory Commander shutting down...")


app = FastAPI(
    title="Incident Memory Commander",
    description=(
        "An AI incident investigator that learns from what actually happened. "
        "Powered by Hindsight persistent memory."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(incidents_router, prefix="/api/incidents", tags=["incidents"])
app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
app.include_router(demo_router, prefix="/api/demo", tags=["demo"])
app.include_router(health_router, prefix="/api", tags=["health"])


@app.get("/")
async def root():
    return {
        "name": "Incident Memory Commander",
        "tagline": "An AI incident investigator that learns from what actually happened.",
        "version": "1.0.0",
        "docs": "/docs",
    }
