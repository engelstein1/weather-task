import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.database.db_initializer import initialize_database


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Weather Data Service",
    description="Weather data analysis service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# @app.on_event("startup")
# async def startup_event():
#     """Initialize database on startup"""
#     try:
#         if not initialize_database():
#             logger.error("Database initialization failed")
#     except Exception as e:
#         logger.error(f"Startup error: {e}")
#         raise

