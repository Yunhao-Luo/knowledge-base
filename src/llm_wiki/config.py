from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(slots=True)
class ProviderConfig:
    kind: str
    model: str
    api_key_env: str | None = None
    base_url: str | None = None
    command: str | None = None


@dataclass(slots=True)
class KnowledgeConfig:
    root: Path
    schema_file: Path


@dataclass(slots=True)
class RuntimeConfig:
    max_context_files: int = 6
    max_source_chars: int = 24_000
    max_page_chars: int = 8_000


@dataclass(slots=True)
class AppConfig:
    provider: ProviderConfig
    knowledge: KnowledgeConfig
    runtime: RuntimeConfig
    config_path: Path


def load_config(config_path: Path) -> AppConfig:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    provider = ProviderConfig(**data["provider"])
    knowledge_data = data["knowledge"]
    runtime = RuntimeConfig(**data.get("runtime", {}))
    knowledge_root = (config_path.parent.parent / knowledge_data["root"]).resolve()
    schema_file = knowledge_root / knowledge_data.get("schema_file", "schema/AGENTS.md")
    return AppConfig(
        provider=provider,
        knowledge=KnowledgeConfig(root=knowledge_root, schema_file=schema_file),
        runtime=runtime,
        config_path=config_path,
    )
