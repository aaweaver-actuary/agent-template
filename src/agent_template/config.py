from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

PathLike = str | Path


def _coerce_path(value: PathLike) -> Path:
    return value if isinstance(value, Path) else Path(value)


@dataclass
class Paths:
    tmp: PathLike = Path(".agent_template/tmp")
    state_file: PathLike = Path(".agent_template/state.json")
    artifacts: PathLike = Path(".agent_template/artifacts")
    logs: PathLike = Path(".agent_template/logs")
    screenshots: PathLike = Path(".agent_template/screenshots")

    def __post_init__(self) -> None:
        self.tmp = _coerce_path(self.tmp)
        self.state_file = _coerce_path(self.state_file)
        self.artifacts = _coerce_path(self.artifacts)
        self.logs = _coerce_path(self.logs)
        self.screenshots = _coerce_path(self.screenshots)


@dataclass
class Config:
    viewport_size: dict[str, int] = field(
        default_factory=lambda: {"width": 1280, "height": 720}
    )
    headless: bool = True
    timeout: float = 30.0
    paths: Paths = field(default_factory=Paths)

    def screenshot_path(self, label: str) -> Path:
        """Return the file path for a screenshot with the given label."""
        return self.paths.screenshots / f"{label}.png"

    def now(self) -> str:
        """Return the current UTC time as an ISO 8601 string."""
        return datetime.now(timezone.utc).isoformat()

    @property
    def stdout(self) -> Path:
        """Return the file path for the standard output log."""
        return self.paths.logs / "stdout.log"

    @property
    def stderr(self) -> Path:
        """Return the file path for the standard error log."""
        return self.paths.logs / "stderr.log"
