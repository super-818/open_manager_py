"""导出导入API测试"""
import pytest
import json
from open_manager_py.app import app


@pytest.fixture
def client():
    """测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_export_endpoint(client):
    """测试导出API"""
    response = client.post('/api/export', json={'format': 'json'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'skills' in data
    assert 'projects' in data
    assert 'exported_at' in data


def test_import_endpoint_empty(client):
    """测试导入空数据"""
    response = client.post('/api/import', json={'skills': [], 'projects': []})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True


def test_export_has_version(client):
    """测试导出包含版本号"""
    response = client.post('/api/export', json={})
    data = response.get_json()
    assert 'version' in data
