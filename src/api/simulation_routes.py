from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from pydantic import BaseModel, Field

from src.models.warehouse import EventType
from src.services.kafka_producer_service import KafkaProducerService, kafka_producer_service

router = APIRouter(
    prefix="/api/simulate",
    tags=["Simulation"],
)

# --- Pydantic схемы для входящих данных ---

class SimulationRequest(BaseModel):
    """Базовая модель для запроса симуляции."""
    product_id: UUID = Field(..., description="ID продукта.")
    warehouse_id: UUID = Field(..., description="ID склада, где происходит событие.")
    quantity: int = Field(..., gt=0, description="Количество товара (должно быть больше 0).")
    movement_id: UUID | None = Field(None, description="Опциональный ID перемещения для связи событий.")

class SimulationResponse(BaseModel):
    """Модель ответа после успешной симуляции."""
    message: str
    movement_id: UUID
    message_id: UUID


# --- Эндпоинты ---

@router.post("/arrival", response_model=SimulationResponse, status_code=202)
async def simulate_arrival(
    request: SimulationRequest,
    producer: KafkaProducerService = Depends(lambda: kafka_producer_service)
):
    """
    Симулирует событие **прибытия** товара на склад.

    Отправляет сообщение в Kafka, которое будет обработано сервисом.
    Используйте этот эндпоинт для пополнения запасов на складе.
    """
    try:
        result = await producer.send_movement_event(
            event_type=EventType.arrival,
            product_id=request.product_id,
            warehouse_id=request.warehouse_id,
            quantity=request.quantity,
            movement_id=request.movement_id,
        )
        return SimulationResponse(
            message="Arrival event sent to Kafka successfully.",
            movement_id=result["movement_id"],
            message_id=result["message_id"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message to Kafka: {str(e)}")


@router.post("/departure", response_model=SimulationResponse, status_code=202)
async def simulate_departure(
    request: SimulationRequest,
    producer: KafkaProducerService = Depends(lambda: kafka_producer_service)
):
    """
    Симулирует событие **убытия** товара со склада.

    Отправляет сообщение в Kafka. Сервис проверит, достаточно ли товара
    на складе, прежде чем обновить остатки.
    """
    try:
        result = await producer.send_movement_event(
            event_type=EventType.departure,
            product_id=request.product_id,
            warehouse_id=request.warehouse_id,
            quantity=request.quantity,
            movement_id=request.movement_id,
        )
        return SimulationResponse(
            message="Departure event sent to Kafka successfully.",
            movement_id=result["movement_id"],
            message_id=result["message_id"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message to Kafka: {str(e)}")
