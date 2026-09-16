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
