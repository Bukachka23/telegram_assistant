# Model Manager — Feature Investigation

**Date:** 2026-04-04  
**Status:** Investigation / Pre-design  

---

## 1. Observation (as-given)

> **Model manager:** predefined model menu, `/model` command, current-model badge, per-agent default model, model aliases like `fast`, `smart`, `research`, and automatic fallback when one provider fails or rate-limits. This fits naturally because the bot already has agent profiles, OpenRouter integration, and conversation-level model state, so we are extending an existing concept rather than inventing a new subsystem.

---

## 2. What Already Exists (Current State)

### 2.1 Conversation-level model state ✅
- `Conversation` dataclass (`domain/models/base.py`) has a `model: str` field per user session.
- `ConversationManager` exposes `get_model(user_id)` / `set_model(user_id, model)`.
- New sessions inherit `self._default_model` (sourced from `config.yaml → llm.default_model`).
- `LLMService.stream_response()` reads `model = self._conversations.get_model(user_id)` on every call.

### 2.2 `/model` command ✅ (basic)
- Already registered in `handlers/commands.py`.
- `/model` → shows current model string.
- `/model <raw-slug>` → sets any free-text string as the model.
- **No validation, no menu, no aliases, no badge.**

### 2.3 Agent profiles ✅
- `AgentProfile` dataclass: `name, command, display_name, prompt, temperature, max_tokens, allowed_tools`.
- 4 built-in agents: `default`, `explanatory`, `math_tutor`, `researcher`.
- Per-user agent switching via `/agent <mode>` and direct `/<agent>` commands.
- **Agent profiles do NOT include a default model** — they all inherit the global `llm.default_model`.

### 2.4 OpenRouter integration ✅
- Single `OpenRouterClient` with `stream_completion(messages, model, ...)`.
- Model slug is passed as a string; OpenRouter resolves it to the actual provider.
- Error handling: `httpx.HTTPError` → `LLMError`; no retry/fallback at the client level.

### 2.5 Existing fallback infrastructure ✅
- `shared/decorators/chain_fallback.py` has `chain_fallbacks()` — a generic decorator that tries a primary async function, then sequentially falls through a list of fallback callables if specified exceptions occur.
- **Currently unused** (not applied to any LLM calls).

### 2.6 Deep research ✅
- `DeepResearchService` calls `llm.complete_side_context(model=model)` — model is threaded explicitly.
- If the model manager changes how models are resolved, deep research inherits automatically.

---

## 3. Feature Decomposition

The proposed feature is actually **6 sub-features** that can be delivered independently:

| # | Sub-feature | Complexity | Depends on |
|---|------------|-----------|------------|
| A | **Predefined model registry** — a catalog of known models with metadata | Low | — |
| B | **Model aliases** (`fast`, `smart`, `research`) — semantic shortcuts | Low | A |
| C | **Per-agent default model** — each `AgentProfile` specifies a preferred model | Low | A |
| D | **Enhanced `/model` command** — interactive menu, validation, list | Medium | A, B |
| E | **Current-model badge** — shows model name in responses or status | Low | — |
| F | **Automatic fallback on failure/rate-limit** — retry with alternative model | Medium-High | A |

---

## 4. Sub-feature Analysis

### 4.A — Predefined Model Registry

**What it does:**  
A central catalog of models the bot owner has pre-approved, each with metadata (display name, provider, context window, cost tier, capabilities).

**Where it lives:**

```
# New file: src/bot/config/models.py
# New model: src/bot/domain/models/model_catalog.py
```

**Proposed domain model:**

```python
@dataclass(frozen=True)
class ModelEntry:
    slug: str                # "anthropic/claude-sonnet-4"
    display_name: str        # "Claude Sonnet 4"
    aliases: list[str]       # ["smart", "default"]
    context_window: int      # 200_000
    cost_tier: str           # "low" | "medium" | "high"
    capabilities: list[str]  # ["tools", "vision", "long-context"]
    fallback_chain: list[str]  # ["anthropic/claude-haiku-3.5", "google/gemini-2.0-flash-001"]
```

**Config integration** (config.yaml):

```yaml
llm:
  default_model: "anthropic/claude-sonnet-4"
  models:
    - slug: "anthropic/claude-sonnet-4"
      display_name: "Claude Sonnet 4"
      aliases: ["smart", "default"]
      cost_tier: "medium"
      fallback_chain: ["google/gemini-2.5-flash-preview-04-17", "openai/gpt-4.1-mini"]
      
    - slug: "google/gemini-2.5-flash-preview-04-17"
      display_name: "Gemini Flash"
      aliases: ["fast"]
      cost_tier: "low"
      fallback_chain: ["openai/gpt-4.1-mini"]

    - slug: "openai/o3"
      display_name: "o3"
      aliases: ["research", "think"]
      cost_tier: "high"
      fallback_chain: ["anthropic/claude-sonnet-4"]
```

**Impact:** Touches `domain/models/config.py` (new Pydantic model for YAML), `config/config.py` (load), and a new `config/models.py` registry. No existing behavior changes — purely additive.

---

### 4.B — Model Aliases

**What it does:**  
Maps human-friendly names (`fast`, `smart`, `research`) to model slugs.

**How it works:**  
The alias table is derived from `ModelEntry.aliases` in the registry (sub-feature A). A simple resolver function:

```python
def resolve_model(name_or_alias: str) -> str:
    """Resolve an alias or slug to a canonical model slug."""
    # First: exact slug match
    if name_or_alias in MODEL_REGISTRY:
        return name_or_alias
    # Second: alias lookup
    if name_or_alias in ALIAS_MAP:
        return ALIAS_MAP[name_or_alias]
    # Third: return as-is (allow raw OpenRouter slugs)
    return name_or_alias
```

**Integration points:**
- `ConversationManager.set_model()` — resolve before storing.
- `cmd_model` handler — resolve user input.
- Per-agent default model field (sub-feature C).

**Decision:** Should unknown slugs be allowed (pass-through to OpenRouter) or rejected?  
→ **Recommendation: allow pass-through** with a warning, because OpenRouter has hundreds of models and the registry is a curated subset.

---

### 4.C — Per-Agent Default Model

**What it does:**  
Each `AgentProfile` can specify a preferred model. When a user switches agents, the conversation's model automatically switches to that agent's default (unless the user has explicitly overridden it).

**Domain change:**

```python
@dataclass(frozen=True)
class AgentProfile:
    name: str
    command: str
    display_name: str
    prompt: str
    temperature: float
    max_tokens: int
    allowed_tools: list[str] = field(default_factory=list)
    default_model: str | None = None  # NEW — None means "use global default"
```

**Behavior logic:**

```
On agent switch:
  if agent.default_model is not None:
      conversation.model = agent.default_model
  # else: keep current model
```

**Concrete mappings (example):**

| Agent | Default Model | Rationale |
|-------|--------------|-----------|
| `default` | None (global) | General purpose |
| `explanatory` | None (global) | Doesn't need a special model |
| `math_tutor` | `"openai/o3"` | Reasoning benefits from thinking models |
| `researcher` | `"anthropic/claude-sonnet-4"` | Good at synthesis + tool use |

**Conversation state nuance:**  
Need a flag `model_explicitly_set: bool` on `Conversation` to distinguish "user chose this model via /model" from "inherited from agent switch". If the user explicitly set a model, agent switching should NOT override it.

```python
@dataclass
class Conversation:
    user_id: int
    messages: list[Message] = field(default_factory=list)
    model: str = ""
    model_explicit: bool = False  # NEW
    active_agent: str = "default"
    last_active: datetime = field(default_factory=...)
```

---

### 4.D — Enhanced `/model` Command

**Current behavior:**
- `/model` → "Current model: `slug`"
- `/model <slug>` → sets model, no validation

**Proposed behavior:**

```
/model                → Shows current model + list of available models
/model fast           → Resolves alias, switches, confirms
/model anthropic/...  → Sets exact slug, confirms
/model list           → Shows all registered models with aliases
```

**Example output for `/model`:**

```
🧠 Current model: `Claude Sonnet 4` (anthropic/claude-sonnet-4)

Available models:
• `fast` → Gemini Flash (google/gemini-2.5-flash-preview-04-17) — 💰 low
• `smart` → Claude Sonnet 4 (anthropic/claude-sonnet-4) — 💰 medium  ← active
• `research` → o3 (openai/o3) — 💰 high

Use `/model <name>` to switch.
```

**Alternative UX: Inline keyboard buttons.**  
Telegram supports `InlineKeyboardMarkup`. Instead of text, `/model` could send a message with buttons like `[⚡ Fast] [🧠 Smart] [🔬 Research]`. This is better UX but adds complexity (callback query handlers).

**Recommendation:** Start with text-based, add inline keyboard as a follow-up enhancement.

**Impact:** Only `handlers/commands.py` — `cmd_model` handler rewrite. Depends on sub-features A and B.

---

### 4.E — Current-Model Badge

**What it does:**  
Shows the active model name in bot responses so the user always knows which model is responding.

**Options:**

1. **Status line in `/agent` and `/model` output** (easiest — partially exists)
2. **Badge in every response** — prepend "🧠 *Claude Sonnet 4*\n\n" to each reply
3. **Badge only on model/agent switch** — confirmation messages show the model
4. **Footer in streaming responses** — append model name after the final message

**Recommendation:** Option 3 (switch confirmations) + Option 1 (status commands). Adding a badge to every response is noisy and wastes tokens.

**Implementation:**
- Modify `_build_agent_switch_text()` to include model info.
- Modify `cmd_model` confirmation to show display name + slug.
- Optionally: add model info to `/status` output (already has `HealthService.model`).

**Impact:** Minimal. A few string formatting changes in `handlers/commands.py`.

---

### 4.F — Automatic Fallback on Failure/Rate-Limit

**What it does:**  
When an LLM call fails (HTTP 429 rate limit, 5xx server error, timeout), automatically retry with the next model in the fallback chain.

**This is the most architecturally significant sub-feature.**

#### Current error flow:

```
OpenRouterClient.stream_completion() 
  → httpx.HTTPError → LLMError 
    → bubbles up to LLMService.stream_response() 
      → bubbles up to handle_message() 
        → user sees "⚠️ LLM error: ..."
```

#### Proposed error flow:

```
OpenRouterClient.stream_completion(model=M1) 
  → HTTP 429 / 5xx / timeout
    → ModelFallbackService detects retriable error
      → retry with M2 (next in fallback chain)
        → if M2 also fails → retry with M3
          → if all fail → raise LLMError as before
```

#### Design options:

**Option 1: Decorator on `stream_completion` (using existing `chain_fallbacks`)**

```python
@chain_fallbacks(
    fallback_functions=[...],
    handled_exceptions=(LLMError,),
)
async def stream_completion(...): ...
```

Problem: `chain_fallbacks` expects the same function signature for all fallbacks, but we need to change the `model` parameter. Also, the fallback chain is per-model, not global.

**Option 2: Fallback logic in `LLMService`**

```python
async def stream_response(self, user_id, user_text):
    model = self._conversations.get_model(user_id)
    fallback_chain = self._model_registry.get_fallback_chain(model)
    
    for attempt_model in [model] + fallback_chain:
        try:
            async for chunk in self._do_stream(user_id, user_text, attempt_model):
                yield chunk
            return
        except RetriableError:
            logger.warning("Model %s failed, trying fallback", attempt_model)
            continue
    
    yield "⚠️ All models failed. Please try again later."
```

Problem: Streaming complicates fallback — if we already yielded partial text from M1 before it failed mid-stream, we can't retry cleanly.

**Option 3: Pre-flight health check + fallback at model selection time**

Instead of retrying after failure, check model availability before each call and pick the best available model. Use a simple circuit-breaker pattern:

```python
class ModelHealthTracker:
    """Tracks recent failures per model to route around broken providers."""
    
    def pick_model(self, preferred: str) -> str:
        if self._is_healthy(preferred):
            return preferred
        for fallback in self._registry.get_fallback_chain(preferred):
            if self._is_healthy(fallback):
                return fallback
        return preferred  # try anyway if all seem down
    
    def record_failure(self, model: str, error: Exception) -> None: ...
    def record_success(self, model: str) -> None: ...
```

**Recommendation: Option 2 (fallback in LLMService) + Option 3 (health tracking).**

- Use Option 3 for preemptive routing (avoid known-broken models).
- Use Option 2 as a safety net for the first failure of a model.
- For streaming: if M1 fails mid-stream after yielding text, DON'T retry (user already sees partial response). Only retry if failure happens before any text is yielded.

#### Error classification:

```python
def is_retriable(error: LLMError) -> bool:
    """Determine if an error warrants model fallback."""
    msg = str(error).lower()
    return any(indicator in msg for indicator in [
        "429",           # Rate limit
        "502", "503",    # Server errors
        "timeout",       # Timeout
        "overloaded",    # Provider overloaded
        "capacity",      # Capacity limit
    ])
```

**Impact:** Touches `infrastructure/openrouter/openrouter.py` (error classification), `services/llm.py` (fallback loop), new `services/model_health.py` (circuit breaker). Medium-high complexity.

---

## 5. Existing Touchpoints & Impact Map

| File | Sub-features | Change type |
|------|-------------|-------------|
| `domain/models/agents.py` | C | Add `default_model` field |
| `domain/models/base.py` | C | Add `model_explicit` field |
| `domain/models/config.py` | A | Add `ModelEntryConfig` pydantic model |
| `config/agents.py` | C | Add model defaults to agent definitions |
| `config/config.py` | A | Load `models` section from YAML |
| `config/constants.py` | — | Minor: add any new constants |
| `config.yaml` | A | Add `models` section |
| `services/conversation.py` | B, C | Resolve aliases in `set_model()`, handle agent→model coupling |
| `services/llm.py` | F | Fallback loop in `stream_response()` + `complete_side_context()` |
| `handlers/commands.py` | D, E | Rewrite `cmd_model`, update switch confirmations |
| `infrastructure/openrouter/openrouter.py` | F | Error classification (retriable vs terminal) |
| **New: `config/models.py`** | A, B | Model registry + alias resolver |
| **New: `services/model_health.py`** | F | Circuit breaker / health tracker |
| **New: `domain/models/model_catalog.py`** | A | `ModelEntry` dataclass |

---

## 6. Risks & Edge Cases

### 6.1 Alias collision
Two models could claim the same alias. → **Enforce uniqueness at load time.** First-defined wins, or raise `ConfigError`.

### 6.2 Stale fallback chains
If a model is removed from OpenRouter, its slug in a fallback chain becomes invalid. → **Log warning on first failure, don't crash.**

### 6.3 Cost escalation
Fallback might silently switch to a more expensive model (e.g., from Gemini Flash to Claude Sonnet). → **Notify user when fallback activates.** Add a message like "⚠️ Switched to Claude Sonnet 4 (Gemini Flash unavailable)."

### 6.4 Infinite fallback loops
Model A falls back to B, B falls back to A. → **Enforce acyclic fallback chains at config load time**, or use a visited-set at runtime.

### 6.5 Mid-stream failure
Streaming yields partial text, then the model fails. → **Don't retry mid-stream.** Surface the error and let the user re-ask.

### 6.6 Session timeout + model state
When a session expires and resets, model goes back to the default. If the user was using an alias, they need to re-set it. → **This is acceptable existing behavior** (same as agent reset on timeout).

### 6.7 Deep research model
`DeepResearchService` takes model from conversation state. If fallback changes the model mid-research cycle, subsequent cycles could use a different model. → **Pass model explicitly at the start of research, not per-cycle.**

---

## 7. Implementation Order (Recommended)

```
Phase 1 — Foundation (no behavior change)
  ├── 4.A  Model registry + config loading
  └── 4.B  Alias resolution

Phase 2 — User-facing improvements
  ├── 4.D  Enhanced /model command
  ├── 4.E  Current-model badge  
  └── 4.C  Per-agent default model

Phase 3 — Resilience
  └── 4.F  Automatic fallback
```

**Rationale:** Phase 1 is purely additive and lays the data foundation. Phase 2 delivers immediate user value with low risk. Phase 3 is the most complex and benefits from having the registry already in place.

---

## 8. Effort Estimates

| Sub-feature | Code | Tests | Total |
|------------|------|-------|-------|
| A. Model registry | ~120 LOC | ~80 LOC | ~200 LOC |
| B. Aliases | ~40 LOC | ~50 LOC | ~90 LOC |
| C. Per-agent model | ~60 LOC | ~70 LOC | ~130 LOC |
| D. Enhanced /model | ~100 LOC | ~120 LOC | ~220 LOC |
| E. Model badge | ~30 LOC | ~40 LOC | ~70 LOC |
| F. Fallback | ~200 LOC | ~180 LOC | ~380 LOC |
| **Total** | **~550 LOC** | **~540 LOC** | **~1090 LOC** |

---

## 9. Validation Criteria

- [ ] `/model` shows available models with aliases and current selection
- [ ] `/model fast` resolves to the correct model slug and confirms
- [ ] Switching to `math_tutor` agent auto-selects its default model
- [ ] Explicitly setting a model via `/model` is preserved across agent switches
- [ ] If primary model returns 429, fallback model is used transparently
- [ ] User is notified when fallback activates
- [ ] Circular fallback chains are detected and rejected at startup
- [ ] All existing tests pass unchanged (backward compatible)

---

## 10. Open Questions

1. **Should the model registry be hot-reloadable?** (e.g., edit config.yaml without restarting the bot) → Probably not for v1.
2. **Should we query OpenRouter's `/models` endpoint** to validate slugs at startup? → Nice-to-have, adds startup latency + network dependency.
3. **Inline keyboard for model selection?** → Defer to v2. Text commands are sufficient and testable.
4. **Per-user model preferences persistence?** Currently model state is session-only (resets on timeout). Should we persist it in SQLite? → Defer, revisit if users complain about losing their model choice.
5. **Cost tracking / budget limits?** → Out of scope for this feature, but the `cost_tier` metadata in the registry makes it possible later.
