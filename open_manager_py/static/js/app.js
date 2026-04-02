let currentSkills = [];
let currentProjects = [];
let currentEditResource = null;
let currentEditType = null;
let isUpdating = false;

document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initButtons();
    initModal();
    initProgressModal();
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
    document.getElementById('updateAllBtn').addEventListener('click', updateAllProjects);
    
    document.getElementById('skillSearch').addEventListener('input', filterSkills);
    document.getElementById('skillCategory').addEventListener('change', filterSkills);
    
    document.getElementById('projectSearch').addEventListener('input', filterProjects);
    document.getElementById('projectCategory').addEventListener('change', filterProjects);

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

    closeBtns.forEach(btn => btn.addEventListener('click', closeAllModals));
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    if (saveBtn) saveBtn.addEventListener('click', saveResource);
    if (cancelDistributeBtn) cancelDistributeBtn.addEventListener('click', closeDistributeModal);
    if (confirmDistributeBtn) confirmDistributeBtn.addEventListener('click', confirmDistribute);

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
                ${skill.category ? `<span class="meta-tag meta-category">${escapeHtml(skill.category)}</span>` : ''}
                ${skill.tags ? skill.tags.split(',').map(tag => `<span class="meta-tag">#${escapeHtml(tag.trim())}</span>`).join('') : ''}
                ${skill.github_url ? `<a href="${escapeHtml(skill.github_url)}" target="_blank" class="meta-tag meta-link">🔗 GitHub</a>` : ''}
            </div>
            ${skill.notes ? `<div class="resource-notes">${escapeHtml(skill.notes)}</div>` : ''}
            <div class="resource-actions">
                <button class="btn btn-small btn-primary btn-action" data-action="edit">编辑</button>
                <button class="btn btn-small btn-secondary btn-action" data-action="open">打开目录</button>
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
                ${project.category ? `<span class="meta-tag meta-category">${escapeHtml(project.category)}</span>` : ''}
                ${project.tags ? project.tags.split(',').map(tag => `<span class="meta-tag">#${escapeHtml(tag.trim())}</span>`).join('') : ''}
                ${project.github_url ? `<a href="${escapeHtml(project.github_url)}" target="_blank" class="meta-tag meta-link">🔗 GitHub</a>` : ''}
            </div>
            ${project.notes ? `<div class="resource-notes">${escapeHtml(project.notes)}</div>` : ''}
            <div class="resource-actions">
                <button class="btn btn-small btn-primary btn-action" data-action="edit">编辑</button>
                <button class="btn btn-small btn-secondary btn-action" data-action="open">打开目录</button>
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

function distributeSkills() {
    document.getElementById('distributeModal').classList.add('show');
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

function updateCategorySelect(selectId, resources) {
    const select = document.getElementById(selectId);
    const categories = [...new Set(resources.map(r => r.category).filter(c => c))];
    select.innerHTML = '<option value="">全部分类</option>' + 
        categories.map(cat => `<option value="${escapeHtml(cat)}">${escapeHtml(cat)}</option>`).join('');
}

function filterSkills() {
    const search = document.getElementById('skillSearch').value.toLowerCase();
    const category = document.getElementById('skillCategory').value;
    
    const filtered = currentSkills.filter(skill => {
        const matchSearch = !search || 
            skill.name.toLowerCase().includes(search) || 
            (skill.notes && skill.notes.toLowerCase().includes(search));
        const matchCategory = !category || skill.category === category;
        return matchSearch && matchCategory;
    });
    
    renderSkills(filtered);
}

function filterProjects() {
    const search = document.getElementById('projectSearch').value.toLowerCase();
    const category = document.getElementById('projectCategory').value;
    
    const filtered = currentProjects.filter(project => {
        const matchSearch = !search || 
            project.name.toLowerCase().includes(search) || 
            (project.notes && project.notes.toLowerCase().includes(search));
        const matchCategory = !category || project.category === category;
        return matchSearch && matchCategory;
    });
    
    renderProjects(filtered);
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
    document.getElementById('editCategory').value = resource.category || '';
    document.getElementById('editTags').value = resource.tags || '';
    document.getElementById('editNotes').value = resource.notes || '';
    
    document.getElementById('editModal').classList.add('show');
}

async function saveResource() {
    if (!currentEditResource || !currentEditType) return;
    
    const data = {
        category: document.getElementById('editCategory').value,
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