import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings

from bot.config.constants import CWD, PROJECT_ROOT
from bot.domain.models.config import (
    ChannelsConfig,
    ConversationConfig,
    LLMConfig,
    SchedulerConfig,
    StreamingConfig,
    TelegraphConfig,
    VaultConfig,
)


class Settings(BaseSettings):
    # Secrets from .env
    bot_token: str = ""
    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    owner_user_id: int = 0

    memory_db_path: str = "data/memory.db"

    # YAML config sections
    llm: LLMConfig = Field(default_factory=LLMConfig)
    vault: VaultConfig = Field(default_factory=VaultConfig)
    conversation: ConversationConfig = Field(default_factory=ConversationConfig)
    streaming: StreamingConfig = Field(default_factory=StreamingConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    telegraph: TelegraphConfig = Field(default_factory=TelegraphConfig)

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "extra": "ignore"}


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file, return empty dict if missing."""
    if not path.exists():
        return {}
    with Path(path).open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _find_file(name: str) -> Path:
    """Find a config file in CWD or project root."""
    for base in (CWD, PROJECT_ROOT):
        path = base / name
        if path.exists():
            return path
    return CWD / name


def load_settings(yaml_path: Path | None = None, env_path: Path | None = None) -> Settings:
    """Load settings from .env (secrets) + config.yaml (settings)."""
    yaml_path = yaml_path or _find_file("config.yaml")
    yaml_data = _load_yaml(yaml_path)

    # Allow VAULT_PATH env var to override yaml config (for Docker)
    vault_override = os.environ.get("VAULT_PATH")
    if vault_override:
        vault_cfg = yaml_data.get("vault", {})
        vault_cfg["path"] = vault_override
        yaml_data["vault"] = vault_cfg

    kwargs: dict[str, Any] = {}
    if env_path:
        kwargs["_env_file"] = str(env_path)

    return Settings(**yaml_data, **kwargs)
