let currentSkills = [];
let currentProjects = [];
let currentEditResource = null;
let currentEditType = null;
let isUpdating = false;
let categoriesCache = [];

const DEFAULT_CATEGORIES = [
    {value: '科研类', label: '科研类', color: '#6c5ce7'},
    {value: '金融类', label: '金融类', color: '#00b894'},
    {value: '开发工具', label: '开发工具', color: '#0984e3'},
    {value: '数据分析', label: '数据分析', color: '#e17055'},
    {value: 'AI/ML', label: 'AI/ML', color: '#fdcb6e'},
    {value: '自动化', label: '自动化', color: '#e84393'},
    {value: '安全', label: '安全', color: '#d63031'},
    {value: '设计', label: '设计', color: '#a29bfe'},
    {value: '其他', label: '其他', color: '#636e72'},
];

function getCategoryColor(category) {
    if (!category) return '#636e72';
    const found = categoriesCache.find(c => c.value === category);
    return found ? found.color : '#636e72';
}

document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initButtons();
    initModal();
    initProgressModal();
    loadCategories();
    loadStats();
    loadSkills();
    loadProjects();
});

function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    document.getElementById(`${tab}-tab`).classList.add('active');
}

function initButtons() {
    document.getElementById('scanBtn').addEventListener('click', scanDirectories);
    document.getElementById('distributeSkillsBtn').addEventListener('click', distributeSkills);
    document.getElementById('exportPathsBtn').addEventListener('click', exportPaths);
    document.getElementById('checkUpdatesBtn').addEventListener('click', checkProjectUpdates);
    document.getElementById('updateAllBtn').addEventListener('click', updateAllProjects);
    document.getElementById('exportBtn').addEventListener('click', exportData);
    document.getElementById('importBtn').addEventListener('click', openImportModal);
    document.getElementById('confirmImportBtn').addEventListener('click', importData);
    
    document.getElementById('skillSearch').addEventListener('input', debounce(searchSkills, 300));
    document.getElementById('skillCategory').addEventListener('change', searchSkills);
    document.getElementById('skillTags').addEventListener('input', debounce(searchSkills, 300));

    document.getElementById('projectSearch').addEventListener('input', debounce(searchProjects, 300));
    document.getElementById('projectCategory').addEventListener('change', searchProjects);
    document.getElementById('projectTags').addEventListener('input', debounce(searchProjects, 300));

    // 事件委托：处理资源卡片上的按钮点击
    document.getElementById('skillsList').addEventListener('click', handleResourceAction);
    document.getElementById('projectsList').addEventListener('click', handleResourceAction);
}

function handleResourceAction(event) {
    const btn = event.target.closest('.btn-action');
    if (!btn) return;

    const card = btn.closest('.resource-card');
    if (!card) return;

    const type = card.dataset.type;
    const id = parseInt(card.dataset.id);
    const path = card.dataset.path;
    const action = btn.dataset.action;

    switch(action) {
        case 'edit':
            editResource(type, id);
            break;
        case 'open':
            openDirectory(path);
            break;
        case 'readme':
            viewReadme(type, id);
            break;
        case 'update':
            updateResource(type, id);
            break;
        case 'delete':
            deleteResource(type, id);
            break;
    }
}

function initModal() {
    const editModal = document.getElementById('editModal');
    const distributeModal = document.getElementById('distributeModal');
    const closeBtns = document.querySelectorAll('.close-btn');
    const cancelBtn = document.getElementById('cancelBtn');
    const saveBtn = document.getElementById('saveBtn');
    const cancelDistributeBtn = document.getElementById('cancelDistributeBtn');
    const confirmDistributeBtn = document.getElementById('confirmDistributeBtn');
    const categorySelect = document.getElementById('editCategorySelect');
    const categoryCustomInput = document.getElementById('editCategoryCustom');

    closeBtns.forEach(btn => btn.addEventListener('click', closeAllModals));
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    if (saveBtn) saveBtn.addEventListener('click', saveResource);
    if (cancelDistributeBtn) cancelDistributeBtn.addEventListener('click', closeDistributeModal);
    if (confirmDistributeBtn) confirmDistributeBtn.addEventListener('click', confirmDistribute);

    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            if (this.value === '__custom__') {
                categoryCustomInput.style.display = 'block';
                categoryCustomInput.focus();
            } else {
                categoryCustomInput.style.display = 'none';
                categoryCustomInput.value = '';
            }
        });
    }

    if (editModal) {
        editModal.addEventListener('click', function(e) {
            if (e.target === editModal) {
                closeModal();
            }
        });
    }

    if (distributeModal) {
        distributeModal.addEventListener('click', function(e) {
            if (e.target === distributeModal) {
                closeDistributeModal();
            }
        });
    }
}

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const data = await response.json();
        categoriesCache = data;
    } catch (error) {
        categoriesCache = DEFAULT_CATEGORIES;
    }
}

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

async function loadSkills() {
    try {
        const response = await fetch('/api/skills');
        const data = await response.json();
        currentSkills = data;
        renderSkills(currentSkills);
        updateCategorySelect('skillCategory', currentSkills);
    } catch (error) {
        showToast('加载技能失败', 'error');
        console.error(error);
    }
}

async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        currentProjects = data;
        renderProjects(currentProjects);
        updateCategorySelect('projectCategory', currentProjects);
    } catch (error) {
        showToast('加载项目失败', 'error');
        console.error(error);
    }
}

async function loadDuplicates() {
    try {
        const response = await fetch('/api/duplicates');
        const data = await response.json();
        renderDuplicates(data);
    } catch (error) {
        showToast('加载重复资源失败', 'error');
        console.error(error);
    }
}

function renderSkills(skills) {
    const container = document.getElementById('skillsList');
    
    if (skills.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📦</div>
                <div class="empty-state-text">暂无技能</div>
                <div class="empty-state-hint">点击"扫描目录"按钮添加技能</div>
            </div>
        `;
        return;
    }

    container.innerHTML = skills.map(skill => `
        <div class="resource-card" data-type="skill" data-id="${skill.id}" data-path="${escapeHtml(skill.path)}">
            <div class="resource-header">
                <div>
                    <div class="resource-title">${escapeHtml(skill.name)}</div>
                    <div class="resource-path">${escapeHtml(skill.path)}</div>
                </div>
            </div>
            <div class="resource-meta">
                ${skill.category ? `<span class="meta-tag meta-category" style="background:${getCategoryColor(skill.category)}20;color:${getCategoryColor(skill.category)};border:1px solid ${getCategoryColor(skill.category)}40">${escapeHtml(skill.category)}</span>` : ''}
                ${skill.tags ? skill.tags.split(',').map(tag => `<span class="meta-tag">#${escapeHtml(tag.trim())}</span>`).join('') : ''}
                ${skill.github_url ? `<a href="${escapeHtml(skill.github_url)}" target="_blank" class="meta-tag meta-link">🔗 GitHub</a>` : ''}
            </div>
            ${skill.notes ? `<div class="resource-notes">${escapeHtml(skill.notes)}</div>` : ''}
            <div class="resource-actions">
                <button class="btn btn-small btn-primary btn-action" data-action="edit">编辑</button>
                <button class="btn btn-small btn-secondary btn-action" data-action="open">打开目录</button>
                <button class="btn btn-small btn-info btn-action" data-action="readme">README</button>
                <button class="btn btn-small btn-success btn-action" data-action="update">更新</button>
                <button class="btn btn-small btn-danger btn-action" data-action="delete">删除</button>
            </div>
        </div>
    `).join('');
}

function renderProjects(projects) {
    const container = document.getElementById('projectsList');
    
    if (projects.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🚀</div>
                <div class="empty-state-text">暂无项目</div>
                <div class="empty-state-hint">点击"扫描目录"按钮添加项目</div>
            </div>
        `;
        return;
    }

    container.innerHTML = projects.map(project => {
        let title = escapeHtml(project.name);
        if (project.version) {
            title += ` <span class="version-tag">v${escapeHtml(project.version)}</span>`;
        }
        if (project.has_update) {
            title += ' <span class="update-badge">有更新</span>';
        }

        return `
        <div class="resource-card" data-type="project" data-id="${project.id}" data-path="${escapeHtml(project.path)}">
            <div class="resource-header">
                <div>
                    <div class="resource-title">${title}</div>
                    <div class="resource-path">${escapeHtml(project.path)}</div>
                    ${project.create_time ? `<div class="resource-time">克隆时间: ${formatDate(project.create_time)}</div>` : ''}
                </div>
            </div>
            <div class="resource-meta">
                ${project.category ? `<span class="meta-tag meta-category" style="background:${getCategoryColor(project.category)}20;color:${getCategoryColor(project.category)};border:1px solid ${getCategoryColor(project.category)}40">${escapeHtml(project.category)}</span>` : ''}
                ${project.tags ? project.tags.split(',').map(tag => `<span class="meta-tag">#${escapeHtml(tag.trim())}</span>`).join('') : ''}
                ${project.github_url ? `<a href="${escapeHtml(project.github_url)}" target="_blank" class="meta-tag meta-link">🔗 GitHub</a>` : ''}
            </div>
            ${project.notes ? `<div class="resource-notes">${escapeHtml(project.notes)}</div>` : ''}
            <div class="resource-actions">
                <button class="btn btn-small btn-primary btn-action" data-action="edit">编辑</button>
                <button class="btn btn-small btn-secondary btn-action" data-action="open">打开目录</button>
                <button class="btn btn-small btn-info btn-action" data-action="readme">README</button>
                <button class="btn btn-small btn-success btn-action" data-action="update">更新</button>
                <button class="btn btn-small btn-danger btn-action" data-action="delete">删除</button>
            </div>
        </div>
    `}).join('');
}

function formatDate(dateStr) {
    try {
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateStr;
    }
}

async function updateResource(type, id) {
    try {
        const response = await fetch(`/api/${type}/${id}/update`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showToast('更新成功', 'success');
            await loadSkills();
            await loadProjects();
        } else {
            showToast(data.error || '更新失败', 'error');
        }
    } catch (error) {
        showToast('更新失败', 'error');
        console.error(error);
    }
}

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

function closeAllModals() {
    closeModal();
    closeDistributeModal();
}

function closeDistributeModal() {
    document.getElementById('distributeModal').classList.remove('show');
}

async function confirmDistribute() {
    const category = document.getElementById('skillCategory').value;
    const customPath = document.getElementById('customPath').value;
    const tools = Array.from(document.querySelectorAll('input[name="tool"]:checked')).map(cb => cb.value);
    
    if (tools.length === 0 && !customPath) {
        showToast('请至少选择一个工具或输入自定义路径', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/skills/distribute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                category,
                tools,
                customPath: customPath || null
            })
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(`分发成功！已分发 ${data.count} 个技能`, 'success');
            closeDistributeModal();
        } else {
            showToast(data.error || '分发失败', 'error');
        }
    } catch (error) {
        showToast('分发失败', 'error');
        console.error(error);
    }
}

async function exportPaths() {
    const category = document.getElementById('projectCategory').value;
    try {
        const response = await fetch('/api/projects/export-paths', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category })
        });
        const data = await response.json();

        if (data.success) {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(data.paths);
                showToast(`已复制 ${data.count} 个路径到剪贴板`, 'success');
            } else {
                showToast('复制失败，请手动复制', 'error');
            }
        } else {
            showToast(data.error || '导出失败', 'error');
        }
    } catch (error) {
        showToast('导出失败', 'error');
        console.error(error);
    }
}

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

function updateCategorySelect(selectId, resources) {
    const select = document.getElementById(selectId);
    const usedCategories = [...new Set(resources.map(r => r.category).filter(c => c))];
    const allCategoryValues = new Set(categoriesCache.map(c => c.value));
    const merged = [...categoriesCache];
    for (const cat of usedCategories) {
        if (!allCategoryValues.has(cat)) {
            merged.push({value: cat, label: cat, color: '#636e72'});
        }
    }
    select.innerHTML = '<option value="">全部分类</option>' + 
        merged.map(cat => `<option value="${escapeHtml(cat.value)}">${escapeHtml(cat.label)}</option>`).join('');
}

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

async function scanDirectories() {
    const btn = document.getElementById('scanBtn');
    btn.disabled = true;
    btn.textContent = '扫描中...';
    
    try {
        const response = await fetch('/api/scan', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(`扫描完成！发现 ${data.skills_count} 个技能，${data.projects_count} 个项目`, 'success');
            await loadSkills();
            await loadProjects();
        } else {
            showToast('扫描失败', 'error');
        }
    } catch (error) {
        showToast('扫描失败', 'error');
        console.error(error);
    } finally {
        btn.disabled = false;
        btn.textContent = '扫描目录';
    }
}

function editResource(type, id) {
    const resources = type === 'skill' ? currentSkills : currentProjects;
    const resource = resources.find(r => r.id === id);
    
    if (!resource) return;
    
    currentEditResource = resource;
    currentEditType = type;
    
    document.getElementById('modalTitle').textContent = `编辑${type === 'skill' ? '技能' : '项目'}`;
    
    populateCategorySelect(resource.category || '');
    document.getElementById('editTags').value = resource.tags || '';
    document.getElementById('editNotes').value = resource.notes || '';
    
    document.getElementById('editModal').classList.add('show');
}

function populateCategorySelect(currentCategory) {
    const select = document.getElementById('editCategorySelect');
    const customInput = document.getElementById('editCategoryCustom');
    
    const allCategoryValues = new Set(categoriesCache.map(c => c.value));
    const merged = [...categoriesCache];
    if (currentCategory && !allCategoryValues.has(currentCategory)) {
        merged.push({value: currentCategory, label: currentCategory, color: '#636e72'});
    }
    
    select.innerHTML = '<option value="">选择分类...</option>' +
        merged.map(cat => `<option value="${escapeHtml(cat.value)}">${escapeHtml(cat.label)}</option>`).join('') +
        '<option value="__custom__">自定义分类...</option>';
    
    if (currentCategory && allCategoryValues.has(currentCategory)) {
        select.value = currentCategory;
        customInput.style.display = 'none';
        customInput.value = '';
    } else if (currentCategory) {
        select.value = '__custom__';
        customInput.style.display = 'block';
        customInput.value = currentCategory;
    } else {
        select.value = '';
        customInput.style.display = 'none';
        customInput.value = '';
    }
}

async function saveResource() {
    if (!currentEditResource || !currentEditType) return;
    
    const categorySelect = document.getElementById('editCategorySelect');
    const customInput = document.getElementById('editCategoryCustom');
    let category = '';
    if (categorySelect.value === '__custom__') {
        category = customInput.value.trim();
    } else {
        category = categorySelect.value;
    }
    
    const data = {
        category: category,
        tags: document.getElementById('editTags').value,
        notes: document.getElementById('editNotes').value
    };
    
    try {
        const response = await fetch(`/api/${currentEditType}/${currentEditResource.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('保存成功', 'success');
            closeModal();
            await loadSkills();
            await loadProjects();
        } else {
            showToast('保存失败', 'error');
        }
    } catch (error) {
        showToast('保存失败', 'error');
        console.error(error);
    }
}

function closeModal() {
    document.getElementById('editModal').classList.remove('show');
    document.getElementById('editCategoryCustom').style.display = 'none';
    document.getElementById('editCategoryCustom').value = '';
    currentEditResource = null;
    currentEditType = null;
}

async function deleteResource(type, id) {
    if (!confirm('确定要删除这个资源吗？')) return;
    
    try {
        const response = await fetch(`/api/${type}/${id}/delete`, { method: 'POST' });
        
        if (response.ok) {
            showToast('删除成功', 'success');
            await loadSkills();
            await loadProjects();
        } else {
            showToast('删除失败', 'error');
        }
    } catch (error) {
        showToast('删除失败', 'error');
        console.error(error);
    }
}

async function openDirectory(path) {
    try {
        const response = await fetch('/api/open/directory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const data = await response.json();
        
        if (data.success) {
            showToast('已打开目录', 'success');
        } else {
            showToast(data.error || '打开目录失败', 'error');
        }
    } catch (error) {
        showToast('打开目录失败', 'error');
        console.error(error);
    }
}

async function openGitHub(url) {
    try {
        await fetch('/api/open/github', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
    } catch (error) {
        console.error(error);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type + ' show';
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function initProgressModal() {
    const closeBtn = document.getElementById('closeProgressBtn');
    const closeModalBtn = document.getElementById('closeProgressModalBtn');
    const progressModal = document.getElementById('progressModal');
    
    if (closeBtn) closeBtn.addEventListener('click', closeProgressModal);
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeProgressModal);
    
    if (progressModal) {
        progressModal.addEventListener('click', function(e) {
            if (e.target === progressModal && !isUpdating) {
                closeProgressModal();
            }
        });
    }
}

function showProgressModal(title) {
    const progressTitle = document.getElementById('progressTitle');
    const progressSubtitle = document.getElementById('progressSubtitle');
    const progressBar = document.getElementById('progressBar');
    const progressBarText = document.getElementById('progressBarText');
    const progressDetails = document.getElementById('progressDetails');
    const closeProgressModalBtn = document.getElementById('closeProgressModalBtn');
    const progressModal = document.getElementById('progressModal');
    
    if (progressTitle) progressTitle.textContent = title;
    if (progressSubtitle) progressSubtitle.textContent = '准备中...';
    if (progressBar) progressBar.style.width = '0%';
    if (progressBarText) progressBarText.textContent = '0%';
    if (progressDetails) progressDetails.innerHTML = '';
    if (closeProgressModalBtn) closeProgressModalBtn.style.display = 'none';
    if (progressModal) progressModal.classList.add('show');
    isUpdating = true;
}

function closeProgressModal() {
    if (isUpdating) return;
    const progressModal = document.getElementById('progressModal');
    if (progressModal) progressModal.classList.remove('show');
}

function updateProgress(current, total, subtitle) {
    const percent = Math.round((current / total) * 100);
    const progressBar = document.getElementById('progressBar');
    const progressBarText = document.getElementById('progressBarText');
    const progressSubtitle = document.getElementById('progressSubtitle');
    
    if (progressBar) progressBar.style.width = percent + '%';
    if (progressBarText) progressBarText.textContent = percent + '%';
    if (progressSubtitle) progressSubtitle.textContent = subtitle;
}

function addProgressDetail(name, status) {
    const details = document.getElementById('progressDetails');
    if (!details) return;
    
    const item = document.createElement('div');
    item.className = 'progress-item ' + status;
    let statusText = '';
    switch(status) {
        case 'pending':
            statusText = '⏳ 等待中';
            break;
        case 'updating':
            statusText = '🔄 更新中';
            break;
        case 'success':
            statusText = '✅ 成功';
            break;
        case 'error':
            statusText = '❌ 失败';
            break;
    }
    item.textContent = `${name} - ${statusText}`;
    details.appendChild(item);
    details.scrollTop = details.scrollHeight;
}

async function updateResource(type, id) {
    if (type !== 'project') {
        showToast('只有项目可以更新', 'error');
        return;
    }
    
    const project = currentProjects.find(p => p.id === id);
    if (!project) return;
    
    showProgressModal('更新项目');
    
    addProgressDetail(project.name, 'updating');
    updateProgress(0, 1, `正在更新: ${project.name}`);
    
    try {
        const response = await fetch(`/api/${type}/${id}/update`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            addProgressDetail(project.name, 'success');
            updateProgress(1, 1, '更新完成');
            showToast('更新成功', 'success');
            await loadSkills();
            await loadProjects();
        } else {
            addProgressDetail(project.name, 'error');
            updateProgress(1, 1, '更新失败');
            showToast(data.error || '更新失败', 'error');
        }
    } catch (error) {
        addProgressDetail(project.name, 'error');
        updateProgress(1, 1, '更新失败');
        showToast('更新失败', 'error');
        console.error(error);
    }
    
    isUpdating = false;
    const closeProgressModalBtn = document.getElementById('closeProgressModalBtn');
    if (closeProgressModalBtn) closeProgressModalBtn.style.display = 'block';
}

async function updateAllProjects() {
    if (!confirm('确定要更新所有项目吗？这可能需要一些时间。')) return;
    if (currentProjects.length === 0) {
        showToast('没有可更新的项目', 'error');
        return;
    }
    
    showProgressModal('批量更新项目');
    
    currentProjects.forEach(project => {
        addProgressDetail(project.name, 'pending');
    });
    
    let updatedCount = 0;
    let failedCount = 0;
    
    for (let i = 0; i < currentProjects.length; i++) {
        const project = currentProjects[i];
        
        updateProgress(i, currentProjects.length, `正在更新: ${project.name}`);
        
        const details = document.getElementById('progressDetails');
        const items = details.querySelectorAll('.progress-item');
        if (items[i]) {
            items[i].className = 'progress-item updating';
            items[i].textContent = `${project.name} - 🔄 更新中`;
        }
        
        try {
            const response = await fetch(`/api/project/${project.id}/update`, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                updatedCount++;
                if (items[i]) {
                    items[i].className = 'progress-item success';
                    items[i].textContent = `${project.name} - ✅ 成功`;
                }
            } else {
                failedCount++;
                if (items[i]) {
                    items[i].className = 'progress-item error';
                    items[i].textContent = `${project.name} - ❌ 失败: ${data.error || '未知错误'}`;
                }
            }
        } catch (error) {
            failedCount++;
            if (items[i]) {
                items[i].className = 'progress-item error';
                items[i].textContent = `${project.name} - ❌ 失败: ${error.message}`;
            }
            console.error(error);
        }
    }
    
    updateProgress(currentProjects.length, currentProjects.length, '更新完成');
    
    isUpdating = false;
    const closeProgressModalBtn = document.getElementById('closeProgressModalBtn');
    if (closeProgressModalBtn) closeProgressModalBtn.style.display = 'block';
    
    showToast(`更新完成！成功: ${updatedCount}, 失败: ${failedCount}`, updatedCount > 0 ? 'success' : 'error');
    await loadProjects();
}