import os
import json
import uuid
import time
from datetime import datetime, timezone
import argparse
from kafka import KafkaProducer
from kafka.errors import KafkaError

# --- Настройки ---
KAFKA_BROKER = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:29092')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'warehouse-movements')

# --- Тестовые данные ---
# Используем константы, чтобы было легко проверять API
TEST_WAREHOUSE_ID = "c1d70455-7e14-11e9-812a-70106f431230"
TEST_PRODUCT_ID = "4705204f-498f-4f96-b4ba-df17fb56bf55"

def create_message(event_type: str, quantity: int, movement_id: str):
    """Генерирует тестовое сообщение для Kafka."""
    if not movement_id:
        movement_id = str(uuid.uuid4())

    source_wh = "WH-3322" if event_type == "departure" else "WH-3423"
    subject = f"{source_wh}:{event_type.upper()}"

    message = {
        "id": str(uuid.uuid4()),
        "source": source_wh,
        "specversion": "1.0",
        "type": "ru.retail.warehouses.movement",
        "datacontenttype": "application/json",
        "dataschema": "ru.retail.warehouses.movement.v1.0",
        "time": int(time.time() * 1000),
        "subject": subject,
        "destination": "ru.retail.warehouses",
        "data": {
            "movement_id": movement_id,
            "warehouse_id": TEST_WAREHOUSE_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "product_id": TEST_PRODUCT_ID,
            "quantity": quantity
        }
    }
    return message

def send_message(producer, topic, message):
    """Отправляет сообщение в Kafka и выводит полезную информацию."""
    try:
        future = producer.send(topic, value=json.dumps(message).encode('utf-8'))
        record_metadata = future.get(timeout=10)
        
        print("\n--- ✅ Сообщение успешно отправлено! ---")
        print(f"Топик: {record_metadata.topic}, Партиция: {record_metadata.partition}, Offset: {record_metadata.offset}")
        
        data = message['data']
        movement_id = data['movement_id']
        warehouse_id = data['warehouse_id']
        product_id = data['product_id']
        
        print("\n--- 🔍 Данные для проверки API ---")
        print(f"Movement ID: {movement_id}")
        print(f"Warehouse ID: {warehouse_id}")
        print(f"Product ID: {product_id}")
        
        print("\n--- 📋 Готовые команды для curl ---")
        print("# Проверить состояние склада:")
        print(f"curl http://localhost:8000/api/warehouses/{warehouse_id}/products/{product_id} | jq")
        print("\n# Проверить детали перемещения:")
        print(f"curl http://localhost:8000/api/movements/{movement_id} | jq")
        print("-------------------------------------\n")

    except KafkaError as e:
        print(f"--- ❌ Ошибка при отправке сообщения: {e} ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Отправка тестовых сообщений в Kafka.")
    parser.add_argument('event', type=str, choices=['arrival', 'departure'], help="Тип события: 'arrival' или 'departure'")
    parser.add_argument('quantity', type=int, help="Количество товара")
    parser.add_argument('--movement_id', type=str, default=None, help="Опционально: существующий movement_id для связки событий")

    args = parser.parse_args()

    kafka_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
    msg = create_message(args.event, args.quantity, args.movement_id)
    send_message(kafka_producer, KAFKA_TOPIC, msg)
    kafka_producer.flush()
    kafka_producer.close()