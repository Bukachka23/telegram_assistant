# Telegram Assistant Bot

Personal Telegram bot with LLM-powered assistance, Obsidian vault integration, and channel monitoring.

## Features

- **LLM Chat** — OpenRouter with any model, real-time streaming via `sendMessageDraft`
- **Obsidian Vault** — search, read, create, append notes via LLM tool calling
- **Channel Monitoring** — real-time keyword alerts + on-demand channel queries
- **Model Switching** — change LLM model mid-conversation with `/model`

## Setup

```bash
# Clone and install
pip install -e ".[dev]"

# Configure
cp config.example.yaml config.yaml
cp .env.example .env
# Edit both files with your values

# Run
telegram-assistant
```

## Configuration

- `.env` — secrets (bot token, API keys, user ID)
- `config.yaml` — settings (model, vault path, channel monitors)

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/model [name]` | Show or switch LLM model |
| `/monitor` | Manage channel monitors |
| `/vault search <query>` | Search vault notes |
| `/clear` | Clear conversation history |
