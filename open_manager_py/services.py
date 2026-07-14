"""业务逻辑服务层 - Web和CLI共用的核心逻辑"""
from typing import List, Dict, Any, Optional
from pathlib import Path

from .database import get_database
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
