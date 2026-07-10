from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemCreate(BaseModel):
    name: str
    quantity: int


class ItemResponse(BaseModel):
    id: int
    name: str
    quantity: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
