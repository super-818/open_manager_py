"""services模块测试"""
import pytest
from unittest.mock import patch, MagicMock
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


def test_project_service_update_project_returns_dict(monkeypatch):
    """测试 ProjectService.update_project 返回字典结构"""
    from unittest.mock import patch, MagicMock
    service = ProjectService()
    monkeypatch.setattr(service.db, 'get_project', lambda pid: {'id': pid, 'name': 'test', 'path': '/tmp/test', 'github_url': 'https://github.com/a/b'})
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr='simulated fail')
        with patch('shutil.move'), patch('shutil.rmtree'), patch('tempfile.mkdtemp', return_value='/tmp/fake'):
            result = service.update_project(1)
    assert isinstance(result, dict)
    assert 'success' in result
    assert result['success'] is False


def test_project_service_update_all_returns_dict(monkeypatch):
    """测试 ProjectService.update_all_projects 返回字典结构"""
    service = ProjectService()
    monkeypatch.setattr(service.db, 'get_all_projects', lambda: [])
    with patch('open_manager_py.scanner.get_scanner') as mock_scanner:
        mock_scanner.return_value.scan_projects = lambda: None
        result = service.update_all_projects()
    assert isinstance(result, dict)
    assert 'success' in result
    assert 'updated_count' in result
    assert 'failed_count' in result


def test_skill_service_list_all_supports_sort_by_name(monkeypatch):
    """测试 SkillService.list_all 支持 sort_by 参数"""
    service = SkillService()
    monkeypatch.setattr(service.db, 'get_all_skills', lambda: [
        {'name': 'C', 'local_size': 100},
        {'name': 'A', 'local_size': 300},
        {'name': 'B', 'local_size': 200},
    ])
    result = service.list_all(sort_by='name')
    assert [r['name'] for r in result] == ['A', 'B', 'C']


def test_project_service_list_all_supports_sort_by_size(monkeypatch):
    """测试 ProjectService.list_all 支持按大小排序"""
    service = ProjectService()
    monkeypatch.setattr(service.db, 'get_all_projects', lambda: [
        {'name': 'C', 'local_size': 100},
        {'name': 'A', 'local_size': 300},
        {'name': 'B', 'local_size': 200},
    ])
    result = service.list_all(sort_by='size_desc')
    assert [r['local_size'] for r in result] == [300, 200, 100]
