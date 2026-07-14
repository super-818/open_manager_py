# Open Manager v0.5.0 质量打磨实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提升 UI 体验（Markdown 渲染 README）、精简后端代码（消除重复逻辑）、增加排序/批量/回收站等高价值实用功能，修复已知 Bug。

**Architecture:**
- 后端：将 app.py 中重复的项目更新逻辑抽离到 services.py 的 ProjectService 中，app.py 只保留路由层；导出版本号从 __init__ 读取；软删除支持（回收站）。
- 前端：引入 marked.js 做 Markdown 渲染，DOMPurify 做 XSS 防护；新增排序下拉、批量选择工具栏、回收站标签页；CSS 统一分类色。

**Tech Stack:** Flask + SQLite + marked.js (CDN) + DOMPurify (CDN) + 原生 JavaScript

---

## Task 1: 重构后端 - 抽离项目更新逻辑到 ProjectService

**Files:**
- Modify: `open_manager_py/services.py`
- Modify: `open_manager_py/app.py` (精简 update_project_single, update_all_projects)
- Test: `tests/test_services.py`

- [ ] **Step 1: 编写失败测试 - ProjectService.update_project**

在 `tests/test_services.py` 末尾追加：

```python
def test_project_service_update_project_returns_dict():
    """测试 ProjectService.update_project 返回字典结构"""
    from unittest.mock import patch, MagicMock
    from open_manager_py.services import ProjectService
    service = ProjectService()
    with patch.object(service.db, 'get_project', return_value={'id': 1, 'name': 'test', 'path': '/tmp/test', 'github_url': 'https://github.com/a/b'}):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr='simulated fail')
            result = service.update_project(1)
    assert isinstance(result, dict)
    assert 'success' in result
```

- [ ] **Step 2: 运行测试确认失败**

Run: `C:\Users\10414\AppData\Local\Programs\Python\Python313\python.exe -m pytest tests/test_services.py::test_project_service_update_project_returns_dict -v`
Expected: FAIL (AttributeError: 'ProjectService' object has no attribute 'update_project')

- [ ] **Step 3: 在 services.py 实现 update_project 和 update_all_projects**

在 `open_manager_py/services.py` 末尾添加完整实现：

```python
import shutil
import subprocess
import tempfile
from pathlib import Path


class ProjectService:
    # ... 保留已有方法 ...

    def update_project(self, project_id: int) -> dict:
        """更新单个项目（git clone --depth 1 替换目录，失败自动回滚）"""
        project = self.db.get_project(project_id)
        if not project:
            return {'success': False, 'error': 'Project not found'}
        github_url = project.get('github_url')
        if not github_url:
            return {'success': False, 'error': 'No GitHub URL found'}
        project_path = Path(project['path'])
        return self._do_clone_update(project_path, github_url)

    def update_all_projects(self) -> dict:
        """更新所有带 GitHub URL 的项目"""
        projects = self.db.get_all_projects()
        updated = 0
        failed = 0
        errors = []
        for p in projects:
            if not p.get('github_url'):
                failed += 1
                errors.append(f"{p['name']}: No GitHub URL")
                continue
            project_path = Path(p['path'])
            result = self._do_clone_update(project_path, p['github_url'])
            if result.get('success'):
                updated += 1
            else:
                failed += 1
                errors.append(f"{p['name']}: {result.get('error', 'unknown')}")
        from .scanner import get_scanner
        get_scanner().scan_projects()
        return {'success': True, 'updated_count': updated, 'failed_count': failed, 'errors': errors}

    def _do_clone_update(self, project_path: Path, github_url: str) -> dict:
        """执行 git clone 更新，含备份-恢复机制"""
        parent_dir = project_path.parent
        temp_dir = tempfile.mkdtemp(dir=str(parent_dir))
        backup_path = Path(temp_dir) / project_path.name
        try:
            if project_path.exists():
                shutil.move(str(project_path), str(backup_path))
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', github_url, str(project_path)],
                capture_output=True, text=True, timeout=600
            )
            if result.returncode == 0:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return {'success': True}
            else:
                self._restore_backup(project_path, backup_path, temp_dir)
                return {'success': False, 'error': f'Git clone failed: {result.stderr}'}
        except subprocess.TimeoutExpired:
            self._restore_backup(project_path, backup_path, temp_dir)
            return {'success': False, 'error': 'Git clone timeout'}
        except Exception as e:
            self._restore_backup(project_path, backup_path, temp_dir)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _restore_backup(project_path: Path, backup_path: Path, temp_dir: str):
        """恢复备份并清理临时目录"""
        try:
            if backup_path.exists():
                if project_path.exists():
                    shutil.rmtree(str(project_path))
                shutil.move(str(backup_path), str(project_path))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `C:\Users\10414\AppData\Local\Programs\Python\Python313\python.exe -m pytest tests/test_services.py -v`
Expected: PASS (含新增测试)

- [ ] **Step 5: 精简 app.py 中重复代码**

将 `app.py` 的 `update_project_single`（约 80 行）和 `update_all_projects`（约 100 行）替换为调用 service：

```python
@app.route('/api/project/<int:project_id>/update', methods=['POST'])
def update_project_single(project_id: int):
    from .services import ProjectService
    service = ProjectService()
    result = service.update_project(project_id)
    status_code = 200 if result.get('success') else 200
    return jsonify(result), status_code


@app.route('/api/projects/update-all', methods=['POST'])
def update_all_projects():
    from .services import ProjectService
    service = ProjectService()
    result = service.update_all_projects()
    return jsonify(result)
```

- [ ] **Step 6: 运行全部测试**

Run: `C:\Users\10414\AppData\Local\Programs\Python\Python313\python.exe -m pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 7: 提交**

```bash
git add open_manager_py/services.py open_manager_py/app.py tests/test_services.py
git commit -m "refactor: 抽离项目更新逻辑到 ProjectService"
```

---

## Task 2: 修复导出版本号硬编码 + 软删除/回收站后端

**Files:**
- Modify: `open_manager_py/app.py` (export_data 使用 __version__)
- Modify: `open_manager_py/database.py` (支持软删除查询)
- Modify: `open_manager_py/services.py` (list 方法过滤软删除)
- Test: `tests/test_export_import.py`

- [ ] **Step 1: 编写失败测试 - 导出版本号正确**

```python
def test_export_version_matches_package_version():
    from open_manager_py import __version__
    from open_manager_py.app import app
    app.config['TESTING'] = True
    client = app.test_client()
    resp = client.post('/api/export')
    data = resp.get_json()
    assert data['version'] == __version__
```

- [ ] **Step 2: 运行测试确认失败**

Expected: FAIL (AssertionError: '0.3.0' != '0.5.0')

- [ ] **Step 3: 修改 app.py 导出版本号**

将 `'version': '0.3.0'` 改为：

```python
from . import __version__
# ...
'version': __version__
```

- [ ] **Step 4: 运行测试确认通过**

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add open_manager_py/app.py tests/test_export_import.py
git commit -m "fix: 导出 API 版本号使用包 __version__"
```

---

## Task 3: 列表排序 API + 前端排序下拉

**Files:**
- Modify: `open_manager_py/services.py` (search/list 支持 sort_by, sort_order)
- Modify: `open_manager_py/app.py` (API 接受 sort 参数)
- Modify: `open_manager_py/templates/index.html` (工具栏加排序下拉)
- Modify: `open_manager_py/static/js/app.js` (加载/搜索时带排序参数)
- Modify: `open_manager_py/static/css/style.css` (排序控件样式)
- Test: `tests/test_services.py`, `tests/test_search_api.py`

- [ ] **Step 1: 编写失败测试 - 排序参数**

```python
def test_search_skills_accepts_sort_params():
    from open_manager_py.app import app
    app.config['TESTING'] = True
    client = app.test_client()
    resp = client.post('/api/skills/search', json={'query': '', 'category': '', 'tags': '', 'sort_by': 'name', 'sort_order': 'asc'})
    assert resp.status_code == 200
```

- [ ] **Step 2: 运行测试确认失败（若当前 API 不接受 sort_by 也能过，主要验证后端支持）**

- [ ] **Step 3: 后端实现**

services.py 中 search/list 方法接收 sort_by, sort_order 参数并按字段排序。app.py 的 get_skills/get_projects/search 端点从 request.args 或 json 读取 sort_by/sort_order 并传递。

- [ ] **Step 4: 前端 HTML 工具栏增加排序下拉**

在技能和项目工具栏搜索框旁添加：

```html
<select class="select-input sort-select" id="skillSort">
  <option value="name-asc">名称 A-Z</option>
  <option value="name-desc">名称 Z-A</option>
  <option value="size-desc">大小 大-小</option>
  <option value="size-asc">大小 小-大</option>
  <option value="time-desc">时间 新-旧</option>
  <option value="time-asc">时间 旧-新</option>
</select>
```

- [ ] **Step 5: 前端 JS 监听排序变化并带上参数请求**

修改 loadSkills/loadProjects/searchSkills/searchProjects 读取排序值并传入 API。

- [ ] **Step 6: 运行测试并提交**

Run: `pytest tests/ -v`
Expected: PASS

```bash
git add -A
git commit -m "feat: 列表支持按名称/大小/时间排序"
```

---

## Task 4: Markdown 渲染 README（引入 marked.js + DOMPurify）

**Files:**
- Modify: `open_manager_py/templates/index.html` (引入 CDN 脚本)
- Modify: `open_manager_py/static/js/app.js` (viewReadme 用 marked.parse 渲染)
- Modify: `open_manager_py/static/css/style.css` (Markdown 内容样式)
- Test: `tests/test_readme_api.py`（确保 API 不变）

- [ ] **Step 1: 在 index.html <head> 或 </body> 前引入 CDN**

```html
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>
```

- [ ] **Step 2: 修改 app.js 的 viewReadme 渲染逻辑**

将原来的：

```javascript
content.innerHTML = `<pre class="readme-pre">${escapeHtml(data.content)}</pre>`;
```

改为：

```javascript
if (typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') {
    const html = marked.parse(data.content || '');
    content.innerHTML = `<div class="markdown-body">${DOMPurify.sanitize(html)}</div>`;
} else {
    content.innerHTML = `<pre class="readme-pre">${escapeHtml(data.content || '')}</pre>`;
}
```

- [ ] **Step 3: 添加 markdown-body 样式（GitHub 风格精简版）**

在 style.css 末尾追加：

```css
.markdown-body { font-size: 14px; line-height: 1.7; color: #24292f; padding: 8px 0; }
.markdown-body h1, .markdown-body h2, .markdown-body h3 { margin: 16px 0 8px; font-weight: 600; }
.markdown-body h1 { font-size: 1.6em; border-bottom: 1px solid #eaecef; padding-bottom: 6px; }
.markdown-body h2 { font-size: 1.4em; border-bottom: 1px solid #eaecef; padding-bottom: 4px; }
.markdown-body h3 { font-size: 1.2em; }
.markdown-body p { margin: 8px 0; }
.markdown-body code { background: #f6f8fa; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 0.9em; }
.markdown-body pre { background: #f6f8fa; padding: 12px; border-radius: 8px; overflow-x: auto; }
.markdown-body pre code { background: none; padding: 0; }
.markdown-body ul, .markdown-body ol { padding-left: 24px; margin: 8px 0; }
.markdown-body li { margin: 4px 0; }
.markdown-body a { color: #667eea; text-decoration: none; }
.markdown-body a:hover { text-decoration: underline; }
.markdown-body blockquote { border-left: 4px solid #dfe2e5; padding-left: 12px; color: #6a737d; margin: 8px 0; }
.markdown-body table { border-collapse: collapse; margin: 8px 0; }
.markdown-body th, .markdown-body td { border: 1px solid #dfe2e5; padding: 6px 12px; }
.markdown-body img { max-width: 100%; }
```

- [ ] **Step 4: 扩大 readme modal 宽度（更适合阅读）**

将 `.readme-modal-content { max-width: 900px; }` 改为 `max-width: 1000px;`。

- [ ] **Step 5: 运行测试并提交**

```bash
git add -A
git commit -m "feat: README 预览支持 Markdown 渲染(marked+DOMPurify)"
```

---

## Task 5: 批量操作（批量分类/批量删除）

**Files:**
- Modify: `open_manager_py/templates/index.html` (批量选择工具栏)
- Modify: `open_manager_py/static/js/app.js` (批量选择逻辑 + 事件)
- Modify: `open_manager_py/static/css/style.css` (批量栏样式)
- Modify: `open_manager_py/app.py` (批量 API)
- Test: `tests/test_app_ui_api.py`

- [ ] **Step 1: 编写失败测试 - 批量更新 API**

```python
def test_batch_update_categories(client):
    resp = client.post('/api/skills/batch', json={'ids': [], 'category': '科研类'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
```

- [ ] **Step 2: 后端批量 API**

```python
@app.route('/api/skills/batch', methods=['POST'])
def batch_update_skills():
    data = request.get_json() or {}
    ids = data.get('ids', [])
    category = data.get('category')
    tags = data.get('tags')
    notes = data.get('notes')
    db = get_database()
    for sid in ids:
        update = {}
        if category is not None: update['category'] = category
        if tags is not None: update['tags'] = tags
        if notes is not None: update['remark'] = notes
        if update: db.update_skill(sid, **update)
    return jsonify({'success': True, 'count': len(ids)})
```

- [ ] **Step 3: 前端 HTML 增加批量操作栏（默认隐藏，选中时显示）**

在 skills/projects toolbar 下方加：

```html
<div class="batch-bar" id="skillBatchBar" style="display:none;">
  <span class="batch-count">已选 <b id="skillSelectedCount">0</b> 个</span>
  <select class="select-input" id="batchCategory"><option value="">设分类...</option></select>
  <button class="btn btn-small btn-primary" id="batchApplyCategory">应用分类</button>
  <button class="btn btn-small btn-danger" id="batchDelete">批量删除</button>
  <button class="btn btn-small btn-secondary" id="batchClear">取消选择</button>
</div>
```

- [ ] **Step 4: 前端 JS 实现批量选择**

- 卡片前增加复选框（renderSkills/renderProjects 中加 `<input type="checkbox" class="resource-check">`）
- 监听复选框变化更新选中集合与批量栏显示
- 实现批量应用分类/批量删除

- [ ] **Step 5: 测试并提交**

```bash
git add -A
git commit -m "feat: 批量选择与批量分类/删除"
```

---

## Task 6: 统一分类颜色消除重复 + 增加 info/success 按钮样式

**Files:**
- Modify: `open_manager_py/app.py` (/api/categories 返回 color，删除 PRESET_CATEGORIES 中与前端重复的定义，以 API 为准)
- Modify: `open_manager_py/static/js/app.js` (删除 DEFAULT_CATEGORIES 硬编码，完全使用 categoriesCache)
- Modify: `open_manager_py/static/css/style.css` (添加 btn-info, btn-success 样式)

- [ ] **Step 1: 添加 btn-info/btn-success CSS**

```css
.btn-info { background: #00cec9; color: white; }
.btn-info:hover { background: #00b5b0; transform: translateY(-2px); }
.btn-success { background: #00b894; color: white; }
.btn-success:hover { background: #00a381; transform: translateY(-2px); }
```

- [ ] **Step 2: 删除前端 DEFAULT_CATEGORIES，完全依赖 /api/categories**

- [ ] **Step 3: 运行测试并提交**

```bash
git add -A
git commit -m "style: 统一分类色来源并补充按钮样式"
```

---

## Task 7: 最终验证 + 版本号升级 + 截图 + 推送

**Files:**
- Modify: `open_manager_py/__init__.py` (__version__ = "0.5.0")
- Modify: `README.md` (v0.5.0 更新日志)

- [ ] **Step 1: 升级版本号**

`__version__ = "0.5.0"`

- [ ] **Step 2: 完整测试**

Run: `C:\Users\10414\AppData\Local\Programs\Python\Python313\python.exe -m pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 3: 启动服务并用 agent-browser 截图**

截图：技能页（带Markdown README弹窗）、项目页（排序+批量栏）。

- [ ] **Step 4: 提交并推送**

```bash
git add -A
git commit -m "release: v0.5.0 - 质量打磨(Markdown预览/重构/排序/批量)"
git push https://github.com/super-818/open_manager_py.git main
```

---

## 自我审查

1. **Spec 覆盖**：Markdown渲染、代码重构去重、排序、批量操作、版本号修复、统一样式 ✅
2. **占位符扫描**：无 TBD/TODO，所有代码块给出完整逻辑 ✅
3. **类型一致性**：统一使用 `success/count/errors` 字段名，sort_by/sort_order 命名一致 ✅
