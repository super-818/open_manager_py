"""
数据库模块 - SQLite数据库初始化和操作
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import get_config


class Database:
    """数据库管理类"""
    
    def __init__(self):
        """初始化数据库"""
        self.config = get_config()
        self.db_path = self.config.get_db_path()
        self.conn = None
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                md_hash TEXT,
                github_url TEXT,
                category TEXT,
                tags TEXT,
                remark TEXT,
                local_size INTEGER,
                last_updated DATETIME,
                last_scan_time DATETIME,
                security_status TEXT DEFAULT 'unknown',
                security_report TEXT,
                is_deleted BOOLEAN DEFAULT 0,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                repo_hash TEXT,
                github_url TEXT,
                category TEXT,
                tags TEXT,
                remark TEXT,
                local_size INTEGER,
                last_updated DATETIME,
                last_check_update DATETIME,
                last_scan_time DATETIME,
                has_update BOOLEAN DEFAULT 0,
                security_status TEXT DEFAULT 'unknown',
                security_report TEXT,
                is_deleted BOOLEAN DEFAULT 0,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_skills_path ON skills(path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_path ON projects(path)')
        
        conn.commit()
    
    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """计算文件的SHA256哈希值"""
        try:
            if not file_path.exists():
                return None
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return None
    
    def calculate_dir_size(self, dir_path: Path) -> int:
        """计算目录大小（字节）"""
        total_size = 0
        try:
            for item in dir_path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception:
            pass
        return total_size
    
    def add_skill(self, name: str, path: str, md_hash: Optional[str] = None,
                  github_url: Optional[str] = None, category: Optional[str] = None,
                  tags: Optional[List[str]] = None, remark: Optional[str] = None) -> int:
        """添加技能 - 保留已有分类、标签、备注等信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        tags_json = json.dumps(tags) if tags else None
        local_size = self.calculate_dir_size(Path(path))
        
        try:
            existing = self.get_skill_by_path(path)
            if existing:
                update_fields = ['name', 'md_hash', 'github_url', 'local_size', 'last_updated']
                update_values = [name, md_hash, github_url, local_size, datetime.now().isoformat()]
                
                if category is not None:
                    update_fields.append('category')
                    update_values.append(category)
                if tags is not None:
                    update_fields.append('tags')
                    update_values.append(tags_json)
                if remark is not None:
                    update_fields.append('remark')
                    update_values.append(remark)
                
                update_values.append(existing['id'])
                cursor.execute(f'''
                    UPDATE skills SET {', '.join(f'{f} = ?' for f in update_fields)}
                    WHERE id = ?
                ''', update_values)
                conn.commit()
                return existing['id']
            else:
                cursor.execute('''
                    INSERT INTO skills 
                    (name, path, md_hash, github_url, category, tags, remark, local_size, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, path, md_hash, github_url, category, tags_json, remark, 
                      local_size, datetime.now().isoformat()))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error:
            return -1
    
    def get_skill(self, skill_id: int) -> Optional[Dict[str, Any]]:
        """获取技能"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM skills WHERE id = ? AND is_deleted = 0', (skill_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            if result.get('tags'):
                result['tags'] = json.loads(result['tags'])
            return result
        return None
    
    def get_skill_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """通过路径获取技能"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM skills WHERE path = ? AND is_deleted = 0', (path,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            if result.get('tags'):
                result['tags'] = json.loads(result['tags'])
            return result
        return None
    
    def get_all_skills(self) -> List[Dict[str, Any]]:
        """获取所有技能"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM skills WHERE is_deleted = 0 ORDER BY name')
        skills = []
        for row in cursor.fetchall():
            skill = dict(row)
            if skill.get('tags'):
                skill['tags'] = json.loads(skill['tags'])
            skills.append(skill)
        return skills
    
    def update_skill(self, skill_id: int, **kwargs) -> bool:
        """更新技能"""
        allowed_fields = ['name', 'md_hash', 'github_url', 'category', 'tags', 
                         'remark', 'security_status', 'security_report']
        update_fields = []
        update_values = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'tags' and value:
                    value = json.dumps(value)
                update_fields.append(f'{key} = ?')
                update_values.append(value)
        
        if not update_fields:
            return False
        
        update_fields.append('last_updated = ?')
        update_values.append(datetime.now().isoformat())
        update_values.append(skill_id)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f'UPDATE skills SET {", ".join(update_fields)} WHERE id = ?', 
                          update_values)
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def delete_skill(self, skill_id: int, soft_delete: bool = True) -> bool:
        """删除技能"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if soft_delete:
                cursor.execute('UPDATE skills SET is_deleted = 1 WHERE id = ?', (skill_id,))
            else:
                cursor.execute('DELETE FROM skills WHERE id = ?', (skill_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def get_duplicate_skills(self) -> List[List[Dict[str, Any]]]:
        """获取重复的技能（基于md_hash）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT md_hash, GROUP_CONCAT(id) as ids 
            FROM skills 
            WHERE md_hash IS NOT NULL AND is_deleted = 0
            GROUP BY md_hash 
            HAVING COUNT(*) > 1
        ''')
        
        duplicates = []
        for row in cursor.fetchall():
            ids = [int(x) for x in row['ids'].split(',')]
            group = []
            for skill_id in ids:
                skill = self.get_skill(skill_id)
                if skill:
                    group.append(skill)
            if group:
                duplicates.append(group)
        return duplicates
    
    def add_project(self, name: str, path: str, repo_hash: Optional[str] = None,
                   github_url: Optional[str] = None, category: Optional[str] = None,
                   tags: Optional[List[str]] = None, remark: Optional[str] = None) -> int:
        """添加项目 - 保留已有分类、标签、备注等信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        tags_json = json.dumps(tags) if tags else None
        local_size = self.calculate_dir_size(Path(path))
        
        try:
            existing = self.get_project_by_path(path)
            if existing:
                update_fields = ['name', 'repo_hash', 'github_url', 'local_size', 'last_updated']
                update_values = [name, repo_hash, github_url, local_size, datetime.now().isoformat()]
                
                if category is not None:
                    update_fields.append('category')
                    update_values.append(category)
                if tags is not None:
                    update_fields.append('tags')
                    update_values.append(tags_json)
                if remark is not None:
                    update_fields.append('remark')
                    update_values.append(remark)
                
                update_values.append(existing['id'])
                cursor.execute(f'''
                    UPDATE projects SET {', '.join(f'{f} = ?' for f in update_fields)}
                    WHERE id = ?
                ''', update_values)
                conn.commit()
                return existing['id']
            else:
                cursor.execute('''
                    INSERT INTO projects 
                    (name, path, repo_hash, github_url, category, tags, remark, local_size, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, path, repo_hash, github_url, category, tags_json, remark,
                      local_size, datetime.now().isoformat()))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error:
            return -1
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = ? AND is_deleted = 0', (project_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            if result.get('tags'):
                result['tags'] = json.loads(result['tags'])
            return result
        return None
    
    def get_project_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """通过路径获取项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE path = ? AND is_deleted = 0', (path,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            if result.get('tags'):
                result['tags'] = json.loads(result['tags'])
            return result
        return None
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """获取所有项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE is_deleted = 0 ORDER BY name')
        projects = []
        for row in cursor.fetchall():
            project = dict(row)
            if project.get('tags'):
                project['tags'] = json.loads(project['tags'])
            projects.append(project)
        return projects
    
    def update_project(self, project_id: int, **kwargs) -> bool:
        """更新项目"""
        allowed_fields = ['name', 'repo_hash', 'github_url', 'category', 'tags', 
                         'remark', 'has_update', 'security_status', 'security_report']
        update_fields = []
        update_values = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'tags' and value:
                    value = json.dumps(value)
                update_fields.append(f'{key} = ?')
                update_values.append(value)
        
        if not update_fields:
            return False
        
        update_fields.append('last_updated = ?')
        update_values.append(datetime.now().isoformat())
        update_values.append(project_id)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f'UPDATE projects SET {", ".join(update_fields)} WHERE id = ?', 
                          update_values)
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def delete_project(self, project_id: int, soft_delete: bool = True) -> bool:
        """删除项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if soft_delete:
                cursor.execute('UPDATE projects SET is_deleted = 1 WHERE id = ?', (project_id,))
            else:
                cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def get_duplicate_projects(self) -> List[List[Dict[str, Any]]]:
        """获取重复的项目（基于repo_hash）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT repo_hash, GROUP_CONCAT(id) as ids 
            FROM projects 
            WHERE repo_hash IS NOT NULL AND is_deleted = 0
            GROUP BY repo_hash 
            HAVING COUNT(*) > 1
        ''')
        
        duplicates = []
        for row in cursor.fetchall():
            ids = [int(x) for x in row['ids'].split(',')]
            group = []
            for project_id in ids:
                project = self.get_project(project_id)
                if project:
                    group.append(project)
            if group:
                duplicates.append(group)
        return duplicates


_db_instance: Optional[Database] = None


def get_database() -> Database:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
