"""logger模块测试"""
import pytest
from pathlib import Path
from open_manager_py.logger import get_logger


def test_logger_returns_logger_instance():
    """测试获取logger实例"""
    logger = get_logger()
    assert logger is not None


def test_logger_is_singleton():
    """测试logger是单例"""
    logger1 = get_logger()
    logger2 = get_logger()
    assert logger1 is logger2


def test_logger_has_handlers():
    """测试logger有处理器"""
    logger = get_logger()
    assert len(logger.handlers) >= 2  # 文件+控制台
