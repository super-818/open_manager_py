"""updater模块测试"""
import pytest
from unittest.mock import patch, MagicMock
from open_manager_py.updater import UpdateChecker


def test_update_checker_can_be_instantiated():
    """测试更新检测器可实例化"""
    checker = UpdateChecker()
    assert checker is not None


def test_check_invalid_url_returns_none():
    """测试无效URL返回None"""
    checker = UpdateChecker()
    result = checker._get_remote_commit('https://github.com/nonexistent/repo_xyz')
    assert result is None


def test_check_empty_url_returns_none():
    """测试空URL返回None"""
    checker = UpdateChecker()
    result = checker._get_remote_commit('')
    assert result is None


def test_check_none_url_returns_none():
    """测试None URL返回None"""
    checker = UpdateChecker()
    result = checker._get_remote_commit(None)
    assert result is None


def test_check_projects_returns_dict(monkeypatch):
    """测试check_projects返回字典(使用空数据库避免真实git操作)"""
    checker = UpdateChecker()
    # mock数据库返回空列表,避免真实git操作
    monkeypatch.setattr(checker.db, 'get_all_projects', lambda: [])
    result = checker.check_projects()
    assert isinstance(result, dict)
    assert 'total' in result
    assert 'has_update' in result
    assert 'up_to_date' in result
    assert 'errors' in result
    assert 'details' in result
    assert result['total'] == 0
