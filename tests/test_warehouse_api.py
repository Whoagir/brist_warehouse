import pytest
import asyncio
from uuid import uuid4
import httpx

# Определяем базовый URL нашего сервиса
BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_arrival_and_stock_check():
    """
    Интеграционный тест:
    1. Симулирует прибытие товара через API.
    2. Ждет обработки сообщения.
    3. Проверяет состояние склада через API.
    """
    # Уникальные ID для этого тестового запуска
    product_id = str(uuid4())
    warehouse_id = str(uuid4())
    movement_id = str(uuid4())
    initial_quantity = 100

    # Используем httpx.AsyncClient для асинхронных запросов
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        # --- Шаг 1: Симулируем прибытие товара ---
        arrival_payload = {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "quantity": initial_quantity,
            "movement_id": movement_id,
        }
        
        print(f"\n--> Отправка события 'Прибытие' для warehouse_id: {warehouse_id}")
        response = await client.post("/api/simulate/arrival", json=arrival_payload)
        
        # Проверяем, что запрос на симуляцию был принят
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["movement_id"] == movement_id
        print("--> Событие 'прибытие' успешно отправлено в Kafka.")

        # --- Шаг 2: Ждем обработки ---
        # Даем консьюмеру время на обработку сообщения из Kafka.
        # В реальном проекте здесь могла бы быть более сложная логика ожидания.
        print("--> Ожидание 5 секунд для обработки сообщения консьюмером...")
        await asyncio.sleep(5)

        # --- Шаг 3: Проверяем состояние склада ---
        print(f"--> Проверка остатков для warehouse_id: {warehouse_id}")
        response = await client.get(f"/api/warehouses/{warehouse_id}/products/{product_id}")

        # Проверяем, что API возвращает корректные данные
        assert response.status_code == 200
        stock_data = response.json()
        
        print(f"--> Получены данные со склада: {stock_data}")
        assert stock_data["warehouse_id"] == warehouse_id
        assert stock_data["product_id"] == product_id
        assert stock_data["quantity"] == initial_quantity
        
        print("--> Тест успешно пройден! Остатки на складе верны.")

