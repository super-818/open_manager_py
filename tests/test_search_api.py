"""搜索API测试"""
import pytest
from open_manager_py.app import app


@pytest.fixture
def client():
    """测试客户端fixture"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_search_skills_endpoint(client):
    """测试技能搜索API"""
    response = client.post('/api/skills/search', json={
        'query': 'test',
        'category': '',
        'tags': ''
    })
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_search_projects_endpoint(client):
    """测试项目搜索API"""
    response = client.post('/api/projects/search', json={
        'query': 'test',
        'category': '',
        'tags': ''
    })
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_search_skills_empty_query(client):
    """测试空查询返回所有"""
    response = client.post('/api/skills/search', json={
        'query': '',
        'category': '',
        'tags': ''
    })
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
