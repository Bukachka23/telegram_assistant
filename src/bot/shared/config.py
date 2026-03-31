"""Configuration loading from .env and config.yaml."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CWD = Path.cwd()


class LLMConfig(BaseModel):
    default_model: str = "anthropic/claude-sonnet-4"
    max_tokens: int = 4096
    temperature: float = 0.7


class VaultConfig(BaseModel):
    path: str = "/home/pi/obsidian-vault"
    default_folder: str = "notes"


class ConversationConfig(BaseModel):
    session_timeout_minutes: int = 30
    max_history_messages: int = 50


class StreamingConfig(BaseModel):
    draft_interval_ms: int = 800


class ChannelMonitorEntry(BaseModel):
    username: str
    keywords: list[str] = Field(default_factory=list)


class ChannelsConfig(BaseModel):
    monitor: list[ChannelMonitorEntry] = Field(default_factory=list)


class Settings(BaseSettings):
    # Secrets from .env
    bot_token: str = ""
    openrouter_api_key: str = ""
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    owner_user_id: int = 0

    # YAML config sections
    llm: LLMConfig = Field(default_factory=LLMConfig)
    vault: VaultConfig = Field(default_factory=VaultConfig)
    conversation: ConversationConfig = Field(default_factory=ConversationConfig)
    streaming: StreamingConfig = Field(default_factory=StreamingConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)

    model_config = {"env_file": str(_PROJECT_ROOT / ".env"), "extra": "ignore"}


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file, return empty dict if missing."""
    if not path.exists():
        return {}
    with Path(path).open() as f:
        return yaml.safe_load(f) or {}


def _find_file(name: str) -> Path:
    """Find a config file in CWD or project root."""
    for base in (_CWD, _PROJECT_ROOT):
        path = base / name
        if path.exists():
            return path
    return _CWD / name  # Default to CWD even if missing


def load_settings(
    yaml_path: Path | None = None,
    env_path: Path | None = None,
) -> Settings:
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
