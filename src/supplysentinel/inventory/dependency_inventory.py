import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


DependencyEcosystem = Literal["npm", "python"]


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
}


NPM_DEPENDENCY_GROUPS = [
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "peerDependencies",
]


PYTHON_REQUIREMENT_OPERATORS = [
    "==",
    ">=",
    "<=",
    "~=",
    "!=",
    ">",
    "<",
]


INTERNAL_PACKAGE_KEYWORDS = [
    "internal",
    "private",
    "company",
    "corp",
    "enterprise",
    "auth-sdk",
    "payment-sdk",
    "platform-sdk",
]


INTERNAL_NPM_SCOPES = [
    "@company/",
    "@internal/",
    "@corp/",
    "@private/",
    "@enterprise/",
]


class DependencyRecord(BaseModel):
    ecosystem: DependencyEcosystem
    name: str
    declared_version: str | None = None
    dependency_group: str
    file_path: str
    line_number: int | None = None
    is_pinned: bool
    is_loose: bool
    is_internal_candidate: bool
    private_registry_configured: bool
    lockfile_present: bool | None = None
    risk_indicators: list[str] = Field(default_factory=list)


class DependencyInventorySummary(BaseModel):
    total_dependencies: int
    npm_dependencies: int
    python_dependencies: int
    pinned_dependencies: int
    loose_dependencies: int
    unpinned_dependencies: int
    internal_candidate_dependencies: int
    dependencies_missing_private_registry: int
    npm_dependencies_without_lockfile: int
    ecosystems_detected: list[str]


class DependencyInventory(BaseModel):
    target_path: str
    generated_at: str
    summary: DependencyInventorySummary
    dependencies: list[DependencyRecord]


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def should_ignore(path: Path) -> bool:
    return any(part in IGNORED_DIRECTORIES for part in path.parts)


def find_line_number(content: str, search_text: str) -> int | None:
    for index, line in enumerate(content.splitlines(), start=1):
        if search_text in line:
            return index

    return None


def has_npm_private_registry(package_dir: Path, target_path: Path, package_name: str) -> bool:
    npmrc_candidates = [
        package_dir / ".npmrc",
        target_path / ".npmrc",
    ]

    scope = None

    if package_name.startswith("@") and "/" in package_name:
        scope = package_name.split("/", maxsplit=1)[0]

    for npmrc_path in npmrc_candidates:
        if not npmrc_path.exists():
            continue

        content = read_text_file(npmrc_path).lower()

        if scope and f"{scope.lower()}:registry" in content:
            return True

        if "registry=" in content and "registry.npmjs.org" not in content:
            return True

        if "always-auth=true" in content and "registry" in content:
            return True

    return False


def has_python_private_registry(requirements_dir: Path, target_path: Path, content: str) -> bool:
    if "--index-url" in content or "--extra-index-url" in content:
        if "pypi.org/simple" not in content and "files.pythonhosted.org" not in content:
            return True

    candidates = [
        requirements_dir / "pip.conf",
        requirements_dir / "pip.ini",
        requirements_dir / ".pypirc",
        target_path / "pip.conf",
        target_path / "pip.ini",
        target_path / ".pypirc",
    ]

    for candidate in candidates:
        if not candidate.exists():
            continue

        config_content = read_text_file(candidate).lower()

        if "index-url" in config_content and "pypi.org/simple" not in config_content:
            return True

        if "repository" in config_content and "pypi.org" not in config_content:
            return True

    return False


def has_npm_lockfile(package_dir: Path) -> bool:
    lockfiles = [
        "package-lock.json",
        "npm-shrinkwrap.json",
        "yarn.lock",
        "pnpm-lock.yaml",
    ]

    return any((package_dir / lockfile).exists() for lockfile in lockfiles)


def is_internal_package_candidate(name: str, ecosystem: DependencyEcosystem) -> bool:
    normalized_name = name.lower()

    if ecosystem == "npm":
        if any(normalized_name.startswith(scope) for scope in INTERNAL_NPM_SCOPES):
            return True

    return any(keyword in normalized_name for keyword in INTERNAL_PACKAGE_KEYWORDS)


def is_npm_version_pinned(version_specifier: str | None) -> bool:
    if not version_specifier:
        return False

    version = str(version_specifier).strip().lower()

    if not version:
        return False

    unsafe_tokens = [
        "^",
        "~",
        ">",
        "<",
        "*",
        "x",
        "latest",
        "file:",
        "git+",
        "http:",
        "https:",
        "workspace:",
    ]

    if any(token in version for token in unsafe_tokens):
        return False

    return bool(re.match(r"^\d+\.\d+\.\d+([a-zA-Z0-9.\-_+]+)?$", version))


def is_npm_version_loose(version_specifier: str | None) -> bool:
    if not version_specifier:
        return True

    version = str(version_specifier).strip().lower()

    loose_tokens = [
        "^",
        "~",
        ">",
        "<",
        "*",
        "x",
        "latest",
        "workspace:",
        "file:",
        "git+",
        "http:",
        "https:",
    ]

    return any(token in version for token in loose_tokens)


def extract_python_requirement(line: str) -> tuple[str, str | None] | None:
    cleaned = line.strip()

    if not cleaned or cleaned.startswith("#"):
        return None

    if cleaned.startswith(("-r ", "--requirement", "--index-url", "--extra-index-url", "-i ")):
        return None

    if " #" in cleaned:
        cleaned = cleaned.split(" #", maxsplit=1)[0].strip()

    match = re.match(
        r"^([A-Za-z0-9_.-]+)(?:\[.*?\])?\s*(.*)$",
        cleaned,
    )

    if not match:
        return None

    package_name = match.group(1).strip()
    version_specifier = match.group(2).strip() or None

    if not package_name:
        return None

    return package_name, version_specifier


def is_python_version_pinned(version_specifier: str | None) -> bool:
    if not version_specifier:
        return False

    version = version_specifier.strip()

    if not version.startswith("=="):
        return False

    if "*" in version:
        return False

    return bool(re.match(r"^==\s*[0-9]+(\.[0-9]+)*([a-zA-Z0-9.\-_+]+)?$", version))


def is_python_version_loose(version_specifier: str | None) -> bool:
    if not version_specifier:
        return True

    version = version_specifier.strip()

    if is_python_version_pinned(version):
        return False

    return any(operator in version for operator in PYTHON_REQUIREMENT_OPERATORS)


def build_risk_indicators(
    is_pinned: bool,
    is_loose: bool,
    is_internal_candidate: bool,
    private_registry_configured: bool,
    lockfile_present: bool | None,
) -> list[str]:
    indicators: list[str] = []

    if not is_pinned:
        indicators.append("VERSION_NOT_PINNED")

    if is_loose:
        indicators.append("LOOSE_VERSION_SPECIFIER")

    if is_internal_candidate:
        indicators.append("INTERNAL_PACKAGE_CANDIDATE")

    if is_internal_candidate and not private_registry_configured:
        indicators.append("PRIVATE_REGISTRY_MISSING_FOR_INTERNAL_PACKAGE")

    if lockfile_present is False:
        indicators.append("LOCKFILE_MISSING")

    if not indicators:
        indicators.append("LOW_RISK_DECLARATION")

    return indicators


def parse_npm_package_json(package_json_path: Path, target_path: Path) -> list[DependencyRecord]:
    dependencies: list[DependencyRecord] = []

    try:
        content = read_text_file(package_json_path)
        package_data = json.loads(content)
    except json.JSONDecodeError:
        return dependencies

    package_dir = package_json_path.parent
    lockfile_present = has_npm_lockfile(package_dir)
    file_path = relative_path(package_json_path, target_path)

    for group in NPM_DEPENDENCY_GROUPS:
        group_dependencies = package_data.get(group, {})

        if not isinstance(group_dependencies, dict):
            continue

        for package_name, version_specifier in group_dependencies.items():
            version_text = str(version_specifier)
            is_pinned = is_npm_version_pinned(version_text)
            is_loose = is_npm_version_loose(version_text)
            internal_candidate = is_internal_package_candidate(package_name, "npm")
            private_registry = has_npm_private_registry(
                package_dir=package_dir,
                target_path=target_path,
                package_name=package_name,
            )

            risk_indicators = build_risk_indicators(
                is_pinned=is_pinned,
                is_loose=is_loose,
                is_internal_candidate=internal_candidate,
                private_registry_configured=private_registry,
                lockfile_present=lockfile_present,
            )

            dependencies.append(
                DependencyRecord(
                    ecosystem="npm",
                    name=package_name,
                    declared_version=version_text,
                    dependency_group=group,
                    file_path=file_path,
                    line_number=find_line_number(content, f'"{package_name}"'),
                    is_pinned=is_pinned,
                    is_loose=is_loose,
                    is_internal_candidate=internal_candidate,
                    private_registry_configured=private_registry,
                    lockfile_present=lockfile_present,
                    risk_indicators=risk_indicators,
                )
            )

    return dependencies


def parse_python_requirements(requirements_path: Path, target_path: Path) -> list[DependencyRecord]:
    dependencies: list[DependencyRecord] = []

    content = read_text_file(requirements_path)
    requirements_dir = requirements_path.parent
    private_registry = has_python_private_registry(
        requirements_dir=requirements_dir,
        target_path=target_path,
        content=content.lower(),
    )

    file_path = relative_path(requirements_path, target_path)

    for line_number, line in enumerate(content.splitlines(), start=1):
        parsed = extract_python_requirement(line)

        if parsed is None:
            continue

        package_name, version_specifier = parsed

        is_pinned = is_python_version_pinned(version_specifier)
        is_loose = is_python_version_loose(version_specifier)
        internal_candidate = is_internal_package_candidate(package_name, "python")

        risk_indicators = build_risk_indicators(
            is_pinned=is_pinned,
            is_loose=is_loose,
            is_internal_candidate=internal_candidate,
            private_registry_configured=private_registry,
            lockfile_present=None,
        )

        dependencies.append(
            DependencyRecord(
                ecosystem="python",
                name=package_name,
                declared_version=version_specifier,
                dependency_group="requirements",
                file_path=file_path,
                line_number=line_number,
                is_pinned=is_pinned,
                is_loose=is_loose,
                is_internal_candidate=internal_candidate,
                private_registry_configured=private_registry,
                lockfile_present=None,
                risk_indicators=risk_indicators,
            )
        )

    return dependencies


def discover_package_json_files(target_path: Path) -> list[Path]:
    return [
        path
        for path in target_path.rglob("package.json")
        if path.is_file() and not should_ignore(path)
    ]


def discover_requirements_files(target_path: Path) -> list[Path]:
    return [
        path
        for path in target_path.rglob("requirements*.txt")
        if path.is_file() and not should_ignore(path)
    ]


def build_inventory_summary(dependencies: list[DependencyRecord]) -> DependencyInventorySummary:
    ecosystems = sorted({dependency.ecosystem for dependency in dependencies})

    return DependencyInventorySummary(
        total_dependencies=len(dependencies),
        npm_dependencies=sum(1 for dependency in dependencies if dependency.ecosystem == "npm"),
        python_dependencies=sum(1 for dependency in dependencies if dependency.ecosystem == "python"),
        pinned_dependencies=sum(1 for dependency in dependencies if dependency.is_pinned),
        loose_dependencies=sum(1 for dependency in dependencies if dependency.is_loose),
        unpinned_dependencies=sum(1 for dependency in dependencies if not dependency.is_pinned),
        internal_candidate_dependencies=sum(
            1 for dependency in dependencies if dependency.is_internal_candidate
        ),
        dependencies_missing_private_registry=sum(
            1
            for dependency in dependencies
            if "PRIVATE_REGISTRY_MISSING_FOR_INTERNAL_PACKAGE" in dependency.risk_indicators
        ),
        npm_dependencies_without_lockfile=sum(
            1
            for dependency in dependencies
            if dependency.ecosystem == "npm" and dependency.lockfile_present is False
        ),
        ecosystems_detected=ecosystems,
    )


def build_dependency_inventory(target: str) -> DependencyInventory:
    target_path = Path(target).resolve()

    if not target_path.exists():
        raise FileNotFoundError(f"Target path does not exist: {target}")

    if not target_path.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {target}")

    dependencies: list[DependencyRecord] = []

    for package_json_path in discover_package_json_files(target_path):
        dependencies.extend(
            parse_npm_package_json(
                package_json_path=package_json_path,
                target_path=target_path,
            )
        )

    for requirements_path in discover_requirements_files(target_path):
        dependencies.extend(
            parse_python_requirements(
                requirements_path=requirements_path,
                target_path=target_path,
            )
        )

    summary = build_inventory_summary(dependencies)

    return DependencyInventory(
        target_path=str(Path(target)),
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        dependencies=dependencies,
    )


def generate_inventory_json(inventory: DependencyInventory) -> str:
    return json.dumps(inventory.model_dump(mode="json"), indent=2)


def write_inventory_json(inventory: DependencyInventory, output_path: str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_inventory_json(inventory), encoding="utf-8")
    return path