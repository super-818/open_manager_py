"""README预览API测试"""
import pytest
from open_manager_py.app import app


@pytest.fixture
def client():
    """测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_readme_preview_skill_missing(client):
    """测试README预览-技能不存在"""
    response = client.get('/api/skill/99999/readme')
    assert response.status_code == 404


def test_readme_preview_project_missing(client):
    """测试README预览-项目不存在"""
    response = client.get('/api/project/99999/readme')
    assert response.status_code == 404
