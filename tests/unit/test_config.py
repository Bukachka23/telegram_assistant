"""Tests for configuration loading."""

from pathlib import Path

import yaml

from bot.config import Settings, load_settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.llm.default_model == "anthropic/claude-sonnet-4"
        assert s.conversation.session_timeout_minutes == 30
        assert s.streaming.draft_interval_ms == 800

    def test_load_from_yaml(self, tmp_path: Path):
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            yaml.dump(
                {
                    "llm": {"default_model": "openai/gpt-4o", "max_tokens": 2048},
                    "vault": {"path": "/tmp/vault"},
                }
            )
        )
        env_file = tmp_path / ".env"
        env_file.write_text("BOT_TOKEN=test123\nOWNER_USER_ID=999\n")

        settings = load_settings(yaml_path=yaml_file, env_path=env_file)
        assert settings.llm.default_model == "openai/gpt-4o"
        assert settings.llm.max_tokens == 2048
        assert settings.vault.path == "/tmp/vault"
        assert settings.bot_token == "test123"
        assert settings.owner_user_id == 999

    def test_missing_yaml_uses_defaults(self, tmp_path: Path):
        missing = tmp_path / "nonexistent.yaml"
        settings = load_settings(yaml_path=missing)
        assert settings.llm.default_model == "anthropic/claude-sonnet-4"

    def test_channel_monitor_config(self, tmp_path: Path):
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            yaml.dump(
                {
                    "channels": {
                        "monitor": [
                            {"username": "@test", "keywords": ["python", "ai"]},
                        ]
                    }
                }
            )
        )
        settings = load_settings(yaml_path=yaml_file)
        assert len(settings.channels.monitor) == 1
        assert settings.channels.monitor[0].username == "@test"
        assert settings.channels.monitor[0].keywords == ["python", "ai"]
