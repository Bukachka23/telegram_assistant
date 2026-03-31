# Autoresearch: Best System Prompt

## Objective
Optimize `src/bot/shared/prompt/system_prompt.py` — the default assistant prompt
for a personal Telegram bot with Obsidian vault integration, channel monitoring,
web search, and long-term memory.

The goal is the **best quality prompt**: one that maximally covers all required
agent behaviors while being as concise as possible (fewer tokens = cheaper API calls,
more conversation context window).

## Metrics
- **Primary**: `quality_score` (0–100, **higher is better**) — weighted composite:
  - Coverage (50 pts): all required behaviors present
  - Conciseness (30 pts): word count optimized toward ~400 words
  - Structure (20 pts): well-organized sections
- **Secondary**: `word_count`, `token_estimate`, `coverage_score`, `conciseness_score`, `structure_score`

## How to Run
```bash
./autoresearch.sh
```
Outputs `METRIC name=value` lines.

## Files in Scope
- `src/bot/shared/prompt/system_prompt.py` — **the only file to modify**

## Off Limits
- `scripts/score_prompt.py` — the benchmark, do NOT modify
- `autoresearch.checks.sh` — test runner, do NOT modify
- All other source files

## Constraints
- `SYSTEM_PROMPT` must remain a valid Python string variable
- All tests in `autoresearch.checks.sh` must keep passing
- The prompt must remain a genuine, usable Telegram assistant system prompt
- Do NOT add fake keywords just to game coverage checks
- Do NOT remove real content just to lower word count if it drops coverage

## Coverage Criteria (what the prompt MUST teach the LLM)
The scoring checks 10 behaviors (5pts each). To pass a check, multiple patterns must match:

1. **role_definition** — "personal assistant", "telegram", "second brain/knowledge manager", "notes/vault/channels"
2. **language_mirroring** — Ukrainian + English + mirror/language + mixed
3. **anti_filler** — discourages "Sure!", "Great question!", "Of course!", etc.
4. **mobile_context** — phone/mobile, short/concise, paragraph
5. **context_tracking** — resolves conversation references, earlier/previous context
6. **tool_decision_logic** — explains when to use vs. not use tools, decision tree
7. **web_search_guidance** — query writing, current/real-time data, result handling
8. **memory_guidance** — save_memory/recall_memory, when to save/recall
9. **action_bias** — bias toward action over asking for clarification
10. **tool_discipline** — never fabricate tool results, attribute sources

## What's Been Tried
### Baseline
- Words: 1032, Tokens: ~1571
- quality_score: TBD (run first)

## Optimization Strategy
1. Remove redundant examples and repetitive explanations
2. Consolidate overlapping tool guidance sections
3. Tighten the communication style section
4. Use more direct, imperative phrasing (fewer words per instruction)
5. Ensure all 10 coverage criteria still match after edits
