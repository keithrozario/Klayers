#!/usr/bin/env python3
"""Validation script for Klayers CSV files and configuration."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

EXPECTED_PACKAGES_HEADER = ["Package_Name", "License", "Authors/Maintainers"]
EXPECTED_REGIONS_HEADER = ["Code", "Name"]

logger = logging.getLogger("validate_csv")


def clean_package_name(pkg_spec: str) -> str:
    """Extract clean package name from a package specifier."""
    raw = pkg_spec.strip().strip('"').strip("'")
    try:
        req = Requirement(raw)
        return req.name
    except InvalidRequirement:
        # Fallback regex extraction if specifier has non-standard chars
        match = re.match(r"^([a-zA-Z0-9_\-\.]+)", raw)
        if match:
            return match.group(1)
        return raw


def validate_config_file(config_path: Path) -> list[str]:
    """Validate config.json and ensure referenced packages files exist."""
    errors: list[str] = []
    if not config_path.is_file():
        return [f"Config file does not exist: {config_path}"]

    try:
        with open(config_path, "r", encoding="utf-8") as fp:
            data: dict[str, Any] = json.load(fp)
    except Exception as exc:
        return [f"Failed to parse JSON in {config_path}: {exc}"]

    python_versions = data.get("python_versions")
    if not isinstance(python_versions, list) or not python_versions:
        errors.append(f"{config_path}: 'python_versions' must be a non-empty list")
        return errors

    config_dir = config_path.parent
    for py_ver in python_versions:
        ver_cfg = data.get(py_ver)
        if not isinstance(ver_cfg, dict):
            errors.append(
                f"{config_path}: Missing configuration block for python version '{py_ver}'"
            )
            continue
        packages_file = ver_cfg.get("packages_file")
        if not packages_file or not isinstance(packages_file, str):
            errors.append(f"{config_path}: '{py_ver}' missing valid 'packages_file' setting")
            continue
        target_csv = config_dir / packages_file
        if not target_csv.is_file():
            errors.append(
                f"{config_path}: Referenced CSV for '{py_ver}' does not exist: {target_csv}"
            )

    return errors


def validate_packages_csv(csv_path: Path) -> tuple[list[str], list[str]]:
    """Validate a packages_*.csv file.

    Returns:
        tuple of (errors, list_of_clean_packages)
    """
    errors: list[str] = []
    packages_found: list[str] = []

    if not csv_path.is_file():
        return [f"CSV file does not exist: {csv_path}"], []

    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as fp:
            reader = csv.reader(fp)
            rows = list(reader)
    except Exception as exc:
        return [f"Failed to read CSV {csv_path}: {exc}"], []

    if not rows:
        return [f"{csv_path}: File is empty"], []

    header = [col.strip() for col in rows[0]]
    if header != EXPECTED_PACKAGES_HEADER:
        errors.append(f"{csv_path}: Invalid header {header}. Expected {EXPECTED_PACKAGES_HEADER}")

    seen_packages: dict[str, int] = {}
    for line_idx, row in enumerate(rows[1:], start=2):
        if not row or not any(cell.strip() for cell in row):
            continue  # ignore empty trailing lines

        if len(row) < 1:
            errors.append(f"{csv_path}:{line_idx}: Empty row")
            continue

        pkg_raw = row[0].strip()
        if not pkg_raw:
            errors.append(f"{csv_path}:{line_idx}: Package_Name is empty")
            continue

        try:
            req = Requirement(pkg_raw)
            clean_name = req.name
        except InvalidRequirement as exc:
            errors.append(f"{csv_path}:{line_idx}: Invalid package requirement '{pkg_raw}': {exc}")
            clean_name = clean_package_name(pkg_raw)

        canonical = canonicalize_name(clean_name)
        if canonical in seen_packages:
            prev_line = seen_packages[canonical]
            errors.append(
                f"{csv_path}:{line_idx}: Duplicate package '{clean_name}' "
                f"(previously defined at line {prev_line})"
            )
        else:
            seen_packages[canonical] = line_idx
            packages_found.append(clean_name)

        if len(row) > 1 and not row[1].strip():
            errors.append(f"{csv_path}:{line_idx}: License is empty for package '{clean_name}'")

    return errors, packages_found


def validate_regions_csv(csv_path: Path) -> list[str]:
    """Validate regions.csv header and values."""
    errors: list[str] = []
    if not csv_path.is_file():
        return [f"Regions file does not exist: {csv_path}"]

    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as fp:
            reader = csv.reader(fp)
            rows = list(reader)
    except Exception as exc:
        return [f"Failed to read regions CSV {csv_path}: {exc}"]

    if not rows:
        return [f"{csv_path}: File is empty"]

    header = [col.strip() for col in rows[0]]
    if header != EXPECTED_REGIONS_HEADER:
        errors.append(f"{csv_path}: Invalid header {header}. Expected {EXPECTED_REGIONS_HEADER}")

    seen_codes: set[str] = set()
    for line_idx, row in enumerate(rows[1:], start=2):
        if not row or not any(cell.strip() for cell in row):
            continue
        if len(row) < 2:
            errors.append(f"{csv_path}:{line_idx}: Row has fewer than 2 columns")
            continue
        code = row[0].strip()
        name = row[1].strip()
        if not code:
            errors.append(f"{csv_path}:{line_idx}: Region code is empty")
        elif code in seen_codes:
            errors.append(f"{csv_path}:{line_idx}: Duplicate region code '{code}'")
        else:
            seen_codes.add(code)

        if not name:
            errors.append(f"{csv_path}:{line_idx}: Region name is empty for code '{code}'")

    return errors


def check_pypi_package(
    package_name: str,
    session: requests.Session | None = None,
    timeout: float = 10.0,
) -> list[str]:
    """Query PyPI for package metadata.

    Fails if:
    - HTTP 404 (package not found)
    - Non-200 HTTP response
    - Zero non-prerelease versions available
    """
    clean_name = clean_package_name(package_name)
    url = f"https://pypi.org/pypi/{clean_name}/json"
    headers = {"User-Agent": "Klayers-CSV-Validator/1.0"}
    requester = session or requests

    try:
        response = requester.get(url, headers=headers, timeout=timeout)
    except Exception as exc:
        return [f"PyPI check failed for '{clean_name}': network error ({exc})"]

    if response.status_code == 404:
        return [f"PyPI check failed: Package '{clean_name}' not found on PyPI (404)"]
    if response.status_code != 200:
        return [f"PyPI check failed for '{clean_name}': HTTP status {response.status_code}"]

    try:
        data = response.json()
    except Exception as exc:
        return [f"PyPI check failed for '{clean_name}': Invalid JSON response ({exc})"]

    releases = data.get("releases", {})
    non_prereleases: list[str] = []

    for ver_str in releases.keys():
        try:
            ver = Version(ver_str)
            if not ver.is_prerelease:
                non_prereleases.append(ver_str)
        except InvalidVersion:
            continue

    if not non_prereleases:
        # Fallback check info.version
        info_ver = data.get("info", {}).get("version", "")
        if info_ver:
            try:
                ver = Version(info_ver)
                if not ver.is_prerelease:
                    non_prereleases.append(info_ver)
            except InvalidVersion:
                pass

    if not non_prereleases:
        return [
            f"PyPI check failed: Package '{clean_name}' has zero non-prerelease versions on PyPI"
        ]

    return []


def get_added_packages_from_git_diff(base_ref: str, repo_root: Path) -> list[str]:
    """Extract newly added package names from git diff against base_ref."""
    cmd = [
        "git",
        "diff",
        "--unified=0",
        base_ref,
        "--",
        "pipeline/config/packages_*.csv",
        "pipeline/config/test_config/packages_*.csv",
    ]
    logger.info("Running git diff: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "Failed to run git diff against %s: %s (stderr: %s)",
            base_ref,
            exc,
            exc.stderr.strip(),
        )
        return []

    added_packages: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:].strip()
            if not content:
                continue
            try:
                row = next(csv.reader([content]))
                if row:
                    pkg_raw = row[0].strip()
                    if pkg_raw and pkg_raw.lower() != "package_name":
                        clean = clean_package_name(pkg_raw)
                        added_packages.append(clean)
            except Exception:
                continue

    # De-duplicate while preserving order
    unique_added: list[str] = []
    seen: set[str] = set()
    for pkg in added_packages:
        canon = canonicalize_name(pkg)
        if canon not in seen:
            seen.add(canon)
            unique_added.append(pkg)

    return unique_added


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Klayers CSV files and config")
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=None,
        help="Path to pipeline/config directory (defaults to ../config relative to this script)",
    )
    parser.add_argument(
        "--check-pypi",
        action="store_true",
        help="Enable PyPI existence and stable release checks",
    )
    parser.add_argument(
        "--packages",
        nargs="*",
        default=[],
        help="Specific package names to validate on PyPI",
    )
    parser.add_argument(
        "--base-ref",
        type=str,
        default=None,
        help="Git base ref (e.g. origin/master) to inspect git diff for added packages",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args(args)


def main(cli_args: list[str] | None = None) -> int:
    args = parse_args(cli_args)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent

    config_dir = args.config_dir or (repo_root / "pipeline" / "config")
    if not config_dir.is_dir():
        logger.error("Configuration directory not found: %s", config_dir)
        return 1

    all_errors: list[str] = []
    all_packages_discovered: list[str] = []

    # 1. Validate config.json in config_dir and test_config
    config_candidates = [
        config_dir / "config.json",
        config_dir / "test_config" / "config.json",
    ]
    for cfg in config_candidates:
        if cfg.is_file():
            logger.info("Validating config: %s", cfg)
            cfg_errors = validate_config_file(cfg)
            all_errors.extend(cfg_errors)

    # 2. Validate all packages_*.csv files in config_dir and test_config
    csv_files = sorted(config_dir.glob("packages_*.csv")) + sorted(
        (config_dir / "test_config").glob("packages_*.csv")
    )
    if not csv_files:
        all_errors.append(f"No packages_*.csv files found in {config_dir}")

    for csv_file in csv_files:
        logger.info("Validating packages CSV: %s", csv_file)
        csv_errors, pkgs = validate_packages_csv(csv_file)
        all_errors.extend(csv_errors)
        all_packages_discovered.extend(pkgs)

    # 3. Validate regions.csv if present
    regions_files = [
        config_dir / "regions.csv",
        config_dir / "test_config" / "regions.csv",
    ]
    for reg_file in regions_files:
        if reg_file.is_file():
            logger.info("Validating regions CSV: %s", reg_file)
            reg_errors = validate_regions_csv(reg_file)
            all_errors.extend(reg_errors)

    # 4. PyPI verification if requested
    if args.check_pypi:
        target_packages: list[str] = []

        if args.packages:
            target_packages.extend(args.packages)

        if args.base_ref:
            diff_pkgs = get_added_packages_from_git_diff(args.base_ref, repo_root)
            logger.info("Packages added in diff vs %s: %s", args.base_ref, diff_pkgs)
            target_packages.extend(diff_pkgs)

        # If --check-pypi is enabled but neither --packages nor --base-ref returned packages:
        # If --base-ref was provided and no packages were added in diff, it's a no-op (passes).
        # If neither was provided, check all discovered packages.
        if not target_packages and not args.base_ref and not args.packages:
            target_packages.extend(all_packages_discovered)

        # De-duplicate
        unique_targets: list[str] = []
        seen_targets: set[str] = set()
        for pkg in target_packages:
            canon = canonicalize_name(pkg)
            if canon not in seen_targets:
                seen_targets.add(canon)
                unique_targets.append(pkg)

        if unique_targets:
            logger.info("Checking %d packages on PyPI...", len(unique_targets))
            session = requests.Session()
            for pkg in unique_targets:
                pypi_errors = check_pypi_package(pkg, session=session)
                all_errors.extend(pypi_errors)
        else:
            logger.info("No packages required PyPI verification.")

    if all_errors:
        logger.error("Validation failed with %d error(s):", len(all_errors))
        for err in all_errors:
            logger.error("  - %s", err)
        return 1

    logger.info("All CSV and config validations passed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
