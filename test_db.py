"""
测试数据库备注保存功能
"""
import sys
from pathlib import Path

# 添加当前目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from open_manager_py.database import get_database
from open_manager_py.config import get_config

def test_database():
    print("=== 测试数据库备注保存功能 ===")
    
    config = get_config()
    print(f"数据库路径: {config.get_db_path()}")
    
    db = get_database()
    
    print("\n1. 查看当前所有技能:")
    skills = db.get_all_skills()
    print(f"技能数量: {len(skills)}")
    for skill in skills:
        print(f"  - ID: {skill['id']}, 名称: {skill['name']}")
        print(f"    备注: {skill.get('remark')}")
        print(f"    分类: {skill.get('category')}")
        print(f"    标签: {skill.get('tags')}")
    
    print("\n2. 查看当前所有项目:")
    projects = db.get_all_projects()
    print(f"项目数量: {len(projects)}")
    for project in projects:
        print(f"  - ID: {project['id']}, 名称: {project['name']}")
        print(f"    备注: {project.get('remark')}")
        print(f"    分类: {project.get('category')}")
        print(f"    标签: {project.get('tags')}")
    
    if skills:
        print("\n3. 测试更新技能备注:")
        skill_id = skills[0]['id']
        test_notes = "这是一个测试备注 " + str(skills[0]['name'])
        success = db.update_skill(skill_id, remark=test_notes)
        print(f"更新备注 {'成功' if success else '失败'}")
        
        updated_skill = db.get_skill(skill_id)
        print(f"更新后的备注: {updated_skill.get('remark')}")
    
    if projects:
        print("\n4. 测试更新项目备注:")
        project_id = projects[0]['id']
        test_notes = "这是一个测试备注 " + str(projects[0]['name'])
        success = db.update_project(project_id, remark=test_notes)
        print(f"更新备注 {'成功' if success else '失败'}")
        
        updated_project = db.get_project(project_id)
        print(f"更新后的备注: {updated_project.get('remark')}")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_database()
