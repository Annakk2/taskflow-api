import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.logging_config import configure_logging
from app.metrics import Timer, metrics
from app.routers import projects, tasks, users
from app.utils.exceptions import DuplicateError, NotFoundError

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TaskFlow API starting up")
    yield
    logger.info("TaskFlow API shutting down")


app = FastAPI(
    title="TaskFlow API",
    description="A small, professionally structured REST backend for managing users, projects, and tasks.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    endpoint = f"{request.method} {request.url.path}"
    with Timer() as timer:
        response = await call_next(request)
    metrics.record_request(endpoint, timer.duration_ms, is_error=response.status_code >= 400)
    return response


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(DuplicateError)
async def duplicate_handler(request: Request, exc: DuplicateError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak internal stack traces / exception details through the API.
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["observability"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/metrics", tags=["observability"])
def get_metrics() -> dict:
    return metrics.snapshot()
