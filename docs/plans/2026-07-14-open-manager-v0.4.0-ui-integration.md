# Open Manager v0.4.0 UI 集成计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 v0.3.0 新增的后端能力（搜索、统计、README预览、更新检测、导出导入、多工具分发）完整集成到 Web UI，使用户无需 CLI 即可使用全部功能。

**Architecture:** 保持现有 Flask 后端和原生 JS 前端。新增 Dashboard 标签页承载统计信息；扩展资源卡片操作（查看README、复制路径）；将前端本地过滤改为调用后端搜索 API；通过动态加载 `/api/distribute-targets` 支持全部 AI 工具分发目标。

**Tech Stack:** Python 3.8+, Flask, SQLite, 原生 JavaScript, CSS3

---

## 文件结构

| 文件 | 责任 |
|------|------|
| `open_manager_py/templates/index.html` | 新增 Dashboard 标签页、README 弹窗、导入弹窗 |
| `open_manager_py/static/js/app.js` | 新增搜索 API 调用、统计加载、README 弹窗、更新检测、导出导入、动态分发目标 |
| `open_manager_py/static/css/style.css` | 新增 Dashboard 卡片、README 弹窗、更新徽章样式 |
| `tests/test_app_ui_api.py` | 新增前端相关 API 集成测试（README/搜索/统计/导出） |

---

## Task 1: 新增 Dashboard 统计标签页

**Files:**
- Modify: `open_manager_py/templates/index.html:18-21`
- Modify: `open_manager_py/templates/index.html:23-46`
- Modify: `open_manager_py/static/js/app.js`
- Modify: `open_manager_py/static/css/style.css`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_app_ui_api.py
import pytest
from open_manager_py.app import app

@pytest.fixture
def client():
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_app_ui_api.py::test_index_contains_dashboard_tab -v`
Expected: FAIL with "AssertionError: assert '仪表盘' in html"

- [ ] **Step 3: Modify index.html 添加 Dashboard 标签页**

```html
<!-- 在 templates/index.html 的 nav.tabs 中添加 -->
<button class="tab-btn" data-tab="dashboard">📊 仪表盘</button>

<!-- 在 main.content 中添加 dashboard 标签内容 -->
<div id="dashboard-tab" class="tab-content">
    <div id="statsContainer" class="stats-container">
        <div class="stats-loading">加载统计中...</div>
    </div>
</div>
```

- [ ] **Step 4: Add dashboard loading in app.js**

```javascript
// 在 DOMContentLoaded 事件处理中，loadCategories 后添加
loadStats();

// 新增函数
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        renderStats(data);
    } catch (error) {
        console.error('加载统计失败', error);
        const container = document.getElementById('statsContainer');
        if (container) container.innerHTML = '<div class="empty-state">加载统计失败</div>';
    }
}

function renderStats(data) {
    const container = document.getElementById('statsContainer');
    if (!container) return;
    
    const categoriesHtml = Object.entries(data.categories || {})
        .sort((a, b) => b[1] - a[1])
        .map(([cat, count]) => `
            <div class="stat-category-item">
                <span class="stat-category-name">${escapeHtml(cat)}</span>
                <span class="stat-category-count">${count}</span>
            </div>
        `).join('');
    
    container.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${data.skills_count}</div>
                <div class="stat-label">技能总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.projects_count}</div>
                <div class="stat-label">项目总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${escapeHtml(data.total_size_formatted || '0 B')}</div>
                <div class="stat-label">总占用空间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.skills_with_github + data.projects_with_github}</div>
                <div class="stat-label">含 GitHub 链接</div>
            </div>
        </div>
        <div class="stats-section">
            <h3>分类分布</h3>
            <div class="stat-categories">
                ${categoriesHtml || '<div class="empty-state-hint">暂无分类数据</div>'}
            </div>
        </div>
    `;
}
```

- [ ] **Step 5: Add CSS for dashboard**

```css
/* 在 style.css 末尾添加 */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 24px;
    border-radius: 12px;
    text-align: center;
}

.stat-value {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 8px;
}

.stat-label {
    font-size: 14px;
    opacity: 0.9;
}

.stat-categories {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin-top: 12px;
}

.stat-category-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.stat-category-count {
    font-weight: 700;
    color: #667eea;
}
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_app_ui_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add open_manager_py/templates/index.html open_manager_py/static/js/app.js open_manager_py/static/css/style.css tests/test_app_ui_api.py
git commit -m "feat: 新增 Dashboard 统计仪表盘标签页"
```

---

## Task 2: 搜索调用后端 API（支持标签、GitHub URL）

**Files:**
- Modify: `open_manager_py/templates/index.html:26-41`
- Modify: `open_manager_py/static/js/app.js`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_app_ui_api.py::test_search_skills_api_filters_by_tag -v`
Expected: PASS (backend already supports this)

- [ ] **Step 3: Add tags input to HTML toolbar**

```html
<!-- 在 skills-tab toolbar 中添加标签输入 -->
<input type="text" id="skillTags" placeholder="标签(逗号分隔)" class="search-input" style="flex: 0.5;">

<!-- 在 projects-tab toolbar 中添加标签输入 -->
<input type="text" id="projectTags" placeholder="标签(逗号分隔)" class="search-input" style="flex: 0.5;">
```

- [ ] **Step 4: Replace local filter with backend search in app.js**

```javascript
// 替换 filterSkills 和 filterProjects
async function searchSkills() {
    const query = document.getElementById('skillSearch').value;
    const category = document.getElementById('skillCategory').value;
    const tags = document.getElementById('skillTags').value;
    
    try {
        const response = await fetch('/api/skills/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, category, tags })
        });
        const data = await response.json();
        renderSkills(data);
    } catch (error) {
        showToast('搜索失败', 'error');
        console.error(error);
    }
}

async function searchProjects() {
    const query = document.getElementById('projectSearch').value;
    const category = document.getElementById('projectCategory').value;
    const tags = document.getElementById('projectTags').value;
    
    try {
        const response = await fetch('/api/projects/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, category, tags })
        });
        const data = await response.json();
        renderProjects(data);
    } catch (error) {
        showToast('搜索失败', 'error');
        console.error(error);
    }
}

// 修改 initButtons 中的事件监听
document.getElementById('skillSearch').addEventListener('input', debounce(searchSkills, 300));
document.getElementById('skillCategory').addEventListener('change', searchSkills);
document.getElementById('skillTags').addEventListener('input', debounce(searchSkills, 300));

document.getElementById('projectSearch').addEventListener('input', debounce(searchProjects, 300));
document.getElementById('projectCategory').addEventListener('change', searchProjects);
document.getElementById('projectTags').addEventListener('input', debounce(searchProjects, 300));

// 添加 debounce 辅助函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_app_ui_api.py tests/test_search_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add open_manager_py/templates/index.html open_manager_py/static/js/app.js tests/test_app_ui_api.py
git commit -m "feat: 前端搜索调用后端API,支持标签和分类组合过滤"
```

---

## Task 3: README 预览弹窗

**Files:**
- Modify: `open_manager_py/templates/index.html`
- Modify: `open_manager_py/static/js/app.js`
- Modify: `open_manager_py/static/css/style.css`

- [ ] **Step 1: Write the failing test**

```python
def test_skill_readme_api_returns_content(client):
    """测试技能README API返回内容结构"""
    response = client.get('/api/skill/99999/readme')
    assert response.status_code == 404

def test_project_readme_api_returns_content(client):
    """测试项目README API返回内容结构"""
    response = client.get('/api/project/99999/readme')
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_app_ui_api.py::test_skill_readme_api_returns_content -v`
Expected: PASS (backend already exists)

- [ ] **Step 3: Add README modal to HTML**

```html
<!-- 在 index.html 末尾，editModal 后添加 -->
<div id="readmeModal" class="modal">
    <div class="modal-content readme-modal-content">
        <div class="modal-header">
            <h2 id="readmeModalTitle">README</h2>
            <button class="close-btn" onclick="closeReadmeModal()">&times;</button>
        </div>
        <div class="modal-body">
            <div id="readmeContent" class="readme-content">
                <div class="readme-loading">加载中...</div>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeReadmeModal()">关闭</button>
        </div>
    </div>
</div>
```

- [ ] **Step 4: Add README preview logic to app.js**

```javascript
// 在 handleResourceAction switch 中添加
case 'readme':
    viewReadme(type, id);
    break;

// 在 resource-actions 渲染中添加 README 按钮（修改 renderSkills 和 renderProjects 中的 actions）
// 在"打开目录"按钮后添加：
// <button class="btn btn-small btn-info btn-action" data-action="readme">README</button>

async function viewReadme(type, id) {
    const modal = document.getElementById('readmeModal');
    const content = document.getElementById('readmeContent');
    const title = document.getElementById('readmeModalTitle');
    
    modal.classList.add('show');
    content.innerHTML = '<div class="readme-loading">加载中...</div>';
    title.textContent = 'README';
    
    try {
        const response = await fetch(`/api/${type}/${id}/readme`);
        const data = await response.json();
        
        if (response.ok) {
            title.textContent = `README - ${escapeHtml(data.filename || '无文件')}`;
            if (data.content) {
                content.innerHTML = `<pre class="readme-pre">${escapeHtml(data.content)}</pre>`;
            } else {
                content.innerHTML = '<div class="empty-state">未找到 README 文件</div>';
            }
        } else {
            content.innerHTML = `<div class="empty-state">${escapeHtml(data.error || '加载失败')}</div>`;
        }
    } catch (error) {
        content.innerHTML = '<div class="empty-state">加载失败</div>';
        console.error(error);
    }
}

function closeReadmeModal() {
    document.getElementById('readmeModal').classList.remove('show');
}
```

- [ ] **Step 5: Add CSS for readme modal**

```css
.readme-modal-content {
    max-width: 900px;
    width: 90%;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
}

.readme-content {
    overflow: auto;
    max-height: 60vh;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
}

.readme-pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #333;
    margin: 0;
}

.btn-info {
    background: #17a2b8;
    color: white;
}

.btn-info:hover {
    background: #138496;
}
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_readme_api.py tests/test_app_ui_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add open_manager_py/templates/index.html open_manager_py/static/js/app.js open_manager_py/static/css/style.css tests/test_app_ui_api.py
git commit -m "feat: 前端新增README预览弹窗"
```

---

## Task 4: 项目更新检测标记和一键检测

**Files:**
- Modify: `open_manager_py/static/js/app.js`
- Modify: `open_manager_py/static/css/style.css`
- Modify: `open_manager_py/templates/index.html`

- [ ] **Step 1: Write the failing test**

```python
def test_check_updates_api(client):
    """测试更新检测API"""
    response = client.post('/api/projects/check-updates', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_app_ui_api.py::test_check_updates_api -v`
Expected: PASS (backend already exists)

- [ ] **Step 3: Add update check button to projects toolbar**

```html
<!-- 在 projects-tab toolbar 中 updateAllBtn 前添加 -->
<button id="checkUpdatesBtn" class="btn btn-secondary">🔍 检测更新</button>
```

- [ ] **Step 4: Add update badge rendering and handler**

```javascript
// 在 initButtons 中添加
document.getElementById('checkUpdatesBtn').addEventListener('click', checkProjectUpdates);

// 修改 renderProjects 中标题部分
let title = escapeHtml(project.name);
if (project.version) {
    title += ` <span class="version-tag">v${escapeHtml(project.version)}</span>`;
}
if (project.has_update) {
    title += ' <span class="update-badge">有更新</span>';
}

async function checkProjectUpdates() {
    const btn = document.getElementById('checkUpdatesBtn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '检测中...';
    
    try {
        const response = await fetch('/api/projects/check-updates', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(`检测完成：${data.result.has_update} 个有更新`, 'success');
            await loadProjects();
        } else {
            showToast(data.error || '检测失败', 'error');
        }
    } catch (error) {
        showToast('检测失败', 'error');
        console.error(error);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}
```

- [ ] **Step 5: Add CSS for update badge**

```css
.update-badge {
    display: inline-block;
    background: #ff6b6b;
    color: white;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 12px;
    margin-left: 8px;
    font-weight: 600;
}
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_app_ui_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add open_manager_py/templates/index.html open_manager_py/static/js/app.js open_manager_py/static/css/style.css tests/test_app_ui_api.py
git commit -m "feat: 前端集成项目更新检测,显示更新徽章"
```

---

## Task 5: 分发技能支持动态加载全部 AI 工具

**Files:**
- Modify: `open_manager_py/static/js/app.js`
- Modify: `open_manager_py/templates/index.html:82-115`

- [ ] **Step 1: Write the failing test**

```python
def test_distribute_targets_api(client):
    """测试分发目标API返回10+工具"""
    response = client.get('/api/distribute-targets')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 10
    assert 'trae' in data
    assert 'cursor' in data
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_app_ui_api.py::test_distribute_targets_api -v`
Expected: PASS (backend already exists)

- [ ] **Step 3: Replace static tool checkboxes with dynamic container**

```html
<!-- 在 distributeModal 的 tool-options 中，替换静态 checkbox 为 -->
<div id="distributeToolOptions" class="tool-options">
    <div class="loading-tools">加载工具列表...</div>
</div>
```

- [ ] **Step 4: Add dynamic tool loading in app.js**

```javascript
// 在 distributeSkills 函数中加载工具列表
async function distributeSkills() {
    document.getElementById('distributeModal').classList.add('show');
    await loadDistributeTargets();
}

async function loadDistributeTargets() {
    const container = document.getElementById('distributeToolOptions');
    try {
        const response = await fetch('/api/distribute-targets');
        const data = await response.json();
        
        container.innerHTML = Object.entries(data).map(([key, path]) => `
            <label class="tool-option" title="${escapeHtml(path)}">
                <input type="checkbox" name="tool" value="${escapeHtml(key)}">
                <span>${escapeHtml(key)}</span>
            </label>
        `).join('');
    } catch (error) {
        container.innerHTML = '<div class="empty-state-hint">加载工具列表失败</div>';
        console.error(error);
    }
}
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_app_ui_api.py tests/test_targets.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add open_manager_py/templates/index.html open_manager_py/static/js/app.js tests/test_app_ui_api.py
git commit -m "feat: 分发技能弹窗动态加载全部AI工具目标"
```

---

## Task 6: 数据导出导入 UI

**Files:**
- Modify: `open_manager_py/templates/index.html`
- Modify: `open_manager_py/static/js/app.js`
- Modify: `open_manager_py/static/css/style.css`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_app_ui_api.py::test_export_api -v`
Expected: PASS (backend already exists)

- [ ] **Step 3: Add export/import buttons to header**

```html
<!-- 在 header-actions 中 scanBtn 后添加 -->
<button id="exportBtn" class="btn btn-secondary">📥 导出</button>
<button id="importBtn" class="btn btn-secondary">📤 导入</button>
```

- [ ] **Step 4: Add import modal to HTML**

```html
<div id="importModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2>导入数据</h2>
            <button class="close-btn" onclick="closeImportModal()">&times;</button>
        </div>
        <div class="modal-body">
            <div class="form-group">
                <label for="importFile">选择 JSON 文件</label>
                <input type="file" id="importFile" accept=".json" class="form-input">
            </div>
            <div class="form-hint">导入将更新现有记录的分类、标签和备注，不会创建新记录。</div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeImportModal()">取消</button>
            <button id="confirmImportBtn" class="btn btn-primary">导入</button>
        </div>
    </div>
</div>
```

- [ ] **Step 5: Add export/import logic to app.js**

```javascript
// 在 initButtons 中添加
document.getElementById('exportBtn').addEventListener('click', exportData);
document.getElementById('importBtn').addEventListener('click', openImportModal);
document.getElementById('confirmImportBtn').addEventListener('click', importData);

async function exportData() {
    try {
        const response = await fetch('/api/export', { method: 'POST' });
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `open_manager_backup_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('导出成功', 'success');
    } catch (error) {
        showToast('导出失败', 'error');
        console.error(error);
    }
}

function openImportModal() {
    document.getElementById('importModal').classList.add('show');
}

function closeImportModal() {
    document.getElementById('importModal').classList.remove('show');
    document.getElementById('importFile').value = '';
}

async function importData() {
    const fileInput = document.getElementById('importFile');
    const file = fileInput.files[0];
    if (!file) {
        showToast('请选择文件', 'error');
        return;
    }
    
    try {
        const text = await file.text();
        const data = JSON.parse(text);
        
        const response = await fetch('/api/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            showToast(`导入成功：更新 ${result.skills_updated} 个技能，${result.projects_updated} 个项目`, 'success');
            closeImportModal();
            await loadSkills();
            await loadProjects();
            await loadStats();
        } else {
            showToast(result.error || '导入失败', 'error');
        }
    } catch (error) {
        showToast('导入失败：文件格式错误', 'error');
        console.error(error);
    }
}
```

- [ ] **Step 6: Add CSS for import modal**

```css
.form-hint {
    font-size: 12px;
    color: #666;
    margin-top: 8px;
    line-height: 1.5;
}
```

- [ ] **Step 7: Run tests**

Run: `python -m pytest tests/test_export_import.py tests/test_app_ui_api.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add open_manager_py/templates/index.html open_manager_py/static/js/app.js open_manager_py/static/css/style.css tests/test_app_ui_api.py
git commit -m "feat: 前端新增数据导出导入UI"
```

---

## Task 7: 运行完整测试并修复问题

- [ ] **Step 1: Run all tests**

Run: `python -m pytest tests/ -v --timeout=30`
Expected: All PASS

- [ ] **Step 2: Run demo and verify manually**

Run: `python run.py`
Then open `http://127.0.0.1:5000` and verify:
1. Dashboard tab shows stats
2. Search with tags works
3. README button opens modal
4. Check updates button works
5. Distribute shows all tools
6. Export/Import works

- [ ] **Step 3: Commit any fixes**

```bash
git commit -m "fix: v0.4.0 UI集成测试修复"
```

---

## Task 8: 推送 GitHub

- [ ] **Step 1: Push to GitHub**

```bash
git push origin main
```

Expected: push successful

---

## Self-Review

**1. Spec coverage:**
- Dashboard 统计：Task 1
- 后端搜索 API 集成：Task 2
- README 预览：Task 3
- 更新检测：Task 4
- 多工具分发：Task 5
- 导出导入：Task 6
- 测试验证：Task 7
- 推送：Task 8

**2. Placeholder scan:** 无 TBD/TODO，所有步骤包含完整代码。

**3. Type consistency:** API 路径与 v0.3.0 后端一致，函数名统一使用 camelCase。
