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
    """获取所有技能"""
    db = get_database()
    skills = db.get_all_skills()
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
    """获取所有项目"""
    db = get_database()
    projects = db.get_all_projects()
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
    """更新单个项目 - 使用git clone最新版（静默进行）"""
    import shutil
    import tempfile
    
    try:
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'})
        
        project_path = Path(project['path'])
        github_url = project.get('github_url')
        
        if not github_url:
            return jsonify({'success': False, 'error': 'No GitHub URL found'})
        
        # 备份旧目录
        parent_dir = project_path.parent
        temp_dir = tempfile.mkdtemp(dir=str(parent_dir))
        backup_path = Path(temp_dir) / project_path.name
        
        try:
            if project_path.exists():
                shutil.move(str(project_path), str(backup_path))
            
            # 克隆最新版
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', github_url, str(project_path)],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                # 克隆成功，删除备份
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                
                scanner = get_scanner()
                scan_result = scanner.scan_projects()
                return jsonify({
                    'success': True,
                    'message': 'Project updated successfully',
                    'result': scan_result
                })
            else:
                # 克隆失败，恢复备份
                if backup_path.exists():
                    if project_path.exists():
                        shutil.rmtree(str(project_path))
                    shutil.move(str(backup_path), str(project_path))
                
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                
                return jsonify({
                    'success': False,
                    'error': f'Git clone failed: {result.stderr}'
                })
        except subprocess.TimeoutExpired:
            # 超时，恢复备份
            if backup_path.exists():
                if project_path.exists():
                    shutil.rmtree(str(project_path))
                shutil.move(str(backup_path), str(project_path))
            
            # 清理临时目录
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            return jsonify({'success': False, 'error': 'Git clone timeout'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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
    """更新所有项目 - 使用git clone最新版（静默进行）"""
    import shutil
    import tempfile
    
    try:
        db = get_database()
        projects = db.get_all_projects()
        updated_count = 0
        failed_count = 0
        errors = []
        
        for project in projects:
            project_path = Path(project['path'])
            github_url = project.get('github_url')
            
            if not github_url:
                failed_count += 1
                errors.append(f"{project['name']}: No GitHub URL")
                continue
            
            # 备份旧目录
            parent_dir = project_path.parent
            temp_dir = tempfile.mkdtemp(dir=str(parent_dir))
            backup_path = Path(temp_dir) / project_path.name
            
            try:
                if project_path.exists():
                    shutil.move(str(project_path), str(backup_path))
                
                # 克隆最新版
                result = subprocess.run(
                    ['git', 'clone', '--depth', '1', github_url, str(project_path)],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode == 0:
                    # 克隆成功，删除备份
                    updated_count += 1
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                else:
                    # 克隆失败，恢复备份
                    failed_count += 1
                    errors.append(f"{project['name']}: {result.stderr}")
                    if backup_path.exists():
                        if project_path.exists():
                            shutil.rmtree(str(project_path))
                        shutil.move(str(backup_path), str(project_path))
                    
                    # 清理临时目录
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                    
            except subprocess.TimeoutExpired:
                # 超时，恢复备份
                failed_count += 1
                errors.append(f"{project['name']}: Timeout")
                if backup_path.exists():
                    if project_path.exists():
                        shutil.rmtree(str(project_path))
                    shutil.move(str(backup_path), str(project_path))
                
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            except Exception as e:
                failed_count += 1
                errors.append(f"{project['name']}: {str(e)}")
                if backup_path.exists():
                    if project_path.exists():
                        shutil.rmtree(str(project_path))
                    shutil.move(str(backup_path), str(project_path))
                
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
        
        # 重新扫描项目
        scanner = get_scanner()
        scan_result = scanner.scan_projects()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'failed_count': failed_count,
            'errors': errors,
            'result': scan_result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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
