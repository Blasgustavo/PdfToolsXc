import logging
import sys
import traceback
import platform
import os
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

APP_VERSION = "1.0.0"

def setup_logger(name: str = "PdfToolsXc") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger
    
    log_file = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("=" * 60)
    logger.info(f"[{name}] v{APP_VERSION} - Inicio de sesion")
    logger.info("=" * 60)
    logger.info(f"Plataforma: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Directorio de trabajo: {os.getcwd()}")
    logger.info(f"Directorio de logs: {LOG_DIR}")
    logger.info("=" * 60)
    
    return logger

logger = setup_logger()

def log_exception(e: Exception, context: str = ""):
    exc_type = type(e).__name__
    exc_msg = str(e)
    exc_trace = "".join(traceback.format_tb(e.__traceback__))
    
    if context:
        logger.error(f"[ERROR] {context} | {exc_type}: {exc_msg}\n{exc_trace}")
    else:
        logger.error(f"[ERROR] Excepcion | {exc_type}: {exc_msg}\n{exc_trace}")

def log_module_load(module_name: str, status: str = "OK"):
    if status == "OK":
        logger.info(f"Modulo cargado: {module_name}")
    else:
        logger.warning(f"Modulo no encontrado: {module_name} ({status})")

def log_ui_event(event: str, details: str = ""):
    if details:
        logger.debug(f"UI: {event} | {details}")
    else:
        logger.debug(f"UI: {event}")

def log_file_operation(operation: str, filepath: str, status: str = "OK"):
    filename = Path(filepath).name
    if status == "OK":
        logger.info(f"Archivo {operation}: {filename}")
    else:
        logger.error(f"Error en archivo {operation}: {filename} | {status}")
