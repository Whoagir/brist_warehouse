import asyncio
import json
import logging
from uuid import uuid4, UUID
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer
from src.core.config import settings
from src.models.warehouse import EventType

logger = logging.getLogger(__name__)


class KafkaProducerService:
    def __init__(self, bootstrap_servers: str):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',  # Гарантирует, что сообщение получено всеми репликами
        )
        self._is_running = False

    async def start(self):
        """Запускает продюсера Kafka."""
        if self._is_running:
            logger.warning("KafkaProducerService is already running.")
            return
        logger.info("Starting KafkaProducerService...")
        await self._producer.start()
        self._is_running = True
        logger.info("KafkaProducerService started successfully.")

    async def stop(self):
        """Останавливает продюсера Kafka."""
        if not self._is_running:
            logger.warning("KafkaProducerService is not running.")
            return
        logger.info("Stopping KafkaProducerService...")
        await self._producer.stop()
        self._is_running = False
        logger.info("KafkaProducerService stopped successfully.")

    async def send_movement_event(
        self,
        event_type: EventType,
        product_id: UUID,
        quantity: int,
        warehouse_id: UUID,
        movement_id: UUID = None,
    ):
        """
        Создает и отправляет событие перемещения товара в топик Kafka.
        """
        if not self._is_running:
            raise RuntimeError("KafkaProducerService is not running. Call start() first.")

        # Если movement_id не предоставлен, генерируем новый
        if movement_id is None:
            movement_id = uuid4()

        message_id = uuid4()
        event_time = datetime.now(timezone.utc)

        # Определяем источник и тему сообщения в зависимости от типа события
        if event_type == EventType.arrival:
            source_warehouse = "EXTERNAL" # Условный внешний источник
            subject = f"{warehouse_id}:ARRIVAL"
        else: # departure
            source_warehouse = f"WH-{warehouse_id.hex[:4].upper()}" # Генерируем имя склада
            subject = f"{source_warehouse}:DEPARTURE"

        message = {
            "id": str(message_id),
            "source": source_warehouse,
            "specversion": "1.0",
            "type": "ru.retail.warehouses.movement",
            "datacontenttype": "application/json",
            "dataschema": "ru.retail.warehouses.movement.v1.0",
            "time": int(event_time.timestamp() * 1000),
            "subject": subject,
            "destination": "ru.retail.warehouses",
            "data": {
                "movement_id": str(movement_id),
                "warehouse_id": str(warehouse_id),
                "timestamp": event_time.isoformat().replace("+00:00", "Z"),
                "event": event_type.value,
                "product_id": str(product_id),
                "quantity": quantity,
            },
        }

        try:
            logger.info(f"Sending message to Kafka: {message}")
            await self._producer.send_and_wait(settings.KAFKA_TOPIC, value=message)
            logger.info(f"Message {message_id} sent successfully to topic {settings.KAFKA_TOPIC}.")
            return {"movement_id": movement_id, "message_id": message_id}
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}", exc_info=True)
            raise

# Синглтон для нашего продюсера
kafka_producer_service = KafkaProducerService(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
