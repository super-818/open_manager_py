"""pytest公共配置和fixtures"""
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture(autouse=True)
def reset_singletons(monkeypatch, tmp_path):
    """每个测试前重置单例,避免状态泄漏"""
    # 重置数据库
    import open_manager_py.database as db_module
    monkeypatch.setattr(db_module, '_db_instance', None)

    # 重置配置 - 指向临时目录避免污染真实数据
    import open_manager_py.config as config_module
    monkeypatch.setattr(config_module, '_config_instance', None)

    # 重置扫描器
    import open_manager_py.scanner as scanner_module
    monkeypatch.setattr(scanner_module, '_scanner_instance', None)

    # 重置logger
    import open_manager_py.logger as logger_module
    monkeypatch.setattr(logger_module, '_logger_instance', None)

    yield
