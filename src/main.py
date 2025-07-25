import logging
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from src.core.database import init_db, async_session
from src.services.kafka_consumer import WarehouseKafkaConsumer
from src.services.kafka_producer_service import kafka_producer_service
from src.api import routes as warehouse_routes
from src.api import simulation_routes
from src.core.logging_config import setup_logging

# Настраиваем логирование
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    """
    logger.info("Application startup...")

    # Инициализация базы данных
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")

    # Запуск Kafka Producer
    await kafka_producer_service.start()

    # Запуск Kafka Consumer в фоновом режиме
    consumer = WarehouseKafkaConsumer(session_factory=async_session)
    consumer_task = asyncio.create_task(consumer.start())
    
    yield
    
    logger.info("Application shutdown...")
    # Остановка Kafka Consumer
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("Kafka consumer task successfully cancelled.")
    
    # Остановка Kafka Producer
    await kafka_producer_service.stop()


app = FastAPI(
    title="Warehouse Monitoring Service",
    description="Сервис для мониторинга состояния складов через обработку событий Kafka.",
    version="1.0.0",
    lifespan=lifespan,
)

# Подключаем роутеры
app.include_router(warehouse_routes.router)
app.include_router(simulation_routes.router)

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Проверяет работоспособность сервиса.
    """
    return {"status": "ok"}
