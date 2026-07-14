"""日志模块 - 提供统一的日志记录功能"""
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import get_config


_logger_instance: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """获取全局logger实例,支持文件轮转和控制台输出"""
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    config = get_config()
    log_dir = config.get_log_dir()
    log_file = log_dir / "open_manager.log"

    logger = logging.getLogger("open_manager")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []

    # 文件处理器(轮转,单文件1MB,保留3个)
    file_handler = RotatingFileHandler(
        str(log_file), maxBytes=1024 * 1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))
    logger.addHandler(file_handler)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_handler)

    _logger_instance = logger
    return logger
