from __future__ import annotations

from dataclasses import dataclass
from typing import Any


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    issues: list[ValidationIssue]

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]


@dataclass(frozen=True)
class PlatformBundle:
    platform: JsonDict
    signup_bonus: JsonDict
    trading_fee: JsonDict | None
    fiat_onramp: JsonDict | None
    regional_availability: JsonDict | None
    benefit_claims: list[JsonDict]


@dataclass(frozen=True)
class ComparisonBundle:
    job: JsonDict
    platform_a: PlatformBundle
    platform_b: PlatformBundle
    editorial_rules: JsonDict
    sources_by_id: dict[str, JsonDict]
