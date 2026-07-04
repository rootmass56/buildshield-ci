from pathlib import Path

import pytest

from supplysentinel.core.scanner import scan_repository


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def vulnerable_repo(project_root: Path) -> Path:
    return project_root / "samples" / "vulnerable-repo"


@pytest.fixture(scope="session")
def secure_repo(project_root: Path) -> Path:
    return project_root / "samples" / "secure-repo"


@pytest.fixture(scope="session")
def policy_file(project_root: Path) -> Path:
    return project_root / "buildshield-policy.yml"


@pytest.fixture(scope="session")
def vulnerable_scan(vulnerable_repo: Path):
    return scan_repository(str(vulnerable_repo))


@pytest.fixture(scope="session")
def secure_scan(secure_repo: Path):
    return scan_repository(str(secure_repo))