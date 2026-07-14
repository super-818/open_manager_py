"""targets模块测试"""
import pytest
from open_manager_py.targets import get_target_paths, list_targets


def test_list_targets_returns_dict():
    """测试目标列表"""
    targets = list_targets()
    assert isinstance(targets, dict)
    assert 'trae' in targets
    assert 'cursor' in targets
    assert 'claude-code' in targets


def test_get_target_paths_known_tool():
    """测试获取已知工具路径"""
    paths = get_target_paths(['trae', 'cursor'])
    assert len(paths) == 2


def test_get_target_paths_unknown_tool():
    """测试未知工具返回空"""
    paths = get_target_paths(['nonexistent_tool'])
    assert len(paths) == 0


def test_get_target_paths_custom():
    """测试自定义路径"""
    paths = get_target_paths([], custom_path='/tmp/test_skills')
    assert len(paths) == 1


def test_get_target_paths_mixed():
    """测试混合已知和未知工具"""
    paths = get_target_paths(['trae', 'unknown'], custom_path='/tmp/x')
    assert len(paths) == 2  # trae + custom


def test_list_targets_has_10_plus_tools():
    """测试支持10+个工具"""
    targets = list_targets()
    assert len(targets) >= 10
