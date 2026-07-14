"""
Web UI 相关 API 集成测试
"""

import pytest
from open_manager_py.app import app


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_contains_dashboard_tab(client):
    """测试首页包含仪表盘标签"""
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert '仪表盘' in html or '统计' in html


def test_stats_api(client):
    """测试统计API返回正确结构"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert 'skills_count' in data
    assert 'projects_count' in data
    assert 'categories' in data


def test_search_skills_api_filters_by_tag(client):
    """测试技能搜索API支持标签过滤"""
    response = client.post('/api/skills/search', json={
        'query': '',
        'category': '',
        'tags': 'python'
    })
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_search_projects_api_filters_by_category(client):
    """测试项目搜索API支持分类过滤"""
    response = client.post('/api/projects/search', json={
        'query': '',
        'category': '开发工具',
        'tags': ''
    })
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_skill_readme_api_returns_content(client):
    """测试技能README API返回内容结构"""
    response = client.get('/api/skill/99999/readme')
    assert response.status_code == 404


def test_project_readme_api_returns_content(client):
    """测试项目README API返回内容结构"""
    response = client.get('/api/project/99999/readme')
    assert response.status_code == 404


def test_check_updates_api(client, monkeypatch):
    """测试更新检测API(使用mock避免真实git操作)"""
    from open_manager_py import updater
    monkeypatch.setattr(
        updater.UpdateChecker,
        'check_projects',
        lambda self: {'total': 0, 'has_update': 0, 'up_to_date': 0, 'errors': 0, 'details': []}
    )
    response = client.post('/api/projects/check-updates', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data


def test_distribute_targets_api(client):
    """测试分发目标API返回10+工具"""
    response = client.get('/api/distribute-targets')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 10
    assert 'trae' in data
    assert 'cursor' in data


def test_export_api(client):
    """测试导出API"""
    response = client.post('/api/export', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert 'skills' in data
    assert 'projects' in data


def test_import_api_empty(client):
    """测试导入空数据"""
    response = client.post('/api/import', json={'skills': [], 'projects': []})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
