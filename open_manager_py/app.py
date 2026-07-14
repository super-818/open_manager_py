"""
Flask Web应用 - 主应用入口
"""

from flask import Flask, render_template, jsonify, request
import subprocess
import platform
import webbrowser
import os
from pathlib import Path

from .config import get_config
from .database import get_database
from .scanner import get_scanner
from . import __version__

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if not size_bytes:
        return '0 B'
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/skills')
def get_skills():
    """获取所有技能，支持 ?sort_by= 参数"""
    from .services import SkillService
    sort_by = request.args.get('sort_by')
    service = SkillService()
    skills = service.list_all(sort_by=sort_by)
    for skill in skills:
        skill['local_size_formatted'] = format_size(skill.get('local_size', 0))
        if 'remark' in skill:
            skill['notes'] = skill['remark']
        tags = skill.get('tags')
        if tags and isinstance(tags, list):
            skill['tags'] = ', '.join(tags)
    return jsonify(skills)


@app.route('/api/projects')
def get_projects():
    """获取所有项目，支持 ?sort_by= 参数"""
    from .services import ProjectService
    sort_by = request.args.get('sort_by')
    service = ProjectService()
    projects = service.list_all(sort_by=sort_by)
    for project in projects:
        project['local_size_formatted'] = format_size(project.get('local_size', 0))
        if 'remark' in project:
            project['notes'] = project['remark']
        tags = project.get('tags')
        if tags and isinstance(tags, list):
            project['tags'] = ', '.join(tags)
    return jsonify(projects)


@app.route('/api/scan', methods=['POST'])
def scan_directories():
    """扫描目录"""
    scanner = get_scanner()
    result = scanner.scan_all()
    db = get_database()
    skills_count = len(db.get_all_skills())
    projects_count = len(db.get_all_projects())
    return jsonify({
        'success': True,
        'skills_count': skills_count,
        'projects_count': projects_count,
        'result': result
    })


@app.route('/api/skill/<int:skill_id>', methods=['PUT'])
def update_skill(skill_id: int):
    """更新技能"""
    data = request.get_json()
    db_data = {}
    if 'notes' in data:
        db_data['remark'] = data['notes']
    if 'category' in data:
        db_data['category'] = data['category']
    if 'tags' in data:
        tags_str = data['tags']
        if tags_str:
            db_data['tags'] = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        else:
            db_data['tags'] = None
    db = get_database()
    success = db.update_skill(skill_id, **db_data)
    return jsonify({'success': success})


@app.route('/api/project/<int:project_id>', methods=['PUT'])
def update_project(project_id: int):
    """更新项目"""
    data = request.get_json()
    db_data = {}
    if 'notes' in data:
        db_data['remark'] = data['notes']
    if 'category' in data:
        db_data['category'] = data['category']
    if 'tags' in data:
        tags_str = data['tags']
        if tags_str:
            db_data['tags'] = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        else:
            db_data['tags'] = None
    db = get_database()
    success = db.update_project(project_id, **db_data)
    return jsonify({'success': success})


@app.route('/api/skill/<int:skill_id>/delete', methods=['POST'])
def delete_skill(skill_id: int):
    """删除技能"""
    db = get_database()
    success = db.delete_skill(skill_id, soft_delete=False)
    return jsonify({'success': success})


@app.route('/api/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id: int):
    """删除项目"""
    db = get_database()
    success = db.delete_project(project_id, soft_delete=False)
    return jsonify({'success': success})


@app.route('/api/open/directory', methods=['POST'])
def open_directory():
    """打开目录"""
    data = request.get_json()
    path = data.get('path')
    if not path:
        return jsonify({'success': False, 'error': 'Path is required'})
    
    try:
        if platform.system() == 'Windows':
            os.startfile(path)
        elif platform.system() == 'Darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/open/github', methods=['POST'])
def open_github():
    """打开GitHub URL"""
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    try:
        webbrowser.open(url)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})





PRESET_CATEGORIES = [
    {'value': '科研类', 'label': '科研类', 'color': '#6c5ce7'},
    {'value': '金融类', 'label': '金融类', 'color': '#00b894'},
    {'value': '开发工具', 'label': '开发工具', 'color': '#0984e3'},
    {'value': '数据分析', 'label': '数据分析', 'color': '#e17055'},
    {'value': 'AI/ML', 'label': 'AI/ML', 'color': '#fdcb6e'},
    {'value': '自动化', 'label': '自动化', 'color': '#e84393'},
    {'value': '安全', 'label': '安全', 'color': '#d63031'},
    {'value': '设计', 'label': '设计', 'color': '#a29bfe'},
    {'value': '其他', 'label': '其他', 'color': '#636e72'},
]


@app.route('/api/categories')
def get_categories():
    """获取预设分类列表（自定义分类自动生成稳定颜色）"""
    def _hash_color(name: str) -> str:
        h = 0
        for ch in name:
            h = ord(ch) + ((h << 5) - h)
        hue = abs(h) % 360
        return f'hsl({hue}, 60%, 45%)'

    db = get_database()
    skills = db.get_all_skills()
    projects = db.get_all_projects()
    used_categories = set()
    for s in skills:
        if s.get('category'):
            used_categories.add(s['category'])
    for p in projects:
        if p.get('category'):
            used_categories.add(p['category'])
    custom_categories = []
    for cat in used_categories:
        if not any(p['value'] == cat for p in PRESET_CATEGORIES):
            custom_categories.append({'value': cat, 'label': cat, 'color': _hash_color(cat)})
    all_categories = PRESET_CATEGORIES + custom_categories
    return jsonify(all_categories)


@app.route('/api/config')
def get_config_api():
    """获取配置"""
    config = get_config()
    return jsonify({
        'skills_dir': str(config.get_skills_dir()),
        'github_dir': str(config.get_github_dir())
    })


@app.route('/api/skill/<int:skill_id>/update', methods=['POST'])
def update_skill_single(skill_id: int):
    """更新单个技能"""
    try:
        db = get_database()
        skill = db.get_skill(skill_id)
        if not skill:
            return jsonify({'success': False, 'error': 'Skill not found'})
        
        scanner = get_scanner()
        result = scanner.scan_skills()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/project/<int:project_id>/update', methods=['POST'])
def update_project_single(project_id: int):
    """更新单个项目"""
    from .services import ProjectService
    service = ProjectService()
    result = service.update_project(project_id)
    return jsonify(result)


@app.route('/api/skills/distribute', methods=['POST'])
def distribute_skills():
    """分发技能到各个工具"""
    try:
        data = request.get_json()
        category = data.get('category')
        tools = data.get('tools', [])
        custom_path = data.get('customPath')
        
        db = get_database()
        skills = db.get_all_skills()
        
        if category:
            skills = [s for s in skills if s.get('category') == category]
        
        count = len(skills)
        
        target_paths = []
        
        for tool in tools:
            if tool == 'trae':
                trae_path = Path.home() / '.trae' / 'skills'
                target_paths.append(trae_path)
            elif tool == 'claude-code':
                claude_path = Path.home() / 'claude-code' / 'skills'
                target_paths.append(claude_path)
            elif tool == 'openclaw':
                openclaw_path = Path.home() / 'openclaw' / 'skills'
                target_paths.append(openclaw_path)
        
        if custom_path:
            target_paths.append(Path(custom_path))
        
        import shutil
        
        for target_path in target_paths:
            try:
                target_path.mkdir(parents=True, exist_ok=True)
                
                for skill in skills:
                    skill_path = Path(skill['path'])
                    if skill_path.exists():
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
            except Exception as e:
                print(f"Error distributing to {target_path}: {e}")
        
        return jsonify({
            'success': True,
            'count': count,
            'message': f'已分发 {count} 个技能到 {len(target_paths)} 个目标'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/projects/export-paths', methods=['POST'])
def export_project_paths():
    """导出项目路径到剪贴板"""
    try:
        data = request.get_json()
        category = data.get('category')
        
        db = get_database()
        projects = db.get_all_projects()
        
        if category:
            projects = [p for p in projects if p.get('category') == category]
        
        paths = '\n'.join([p['path'] for p in projects])
        
        return jsonify({
            'success': True,
            'paths': paths,
            'count': len(projects)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/projects/update-all', methods=['POST'])
def update_all_projects():
    """更新所有项目"""
    from .services import ProjectService
    service = ProjectService()
    result = service.update_all_projects()
    return jsonify(result)


@app.route('/api/skills/search', methods=['POST'])
def search_skills():
    """搜索技能(按名称、备注、标签、分类)"""
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
    """搜索项目(按名称、备注、标签、分类)"""
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


@app.route('/api/stats')
def get_stats():
    """获取统计数据(技能/项目数量、分类分布、总大小)"""
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


@app.route('/api/projects/check-updates', methods=['POST'])
def check_updates():
    """检测所有项目的远程更新状态(轻量,不下载代码)"""
    from .updater import UpdateChecker
    checker = UpdateChecker()
    result = checker.check_projects()
    return jsonify({'success': True, 'result': result})


@app.route('/api/distribute-targets')
def get_distribute_targets():
    """获取所有可用的分发目标"""
    from .targets import list_targets
    return jsonify(list_targets())


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
        'version': __version__
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


def run_server(host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    """运行Web服务器"""
    app.run(host=host, port=port, debug=debug)


def main():
    """主函数入口"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='开源资源管理器 - Web版本')
    parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    print(f'启动开源资源管理器Web服务...')
    print(f'访问地址: http://{args.host}:{args.port}')
    run_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
