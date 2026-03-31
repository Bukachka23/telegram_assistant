# Private Channel Monitoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Support runtime-addable public and private Telegram channel monitors using persisted channel IDs, forwarded-message setup for private channels, and dynamic monitoring without requiring restart.

**Architecture:** Introduce a SQLite-backed monitor store plus a monitor service that resolves public usernames and forwarded private channel messages into persisted monitor records keyed by chat ID. Replace startup-only username-based Telethon monitoring with a single event handler that filters incoming messages against persisted monitor records. Keep pending "forward me a message" setup state in memory per owner session, while persisting confirmed monitor records to SQLite.

**Tech Stack:** aiogram 3, Telethon, aiosqlite, existing bot services/tests

---

### Task 1: Add persisted monitor model and storage

**Files:**
- Create: `src/bot/services/monitors.py`
- Modify: `src/bot/domain/models.py`
- Modify: `src/bot/shared/constants.py`
- Test: `tests/unit/test_monitors.py`

**Step 1: Write the failing storage tests**
- Add tests for creating monitor rows, listing monitors by owner, finding a monitor by chat ID, and deleting by username/chat ID.
- Add a test that `init()` creates the monitor schema in a fresh SQLite file.

**Step 2: Run focused tests to confirm failure**
- Run: `pytest tests/unit/test_monitors.py -q`
- Expected: import/attribute failures because monitor store does not exist yet.

**Step 3: Add domain and schema support**
- Add a persisted monitor dataclass with fields for `owner_user_id`, `chat_id`, `username`, `title`, `keywords`, and `source_type`.
- Extend `SCHEMA` in `src/bot/shared/constants.py` with a `channel_monitors` table.

**Step 4: Implement `MonitorStore`**
- Implement async init/close and CRUD methods:
  - `upsert_monitor(...)`
  - `list_monitors(owner_user_id)`
  - `get_monitor_by_chat_id(chat_id)`
  - `remove_monitor(owner_user_id, identifier)`
- Persist keywords as JSON text.

**Step 5: Run focused tests**
- Run: `pytest tests/unit/test_monitors.py -q`
- Expected: PASS.

### Task 2: Add monitor service for public resolution and pending private setup

**Files:**
- Modify: `src/bot/services/monitors.py`
- Test: `tests/unit/test_monitors.py`

**Step 1: Write service-level failing tests**
- Add tests for:
  - starting pending private setup
  - resolving a public `@username` through a fake Telethon client and persisting it
  - consuming a forwarded channel message and persisting it
  - rejecting invalid forwarded messages

**Step 2: Run focused tests to confirm failure**
- Run: `pytest tests/unit/test_monitors.py -q`
- Expected: missing service methods / failing assertions.

**Step 3: Implement `MonitorService`**
- Add in-memory pending state keyed by owner user ID.
- Add methods:
  - `begin_pending_add(owner_user_id, keywords)`
  - `has_pending_add(owner_user_id)`
  - `add_public_monitor(owner_user_id, channel_ref, keywords)`
  - `add_forwarded_monitor(owner_user_id, forwarded_chat)`
  - `list_monitors(owner_user_id)`
  - `remove_monitor(owner_user_id, identifier)`
- Use Telethon `get_entity()` for public adds.

**Step 4: Run focused tests**
- Run: `pytest tests/unit/test_monitors.py -q`
- Expected: PASS.

### Task 3: Rework `/monitor` commands to use persisted monitors and forwarded-message flow

**Files:**
- Modify: `src/bot/handlers/commands.py`
- Modify: `src/bot/main.py`
- Test: `tests/unit/test_commands.py`

**Step 1: Write failing command tests**
- Add tests for:
  - `/monitor` listing persisted monitors
  - `/monitor add` entering pending forward mode
  - `/monitor add @public_channel` persisting immediately
  - forwarded channel message completing setup
  - `/monitor remove <id-or-username>` removing a persisted monitor

**Step 2: Run focused tests to confirm failure**
- Run: `pytest tests/unit/test_commands.py -q`
- Expected: failures because current commands still mutate in-memory YAML config objects.

**Step 3: Implement command changes**
- Update `setup_commands(...)` signature to accept `MonitorService`.
- Replace `monitor_config` mutations with monitor service calls.
- Add a non-command message handler in the commands router that consumes the next forwarded channel message when pending setup exists.
- Keep clear user guidance/error messages.

**Step 4: Run focused tests**
- Run: `pytest tests/unit/test_commands.py -q`
- Expected: PASS.

### Task 4: Replace startup-only username monitoring with dynamic chat-ID monitoring

**Files:**
- Modify: `src/bot/handlers/channels.py`
- Modify: `src/bot/main.py`
- Test: `tests/unit/test_channels_handler.py`

**Step 1: Write failing handler tests**
- Add tests for matching by `chat_id` instead of username.
- Add a test that private channels without usernames still match if their `chat_id` is monitored.

**Step 2: Run focused tests to confirm failure**
- Run: `pytest tests/unit/test_channels_handler.py -q`
- Expected: failures because current handler is username-based.

**Step 3: Implement dynamic monitoring**
- Register one broad Telethon `NewMessage` handler when userbot exists.
- On each event, load or query persisted monitor data by `chat_id`.
- Keep keyword matching and saved-message notification behavior.
- Remove dependence on startup `settings.channels.monitor` for runtime monitor activation.

**Step 4: Run focused tests**
- Run: `pytest tests/unit/test_channels_handler.py -q`
- Expected: PASS.

### Task 5: Wire stores/services at startup and verify restart persistence

**Files:**
- Modify: `src/bot/main.py`
- Test: `tests/unit/test_main.py`
- Test: `tests/unit/test_monitors.py`

**Step 1: Write failing integration-oriented tests**
- Add a test that monitor data survives store re-open.
- Add a startup helper test if needed for monitor-service wiring.

**Step 2: Run focused tests to confirm failure**
- Run: `pytest tests/unit/test_monitors.py tests/unit/test_main.py -q`
- Expected: failures because startup does not yet create/wire monitor store.

**Step 3: Implement wiring**
- Instantiate and initialize `MonitorStore` in `run()`.
- Create `MonitorService` when userbot exists.
- Pass it to command setup and channel monitoring setup.
- Ensure clean shutdown closes the store.

**Step 4: Run focused tests**
- Run: `pytest tests/unit/test_monitors.py tests/unit/test_main.py -q`
- Expected: PASS.

### Task 6: Final regression verification and small UX polish

**Files:**
- Modify: `src/bot/handlers/commands.py` (if wording needs polish)
- Verify: affected unit tests + full suite

**Step 1: Run focused verification**
- Run: `pytest tests/unit/test_monitors.py tests/unit/test_commands.py tests/unit/test_channels_handler.py -q`
- Expected: PASS.

**Step 2: Run full verification**
- Run: `pytest -q`
- Expected: PASS.
- Run: `python -m py_compile $(find src -name '*.py' | tr '\n' ' ')`
- Expected: no output / success.

**Step 3: Final polish**
- Ensure `/monitor` help text documents private setup via forwarded message.
- Ensure errors explain when Telethon/userbot is unavailable.

**Step 4: Commit**
- Suggested message: `feat: support persisted private channel monitoring`
