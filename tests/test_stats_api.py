"""统计API测试"""
import pytest
from open_manager_py.app import app


@pytest.fixture
def client():
    """测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_stats_endpoint(client):
    """测试统计API"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert 'skills_count' in data
    assert 'projects_count' in data
    assert 'categories' in data
    assert 'total_size' in data


def test_stats_endpoint_returns_int_counts(client):
    """测试统计API返回整数计数"""
    response = client.get('/api/stats')
    data = response.get_json()
    assert isinstance(data['skills_count'], int)
    assert isinstance(data['projects_count'], int)
