"""命令行界面 - 提供headless环境下的管理能力"""
import json
import click
from pathlib import Path

from .config import get_config
from .database import get_database
from .scanner import get_scanner
from .services import SkillService, ProjectService
from .logger import get_logger


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if not size_bytes:
        return '0 B'
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


@click.group()
@click.version_option(version='0.3.0')
def cli():
    """Open Manager - 开源技能与GitHub项目管理器"""
    pass


@cli.command()
@click.option('--skills-only', is_flag=True, help='仅扫描技能')
@click.option('--projects-only', is_flag=True, help='仅扫描项目')
def scan(skills_only, projects_only):
    """扫描本地目录,同步到数据库"""
    scanner = get_scanner()

    if not projects_only:
        click.echo('扫描技能目录...')
        new, updated, deleted = scanner.scan_skills()
        click.echo(f'  技能: 新增 {new}, 更新 {updated}, 删除 {deleted}')

    if not skills_only:
        click.echo('扫描项目目录...')
        new, updated, deleted = scanner.scan_projects()
        click.echo(f'  项目: 新增 {new}, 更新 {updated}, 删除 {deleted}')


@cli.command(name='list')
@click.argument('type', type=click.Choice(['skills', 'projects']))
@click.option('--category', '-c', help='按分类筛选')
@click.option('--limit', '-n', default=50, help='显示数量')
def list_items(type, category, limit):
    """列出技能或项目"""
    if type == 'skills':
        service = SkillService()
        items = service.list_all()
    else:
        service = ProjectService()
        items = service.list_all()

    if category:
        items = [i for i in items if i.get('category') == category]

    items = items[:limit]

    if not items:
        click.echo('没有找到记录')
        return

    click.echo(f"{'ID':<6} {'名称':<30} {'分类':<10} {'大小':<10} {'备注'}")
    click.echo('-' * 80)
    for item in items:
        click.echo(
            f"{item['id']:<6} "
            f"{item['name'][:30]:<30} "
            f"{(item.get('category') or '-'):<10} "
            f"{format_size(item.get('local_size', 0)):<10} "
            f"{(item.get('remark') or '')[:30]}"
        )


@cli.command()
@click.argument('query')
@click.option('--type', '-t', 'item_type',
              type=click.Choice(['skills', 'projects', 'all']),
              default='all', help='搜索类型')
@click.option('--category', '-c', help='按分类筛选')
@click.option('--tags', help='按标签筛选(逗号分隔)')
def search(query, item_type, category, tags):
    """搜索技能或项目"""
    results = []

    if item_type in ('all', 'skills'):
        service = SkillService()
        results.extend([('skill', s) for s in service.search(query, category, tags)])

    if item_type in ('all', 'projects'):
        service = ProjectService()
        results.extend([('project', p) for p in service.search(query, category, tags)])

    if not results:
        click.echo('没有找到匹配的记录')
        return

    click.echo(f"找到 {len(results)} 条结果:")
    click.echo('-' * 80)
    for item_type, item in results:
        click.echo(
            f"[{item_type[:4]}] {item['name']}: "
            f"{(item.get('remark') or '-')[:60]}"
        )


@cli.command()
def stats():
    """显示统计信息"""
    db = get_database()
    skills = db.get_all_skills()
    projects = db.get_all_projects()

    click.echo('=' * 50)
    click.echo('Open Manager 统计')
    click.echo('=' * 50)
    click.echo(f'技能总数: {len(skills)}')
    click.echo(f'项目总数: {len(projects)}')

    total_size = sum(s.get('local_size', 0) for s in skills + projects)
    click.echo(f'总占用空间: {format_size(total_size)}')

    click.echo('\n分类统计:')
    categories = {}
    for item in skills + projects:
        cat = item.get('category') or '未分类'
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        click.echo(f'  {cat}: {count}')


@cli.command()
@click.argument('skill_id', type=int)
@click.argument('target', type=str)
@click.option('--custom-path', help='自定义目标路径')
def distribute(skill_id, target, custom_path):
    """分发技能到AI工具"""
    from .targets import get_target_paths
    service = SkillService()
    skill = service.get(skill_id)

    if not skill:
        click.echo(f'技能 ID {skill_id} 不存在')
        return

    targets = get_target_paths([target], custom_path)
    if not targets:
        click.echo(f'未知目标: {target}')
        return

    count = service.distribute([skill], targets)
    click.echo(f'已分发技能 {skill["name"]} 到 {len(targets)} 个目标')


@cli.command()
@click.option('--skill-id', type=int, help='技能ID')
@click.option('--project-id', type=int, help='项目ID')
def readme(skill_id, project_id):
    """查看技能或项目的README内容"""
    db = get_database()

    target_path = None
    if skill_id:
        skill = db.get_skill(skill_id)
        if skill:
            target_path = Path(skill['path'])
    elif project_id:
        project = db.get_project(project_id)
        if project:
            target_path = Path(project['path'])

    if not target_path:
        click.echo('未找到指定记录')
        return

    for filename in ['SKILL.md', 'README.md', 'readme.md', 'README.rst']:
        filepath = target_path / filename
        if filepath.exists():
            click.echo(filepath.read_text(encoding='utf-8'))
            return

    click.echo('未找到README文件')


@cli.command()
@click.option('--output', '-o', default='-', help='输出文件(-为stdout)')
def export(output):
    """导出数据到JSON"""
    db = get_database()
    from datetime import datetime
    data = {
        'skills': db.get_all_skills(),
        'projects': db.get_all_projects(),
        'exported_at': datetime.now().isoformat(),
        'version': '0.3.0'
    }

    # 清理不可序列化字段
    for item in data['skills'] + data['projects']:
        item.pop('local_size', None)

    json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if output == '-':
        click.echo(json_str)
    else:
        Path(output).write_text(json_str, encoding='utf-8')
        click.echo(f'已导出到 {output}')


@cli.command()
@click.argument('input_file')
def import_data(input_file):
    """从JSON文件导入数据"""
    db = get_database()
    data = json.loads(Path(input_file).read_text(encoding='utf-8'))

    skill_updated = 0
    project_updated = 0

    for skill in data.get('skills', []):
        path = skill.get('path')
        if path:
            existing = db.get_skill_by_path(path)
            if existing:
                update_data = {}
                if skill.get('category'):
                    update_data['category'] = skill['category']
                if skill.get('tags'):
                    update_data['tags'] = skill['tags']
                if skill.get('remark'):
                    update_data['remark'] = skill['remark']
                if update_data:
                    db.update_skill(existing['id'], **update_data)
                    skill_updated += 1

    for project in data.get('projects', []):
        path = project.get('path')
        if path:
            existing = db.get_project_by_path(path)
            if existing:
                update_data = {}
                if project.get('category'):
                    update_data['category'] = project['category']
                if project.get('tags'):
                    update_data['tags'] = project['tags']
                if project.get('remark'):
                    update_data['remark'] = project['remark']
                if update_data:
                    db.update_project(existing['id'], **update_data)
                    project_updated += 1

    click.echo(f'导入完成: 更新 {skill_updated} 个技能, {project_updated} 个项目')


@cli.command()
def check_updates():
    """检测项目的远程更新(轻量,不下载代码)"""
    from .updater import UpdateChecker
    checker = UpdateChecker()
    click.echo('检测远程更新中...')
    result = checker.check_projects()
    click.echo(f"总计: {result['total']}, 有更新: {result['has_update']}, "
               f"已最新: {result['up_to_date']}, 错误: {result['errors']}")

    if result['has_update'] > 0:
        click.echo('\n有更新的项目:')
        for item in result['details']:
            if item['has_update']:
                click.echo(f"  - {item['name']}")


def main():
    """CLI入口点"""
    cli()


if __name__ == '__main__':
    main()
