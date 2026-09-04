from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ProjectSettings(BaseModel):
    name: str = "agent-office"
    path: Path = Field(default_factory=Path.cwd)


class ObserverSettings(BaseModel):
    idle_timeout: float = 30.0
    scan_interval: float = 1.0


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000


class OfficeSettings(BaseModel):
    desks: int = 8


class FrontendSettings(BaseModel):
    port: int = 5173


class Settings(BaseModel):
    project: ProjectSettings = Field(default_factory=ProjectSettings)
    projects: list[ProjectSettings] = Field(default_factory=list)
    observer: ObserverSettings = Field(default_factory=ObserverSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    office: OfficeSettings = Field(default_factory=OfficeSettings)
    frontend: FrontendSettings = Field(default_factory=FrontendSettings)
    runtime_path: Path = Path("runtime/events.jsonl")

    @classmethod
    def load(cls, path: Path | str = "config/office.yaml") -> "Settings":
        config_path = Path(path)
        if not config_path.exists():
            return cls()
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        settings = cls.model_validate(raw)
        if not settings.project.path.is_absolute():
            settings.project.path = (config_path.parent.parent / settings.project.path).resolve()
        if not settings.runtime_path.is_absolute():
            settings.runtime_path = (config_path.parent.parent / settings.runtime_path).resolve()
        return settings

    @classmethod
    def for_project(cls, path: Path) -> "Settings":
        path = path.resolve()
        return cls(
            project=ProjectSettings(name=path.name, path=path),
            projects=[ProjectSettings(name=path.name, path=path)],
            runtime_path=path / "runtime" / "events.jsonl",
        )
