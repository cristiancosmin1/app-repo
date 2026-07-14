import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import Base, engine, get_db
from app.security import require_roles


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Shopping App",
    version="2.0.0",
)


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


logger = logging.getLogger("shopping-app")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


@app.middleware("http")
async def request_context_middleware(
    request: Request,
    call_next,
) -> Response:
    correlation_id = (
        request.headers.get("X-Correlation-Id")
        or str(uuid.uuid4())
    )

    run_id = request.headers.get("X-Run-Id", "")

    request.state.correlation_id = correlation_id
    request.state.run_id = run_id

    started_at = time.perf_counter()

    try:
        response = await call_next(request)
        status_code = response.status_code
        error_class = None

    except Exception as exc:
        status_code = 500
        error_class = exc.__class__.__name__

        latency_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        logger.exception(
            json.dumps(
                {
                    "timestamp": time.time(),
                    "service": "shopping-app",
                    "env": "local",
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "status_code": status_code,
                    "error_class": error_class,
                    "latency_ms": latency_ms,
                    "path": request.url.path,
                    "method": request.method,
                }
            )
        )

        raise

    latency_ms = round(
        (time.perf_counter() - started_at) * 1000,
        2,
    )

    response.headers["X-Correlation-Id"] = correlation_id

    logger.info(
        json.dumps(
            {
                "timestamp": time.time(),
                "service": "shopping-app",
                "env": "local",
                "run_id": run_id,
                "correlation_id": correlation_id,
                "status_code": status_code,
                "error_class": error_class,
                "latency_ms": latency_ms,
                "path": request.url.path,
                "method": request.method,
            }
        )
    )

    return response


def log_authorized_action(
    request: Request,
    user: dict[str, Any],
    action: str,
) -> None:
    logger.info(
        json.dumps(
            {
                "timestamp": time.time(),
                "service": "shopping-app",
                "env": "local",
                "event": "authorized_action",
                "action": action,
                "username": user.get("username"),
                "roles": user.get("roles", []),
                "run_id": getattr(request.state, "run_id", ""),
                "correlation_id": getattr(
                    request.state,
                    "correlation_id",
                    "",
                ),
            }
        )
    )


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(
    "/items",
    response_model=list[schemas.ItemResponse],
)
def get_items(
    request: Request,
    db: Session = Depends(get_db),
    user: dict[str, Any] = Depends(
        require_roles("reader", "writer", "admin")
    ),
):
    log_authorized_action(
        request=request,
        user=user,
        action="list_items",
    )

    return (
        db.query(models.Item)
        .order_by(models.Item.id)
        .all()
    )


@app.post(
    "/items",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(
    item: schemas.ItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict[str, Any] = Depends(
        require_roles("writer", "admin")
    ),
):
    db_item = models.Item(
        name=item.name,
        quantity=item.quantity,
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    log_authorized_action(
        request=request,
        user=user,
        action="create_item",
    )

    return db_item


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: dict[str, Any] = Depends(
        require_roles("admin")
    ),
):
    db_item = (
        db.query(models.Item)
        .filter(models.Item.id == item_id)
        .first()
    )

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    db.delete(db_item)
    db.commit()

    log_authorized_action(
        request=request,
        user=user,
        action="delete_item",
    )

    return None
