#!/bin/bash
set -euo pipefail

# Correctness checks: only the prompt/agent/LLM tests that are relevant
# and were passing before the session started.

cd "$(dirname "$0")"

python3 -m pytest \
  tests/unit/test_llm.py \
  tests/unit/test_agents_registry.py \
  tests/unit/test_models.py \
  tests/unit/test_conversation.py \
  -q --tb=short 2>&1 | tail -40
