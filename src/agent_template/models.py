from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


ReflectionClassification = Literal[
    "verification_failure",
    "stalled_progress",
    "scope_delta",
    "boot_failure",
    "schema_error",
]

IssueKind = Literal["code", "test", "spec", "scope"]

IssueSubtype = Literal[
    "selector_mismatch",
    "missing_ui",
    "runtime_error",
    "network_error",
    "stale_acceptance_criteria",
    "outside_work_package",
    "schema_violation",
    "same_files_same_failure",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ArtifactRef(BaseModel):
    """Reference to a stored artifact on disk."""

    kind: Literal[
        "stdout",
        "stderr",
        "screenshot",
        "console_log",
        "network_log",
        "dom_snapshot",
        "trace",
        "json",
        "text",
    ]
    path: str
    created_at: str = Field(default_factory=utc_now_iso)
    label: str | None = None


class CommandResult(BaseModel):
    """Result from executing a command in the sandbox."""

    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    started_at: str
    finished_at: str
    duration_seconds: float
    cwd: str


class ServiceHandle(BaseModel):
    """Represents a long-lived background process."""

    name: str
    pid: int
    command: list[str]
    cwd: str
    started_at: str
    stdout_artifact: ArtifactRef | None = None
    stderr_artifact: ArtifactRef | None = None


class SnapshotRef(BaseModel):
    """Reference to a checkpoint/snapshot for rollback."""

    label: str
    path: str
    created_at: str = Field(default_factory=utc_now_iso)


class CheckResult(BaseModel):
    """Single verifier check result."""

    name: str
    passed: bool
    evidence: str | None = None
    artifacts: list[ArtifactRef] = Field(default_factory=list)


class MilestoneResult(BaseModel):
    """Structured score for a milestone."""

    milestone_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    checks: list[CheckResult]
    summary: str
    artifacts: list[ArtifactRef] = Field(default_factory=list)


class ReflectionRecord(BaseModel):
    """Artifact-linked reflection record for a failed or stalled incident."""

    trigger_type: str
    slice_id: str
    milestone_id: str | None = None
    target: str
    expected_evidence: list[str]
    observed_evidence: list[str]
    changed_since_last_attempt: list[str] = Field(default_factory=list)
    failed_checks: list[str] = Field(default_factory=list)
    classification: ReflectionClassification
    issue_kind: IssueKind
    issue_subtype: IssueSubtype
    touched_files: list[str] = Field(default_factory=list)
    next_strategy: list[str]
    no_progress_count: int = 0
    durable_memory_candidate: bool = False
    artifacts: list[ArtifactRef] = Field(default_factory=list)


class WorkPackage(BaseModel):
    """Machine-readable bounded handoff artifact for the next attempt."""

    slice_id: str
    goal: str
    modify_files: list[str]
    read_files: list[str]
    acceptance_criteria: list[str]
    evidence_required: list[str]
    non_goals: list[str]
    rollback_risk: str
    escalation_conditions: list[str]


class RunState(BaseModel):
    """Machine-readable state for a single autonomous run."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    objective: str
    repo_path: str
    branch_id: str = "main"
    milestone_id: str | None = None
    current_score: float | None = None
    checkpoint: SnapshotRef | None = None
    no_progress_count: int = 0
    touched_files: list[str] = Field(default_factory=list)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    last_reflection: ReflectionRecord | None = None
    last_work_package: WorkPackage | None = None
    updated_at: str = Field(default_factory=utc_now_iso)
