"""
Pytest configuration and fixtures for tests.
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def backup_csv_files():
    """Backup CSV files before all tests and restore after."""
    from backend.data.mock_data import _get_csv_dir

    csv_dir = _get_csv_dir()
    backup_dir = Path(tempfile.gettempdir()) / "smartrecover_csv_backup"
    backup_dir.mkdir(exist_ok=True)

    # Backup all CSV files
    for csv_file in csv_dir.glob("*.csv"):
        shutil.copy(csv_file, backup_dir / csv_file.name)

    yield

    # Restore all CSV files after all tests
    for csv_file in backup_dir.glob("*.csv"):
        shutil.copy(csv_file, csv_dir / csv_file.name)

    # Clean up backup directory
    shutil.rmtree(backup_dir, ignore_errors=True)


@pytest.fixture(scope="module", autouse=True)
def reload_mock_data_per_module():
    """Reload mock data before each test module to ensure fresh state."""
    from backend.data.mock_data import reload_mock_data

    # Reload at the start of each test module
    reload_mock_data()

    yield

    # Reload at the end of each test module
    reload_mock_data()
