import enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Enum,
    PrimaryKeyConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class EventType(enum.Enum):
    arrival = "arrival"
    departure = "departure"


class Movement(Base):
    __tablename__ = "movements"

    id = Column(UUID(as_uuid=True), primary_key=True)
    movement_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Integer, nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    source_warehouse = Column(String)  # Для departure


class WarehouseStock(Base):
    __tablename__ = "warehouse_stocks"

    warehouse_id = Column(UUID(as_uuid=True), primary_key=True)
    product_id = Column(UUID(as_uuid=True), primary_key=True)
    quantity = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('warehouse_id', 'product_id'),
        CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
    )
