"""
Tests for ``preset_cli.cli.superset.sync.dbt.databases``.
"""
# pylint: disable=invalid-name

from pathlib import Path

import pytest
import yaml
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from preset_cli.cli.superset.sync.dbt.databases import sync_database
from preset_cli.exceptions import DatabaseNotFoundError


def test_sync_database_new(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """
    Test ``sync_database`` when we want to import a new DB.
    """
    fs.create_file(
        "/path/to/.dbt/profiles.yml",
        contents=yaml.dump({"my_project": {"outputs": {"dev": {}}}}),
    )
    mocker.patch(
        "preset_cli.cli.superset.sync.dbt.databases.build_sqlalchemy_uri",
        return_value="dummy://",
    )
    client = mocker.MagicMock()
    client.get_databases.return_value = []

    sync_database(
        client=client,
        profiles_path=Path("/path/to/.dbt/profiles.yml"),
        project_name="my_project",
        target_name="dev",
        import_db=True,
        disallow_edits=False,
        external_url_prefix="",
    )

    client.create_database.assert_called_with(
        database_name="my_project_dev",
        sqlalchemy_uri="dummy://",
    )


def test_sync_database_no_project(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """
    Test ``sync_database`` when the project is invalid.
    """
    fs.create_file(
        "/path/to/.dbt/profiles.yml",
        contents=yaml.dump({"my_project": {"outputs": {"dev": {}}}}),
    )
    client = mocker.MagicMock()
    client.get_databases.return_value = []

    with pytest.raises(Exception) as excinfo:
        sync_database(
            client=client,
            profiles_path=Path("/path/to/.dbt/profiles.yml"),
            project_name="my_other_project",
            target_name="dev",
            import_db=True,
            disallow_edits=False,
            external_url_prefix="",
        )
    assert (
        str(excinfo.value)
        == "Project my_other_project not found in /path/to/.dbt/profiles.yml"
    )


def test_sync_database_no_target(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """
    Test ``sync_database`` when the target is invalid.
    """
    fs.create_file(
        "/path/to/.dbt/profiles.yml",
        contents=yaml.dump({"my_project": {"outputs": {"dev": {}}}}),
    )
    client = mocker.MagicMock()
    client.get_databases.return_value = []

    with pytest.raises(Exception) as excinfo:
        sync_database(
            client=client,
            profiles_path=Path("/path/to/.dbt/profiles.yml"),
            project_name="my_project",
            target_name="prod",
            import_db=True,
            disallow_edits=False,
            external_url_prefix="",
        )
    assert (
        str(excinfo.value)
        == "Target prod not found in the outputs of /path/to/.dbt/profiles.yml"
    )


def test_sync_database_multiple_databases(
    mocker: MockerFixture,
    fs: FakeFilesystem,
) -> None:
    """
    Test ``sync_database`` when multiple databases are found.

    This should not happen, since database names are unique.
    """
    fs.create_file(
        "/path/to/.dbt/profiles.yml",
        contents=yaml.dump({"my_project": {"outputs": {"dev": {}}}}),
    )
    mocker.patch(
        "preset_cli.cli.superset.sync.dbt.databases.build_sqlalchemy_uri",
        return_value="dummy://",
    )
    client = mocker.MagicMock()
    client.get_databases.return_value = [
        {"id": 1, "database_name": "my_project_dev", "sqlalchemy_uri": "dummy://"},
        {"id": 2, "database_name": "my_project_dev", "sqlalchemy_uri": "dummy://"},
    ]

    with pytest.raises(Exception) as excinfo:
        sync_database(
            client=client,
            profiles_path=Path("/path/to/.dbt/profiles.yml"),
            project_name="my_project",
            target_name="dev",
            import_db=True,
            disallow_edits=False,
            external_url_prefix="",
        )
    assert (
        str(excinfo.value)
        == "More than one database with the same SQLAlchemy URI and name found"
    )


def test_sync_database_external_url_prefix(
    mocker: MockerFixture,
    fs: FakeFilesystem,
) -> None:
    """
    Test ``sync_database`` with an external URL prefix.
    """
    fs.create_file(
        "/path/to/.dbt/profiles.yml",
        contents=yaml.dump({"my_project": {"outputs": {"dev": {}}}}),
    )
    mocker.patch(
        "preset_cli.cli.superset.sync.dbt.databases.build_sqlalchemy_uri",
        return_value="dummy://",
    )
    client = mocker.MagicMock()
    client.get_databases.return_value = []

    sync_database(
        client=client,
        profiles_path=Path("/path/to/.dbt/profiles.yml"),
        project_name="my_project",
        target_name="dev",
        import_db=True,
        disallow_edits=False,
        external_url_prefix="https://dbt.example.org/",
    )

    client.create_database.assert_called_with(
        database_name="my_project_dev",
        sqlalchemy_uri="dummy://",
        external_url="https://dbt.example.org/#!/overview",
    )


def test_sync_database_existing(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """
    Test ``sync_database`` when we want to import an existing DB.
    """
    fs.create_file(
        "/path/to/.dbt/profiles.yml",
        contents=yaml.dump({"my_project": {"outputs": {"dev": {}}}}),
    )
    mocker.patch(
        "preset_cli.cli.superset.sync.dbt.databases.build_sqlalchemy_uri",
        return_value="dummy://",
    )
    client = mocker.MagicMock()
    client.get_databases.return_value = [
        {"id": 1, "database_name": "my_project_dev", "sqlalchemy_uri": "dummy://"},
    ]

    sync_database(
        client=client,
        profiles_path=Path("/path/to/.dbt/profiles.yml"),
        project_name="my_project",
        target_name="dev",
        import_db=True,
        disallow_edits=False,
        external_url_prefix="",
    )

    client.update_database.assert_called_with(
        database_id=1,
        database_name="my_project_dev",
    )


def test_sync_database_new_no_import(mocker: MockerFixture, fs: FakeFilesystem) -> None:
    """
    Test ``sync_database`` when we want to import a new DB.
    """
    fs.create_file(
        "/path/to/.dbt/profiles.yml",
        contents=yaml.dump({"my_project": {"outputs": {"dev": {}}}}),
    )
    mocker.patch(
        "preset_cli.cli.superset.sync.dbt.databases.build_sqlalchemy_uri",
        return_value="dummy://",
    )
    client = mocker.MagicMock()
    client.get_databases.return_value = []

    with pytest.raises(DatabaseNotFoundError):
        sync_database(
            client=client,
            profiles_path=Path("/path/to/.dbt/profiles.yml"),
            project_name="my_project",
            target_name="dev",
            import_db=False,
            disallow_edits=False,
            external_url_prefix="",
        )