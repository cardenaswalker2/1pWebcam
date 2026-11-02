import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO) -> logging.Logger:
    """
    Configura el sistema de registro con rotación de archivos y salida a consola.
    Evita la duplicación de handlers y protege contra escritura descontrolada.
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "vision_inspection.log")

    logger = logging.getLogger("vision_inspection")
    logger.setLevel(log_level)

    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Handler de archivo con rotación: máx 5MB, hasta 3 archivos de respaldo
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

        # Handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    return logger

def sanitize_url_for_logging(url: str) -> str:
    """
    Oculta credenciales si la URL contiene user:pass@host.
    """
    if "@" in url and "://" in url:
        try:
            proto, rest = url.split("://", 1)
            _, host = rest.split("@", 1)
            return f"{proto}://***:***@{host}"
        except Exception:
            return "***"
    return url
