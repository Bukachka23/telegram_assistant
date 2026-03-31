#!/usr/bin/env python3
"""
Prompt quality scoring script for autoresearch.

Measures quality across three dimensions:
  - Coverage (50 pts): Do all required behaviors appear in the prompt?
  - Conciseness (30 pts): Is the prompt as short as possible while covering everything?
  - Structure (20 pts): Is it well-organized for an LLM system prompt?

Anti-gaming design:
  - Coverage uses multi-pattern checks (not single keyword)
  - Conciseness is a smooth curve (no cliff to game)
  - Structure checks semantics, not just formatting
"""

import re
import sys
import importlib.util
from pathlib import Path

PROMPT_PATH = Path(__file__).parent.parent / "src" / "bot" / "shared" / "prompt" / "system_prompt.py"


def load_prompt() -> str:
    spec = importlib.util.spec_from_file_location("system_prompt", PROMPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SYSTEM_PROMPT


# ──────────────────────────────────────────────
# COVERAGE CHECKS (50 pts, 5 pts each)
# Each check requires at least 2 of N patterns to pass (prevents gaming via
# single keyword injection).
# ──────────────────────────────────────────────
COVERAGE_CRITERIA = [
    {
        "name": "role_definition",
        "desc": "Defines the assistant role and context clearly",
        "patterns": [
            r"personal assistant",
            r"telegram",
            r"second brain|knowledge manager|research aide",
            r"notes|vault|channels",
        ],
        "threshold": 3,  # need 3 of 4
    },
    {
        "name": "language_mirroring",
        "desc": "Instructs to mirror user language (Ukrainian/English)",
        "patterns": [
            r"ukrainian",
            r"english",
            r"mirror|language",
            r"mixed",
        ],
        "threshold": 3,
    },
    {
        "name": "anti_filler",
        "desc": "Discourages filler phrases in responses",
        "patterns": [
            r"sure!|great question|of course|certainly",
            r"filler|no filler|direct",
            r"don.t start|avoid|without",
        ],
        "threshold": 2,
    },
    {
        "name": "mobile_context",
        "desc": "Acknowledges Telegram mobile context",
        "patterns": [
            r"telegram",
            r"phone|mobile|scannable",
            r"short|concise|brief",
            r"paragraph",
        ],
        "threshold": 3,
    },
    {
        "name": "context_tracking",
        "desc": "Handles conversation references and context",
        "patterns": [
            r"context|reference|refers",
            r"earlier|previous|recent",
            r"resolve|connect|track",
        ],
        "threshold": 2,
    },
    {
        "name": "tool_decision_logic",
        "desc": "Explains when to use each tool category",
        "patterns": [
            r"general knowledge|casual conversation",
            r"→|->|use .* tools?|call .* tool",
            r"when to use|decision|logic",
            r"no tools|answer directly",
        ],
        "threshold": 3,
    },
    {
        "name": "web_search_guidance",
        "desc": "Covers web search query writing and result handling",
        "patterns": [
            r"web_search|search",
            r"quer|keyword",
            r"current|real.time|live",
            r"result|summar|finding",
        ],
        "threshold": 3,
    },
    {
        "name": "memory_guidance",
        "desc": "Explains when to save and recall memory",
        "patterns": [
            r"save_memory|recall_memory",
            r"remember|preference|decision",
            r"across conversations|between sessions|long.term",
        ],
        "threshold": 2,
    },
    {
        "name": "action_bias",
        "desc": "Biases toward action over clarification",
        "patterns": [
            r"bias toward action|act on|action over",
            r"best guess|most likely|interpret",
            r"don.t block|note your assumption|clarif",
        ],
        "threshold": 2,
    },
    {
        "name": "tool_discipline",
        "desc": "Instructs not to fabricate tool results",
        "patterns": [
            r"never fabricat|don.t fabricat|not fabricat",
            r"attribute|source|where it came from",
            r"tool result|search result|note content",
        ],
        "threshold": 2,
    },
]


def score_coverage(prompt: str) -> tuple[float, dict]:
    prompt_lower = prompt.lower()
    scores = {}
    total = 0.0
    for criterion in COVERAGE_CRITERIA:
        matched = sum(
            1 for p in criterion["patterns"]
            if re.search(p, prompt_lower)
        )
        passed = matched >= criterion["threshold"]
        pts = 5.0 if passed else (5.0 * matched / criterion["threshold"])
        scores[criterion["name"]] = {
            "passed": passed,
            "matched": matched,
            "threshold": criterion["threshold"],
            "pts": pts,
        }
        total += pts
    return total, scores


# ──────────────────────────────────────────────
# CONCISENESS SCORE (30 pts)
# Smooth curve: 400 words → 30pts, 700 words → ~21pts, 1200+ words → 0pts
# Current baseline is ~1032 words.
# ──────────────────────────────────────────────
CONCISENESS_BASELINE = 1032  # current word count
CONCISENESS_OPTIMAL = 400    # target word count
CONCISENESS_ZERO = 1400      # word count that scores 0

def score_conciseness(prompt: str) -> float:
    word_count = len(prompt.split())
    if word_count <= CONCISENESS_OPTIMAL:
        return 30.0
    if word_count >= CONCISENESS_ZERO:
        return 0.0
    return 30.0 * (CONCISENESS_ZERO - word_count) / (CONCISENESS_ZERO - CONCISENESS_OPTIMAL)


# ──────────────────────────────────────────────
# STRUCTURE SCORE (20 pts)
# ──────────────────────────────────────────────

def score_structure(prompt: str) -> tuple[float, dict]:
    details = {}
    pts = 0.0

    # 1. Role intro (first 3 lines define the assistant's role) — 5pts
    first_para = "\n".join(prompt.splitlines()[:4]).lower()
    has_role_intro = any(w in first_para for w in ["assistant", "your job", "personal", "you are"])
    details["role_intro"] = has_role_intro
    pts += 5.0 if has_role_intro else 0.0

    # 2. Has organized sections — 5pts
    section_count = len(re.findall(r'^##\s', prompt, re.MULTILINE))
    has_sections = 3 <= section_count <= 9
    details["sections"] = section_count
    pts += 5.0 if has_sections else max(0, 5.0 - abs(section_count - 5) * 1.5)

    # 3. Sections appear in logical order (role → style → tools) — 5pts
    tool_pos = prompt.lower().find("## tool")
    style_pos = prompt.lower().find("## communication") or prompt.lower().find("## style")
    has_logical_order = (0 < style_pos < tool_pos) if tool_pos > 0 and style_pos and style_pos > 0 else False
    details["logical_order"] = has_logical_order
    pts += 5.0 if has_logical_order else 0.0

    # 4. No orphaned run-on sections (no section > 200 words) — 5pts
    sections_content = re.split(r'^##\s', prompt, flags=re.MULTILINE)
    max_section_words = max((len(s.split()) for s in sections_content), default=0)
    no_bloated_sections = max_section_words < 200
    details["max_section_words"] = max_section_words
    pts += 5.0 if no_bloated_sections else max(0, 5.0 * (300 - max_section_words) / 100)

    return pts, details


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    try:
        prompt = load_prompt()
    except Exception as e:
        print(f"ERROR loading prompt: {e}", file=sys.stderr)
        sys.exit(1)

    word_count = len(prompt.split())
    char_count = len(prompt)
    token_estimate = char_count // 4

    coverage_score, coverage_details = score_coverage(prompt)
    conciseness_score = score_conciseness(prompt)
    structure_score, structure_details = score_structure(prompt)

    quality_score = coverage_score + conciseness_score + structure_score

    # Debug output
    print("=== Prompt Quality Report ===")
    print(f"Word count:    {word_count}")
    print(f"Char count:    {char_count}")
    print(f"Token est.:    {token_estimate}")
    print()
    print(f"Coverage  ({coverage_score:.1f}/50):")
    for name, info in coverage_details.items():
        status = "✓" if info["passed"] else f"~{info['matched']}/{info['threshold']}"
        print(f"  {status:6s} {name}: {info['pts']:.1f}pts")
    print()
    print(f"Conciseness ({conciseness_score:.1f}/30): {word_count} words")
    print()
    print(f"Structure ({structure_score:.1f}/20):")
    print(f"  role_intro:      {'✓' if structure_details['role_intro'] else '✗'}")
    print(f"  sections:        {structure_details['sections']} (optimal 3-9)")
    print(f"  logical_order:   {'✓' if structure_details['logical_order'] else '✗'}")
    print(f"  max_sec_words:   {structure_details['max_section_words']}")
    print()
    print(f"QUALITY SCORE: {quality_score:.1f}/100")

    # Structured METRIC output for autoresearch
    print(f"METRIC quality_score={quality_score:.2f}")
    print(f"METRIC word_count={word_count}")
    print(f"METRIC token_estimate={token_estimate}")
    print(f"METRIC coverage_score={coverage_score:.2f}")
    print(f"METRIC conciseness_score={conciseness_score:.2f}")
    print(f"METRIC structure_score={structure_score:.2f}")


if __name__ == "__main__":
    main()
