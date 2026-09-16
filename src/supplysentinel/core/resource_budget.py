from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from supplysentinel.core.exceptions import SupplySentinelError


SCAN_MAX_ENTRIES_ENV = "BUILDSHIELD_SCAN_MAX_ENTRIES"
SCAN_MAX_FILES_ENV = "BUILDSHIELD_SCAN_MAX_FILES"
SCAN_MAX_FILE_BYTES_ENV = "BUILDSHIELD_SCAN_MAX_FILE_BYTES"
SCAN_MAX_TOTAL_BYTES_ENV = "BUILDSHIELD_SCAN_MAX_TOTAL_BYTES"

DEFAULT_SCAN_MAX_ENTRIES = 20_000
DEFAULT_SCAN_MAX_FILES = 500
DEFAULT_SCAN_MAX_FILE_BYTES = 2_097_152
DEFAULT_SCAN_MAX_TOTAL_BYTES = 10_485_760


class RepositoryResourceLimitError(SupplySentinelError):
    """Raised when repository scanning exceeds a configured resource budget."""


class RepositoryResourceConfigurationError(SupplySentinelError):
    """Raised when repository resource-control configuration is invalid."""


@dataclass(frozen=True)
class RepositoryResourceSettings:
    max_entries: int
    max_files: int
    max_file_bytes: int
    max_total_bytes: int


@dataclass(frozen=True)
class RepositoryResourceUsage:
    entries_seen: int
    relevant_files: int
    relevant_bytes: int


def _parse_positive_int(
    env_name: str,
    default: int,
    *,
    maximum: int,
) -> int:
    raw_value = os.getenv(env_name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except ValueError as error:
        raise RepositoryResourceConfigurationError(
            "Repository scan resource-control configuration is invalid."
        ) from error

    if value < 1 or value > maximum:
        raise RepositoryResourceConfigurationError(
            "Repository scan resource-control configuration is invalid."
        )

    return value


def get_repository_resource_settings() -> RepositoryResourceSettings:
    return RepositoryResourceSettings(
        max_entries=_parse_positive_int(
            SCAN_MAX_ENTRIES_ENV,
            DEFAULT_SCAN_MAX_ENTRIES,
            maximum=1_000_000,
        ),
        max_files=_parse_positive_int(
            SCAN_MAX_FILES_ENV,
            DEFAULT_SCAN_MAX_FILES,
            maximum=50_000,
        ),
        max_file_bytes=_parse_positive_int(
            SCAN_MAX_FILE_BYTES_ENV,
            DEFAULT_SCAN_MAX_FILE_BYTES,
            maximum=67_108_864,
        ),
        max_total_bytes=_parse_positive_int(
            SCAN_MAX_TOTAL_BYTES_ENV,
            DEFAULT_SCAN_MAX_TOTAL_BYTES,
            maximum=536_870_912,
        ),
    )


def _budget_error(reason: str) -> RepositoryResourceLimitError:
    return RepositoryResourceLimitError(
        f"Repository scan resource budget exceeded: {reason}."
    )


def validate_repository_scan_budget(
    target_path: Path,
    *,
    is_relevant_file: Callable[[Path], bool],
    ignored_directories: set[str],
) -> RepositoryResourceUsage:
    settings = get_repository_resource_settings()

    entries_seen = 0
    relevant_files = 0
    relevant_bytes = 0
    directories_to_visit = [target_path]

    while directories_to_visit:
        directory = directories_to_visit.pop()

        with os.scandir(directory) as entries:
            for entry in entries:
                entries_seen += 1

                if entries_seen > settings.max_entries:
                    raise _budget_error(
                        f"entry count exceeds {settings.max_entries}"
                    )

                path = Path(entry.path)

                if entry.is_dir(follow_symlinks=False):
                    if (
                        entry.name not in ignored_directories
                        and not entry.is_symlink()
                    ):
                        directories_to_visit.append(path)

                    continue

                if entry.is_symlink():
                    continue

                if not entry.is_file(follow_symlinks=False):
                    continue

                if not is_relevant_file(path):
                    continue

                relevant_files += 1

                if relevant_files > settings.max_files:
                    raise _budget_error(
                        f"security-relevant file count exceeds {settings.max_files}"
                    )

                file_size = entry.stat(follow_symlinks=False).st_size

                if file_size > settings.max_file_bytes:
                    raise _budget_error(
                        "a security-relevant file exceeds "
                        f"{settings.max_file_bytes} bytes"
                    )

                relevant_bytes += file_size

                if relevant_bytes > settings.max_total_bytes:
                    raise _budget_error(
                        "aggregate security-relevant input exceeds "
                        f"{settings.max_total_bytes} bytes"
                    )

    return RepositoryResourceUsage(
        entries_seen=entries_seen,
        relevant_files=relevant_files,
        relevant_bytes=relevant_bytes,
    )
