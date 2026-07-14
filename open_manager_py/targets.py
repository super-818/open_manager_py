"""AI工具分发目标 - 定义各AI工具的技能目录路径"""
from pathlib import Path
from typing import List, Dict
import platform


def _get_tool_paths() -> Dict[str, Path]:
    """获取所有支持的AI工具及其技能目录路径(跨平台)"""
    home = Path.home()
    system = platform.system()

    tools = {
        'trae': home / '.trae' / 'skills',
        'trae-cn': home / '.trae-cn' / 'skills',
        'claude-code': home / '.claude' / 'skills',
        'cursor': home / '.cursor' / 'skills',
        'continue': home / '.continue' / 'skills',
        'aider': home / '.aider' / 'skills',
        'cline': home / '.cline' / 'skills',
        'openclaw': home / '.openclaw' / 'skills',
        'roo-cline': home / '.roo' / 'skills',
        'windsurf': home / '.codeium' / 'windsurf' / 'skills',
    }

    # Windows 特定路径
    if system == 'Windows':
        tools['claude-desktop'] = Path.home() / 'AppData' / 'Roaming' / 'Claude' / 'skills'

    return tools


def list_targets() -> Dict[str, str]:
    """列出所有支持的分发目标(名称->路径字符串)"""
    return {name: str(path) for name, path in _get_tool_paths().items()}


def get_target_paths(tools: List[str], custom_path: str = None) -> List[Path]:
    """根据工具名列表获取目标路径列表

    Args:
        tools: 工具名列表,如['trae', 'cursor']
        custom_path: 自定义目标路径

    Returns:
        目标Path列表
    """
    all_tools = _get_tool_paths()
    paths = []
    for tool in tools:
        if tool in all_tools:
            paths.append(all_tools[tool])
    if custom_path:
        paths.append(Path(custom_path))
    return paths
