import logging
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.warehouse import Movement, EventType, WarehouseStock
from sqlalchemy.future import select
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class WarehouseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_movement(self, message: dict):
        logger.info(f"Processing movement: {message}")
        try:
            data = message.get("data", {})
            event_type = EventType(data.get("event"))

            movement = Movement(
                id=UUID(message.get("id")),
                movement_id=UUID(data.get("movement_id")),
                warehouse_id=UUID(data.get("warehouse_id")),
                product_id=UUID(data.get("product_id")),
                quantity=data.get("quantity"),
                event_type=event_type,
                timestamp=datetime.fromisoformat(data.get("timestamp").replace("Z", "+00:00")).replace(tzinfo=None),
                source_warehouse=message.get("source") if event_type == EventType.departure else None,
            )

            await self._update_stock(movement)

            self.session.add(movement)
            await self.session.commit()
            logger.info(f"Movement {movement.id} processed and committed.")

        except Exception as e:
            logger.error(f"Failed to process movement: {e}", exc_info=True)
            await self.session.rollback()
            raise

    async def _update_stock(self, movement: Movement):
        # Используем for_update для блокировки строки на время транзакции
        stmt = select(WarehouseStock).where(
            and_(
                WarehouseStock.warehouse_id == movement.warehouse_id,
                WarehouseStock.product_id == movement.product_id
            )
        ).with_for_update()

        result = await self.session.execute(stmt)
        stock = result.scalars().first()

        if movement.event_type == EventType.arrival:
            if stock:
                stock.quantity += movement.quantity
                stock.last_updated = datetime.utcnow()
            else:
                stock = WarehouseStock(
                    warehouse_id=movement.warehouse_id,
                    product_id=movement.product_id,
                    quantity=movement.quantity,
                    last_updated=datetime.utcnow(),
                )
                self.session.add(stock)
            logger.info(f"Stock for product {movement.product_id} on warehouse {movement.warehouse_id} updated: +{movement.quantity}")

        elif movement.event_type == EventType.departure:
            if not stock or stock.quantity < movement.quantity:
                logger.error(f"Insufficient stock for product {movement.product_id} on warehouse {movement.warehouse_id}.")
                raise ValueError("Insufficient stock for departure.")
            
            stock.quantity -= movement.quantity
            stock.last_updated = datetime.utcnow()
            logger.info(f"Stock for product {movement.product_id} on warehouse {movement.warehouse_id} updated: -{movement.quantity}")


    async def get_movement_details(self, movement_id: UUID) -> dict:
        """
        Получает детали перемещения по его ID.

        Ищет связанные события отправки и прибытия, вычисляет время в пути
        и разницу в количестве.
        """
        stmt = select(Movement).where(Movement.movement_id == movement_id)
        result = await self.session.execute(stmt)
        movements = result.scalars().all()

        if not movements:
            return None

        departure = next((m for m in movements if m.event_type == EventType.departure), None)
        arrival = next((m for m in movements if m.event_type == EventType.arrival), None)

        if not departure and not arrival:
            return None # Не должно произойти, но для надежности

        # Собираем ответ, даже если одно из событий отсутствует
        response_data = {
            "movement_id": movement_id,
            "product_id": departure.product_id if departure else arrival.product_id,
            "source_warehouse": departure.source_warehouse if departure else None,
            "destination_warehouse": arrival.warehouse_id if arrival else None,
            "quantity_sent": departure.quantity if departure else None,
            "quantity_received": arrival.quantity if arrival else None,
            "time_in_transit": None,
            "quantity_difference": None,
        }

        if departure and arrival:
            response_data["time_in_transit"] = arrival.timestamp - departure.timestamp
            # Разница: > 0 = недостача, < 0 = излишек
            response_data["quantity_difference"] = departure.quantity - arrival.quantity

        return response_data

