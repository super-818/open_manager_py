"""CLI测试"""
import pytest
from click.testing import CliRunner
from open_manager_py.cli import cli
from open_manager_py import __version__


def test_cli_help():
    """测试CLI帮助"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'scan' in result.output
    assert 'list' in result.output
    assert 'search' in result.output
    assert 'stats' in result.output


def test_cli_list_command():
    """测试list命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ['list', 'skills'])
    assert result.exit_code == 0


def test_cli_stats_command():
    """测试stats命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ['stats'])
    assert result.exit_code == 0


def test_cli_search_command():
    """测试search命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ['search', 'nonexistent_xyz'])
    assert result.exit_code == 0


def test_cli_scan_help():
    """测试scan命令帮助"""
    runner = CliRunner()
    result = runner.invoke(cli, ['scan', '--help'])
    assert result.exit_code == 0


def test_cli_export_command():
    """测试export命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ['export', '-o', '-'])
    assert result.exit_code == 0


def test_cli_version():
    """测试版本"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert __version__ in result.output
