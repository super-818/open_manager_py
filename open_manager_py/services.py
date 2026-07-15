"""业务逻辑服务层 - Web和CLI共用的核心逻辑"""
import shutil
import subprocess
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

from .database import get_database
from .logger import get_logger


def _sort_items(items: List[Dict[str, Any]], sort_by: Optional[str]) -> List[Dict[str, Any]]:
    """通用排序函数: name / name_desc / size / size_desc / time / time_desc
    time排序优先使用last_commit_time（最近git提交时间），降级到last_updated/create_time"""
    if not sort_by:
        return items
    reverse = sort_by.endswith('_desc')
    key = sort_by.replace('_desc', '')
    if key == 'name':
        return sorted(items, key=lambda x: (x.get('name') or '').lower(), reverse=reverse)
    if key == 'size':
        return sorted(items, key=lambda x: x.get('local_size') or 0, reverse=reverse)
    if key == 'time':
        def _time_key(x):
            return x.get('last_commit_time') or x.get('last_updated') or x.get('create_time') or x.get('created_at') or ''
        return sorted(items, key=_time_key, reverse=reverse)
    return items


class SkillService:
    """技能业务服务"""

    def __init__(self):
        """初始化技能服务"""
        self.db = get_database()
        self.logger = get_logger()

    def list_all(self, sort_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有技能，支持排序"""
        return _sort_items(self.db.get_all_skills(), sort_by)

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

    def list_all(self, sort_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有项目，支持排序"""
        return _sort_items(self.db.get_all_projects(), sort_by)

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

    def update_project(self, project_id: int) -> Dict[str, Any]:
        """更新单个项目（git clone --depth 1 替换目录，失败自动回滚）"""
        project = self.db.get_project(project_id)
        if not project:
            return {'success': False, 'error': 'Project not found'}
        github_url = project.get('github_url')
        if not github_url:
            return {'success': False, 'error': 'No GitHub URL found'}
        project_path = Path(project['path'])
        return self._do_clone_update(project_path, github_url)

    def update_all_projects(self) -> Dict[str, Any]:
        """更新所有带 GitHub URL 的项目"""
        from .scanner import get_scanner
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
        try:
            get_scanner().scan_projects()
        except Exception as e:
            self.logger.error(f"更新后重新扫描失败: {e}")
        return {'success': True, 'updated_count': updated, 'failed_count': failed, 'errors': errors}

    def _do_clone_update(self, project_path: Path, github_url: str) -> Dict[str, Any]:
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
