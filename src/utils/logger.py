# src/utils/logger.py
"""
Sistema de logging configurado para o DJE Scraper
"""

import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str = "dje_scraper",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configura e retorna logger para o sistema
    
    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Arquivo específico de log (opcional)
    
    Returns:
        Logger configurado
    """
    
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Nome do arquivo de log
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = f"logs/dje_scraper_{timestamp}.log"
    
    # Configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para console (apenas INFO e acima)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Só warnings e erros no console
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Logger configurado: {name} -> {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retorna logger específico para um módulo
    
    Args:
        name: Nome do módulo (__name__)
    
    Returns:
        Logger do módulo
    """
    return logging.getLogger(f"dje_scraper.{name}")


class LoggerMixin:
    """Mixin para adicionar logging a classes"""
    
    @property
    def logger(self) -> logging.Logger:
        """Logger da classe"""
        return get_logger(self.__class__.__module__)


def log_function_call(func):
    """Decorator para logar chamadas de função"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Chamando {func.__name__} com args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} executada com sucesso")
            return result
        except Exception as e:
            logger.error(f"Erro em {func.__name__}: {e}")
            raise
    
    return wrapper


def log_execution_time(func):
    """Decorator para logar tempo de execução"""
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