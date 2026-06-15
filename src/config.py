import yaml
from pathlib import Path
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class Settings:
    device: str = "cuda"
    host: str = "0.0.0.0"
    port: int = 60615
    mc_version: str = "26.1.2"
    proxy: str | None = None
    models_cache_dir: str | None = None

    @classmethod
    def from_yaml(cls, config_path: Path | None = None) -> "Settings":
        if config_path is None:
            config_path = PROJECT_ROOT / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()


settings = Settings.from_yaml()
