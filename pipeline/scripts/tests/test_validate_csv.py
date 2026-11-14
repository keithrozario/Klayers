"""Unit tests for validate_csv.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from validate_csv import (
    check_pypi_package,
    clean_package_name,
    get_added_packages_from_git_diff,
    main,
    validate_config_file,
    validate_packages_csv,
    validate_regions_csv,
)


def test_clean_package_name():
    assert clean_package_name("requests") == "requests"
    assert clean_package_name('"requests"') == "requests"
    assert clean_package_name("'requests'") == "requests"
    assert clean_package_name("psycopg[binary,pool]") == "psycopg"
    assert clean_package_name('"psycopg[binary,pool]"') == "psycopg"
    assert clean_package_name("urllib3>=1.26.0") == "urllib3"
    assert clean_package_name("Pillow~=10.0") == "Pillow"


def test_validate_config_file_valid(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    csv_file = tmp_path / "packages_p314.csv"
    csv_file.write_text("Package_Name,License,Authors/Maintainers\nrequests,Apache-2.0,Author\n")

    cfg_data = {
        "python_versions": ["p3.14"],
        "p3.14": {"packages_file": "packages_p314.csv"},
    }
    cfg_file.write_text(json.dumps(cfg_data))

    errors = validate_config_file(cfg_file)
    assert errors == []


def test_validate_config_file_errors(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist.json"
    errors = validate_config_file(non_existent)
    assert any("does not exist" in e for e in errors)

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{broken json")
    errors = validate_config_file(invalid_json)
    assert any("Failed to parse JSON" in e for e in errors)

    empty_versions = tmp_path / "empty.json"
    empty_versions.write_text(json.dumps({"python_versions": []}))
    errors = validate_config_file(empty_versions)
    assert any("'python_versions' must be a non-empty list" in e for e in errors)

    missing_block = tmp_path / "missing_block.json"
    missing_block.write_text(json.dumps({"python_versions": ["p3.14"]}))
    errors = validate_config_file(missing_block)
    assert any("Missing configuration block" in e for e in errors)

    missing_target_file = tmp_path / "missing_csv.json"
    missing_target_file.write_text(
        json.dumps(
            {
                "python_versions": ["p3.14"],
                "p3.14": {"packages_file": "not_there.csv"},
            }
        )
    )
    errors = validate_config_file(missing_target_file)
    assert any("Referenced CSV for 'p3.14' does not exist" in e for e in errors)


def test_validate_packages_csv_valid(tmp_path: Path):
    csv_file = tmp_path / "packages_p314.csv"
    csv_file.write_text(
        "Package_Name,License,Authors/Maintainers\n"
        "requests,Apache-2.0,Kenneth Reitz\n"
        '"psycopg[binary,pool]",LGPL-3.0,Daniele\n'
    )
    errors, packages = validate_packages_csv(csv_file)
    assert errors == []
    assert packages == ["requests", "psycopg"]


def test_validate_packages_csv_errors(tmp_path: Path):
    csv_file = tmp_path / "invalid_header.csv"
    csv_file.write_text("Col1,Col2,Col3\nrequests,MIT,Me\n")
    errors, _ = validate_packages_csv(csv_file)
    assert any("Invalid header" in e for e in errors)

    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")
    errors, _ = validate_packages_csv(empty_file)
    assert any("File is empty" in e for e in errors)

    duplicate_file = tmp_path / "duplicates.csv"
    duplicate_file.write_text(
        "Package_Name,License,Authors/Maintainers\n"
        "requests,Apache-2.0,Auth\n"
        "Requests,Apache-2.0,Auth2\n"
    )
    errors, _ = validate_packages_csv(duplicate_file)
    assert any("Duplicate package 'Requests'" in e for e in errors)

    empty_pkg_file = tmp_path / "empty_pkg.csv"
    empty_pkg_file.write_text("Package_Name,License,Authors/Maintainers\n,MIT,Nobody\n")
    errors, _ = validate_packages_csv(empty_pkg_file)
    assert any("Package_Name is empty" in e for e in errors)

    empty_license_file = tmp_path / "empty_lic.csv"
    empty_license_file.write_text("Package_Name,License,Authors/Maintainers\nrequests,,Nobody\n")
    errors, _ = validate_packages_csv(empty_license_file)
    assert any("License is empty" in e for e in errors)


def test_validate_regions_csv(tmp_path: Path):
    regions_file = tmp_path / "regions.csv"
    regions_file.write_text("Code,Name\nus-east-1,US East (N. Virginia)\neu-west-1,EU (Ireland)\n")
    assert validate_regions_csv(regions_file) == []

    invalid_hdr = tmp_path / "invalid_regions.csv"
    invalid_hdr.write_text("Region,Title\nus-east-1,US\n")
    errors = validate_regions_csv(invalid_hdr)
    assert any("Invalid header" in e for e in errors)

    duplicate_reg = tmp_path / "dup_regions.csv"
    duplicate_reg.write_text("Code,Name\nus-east-1,US East 1\nus-east-1,US East Duplicate\n")
    errors = validate_regions_csv(duplicate_reg)
    assert any("Duplicate region code 'us-east-1'" in e for e in errors)


def test_check_pypi_package_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "info": {"version": "2.31.0"},
        "releases": {
            "2.30.0": [],
            "2.31.0": [],
            "3.0.0a1": [],
        },
    }

    session = MagicMock()
    session.get.return_value = mock_resp

    errors = check_pypi_package("requests", session=session)
    assert errors == []


def test_check_pypi_package_404():
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    session = MagicMock()
    session.get.return_value = mock_resp

    errors = check_pypi_package("ghost-package", session=session)
    assert len(errors) == 1
    assert "not found on PyPI (404)" in errors[0]


def test_check_pypi_package_only_prereleases():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "info": {"version": "1.0.0a1"},
        "releases": {
            "1.0.0a1": [],
            "1.0.0b1": [],
            "1.0.0rc1": [],
        },
    }

    session = MagicMock()
    session.get.return_value = mock_resp

    errors = check_pypi_package("alpha-only", session=session)
    assert len(errors) == 1
    assert "zero non-prerelease versions" in errors[0]


def test_check_pypi_package_network_error():
    session = MagicMock()
    session.get.side_effect = requests.RequestException("connection timeout")

    errors = check_pypi_package("requests", session=session)
    assert len(errors) == 1
    assert "network error" in errors[0]


def test_get_added_packages_from_git_diff():
    diff_output = (
        "diff --git a/pipeline/config/packages_p314.csv b/pipeline/config/packages_p314.csv\n"
        "--- a/pipeline/config/packages_p314.csv\n"
        "+++ b/pipeline/config/packages_p314.csv\n"
        "@@ -10,0 +11,2 @@\n"
        "+Pillow,MIT,Auth\n"
        '+"psycopg[binary]",LGPL,Auth\n'
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=diff_output)
        pkgs = get_added_packages_from_git_diff("origin/master", Path("/fake"))
        assert pkgs == ["Pillow", "psycopg"]


def test_main_cli(tmp_path: Path):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.json"
    csv_file = cfg_dir / "packages_p314.csv"

    csv_file.write_text(
        "Package_Name,License,Authors/Maintainers\nrequests,Apache-2.0,Kenneth Reitz\n"
    )
    cfg_file.write_text(
        json.dumps(
            {
                "python_versions": ["p3.14"],
                "p3.14": {"packages_file": "packages_p314.csv"},
            }
        )
    )

    exit_code = main(["--config-dir", str(cfg_dir)])
    assert exit_code == 0
