from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID


class MovementResponse(BaseModel):
    movement_id: UUID
    source_warehouse: Optional[str] = None
    destination_warehouse: Optional[UUID] = None
    product_id: UUID
    quantity_sent: Optional[int] = None
    quantity_received: Optional[int] = None
    time_in_transit: Optional[timedelta] = None
    quantity_difference: Optional[int] = None

    class Config:
        from_attributes = True


class WarehouseStockResponse(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    quantity: int
    last_updated: datetime

    class Config:
        from_attributes = True
