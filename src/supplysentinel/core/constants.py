from enum import Enum


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingCategory(str, Enum):
    DEPENDENCY = "DEPENDENCY"
    REGISTRY = "REGISTRY"
    CICD = "CI_CD"
    SECRETS = "SECRETS"
    BUILD_SCRIPT = "BUILD_SCRIPT"
    CONTAINER = "CONTAINER"
    POLICY = "POLICY"


SECURITY_RELEVANT_FILENAMES = {
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "go.mod",
    "go.sum",
    "pom.xml",
    "build.gradle",
    "gradle.lockfile",
    ".npmrc",
    ".pypirc",
    "pip.conf",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".gitlab-ci.yml",
}