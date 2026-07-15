"""
目录扫描模块 - 扫描技能和项目目录并同步到数据库
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple, Set, Optional
import re
import subprocess

from .config import get_config
from .database import get_database


class DirectoryScanner:
    """目录扫描器"""
    
    def __init__(self):
        """初始化扫描器"""
        self.config = get_config()
        self.db = get_database()
    
    def scan_skills(self) -> Tuple[int, int, int]:
        """
        扫描技能目录
        
        Returns:
            (新增数量, 更新数量, 删除数量)
        """
        skills_dir = self.config.get_skills_dir()
        
        if not skills_dir.exists():
            return 0, 0, 0
        
        existing_skills = self.db.get_all_skills()
        existing_paths = {s['path'] for s in existing_skills}
        
        scanned_paths: Set[str] = set()
        new_count = 0
        update_count = 0
        
        if skills_dir.is_dir():
            for item in skills_dir.iterdir():
                if item.is_dir():
                    skill_md = item / "SKILL.md"
                    if skill_md.exists():
                        path = str(item.resolve())
                        name = item.name
                        md_hash = self.db.calculate_file_hash(skill_md)
                        github_url = self._extract_github_url(skill_md)
                        version = self._extract_dir_version(item)
                        last_commit_time = self._extract_last_commit_time(item)
                        
                        if path not in existing_paths:
                            self.db.add_skill(
                                name=name,
                                path=path,
                                md_hash=md_hash,
                                github_url=github_url,
                                version=version,
                                last_commit_time=last_commit_time
                            )
                            new_count += 1
                        else:
                            existing_skill = self.db.get_skill_by_path(path)
                            update_data = {'md_hash': md_hash, 'github_url': github_url, 'version': version, 'last_commit_time': last_commit_time}
                            need_update = existing_skill and (
                                existing_skill.get('md_hash') != md_hash
                                or existing_skill.get('version') != version
                                or existing_skill.get('last_commit_time') != last_commit_time
                            )
                            if need_update:
                                self.db.update_skill(
                                    existing_skill['id'],
                                    **update_data
                                )
                                update_count += 1
                        
                        scanned_paths.add(path)
        
        delete_count = 0
        for skill in existing_skills:
            if skill['path'] not in scanned_paths:
                self.db.delete_skill(skill['id'], soft_delete=False)
                delete_count += 1
        
        return new_count, update_count, delete_count
    
    def scan_projects(self) -> Tuple[int, int, int]:
        """
        扫描GitHub项目目录
        
        Returns:
            (新增数量, 更新数量, 删除数量)
        """
        github_dir = self.config.get_github_dir()
        
        if not github_dir.exists():
            return 0, 0, 0
        
        existing_projects = self.db.get_all_projects()
        existing_paths = {p['path'] for p in existing_projects}
        
        scanned_paths: Set[str] = set()
        new_count = 0
        update_count = 0
        
        if github_dir.is_dir():
            for item in github_dir.iterdir():
                if item.is_dir():
                    git_dir = item / ".git"
                    if git_dir.exists():
                        path = str(item.resolve())
                        name = item.name
                        repo_hash = self._calculate_repo_hash(item)
                        github_url = self._extract_repo_url(item)
                        version = self._extract_dir_version(item)
                        last_commit_time = self._extract_last_commit_time(item)
                        
                        if path not in existing_paths:
                            self.db.add_project(
                                name=name,
                                path=path,
                                repo_hash=repo_hash,
                                github_url=github_url,
                                version=version,
                                last_commit_time=last_commit_time
                            )
                            new_count += 1
                        else:
                            existing_project = self.db.get_project_by_path(path)
                            update_data = {'repo_hash': repo_hash, 'github_url': github_url, 'version': version, 'last_commit_time': last_commit_time}
                            need_update = existing_project and (
                                existing_project.get('repo_hash') != repo_hash
                                or existing_project.get('version') != version
                                or existing_project.get('last_commit_time') != last_commit_time
                            )
                            if need_update:
                                self.db.update_project(
                                    existing_project['id'],
                                    **update_data
                                )
                                update_count += 1
                        
                        scanned_paths.add(path)
        
        delete_count = 0
        for project in existing_projects:
            if project['path'] not in scanned_paths:
                self.db.delete_project(project['id'], soft_delete=False)
                delete_count += 1
        
        return new_count, update_count, delete_count
    
    def scan_all(self) -> Dict[str, Tuple[int, int, int]]:
        """
        扫描所有目录
        
        Returns:
            {'skills': (新增, 更新, 删除), 'projects': (新增, 更新, 删除)}
        """
        skills_result = self.scan_skills()
        projects_result = self.scan_projects()
        
        return {
            'skills': skills_result,
            'projects': projects_result
        }
    
    def _extract_github_url(self, skill_md: Path) -> Optional[str]:
        """从SKILL.md中提取GitHub URL"""
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()
                github_pattern = r'https?://github\.com/[\w\-]+/[\w\-]+'
                matches = re.findall(github_pattern, content)
                if matches:
                    return matches[0]
        except Exception:
            pass
        return None
    
    def _extract_repo_url(self, repo_dir: Path) -> Optional[str]:
        """从Git仓库中提取远程URL"""
        try:
            git_config = repo_dir / ".git" / "config"
            if git_config.exists():
                with open(git_config, 'r', encoding='utf-8') as f:
                    content = f.read()
                    url_pattern = r'url\s*=\s*(.+)'
                    matches = re.findall(url_pattern, content)
                    if matches:
                        url = matches[0].strip()
                        if url.startswith('git@github.com:'):
                            url = url.replace('git@github.com:', 'https://github.com/')
                        if url.endswith('.git'):
                            url = url[:-4]
                        return url
        except Exception:
            pass
        return None
    
    def _calculate_repo_hash(self, repo_dir: Path) -> Optional[str]:
        """计算Git仓库的哈希值（基于config和README）"""
        try:
            import hashlib
            
            hash_obj = hashlib.sha256()
            
            git_config = repo_dir / ".git" / "config"
            if git_config.exists():
                with open(git_config, 'rb') as f:
                    hash_obj.update(f.read())
            
            readme_files = ['README.md', 'README.rst', 'README.txt', 'readme.md']
            for readme_name in readme_files:
                readme_path = repo_dir / readme_name
                if readme_path.exists():
                    with open(readme_path, 'rb') as f:
                        hash_obj.update(f.read())
                    break
            
            return hash_obj.hexdigest()
        except Exception:
            return None
    
    def _extract_dir_version(self, repo_dir: Path) -> Optional[str]:
        """从目录提取版本号（优先使用git tag，然后从配置文件提取）。
        注意：不会把commit hash当版本号，只有形如v1.2.3/1.2.3的tag或配置文件中的版本才返回。"""
        version = None
        
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                tag = result.stdout.strip()
                if tag and re.match(r'^v?\d+(\.\d+)*', tag):
                    if tag.startswith('v'):
                        tag = tag[1:]
                    return tag
        except Exception:
            pass
        
        version_files = ['setup.py', 'pyproject.toml', 'package.json', 'VERSION', 'SKILL.md']
        for filename in version_files:
            filepath = repo_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if filename == 'setup.py':
                            match = re.search(r'version\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                        elif filename == 'pyproject.toml':
                            match = re.search(r'version\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                        elif filename == 'package.json':
                            import json
                            try:
                                data = json.loads(content)
                                if 'version' in data and isinstance(data['version'], str):
                                    return data['version'].strip()
                            except:
                                pass
                            continue
                        elif filename == 'VERSION':
                            return content.strip()
                        elif filename == 'SKILL.md':
                            match = re.search(r'(?:版本|version)\s*[:：]\s*([^\n\r]+)', content, re.IGNORECASE)
                        else:
                            match = None
                        
                        if match:
                            ver = match.group(1).strip()
                            if ver and re.match(r'^\d+(\.\d+)*', ver):
                                return ver
                except Exception:
                    pass
        
        return version

    def _extract_last_commit_time(self, repo_dir: Path) -> Optional[str]:
        """提取最近一次git commit的时间（ISO格式），非git目录返回文件修改时间"""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%cI'],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                t = result.stdout.strip()
                if t:
                    return t
        except Exception:
            pass
        try:
            import os
            mtime = repo_dir.stat().st_mtime
            from datetime import datetime
            return datetime.fromtimestamp(mtime).isoformat()
        except Exception:
            return None


_scanner_instance: Optional[DirectoryScanner] = None


def get_scanner() -> DirectoryScanner:
    """获取全局扫描器实例"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = DirectoryScanner()
    return _scanner_instance
