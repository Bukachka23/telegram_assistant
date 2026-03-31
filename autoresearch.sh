#!/bin/bash
set -euo pipefail

# Autoresearch benchmark: system_prompt.py quality scoring
# Outputs METRIC lines parsed by run_experiment.

cd "$(dirname "$0")"

# Fast syntax check
python3 -c "from src.bot.shared.prompt.system_prompt import SYSTEM_PROMPT; assert isinstance(SYSTEM_PROMPT, str) and len(SYSTEM_PROMPT) > 100" \
  || { echo "ERROR: SYSTEM_PROMPT missing or too short"; exit 1; }

# Run scoring (run 3 times to confirm stability — scores are deterministic so median = same)
python3 scripts/score_prompt.py
