# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем netcat для скрипта wait-for-it
RUN apt-get update && apt-get install -y netcat-openbsd

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY ./src /app/src
COPY ./tests /app/tests

# Копируем и делаем исполняемым скрипт ожидания
COPY wait-for-it.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/wait-for-it.sh

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]