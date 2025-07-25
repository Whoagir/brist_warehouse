import json
from aiokafka import AIOKafkaConsumer
from src.core.config import settings
from src.services.warehouse_service import WarehouseService
import logging

logger = logging.getLogger(__name__)


class WarehouseKafkaConsumer:
    def __init__(self, session_factory):
        self.consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id="warehouse_group",
            api_version="auto"
        )
        self.session_factory = session_factory

    async def start(self):
        logger.info("Starting Kafka consumer...")
        await self.consumer.start()
        try:
            async for msg in self.consumer:
                logger.info(f"Received message: {msg.value}")
                try:
                    async with self.session_factory() as session:
                        service = WarehouseService(session)
                        await service.process_movement(msg.value)
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
        finally:
            logger.info("Stopping Kafka consumer...")
            await self.consumer.stop()

    async def stop(self):
        await self.consumer.stop()
