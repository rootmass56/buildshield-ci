from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_PATH_LENGTH = 1024
MAX_LABEL_LENGTH = 128
MAX_OSV_TIMEOUT_SECONDS = 30

ScanReportFormat = Literal["json", "md", "html", "sarif"]
CompareReportFormat = Literal["json", "md", "html"]


class StrictRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _validate_path_text(value: str) -> str:
    if "\x00" in value:
        raise ValueError("Path values must not contain NUL bytes.")

    return value


def _validate_label_text(value: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError("Labels must not be blank.")

    if any(character in normalized for character in ("\x00", "\r", "\n")):
        raise ValueError("Labels must not contain control characters.")

    return normalized


class ScanRequest(StrictRequestModel):
    target_path: str = Field(
        default="samples/vulnerable-repo",
        min_length=1,
        max_length=MAX_PATH_LENGTH,
    )
    policy_path: str | None = Field(
        default="buildshield-policy.yml",
        min_length=1,
        max_length=MAX_PATH_LENGTH,
    )
    report_formats: list[ScanReportFormat] = Field(
        default_factory=lambda: ["json", "md", "html", "sarif"],
        max_length=4,
    )

    @field_validator("target_path", "policy_path")
    @classmethod
    def validate_paths(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return _validate_path_text(value)

    @field_validator("report_formats")
    @classmethod
    def reject_duplicate_formats(
        cls,
        value: list[ScanReportFormat],
    ) -> list[ScanReportFormat]:
        if len(value) != len(set(value)):
            raise ValueError("Report formats must be unique.")

        return value


class CompareRequest(StrictRequestModel):
    baseline_path: str = Field(
        default="samples/vulnerable-repo",
        min_length=1,
        max_length=MAX_PATH_LENGTH,
    )
    target_path: str = Field(
        default="samples/secure-repo",
        min_length=1,
        max_length=MAX_PATH_LENGTH,
    )
    baseline_label: str = Field(
        default="Vulnerable Repo",
        min_length=1,
        max_length=MAX_LABEL_LENGTH,
    )
    target_label: str = Field(
        default="Secure Repo",
        min_length=1,
        max_length=MAX_LABEL_LENGTH,
    )
    report_formats: list[CompareReportFormat] = Field(
        default_factory=lambda: ["json", "md", "html"],
        max_length=3,
    )

    @field_validator("baseline_path", "target_path")
    @classmethod
    def validate_paths(cls, value: str) -> str:
        return _validate_path_text(value)

    @field_validator("baseline_label", "target_label")
    @classmethod
    def validate_labels(cls, value: str) -> str:
        return _validate_label_text(value)

    @field_validator("report_formats")
    @classmethod
    def reject_duplicate_formats(
        cls,
        value: list[CompareReportFormat],
    ) -> list[CompareReportFormat]:
        if len(value) != len(set(value)):
            raise ValueError("Report formats must be unique.")

        return value


class InventoryRequest(StrictRequestModel):
    target_path: str = Field(
        default="samples/vulnerable-repo",
        min_length=1,
        max_length=MAX_PATH_LENGTH,
    )

    @field_validator("target_path")
    @classmethod
    def validate_target_path(cls, value: str) -> str:
        return _validate_path_text(value)


class VulnerabilityIntelligenceRequest(StrictRequestModel):
    target_path: str = Field(
        default="samples/secure-repo",
        min_length=1,
        max_length=MAX_PATH_LENGTH,
    )
    online_lookup: bool = Field(default=False)
    timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=MAX_OSV_TIMEOUT_SECONDS,
    )

    @field_validator("target_path")
    @classmethod
    def validate_target_path(cls, value: str) -> str:
        return _validate_path_text(value)
