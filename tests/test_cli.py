"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner
from mnb.cli.main import cli


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'macOS Nextcloud Backup' in result.output


def test_cli_version():
    """Test that version command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert '0.1.0' in result.output


def test_backup_command():
    """Test backup command exists."""
    runner = CliRunner()
    result = runner.invoke(cli, ['backup', '--help'])
    assert result.exit_code == 0
    assert 'Run a backup' in result.output


def test_status_command():
    """Test status command exists."""
    runner = CliRunner()
    result = runner.invoke(cli, ['status', '--help'])
    assert result.exit_code == 0


def test_list_command():
    """Test list command exists."""
    runner = CliRunner()
    result = runner.invoke(cli, ['list', '--help'])
    assert result.exit_code == 0


def test_restore_command():
    """Test restore command exists."""
    runner = CliRunner()
    result = runner.invoke(cli, ['restore', '--help'])
    assert result.exit_code == 0
