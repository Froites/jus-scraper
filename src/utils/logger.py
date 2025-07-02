import logging
import os
from datetime import datetime
from typing import Optional

def setup_logger(
    name: str = "dje_scraper",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = f"logs/dje_scraper_{timestamp}.log"
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    if logger.handlers:
        return logger
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    return logger

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"dje_scraper.{name}")

class LoggerMixin:
    @property
    def logger(self) -> logging.Logger:
        return get_logger(self.__class__.__module__)

def log_function_call(func):
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Chamando {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} executada com sucesso")
            return result
        except Exception as e:
            logger.error(f"Erro em {func.__name__}: {e}")
            raise
    return wrapper

def log_execution_time(func):
    import time
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executada em {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} falhou após {execution_time:.2f}s: {e}")
            raise
    return wrapper