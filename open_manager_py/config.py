"""
配置管理模块 - 处理跨平台配置路径和配置文件
"""

import os
import platform
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """配置管理类"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.yaml"
        self.log_dir = self._get_log_dir()
        self.data_dir = self._get_data_dir()
        
        self._ensure_directories()
        
        self.default_config = {
            "skills_dir": self._get_default_skills_dir(),
            "github_dir": self._get_default_github_dir(),
            "update_interval": "weekly",
            "log_level": "INFO",
            "theme": "default",
            "auto_backup": True,
            "backup_interval": "daily"
        }
        
        self.config = self._load_config()
    
    def _get_config_dir(self) -> Path:
        """获取跨平台配置目录"""
        system = platform.system()
        
        if system == "Windows":
            return Path(os.environ.get("APPDATA", str(Path.home()))) / "SkillProjectManager"
        elif system == "Darwin":
            return Path.home() / "Library" / "Application Support" / "SkillProjectManager"
        else:
            return Path.home() / ".config" / "SkillProjectManager"
    
    def _get_log_dir(self) -> Path:
        """获取跨平台日志目录"""
        system = platform.system()
        
        if system == "Windows":
            return Path(os.environ.get("APPDATA", str(Path.home()))) / "SkillProjectManager" / "logs"
        elif system == "Darwin":
            return Path.home() / "Library" / "Logs" / "SkillProjectManager"
        else:
            return Path.home() / ".local" / "share" / "SkillProjectManager" / "logs"
    
    def _get_data_dir(self) -> Path:
        """获取跨平台数据目录"""
        system = platform.system()
        
        if system == "Windows":
            return Path(os.environ.get("APPDATA", str(Path.home()))) / "SkillProjectManager" / "data"
        elif system == "Darwin":
            return Path.home() / "Library" / "Application Support" / "SkillProjectManager" / "data"
        else:
            return Path.home() / ".local" / "share" / "SkillProjectManager" / "data"
    
    def _get_default_skills_dir(self) -> str:
        """获取默认技能目录。
        优先级: 环境变量 OPEN_MANAGER_SKILLS_DIR > 用户home目录下的skills文件夹
        """
        env_dir = os.environ.get("OPEN_MANAGER_SKILLS_DIR")
        if env_dir:
            return env_dir
        return str(Path.home() / "skills")

    def _get_default_github_dir(self) -> str:
        """获取默认GitHub项目目录。
        优先级: 环境变量 OPEN_MANAGER_GITHUB_DIR > 用户home目录下的github文件夹
        """
        env_dir = os.environ.get("OPEN_MANAGER_GITHUB_DIR")
        if env_dir:
            return env_dir
        return str(Path.home() / "github")
    
    def _ensure_directories(self):
        """确保必要目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    merged = self.default_config.copy()
                    if config:
                        merged.update(config)
                    return merged
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
        self.save_config()
    
    def get_skills_dir(self) -> Path:
        """获取技能目录"""
        return Path(self.config.get("skills_dir", self._get_default_skills_dir()))
    
    def get_github_dir(self) -> Path:
        """获取GitHub项目目录"""
        return Path(self.config.get("github_dir", self._get_default_github_dir()))
    
    def get_db_path(self) -> Path:
        """获取数据库文件路径"""
        return self.data_dir / "manager.db"

    def get_log_dir(self) -> Path:
        """获取日志目录(用于logger模块)"""
        return self.log_dir
    
    def get_backup_dir(self) -> Path:
        """获取备份目录"""
        backup_dir = self.data_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir


_config_instance: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
