from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import auth, interview, jd, report, resume
from src.core.config import settings
from src.core.logger import logger
from src.db.milvus import connect_milvus
from src.db.postgres import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting {}", settings.app_name)
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as exc:
        logger.warning("Database init skipped: {}", exc)
    try:
        connect_milvus()
    except Exception as exc:
        logger.warning("Milvus init skipped: {}", exc)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = settings.api_prefix

app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["auth"])
app.include_router(resume.router, prefix=f"{api_prefix}/resumes", tags=["resume"])
app.include_router(jd.router, prefix=f"{api_prefix}/jd", tags=["jd"])
app.include_router(
    interview.router, prefix=f"{api_prefix}/interviews", tags=["interview"]
)
app.include_router(report.router, prefix=f"{api_prefix}/reports", tags=["report"])


@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok", "app": settings.app_name})
