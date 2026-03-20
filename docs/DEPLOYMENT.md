# Deploying Telegram Assistant on Raspberry Pi 5

## Prerequisites

On your Raspberry Pi:
- Raspberry Pi OS (64-bit) — Bookworm or newer
- Docker and Docker Compose installed
- SSH access from your MacBook
- Syncthing running for Obsidian vault sync (optional)

---

## Step 1: Install Docker on Raspberry Pi

SSH into your Pi and run:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Add your user to docker group (avoids sudo)
sudo usermod -aG docker $USER

# Log out and back in for group to take effect
exit
# SSH back in

# Verify
docker --version
docker compose version
```

---

## Step 2: Clone the project

```bash
# On your Pi
cd ~
git clone <your-repo-url> telegram-assistant
cd telegram-assistant
```

Or copy from your MacBook via SCP:

```bash
# From your MacBook
scp -r /Users/bukachiyboss/Documents/PROJECTS/TELEGRAM_ASSISTANT pi@<PI_IP>:~/telegram-assistant
```

---

## Step 3: Configure secrets

```bash
cd ~/telegram-assistant

# Create .env file with your secrets
cat > .env << 'EOF'
BOT_TOKEN=your_telegram_bot_token
OPENROUTER_API_KEY=sk-or-your_key_here
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
OWNER_USER_ID=your_telegram_user_id
EOF

# Secure the file
chmod 600 .env
```

**Where to get these values:**

| Secret | Where to get it |
|--------|----------------|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → /newbot |
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `TELEGRAM_API_ID` | [my.telegram.org](https://my.telegram.org) → API development tools |
| `TELEGRAM_API_HASH` | Same as above |
| `OWNER_USER_ID` | Send a message to [@userinfobot](https://t.me/userinfobot) |

---

## Step 4: Configure settings

Edit `config.yaml`:

```bash
nano config.yaml
```

Key settings to change:

```yaml
llm:
  default_model: "anthropic/claude-sonnet-4"  # your preferred model

vault:
  path: "/home/pi/obsidian-vault"  # path on Pi (overridden by Docker)
  default_folder: "notes"

streaming:
  draft_interval_ms: 800  # 600-1000ms range for smooth animation
```

---

## Step 5: Set up Obsidian vault sync (optional)

If you want vault tools, set up Syncthing between MacBook and Pi:

```bash
# Install Syncthing on Pi
sudo apt install syncthing

# Enable as service
sudo systemctl enable syncthing@$USER
sudo systemctl start syncthing@$USER

# Access web UI at http://<PI_IP>:8384
# Add your MacBook's vault folder as a shared folder
# Default sync path: /home/pi/obsidian-vault
```

---

## Step 6: Authenticate Telethon (one-time)

This creates the session file for channel monitoring. **Must be done before Docker.**

```bash
cd ~/telegram-assistant

# Create data directory for persistent files
mkdir -p data

# Run auth script directly (not in Docker — needs interactive input)
pip install telethon pydantic pydantic-settings pyyaml python-dotenv
python scripts/auth_telethon.py
```

You'll see:
```
🔐 Telethon Authentication
========================================
A code will be sent to your Telegram app.
Check 'Telegram' service messages.

Please enter your phone: +1234567890
Please enter the code you received: 12345

✅ Authenticated as: YourName (ID: 123456789)
📁 Session saved to: data/userbot.session
```

**The code appears in your Telegram app** — look for a message from "Telegram".

---

## Step 7: Set vault path for Docker

Add your vault path to `.env`:

```bash
echo "VAULT_PATH=/home/pi/obsidian-vault" >> .env
```

This tells Docker Compose where to mount the vault from the host.

---

## Step 8: Build and start

```bash
cd ~/telegram-assistant

# Build the image (first time takes ~3-5 min on Pi)
docker compose build

# Start in background
docker compose up -d

# Check it's running
docker compose logs -f
```

You should see:
```
INFO: Starting Telegram Assistant Bot...
INFO: Model: anthropic/claude-sonnet-4
INFO: Vault: /vault
INFO: Telethon: connected
INFO: Monitors: 0 channels
```

---

## Step 9: Verify it works

1. Open Telegram
2. Find your bot (the one you created with @BotFather)
3. Send `/start`
4. Send a message like "Hello, what can you do?"
5. You should see a streaming response with formatted text

---

## Managing the bot

```bash
# View logs
docker compose logs -f

# Restart
docker compose restart

# Stop
docker compose down

# Rebuild after code changes
docker compose build && docker compose up -d

# Check status
docker compose ps
```

---

## Updating the bot

```bash
cd ~/telegram-assistant

# Pull latest code
git pull

# Rebuild and restart
docker compose build
docker compose up -d
```

---

## File structure on Pi

```
~/telegram-assistant/
├── .env                    # Secrets (never commit)
├── config.yaml             # Settings
├── data/
│   └── userbot.session     # Telethon auth (persistent)
├── docker-compose.yml
├── Dockerfile
└── src/                    # Bot source code

/home/pi/obsidian-vault/    # Synced from MacBook (mounted as /vault in Docker)
```

---

## Troubleshooting

### Bot doesn't respond

```bash
# Check logs for errors
docker compose logs --tail 50

# Common issues:
# - BOT_TOKEN wrong → "Unauthorized"
# - OWNER_USER_ID wrong → messages silently ignored
# - OPENROUTER_API_KEY wrong → "LLM error: 401"
```

### Telethon "session expired"

```bash
# Stop bot
docker compose down

# Re-authenticate
python scripts/auth_telethon.py

# Restart
docker compose up -d
```

### Vault not found

```bash
# Check vault is mounted correctly
docker compose exec bot ls /vault

# If empty, verify VAULT_PATH in .env matches your actual vault path
```

### ARM64 build issues

If a Python package fails to build on Pi:

```bash
# Install system-level build deps
sudo apt install python3-dev libffi-dev build-essential

# Rebuild
docker compose build --no-cache
```

### View resource usage

```bash
docker stats telegram-assistant
```

Typical usage on Pi 5: ~50MB RAM, <1% CPU when idle.
