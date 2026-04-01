"""
启动Web应用的简单脚本
"""
import sys
from pathlib import Path

# 添加当前目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from open_manager_py.app import main

if __name__ == '__main__':
    main()
