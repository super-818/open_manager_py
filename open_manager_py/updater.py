"""更新检测模块 - 使用git ls-remote轻量检测远程更新"""
import subprocess
from typing import Optional, Dict, Any
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
