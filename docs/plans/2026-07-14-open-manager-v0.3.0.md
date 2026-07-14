# Open Manager v0.3.0 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有 Flask Web 应用基础上,新增 CLI 命令行、搜索过滤、统计仪表盘、README 预览、轻量更新检测、日志系统、更多 AI 工具分发目标、导出导入、基础测试套件,使项目从"能用"升级到"好用且可靠"。

**Architecture:** 保持现有 Flask + SQLite 架构。将核心业务逻辑从 `app.py` 抽取到独立的 service 层(`services.py`),让 Web 和 CLI 共用同一套业务逻辑。新增 `cli.py` 提供 Click 命令行入口,新增 `updater.py` 处理轻量更新检测,新增 `logger.py` 统一日志。

**Tech Stack:** Python 3.8+, Flask, Click(CLI), SQLite, PyYAML, pytest(测试)

---

## PM 客观评价

### 现状优势
1. **痛点清晰** - 解决 AI 技能和 GitHub 项目过多后"找不到、忘用途、难更新"的真实问题
2. **跨平台设计** - config.py 已处理 Win/Mac/Linux 路径差异
3. **内容哈希去重** - 基于 SKILL.md 和 git config 哈希,比纯路径去重更可靠
4. **更新备份机制** - clone 前备份,失败自动恢复,保护本地修改
5. **Web UI 直观** - 原生 JS 轻量,无需构建工具

### 现状短板(按影响排序)
| 短板 | 影响 | 商业场景痛点 |
|------|------|-------------|
| 无 CLI | 高 | 服务器/无头环境无法使用,无法脚本化集成 CI/CD |
| 无搜索过滤 | 高 | 项目超过 50 个后基本无法管理 |
| 无 README 预览 | 高 | "忘了这个仓库干嘛的"核心痛点未解决 |
| 无更新检测 | 高 | 不知道哪些项目有新版本,只能盲更新 |
| 无日志 | 中 | 出问题无法排查,企业场景不可接受 |
| 仅 3 个分发目标 | 中 | 缺 Cursor/Continue/Aider/Cline 等主流工具 |
| 无测试 | 中 | 重构和迭代风险高 |
| 无统计仪表盘 | 中 | 无法快速了解资源全貌 |
| 无导出导入 | 低 | 换机器丢失元数据 |
| 裸 except | 低 | 吞异常,调试困难 |

### 商业落地场景考量
1. **个人开发者**:需要 CLI + Web 双入口,快速搜索定位
2. **团队协作**:需要导出导入共享元数据,日志可审计
3. **企业**:需要安全审计(本次先打基础,后续迭代完善)
4. **AI 咨询服务**:需要按客户分发不同技能集(标签+分类筛选)
5. **教育/培训**:需要统计仪表盘展示资源全貌

### 本次迭代范围(v0.3.0)
聚焦"可发现性 + 可靠性 + 多入口"三大主题,10 个任务:

1. 日志系统(基础设施)
2. 业务逻辑抽取到 service 层(重构基础)
3. 搜索过滤 API
4. 统计仪表盘 API
5. README 预览 API
6. 轻量更新检测(git ls-remote)
7. 更多 AI 工具分发目标
8. 导出导入功能
9. CLI 命令行界面
10. 基础测试套件

---

## Task 1: 日志系统

**Files:**
- Create: `open_manager_py/logger.py`
- Modify: `open_manager_py/config.py` (添加 get_log_file 方法)

**Step 1: Write the failing test**

```python
# tests/test_logger.py
import pytest
from pathlib import Path
from open_manager_py.logger import get_logger

def test_logger_returns_logger_instance():
    """测试获取logger实例"""
    logger = get_logger()
    assert logger is not None

def test_logger_writes_to_file(tmp_path, monkeypatch):
    """测试日志写入文件"""
    from open_manager_py import logger as logger_module
    monkeypatch.setattr(logger_module, '_logger_instance', None)
    
    logger = get_logger()
    logger.info("test message")
    
    # 日志文件应该存在
    log_files = list(Path.home().glob("**/SkillProjectManager/logs/*.log"))
    assert len(log_files) > 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_logger.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'open_manager_py.logger'"

**Step 3: Write minimal implementation**

```python
# open_manager_py/logger.py
"""日志模块 - 提供统一的日志记录功能"""
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import get_config


_logger_instance: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """获取全局logger实例,支持文件+控制台输出"""
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance
    
    config = get_config()
    log_dir = config.get_log_dir()
    log_file = log_dir / "open_manager.log"
    
    logger = logging.getLogger("open_manager")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    
    # 文件处理器(轮转,单文件1MB,保留3个)
    file_handler = RotatingFileHandler(
        str(log_file), maxBytes=1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_handler)
    
    _logger_instance = logger
    return logger
```

**Step 4: 在 config.py 添加 get_log_dir 方法**

```python
# 在 Config 类中添加
def get_log_dir(self) -> Path:
    """获取日志目录(用于logger模块)"""
    return self.log_dir
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_logger.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add open_manager_py/logger.py open_manager_py/config.py tests/test_logger.py
git commit -m "feat: 添加统一日志系统,支持文件轮转和控制台输出"
```

---

## Task 2: 业务逻辑抽取到 service 层

**Files:**
- Create: `open_manager_py/services.py`
- Modify: `open_manager_py/app.py` (改为调用 service 层)

**Step 1: Write the failing test**

```python
# tests/test_services.py
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_services.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# open_manager_py/services.py
"""业务逻辑服务层 - Web和CLI共用的核心逻辑"""
from typing import List, Dict, Any, Optional
from pathlib import Path

from .database import get_database
from .scanner import get_scanner
from .logger import get_logger


class SkillService:
    """技能业务服务"""
    
    def __init__(self):
        """初始化技能服务"""
        self.db = get_database()
        self.logger = get_logger()
    
    def list_all(self) -> List[Dict[str, Any]]:
        """获取所有技能"""
        return self.db.get_all_skills()
    
    def get(self, skill_id: int) -> Optional[Dict[str, Any]]:
        """获取单个技能"""
        return self.db.get_skill(skill_id)
    
    def search(self, query: str, category: Optional[str] = None,
               tags: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜索技能(按名称、备注、标签、分类)"""
        query_lower = query.lower() if query else ""
        tag_list = [t.strip().lower() for t in tags.split(',')] if tags else []
        
        results = []
        for skill in self.db.get_all_skills():
            if category and skill.get('category') != category:
                continue
            if tag_list:
                skill_tags = skill.get('tags') or []
                if isinstance(skill_tags, str):
                    skill_tags = [t.strip() for t in skill_tags.split(',')]
                skill_tags_lower = [t.lower() for t in skill_tags]
                if not any(t in skill_tags_lower for t in tag_list):
                    continue
            if query_lower:
                name = (skill.get('name') or '').lower()
                remark = (skill.get('remark') or '').lower()
                github_url = (skill.get('github_url') or '').lower()
                if query_lower not in name and query_lower not in remark and query_lower not in github_url:
                    continue
            results.append(skill)
        return results
    
    def update(self, skill_id: int, **kwargs) -> bool:
        """更新技能"""
        return self.db.update_skill(skill_id, **kwargs)
    
    def delete(self, skill_id: int) -> bool:
        """删除技能"""
        return self.db.delete_skill(skill_id, soft_delete=False)
    
    def distribute(self, skills: List[Dict[str, Any]], target_paths: List[Path]) -> int:
        """分发技能到目标路径,返回成功数量"""
        import shutil
        count = 0
        for target_path in target_paths:
            try:
                target_path.mkdir(parents=True, exist_ok=True)
                for skill in skills:
                    skill_path = Path(skill['path'])
                    if not skill_path.exists():
                        continue
                    dest_path = target_path / skill_path.name
                    if dest_path.exists():
                        if dest_path.is_dir():
                            shutil.rmtree(dest_path)
                        else:
                            dest_path.unlink()
                    if skill_path.is_dir():
                        shutil.copytree(skill_path, dest_path)
                    else:
                        shutil.copy2(skill_path, dest_path)
                    count += 1
            except Exception as e:
                self.logger.error(f"分发到 {target_path} 失败: {e}")
        return count


class ProjectService:
    """项目业务服务"""
    
    def __init__(self):
        """初始化项目服务"""
        self.db = get_database()
        self.logger = get_logger()
    
    def list_all(self) -> List[Dict[str, Any]]:
        """获取所有项目"""
        return self.db.get_all_projects()
    
    def get(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取单个项目"""
        return self.db.get_project(project_id)
    
    def search(self, query: str, category: Optional[str] = None,
               tags: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜索项目(按名称、备注、标签、分类)"""
        query_lower = query.lower() if query else ""
        tag_list = [t.strip().lower() for t in tags.split(',')] if tags else []
        
        results = []
        for project in self.db.get_all_projects():
            if category and project.get('category') != category:
                continue
            if tag_list:
                proj_tags = project.get('tags') or []
                if isinstance(proj_tags, str):
                    proj_tags = [t.strip() for t in proj_tags.split(',')]
                proj_tags_lower = [t.lower() for t in proj_tags]
                if not any(t in proj_tags_lower for t in tag_list):
                    continue
            if query_lower:
                name = (project.get('name') or '').lower()
                remark = (project.get('remark') or '').lower()
                github_url = (project.get('github_url') or '').lower()
                if query_lower not in name and query_lower not in remark and query_lower not in github_url:
                    continue
            results.append(project)
        return results
    
    def update(self, project_id: int, **kwargs) -> bool:
        """更新项目"""
        return self.db.update_project(project_id, **kwargs)
    
    def delete(self, project_id: int) -> bool:
        """删除项目"""
        return self.db.delete_project(project_id, soft_delete=False)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_services.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add open_manager_py/services.py tests/test_services.py
git commit -m "refactor: 抽取业务逻辑到services层,Web和CLI共用"
```

---

## Task 3: 搜索过滤 API

**Files:**
- Modify: `open_manager_py/app.py` (添加搜索端点)

**Step 1: Write the failing test**

```python
# tests/test_search_api.py
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_search_api.py -v`
Expected: FAIL with "404 Not Found"

**Step 3: Write minimal implementation**

```python
# 在 app.py 中添加
@app.route('/api/skills/search', methods=['POST'])
def search_skills():
    """搜索技能"""
    from .services import SkillService
    data = request.get_json() or {}
    service = SkillService()
    results = service.search(
        query=data.get('query', ''),
        category=data.get('category'),
        tags=data.get('tags')
    )
    for skill in results:
        skill['local_size_formatted'] = format_size(skill.get('local_size', 0))
        if 'remark' in skill:
            skill['notes'] = skill['remark']
        tags_val = skill.get('tags')
        if tags_val and isinstance(tags_val, list):
            skill['tags'] = ', '.join(tags_val)
    return jsonify(results)


@app.route('/api/projects/search', methods=['POST'])
def search_projects():
    """搜索项目"""
    from .services import ProjectService
    data = request.get_json() or {}
    service = ProjectService()
    results = service.search(
        query=data.get('query', ''),
        category=data.get('category'),
        tags=data.get('tags')
    )
    for project in results:
        project['local_size_formatted'] = format_size(project.get('local_size', 0))
        if 'remark' in project:
            project['notes'] = project['remark']
        tags_val = project.get('tags')
        if tags_val and isinstance(tags_val, list):
            project['tags'] = ', '.join(tags_val)
    return jsonify(results)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_search_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add open_manager_py/app.py tests/test_search_api.py
git commit -m "feat: 添加技能和项目的搜索过滤API"
```

---

## Task 4: 统计仪表盘 API

**Files:**
- Modify: `open_manager_py/app.py`

**Step 1: Write the failing test**

```python
# tests/test_stats_api.py
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_stats_api.py -v`
Expected: FAIL with "404 Not Found"

**Step 3: Write minimal implementation**

```python
# 在 app.py 中添加
@app.route('/api/stats')
def get_stats():
    """获取统计数据"""
    db = get_database()
    skills = db.get_all_skills()
    projects = db.get_all_projects()
    
    # 分类统计
    categories = {}
    for s in skills + projects:
        cat = s.get('category') or '未分类'
        categories[cat] = categories.get(cat, 0) + 1
    
    # 总大小
    total_size = sum(s.get('local_size', 0) for s in skills + projects)
    
    # 有GitHub链接的数量
    skills_with_github = sum(1 for s in skills if s.get('github_url'))
    projects_with_github = sum(1 for p in projects if p.get('github_url'))
    
    return jsonify({
        'skills_count': len(skills),
        'projects_count': len(projects),
        'categories': categories,
        'total_size': total_size,
        'total_size_formatted': format_size(total_size),
        'skills_with_github': skills_with_github,
        'projects_with_github': projects_with_github
    })
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_stats_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add open_manager_py/app.py tests/test_stats_api.py
git commit -m "feat: 添加统计仪表盘API"
```

---

## Task 5: README 预览 API

**Files:**
- Modify: `open_manager_py/app.py`

**Step 1: Write the failing test**

```python
# tests/test_readme_api.py
import pytest
import tempfile
from pathlib import Path
from open_manager_py.app import app

@pytest.fixture
def client():
    """测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_readme_preview_missing_id(client):
    """测试README预览-技能不存在"""
    response = client.get('/api/skill/99999/readme')
    assert response.status_code == 404

def test_readme_preview_project_missing(client):
    """测试README预览-项目不存在"""
    response = client.get('/api/project/99999/readme')
    assert response.status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_readme_api.py -v`
Expected: FAIL with "404 Not Found" on route

**Step 3: Write minimal implementation**

```python
# 在 app.py 中添加
@app.route('/api/skill/<int:skill_id>/readme')
def get_skill_readme(skill_id: int):
    """获取技能的README/SKILL.md内容"""
    db = get_database()
    skill = db.get_skill(skill_id)
    if not skill:
        return jsonify({'error': 'Skill not found'}), 404
    
    skill_path = Path(skill['path'])
    readme_content = ''
    readme_file = None
    
    # 优先 SKILL.md,然后 README.md
    for filename in ['SKILL.md', 'README.md', 'readme.md', 'README.rst', 'README.txt']:
        filepath = skill_path / filename
        if filepath.exists():
            readme_file = filepath
            break
    
    if readme_file and readme_file.exists():
        try:
            readme_content = readme_file.read_text(encoding='utf-8')
        except Exception as e:
            readme_content = f'读取失败: {e}'
    
    return jsonify({
        'content': readme_content,
        'filename': readme_file.name if readme_file else None,
        'path': str(readme_file) if readme_file else None
    })


@app.route('/api/project/<int:project_id>/readme')
def get_project_readme(project_id: int):
    """获取项目的README内容"""
    db = get_database()
    project = db.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    project_path = Path(project['path'])
    readme_content = ''
    readme_file = None
    
    for filename in ['README.md', 'README.rst', 'README.txt', 'readme.md']:
        filepath = project_path / filename
        if filepath.exists():
            readme_file = filepath
            break
    
    if readme_file and readme_file.exists():
        try:
            readme_content = readme_file.read_text(encoding='utf-8')
        except Exception as e:
            readme_content = f'读取失败: {e}'
    
    return jsonify({
        'content': readme_content,
        'filename': readme_file.name if readme_file else None,
        'path': str(readme_file) if readme_file else None
    })
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_readme_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add open_manager_py/app.py tests/test_readme_api.py
git commit -m "feat: 添加技能和项目的README预览API"
```

---

## Task 6: 轻量更新检测

**Files:**
- Create: `open_manager_py/updater.py`
- Modify: `open_manager_py/app.py`

**Step 1: Write the failing test**

```python
# tests/test_updater.py
import pytest
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_updater.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# open_manager_py/updater.py
"""更新检测模块 - 使用git ls-remote轻量检测远程更新"""
import subprocess
from typing import Optional, Dict, List, Any
from pathlib import Path

from .database import get_database
from .logger import get_logger


class UpdateChecker:
    """更新检测器 - 通过git ls-remote获取远程HEAD,与本地对比"""
    
    def __init__(self):
        """初始化更新检测器"""
        self.db = get_database()
        self.logger = get_logger()
    
    def _get_remote_commit(self, github_url: str) -> Optional[str]:
        """获取远程仓库的HEAD commit hash(不下载代码)"""
        if not github_url:
            return None
        try:
            url = github_url
            if not url.endswith('.git'):
                url = url + '.git'
            result = subprocess.run(
                ['git', 'ls-remote', url, 'HEAD'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout:
                # 格式: "<commit_hash>\tHEAD"
                return result.stdout.split()[0]
        except subprocess.TimeoutExpired:
            self.logger.warning(f"获取远程commit超时: {github_url}")
        except Exception as e:
            self.logger.error(f"获取远程commit失败 {github_url}: {e}")
        return None
    
    def _get_local_commit(self, repo_path: Path) -> Optional[str]:
        """获取本地仓库的HEAD commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(repo_path), capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"获取本地commit失败 {repo_path}: {e}")
        return None
    
    def check_projects(self) -> Dict[str, Any]:
        """检测所有项目的更新状态"""
        projects = self.db.get_all_projects()
        has_update_count = 0
        no_update_count = 0
        error_count = 0
        results = []
        
        for project in projects:
            project_path = Path(project['path'])
            github_url = project.get('github_url')
            
            if not github_url or not project_path.exists():
                continue
            
            local_commit = self._get_local_commit(project_path)
            remote_commit = self._get_remote_commit(github_url)
            
            if remote_commit is None:
                error_count += 1
                has_update = False
            elif local_commit == remote_commit:
                no_update_count += 1
                has_update = False
            else:
                has_update_count += 1
                has_update = True
            
            # 更新数据库
            self.db.update_project(project['id'], has_update=has_update)
            
            results.append({
                'id': project['id'],
                'name': project['name'],
                'has_update': has_update,
                'local_commit': local_commit,
                'remote_commit': remote_commit
            })
        
        return {
            'total': len(results),
            'has_update': has_update_count,
            'up_to_date': no_update_count,
            'errors': error_count,
            'details': results
        }
```

**Step 4: 在 app.py 添加检测端点**

```python
@app.route('/api/projects/check-updates', methods=['POST'])
def check_updates():
    """检测所有项目的远程更新状态(轻量,不下载代码)"""
    from .updater import UpdateChecker
    checker = UpdateChecker()
    result = checker.check_projects()
    return jsonify({'success': True, 'result': result})
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_updater.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add open_manager_py/updater.py open_manager_py/app.py tests/test_updater.py
git commit -m "feat: 添加轻量更新检测,使用git ls-remote对比commit"
```

---

## Task 7: 更多 AI 工具分发目标

**Files:**
- Create: `open_manager_py/targets.py`
- Modify: `open_manager_py/app.py`

**Step 1: Write the failing test**

```python
# tests/test_targets.py
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_targets.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# open_manager_py/targets.py
"""AI工具分发目标 - 定义各AI工具的技能目录路径"""
from pathlib import Path
from typing import List, Dict
import platform


def _get_tool_paths() -> Dict[str, Path]:
    """获取所有支持的AI工具及其技能目录路径(跨平台)"""
    home = Path.home()
    system = platform.system()
    
    tools = {
        'trae': home / '.trae' / 'skills',
        'trae-cn': home / '.trae-cn' / 'skills',
        'claude-code': home / '.claude' / 'skills',
        'cursor': home / '.cursor' / 'skills',
        'continue': home / '.continue' / 'skills',
        'aider': home / '.aider' / 'skills',
        'cline': home / '.cline' / 'skills',
        'openclaw': home / '.openclaw' / 'skills',
        'roo-cline': home / '.roo' / 'skills',
        'windsurf': home / '.codeium' / 'windsurf' / 'skills',
    }
    
    # Windows 特定路径
    if system == 'Windows':
        tools['claude-desktop'] = Path.home() / 'AppData' / 'Roaming' / 'Claude' / 'skills'
    
    return tools


def list_targets() -> Dict[str, str]:
    """列出所有支持的分发目标(名称->路径字符串)"""
    return {name: str(path) for name, path in _get_tool_paths().items()}


def get_target_paths(tools: List[str], custom_path: str = None) -> List[Path]:
    """根据工具名列表获取目标路径列表
    
    Args:
        tools: 工具名列表,如['trae', 'cursor']
        custom_path: 自定义目标路径
    
    Returns:
        目标Path列表
    """
    all_tools = _get_tool_paths()
    paths = []
    for tool in tools:
        if tool in all_tools:
            paths.append(all_tools[tool])
    if custom_path:
        paths.append(Path(custom_path))
    return paths
```

**Step 4: 在 app.py 的 distribute_skills 中使用 targets.py**

```python
# 修改 distribute_skills 函数
@app.route('/api/skills/distribute', methods=['POST'])
def distribute_skills():
    """分发技能到各个工具"""
    from .services import SkillService
    from .targets import get_target_paths, list_targets
    try:
        data = request.get_json()
        category = data.get('category')
        tools = data.get('tools', [])
        custom_path = data.get('customPath')
        
        service = SkillService()
        skills = service.list_all()
        if category:
            skills = [s for s in skills if s.get('category') == category]
        
        target_paths = get_target_paths(tools, custom_path)
        count = service.distribute(skills, target_paths)
        
        return jsonify({
            'success': True,
            'count': count,
            'message': f'已分发 {count} 个技能到 {len(target_paths)} 个目标',
            'available_targets': list_targets()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/distribute-targets')
def get_distribute_targets():
    """获取所有可用的分发目标"""
    from .targets import list_targets
    return jsonify(list_targets())
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_targets.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add open_manager_py/targets.py open_manager_py/app.py tests/test_targets.py
git commit -m "feat: 扩展AI工具分发目标,支持Cursor/Continue/Aider/Cline等10+工具"
```

---

## Task 8: 导出导入功能

**Files:**
- Modify: `open_manager_py/app.py`

**Step 1: Write the failing test**

```python
# tests/test_export_import.py
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_export_import.py -v`
Expected: FAIL with "404 Not Found"

**Step 3: Write minimal implementation**

```python
# 在 app.py 中添加
@app.route('/api/export', methods=['POST'])
def export_data():
    """导出所有技能和项目数据(含元数据,不含文件内容)"""
    db = get_database()
    skills = db.get_all_skills()
    projects = db.get_all_projects()
    
    # 清理不可序列化的字段
    for item in skills + projects:
        item.pop('local_size', None)
    
    from datetime import datetime
    return jsonify({
        'skills': skills,
        'projects': projects,
        'exported_at': datetime.now().isoformat(),
        'version': '0.3.0'
    })


@app.route('/api/import', methods=['POST'])
def import_data():
    """导入技能和项目元数据(仅更新category/tags/remark,不创建新记录)"""
    db = get_database()
    data = request.get_json()
    
    skills = data.get('skills', [])
    projects = data.get('projects', [])
    
    skill_updated = 0
    project_updated = 0
    errors = []
    
    for skill in skills:
        try:
            skill_id = skill.get('id')
            if not skill_id:
                continue
            existing = db.get_skill(skill_id)
            if not existing:
                # 尝试按path匹配
                path = skill.get('path')
                if path:
                    existing = db.get_skill_by_path(path)
            if existing:
                update_data = {}
                if skill.get('category'):
                    update_data['category'] = skill['category']
                if skill.get('tags'):
                    update_data['tags'] = skill['tags']
                if skill.get('remark'):
                    update_data['remark'] = skill['remark']
                if update_data:
                    db.update_skill(existing['id'], **update_data)
                    skill_updated += 1
        except Exception as e:
            errors.append(f"技能 {skill.get('name')}: {e}")
    
    for project in projects:
        try:
            project_id = project.get('id')
            if not project_id:
                continue
            existing = db.get_project(project_id)
            if not existing:
                path = project.get('path')
                if path:
                    existing = db.get_project_by_path(path)
            if existing:
                update_data = {}
                if project.get('category'):
                    update_data['category'] = project['category']
                if project.get('tags'):
                    update_data['tags'] = project['tags']
                if project.get('remark'):
                    update_data['remark'] = project['remark']
                if update_data:
                    db.update_project(existing['id'], **update_data)
                    project_updated += 1
        except Exception as e:
            errors.append(f"项目 {project.get('name')}: {e}")
    
    return jsonify({
        'success': True,
        'skills_updated': skill_updated,
        'projects_updated': project_updated,
        'errors': errors
    })
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_export_import.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add open_manager_py/app.py tests/test_export_import.py
git commit -m "feat: 添加数据导出导入功能,支持元数据备份迁移"
```

---

## Task 9: CLI 命令行界面

**Files:**
- Create: `open_manager_py/cli.py`
- Modify: `setup.py` (添加 CLI 入口点)
- Modify: `requirements.txt` (添加 click)

**Step 1: Write the failing test**

```python
# tests/test_cli.py
import pytest
from click.testing import CliRunner
from open_manager_py.cli import cli

def test_cli_help():
    """测试CLI帮助"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'scan' in result.output
    assert 'list' in result.output
    assert 'search' in result.output
    assert 'stats' in result.output

def test_cli_list_command():
    """测试list命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ['list', 'skills'])
    assert result.exit_code == 0

def test_cli_stats_command():
    """测试stats命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ['stats'])
    assert result.exit_code == 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# open_manager_py/cli.py
"""命令行界面 - 提供headless环境下的管理能力"""
import json
import sys
import click
from pathlib import Path

from .config import get_config
from .database import get_database
from .scanner import get_scanner
from .services import SkillService, ProjectService
from .logger import get_logger


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if not size_bytes:
        return '0 B'
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


@click.group()
@click.version_option(version='0.3.0')
def cli():
    """Open Manager - 开源技能与GitHub项目管理器"""
    pass


@cli.command()
@click.option('--skills-only', is_flag=True, help='仅扫描技能')
@click.option('--projects-only', is_flag=True, help='仅扫描项目')
def scan(skills_only, projects_only):
    """扫描本地目录,同步到数据库"""
    scanner = get_scanner()
    
    if not projects_only:
        click.echo('扫描技能目录...')
        new, updated, deleted = scanner.scan_skills()
        click.echo(f'  技能: 新增 {new}, 更新 {updated}, 删除 {deleted}')
    
    if not skills_only:
        click.echo('扫描项目目录...')
        new, updated, deleted = scanner.scan_projects()
        click.echo(f'  项目: 新增 {new}, 更新 {updated}, 删除 {deleted}')


@cli.command(name='list')
@click.argument('type', type=click.Choice(['skills', 'projects']))
@click.option('--category', '-c', help='按分类筛选')
@click.option('--limit', '-n', default=50, help='显示数量')
def list_items(type, category, limit):
    """列出技能或项目"""
    if type == 'skills':
        service = SkillService()
        items = service.list_all()
    else:
        service = ProjectService()
        items = service.list_all()
    
    if category:
        items = [i for i in items if i.get('category') == category]
    
    items = items[:limit]
    
    if not items:
        click.echo('没有找到记录')
        return
    
    click.echo(f"{'ID':<6} {'名称':<30} {'分类':<10} {'大小':<10} {'备注'}")
    click.echo('-' * 80)
    for item in items:
        click.echo(
            f"{item['id']:<6} "
            f"{item['name'][:30]:<30} "
            f"{(item.get('category') or '-'):<10} "
            f"{format_size(item.get('local_size', 0)):<10} "
            f"{(item.get('remark') or '')[:30]}"
        )


@cli.command()
@click.argument('query')
@click.option('--type', '-t', 'item_type',
              type=click.Choice(['skills', 'projects', 'all']),
              default='all', help='搜索类型')
@click.option('--category', '-c', help='按分类筛选')
@click.option('--tags', help='按标签筛选(逗号分隔)')
def search(query, item_type, category, tags):
    """搜索技能或项目"""
    results = []
    
    if item_type in ('all', 'skills'):
        service = SkillService()
        results.extend([('skill', s) for s in service.search(query, category, tags)])
    
    if item_type in ('all', 'projects'):
        service = ProjectService()
        results.extend([('project', p) for p in service.search(query, category, tags)])
    
    if not results:
        click.echo('没有找到匹配的记录')
        return
    
    click.echo(f"找到 {len(results)} 条结果:")
    click.echo('-' * 80)
    for item_type, item in results:
        click.echo(
            f"[{item_type[:4]}] {item['name']}: "
            f"{(item.get('remark') or '-')[:60]}"
        )


@cli.command()
def stats():
    """显示统计信息"""
    db = get_database()
    skills = db.get_all_skills()
    projects = db.get_all_projects()
    
    click.echo('=' * 50)
    click.echo('Open Manager 统计')
    click.echo('=' * 50)
    click.echo(f'技能总数: {len(skills)}')
    click.echo(f'项目总数: {len(projects)}')
    
    total_size = sum(s.get('local_size', 0) for s in skills + projects)
    click.echo(f'总占用空间: {format_size(total_size)}')
    
    click.echo('\n分类统计:')
    categories = {}
    for item in skills + projects:
        cat = item.get('category') or '未分类'
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        click.echo(f'  {cat}: {count}')


@cli.command()
@click.argument('skill_id', type=int)
@click.argument('target', type=str)
@click.option('--custom-path', help='自定义目标路径')
def distribute(skill_id, target, custom_path):
    """分发技能到AI工具"""
    from .targets import get_target_paths
    service = SkillService()
    skill = service.get(skill_id)
    
    if not skill:
        click.echo(f'技能 ID {skill_id} 不存在')
        return
    
    targets = get_target_paths([target], custom_path)
    if not targets:
        click.echo(f'未知目标: {target}')
        return
    
    count = service.distribute([skill], targets)
    click.echo(f'已分发技能 {skill["name"]} 到 {len(targets)} 个目标')


@cli.command()
@click.option('--skill-id', type=int, help='技能ID')
@click.option('--project-id', type=int, help='项目ID')
def readme(skill_id, project_id):
    """查看技能或项目的README内容"""
    db = get_database()
    
    target_path = None
    if skill_id:
        skill = db.get_skill(skill_id)
        if skill:
            target_path = Path(skill['path'])
    elif project_id:
        project = db.get_project(project_id)
        if project:
            target_path = Path(project['path'])
    
    if not target_path:
        click.echo('未找到指定记录')
        return
    
    for filename in ['SKILL.md', 'README.md', 'readme.md', 'README.rst']:
        filepath = target_path / filename
        if filepath.exists():
            click.echo(filepath.read_text(encoding='utf-8'))
            return
    
    click.echo('未找到README文件')


@cli.command()
@click.option('--output', '-o', default='-', help='输出文件(-为stdout)')
def export(output):
    """导出数据到JSON"""
    db = get_database()
    from datetime import datetime
    data = {
        'skills': db.get_all_skills(),
        'projects': db.get_all_projects(),
        'exported_at': datetime.now().isoformat(),
        'version': '0.3.0'
    }
    
    # 清理不可序列化字段
    for item in data['skills'] + data['projects']:
        item.pop('local_size', None)
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    
    if output == '-':
        click.echo(json_str)
    else:
        Path(output).write_text(json_str, encoding='utf-8')
        click.echo(f'已导出到 {output}')


@cli.command()
@click.argument('input_file')
def import_data(input_file):
    """从JSON文件导入数据"""
    db = get_database()
    data = json.loads(Path(input_file).read_text(encoding='utf-8'))
    
    skill_updated = 0
    project_updated = 0
    
    for skill in data.get('skills', []):
        path = skill.get('path')
        if path:
            existing = db.get_skill_by_path(path)
            if existing:
                update_data = {}
                if skill.get('category'):
                    update_data['category'] = skill['category']
                if skill.get('tags'):
                    update_data['tags'] = skill['tags']
                if skill.get('remark'):
                    update_data['remark'] = skill['remark']
                if update_data:
                    db.update_skill(existing['id'], **update_data)
                    skill_updated += 1
    
    for project in data.get('projects', []):
        path = project.get('path')
        if path:
            existing = db.get_project_by_path(path)
            if existing:
                update_data = {}
                if project.get('category'):
                    update_data['category'] = project['category']
                if project.get('tags'):
                    update_data['tags'] = project['tags']
                if project.get('remark'):
                    update_data['remark'] = project['remark']
                if update_data:
                    db.update_project(existing['id'], **update_data)
                    project_updated += 1
    
    click.echo(f'导入完成: 更新 {skill_updated} 个技能, {project_updated} 个项目')


@cli.command()
def check_updates():
    """检测项目的远程更新(轻量,不下载代码)"""
    from .updater import UpdateChecker
    checker = UpdateChecker()
    click.echo('检测远程更新中...')
    result = checker.check_projects()
    click.echo(f"总计: {result['total']}, 有更新: {result['has_update']}, "
               f"已最新: {result['up_to_date']}, 错误: {result['errors']}")
    
    if result['has_update'] > 0:
        click.echo('\n有更新的项目:')
        for item in result['details']:
            if item['has_update']:
                click.echo(f"  - {item['name']}")


def main():
    """CLI入口点"""
    cli()


if __name__ == '__main__':
    main()
```

**Step 4: 更新 setup.py 和 requirements.txt**

```python
# setup.py - 添加 click 和 cli 入口点
from setuptools import setup, find_packages

setup(
    name='open_manager_py',
    version='0.3.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask>=2.0.0',
        'PyYAML>=5.4',
        'click>=8.0.0',
    ],
    entry_points={
        'console_scripts': [
            'open-manager=open_manager_py.app:main',
            'open-manager-cli=open_manager_py.cli:main',
        ],
    },
    author='Open Manager',
    description='开源技能与GitHub项目管理器 - Web+CLI',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
```

```
# requirements.txt
Flask>=2.0.0
PyYAML>=5.4
click>=8.0.0
pytest>=7.0.0
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add open_manager_py/cli.py setup.py requirements.txt tests/test_cli.py
git commit -m "feat: 添加CLI命令行界面,支持scan/list/search/stats/distribute等命令"
```

---

## Task 10: 基础测试套件整合

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `pytest.ini`

**Step 1: Write the conftest**

```python
# tests/conftest.py
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
    
    # 重置配置
    import open_manager_py.config as config_module
    monkeypatch.setattr(config_module, '_config_instance', None)
    
    # 重置扫描器
    import open_manager_py.scanner as scanner_module
    monkeypatch.setattr(scanner_module, '_scanner_instance', None)
    
    # 重置logger
    import open_manager_py.logger as logger_module
    monkeypatch.setattr(logger_module, '_logger_instance', None)
    
    yield
```

```python
# tests/__init__.py
"""测试包初始化"""
```

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

**Step 2: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/__init__.py tests/conftest.py pytest.ini
git commit -m "test: 添加pytest配置和公共fixtures"
```

---

## 执行顺序总览

1. Task 1: 日志系统
2. Task 2: service层抽取
3. Task 3: 搜索API
4. Task 4: 统计API
5. Task 5: README预览API
6. Task 6: 更新检测
7. Task 7: AI工具分发目标
8. Task 8: 导出导入
9. Task 9: CLI界面
10. Task 10: 测试套件整合

每个Task完成后立即commit,保持频繁提交。
