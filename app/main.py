from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import Base, engine, get_db


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Shopping App",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(
    "/items",
    response_model=list[schemas.ItemResponse],
)
def get_items(db: Session = Depends(get_db)):
    return db.query(models.Item).order_by(models.Item.id).all()


@app.post(
    "/items",
    response_model=schemas.ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
):
    db_item = models.Item(
        name=item.name,
        quantity=item.quantity,
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
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

    return None
