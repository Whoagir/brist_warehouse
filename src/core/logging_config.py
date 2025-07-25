import logging
import sys
from logging.handlers import RotatingFileHandler
import os


LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

def setup_logging():
    """Настраивает базовое логирование."""
    
    # Получаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Удаляем все существующие обработчики, чтобы избежать дублирования
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(console_handler)

    # Обработчик для записи в файл с ротацией
    # 5 MB на файл, храним 5 последних файлов
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(file_handler)

    # Устанавливаем уровень INFO для основных библиотек, чтобы не засорять логи
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("aiokafka").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    logging.info("Logging configured successfully.")

