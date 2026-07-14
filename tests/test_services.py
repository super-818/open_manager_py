"""services模块测试"""
import pytest
from open_manager_py.services import SkillService, ProjectService


def test_skill_service_can_be_instantiated():
    """测试SkillService可实例化"""
    service = SkillService()
    assert service is not None


def test_project_service_can_be_instantiated():
    """测试ProjectService可实例化"""
    service = ProjectService()
    assert service is not None


def test_skill_service_search_returns_list():
    """测试搜索返回列表"""
    service = SkillService()
    result = service.search("nonexistent_query_xyz")
    assert isinstance(result, list)
    assert len(result) == 0


def test_project_service_search_returns_list():
    """测试项目搜索返回列表"""
    service = ProjectService()
    result = service.search("nonexistent_query_xyz")
    assert isinstance(result, list)
    assert len(result) == 0


def test_skill_service_list_all_returns_list():
    """测试list_all返回列表"""
    service = SkillService()
    result = service.list_all()
    assert isinstance(result, list)


def test_project_service_list_all_returns_list():
    """测试项目list_all返回列表"""
    service = ProjectService()
    result = service.list_all()
    assert isinstance(result, list)
