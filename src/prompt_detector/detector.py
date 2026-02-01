from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import os
import re

from .rules import Rule, get_rules

try:
    from guardrails import Guard
    try:
        from guardrails.hub import DetectJailbreak
    except Exception:  # pragma: no cover - compatibility fallback
        from guardrails.hub import JailbreakDetection as DetectJailbreak
except Exception:  # pragma: no cover - guardrails optional
    Guard = None
    DetectJailbreak = None

USE_GUARDRAILS = os.getenv("PROMPTDETECTOR_USE_GUARDRAILS", "0") == "1"


@dataclass
class RuleMatch:
    rule_id: str
    name: str
    description: str
    weight: int
    tags: List[str]
    pattern: str
    snippet: str


def _extract_snippet(text: str, match: re.Match, radius: int = 32) -> str:
    start = max(match.start() - radius, 0)
    end = min(match.end() + radius, len(text))
    return text[start:end].strip()


def _score_to_action(score: int) -> str:
    if score >= 70:
        return "拒绝"
    if score >= 40:
        return "二次确认"
    return "允许"


def _guardrails_jailbreak_score(text: str) -> Tuple[float, Dict[str, Any]]:
    if Guard is None or DetectJailbreak is None:
        return 0.0, {"enabled": False, "reason": "guardrails-ai not available"}

    try:
        guard = Guard().use(DetectJailbreak, on_fail="noop")
        result = guard.validate(text)
        passed = getattr(result, "validation_passed", None)

        if passed is True:
            return 0.0, {"enabled": True, "passed": True}
        if passed is False:
            return 0.6, {"enabled": True, "passed": False}

        return 0.4, {"enabled": True, "passed": None}
    except Exception as exc:  # pragma: no cover - runtime guard
        return 0.0, {"enabled": True, "error": str(exc)}


def analyze(text: str) -> Dict[str, Any]:
    cleaned = (text or "").strip()
    if not cleaned:
        return {
            "risk_score": 0,
            "action": "允许",
            "matched_rules": [],
            "summary": "空输入，无风险信号。",
        }

    rules: List[Rule] = get_rules()
    matches: List[RuleMatch] = []
    score = 0

    for rule in rules:
        for pattern in rule.patterns:
            match = re.search(pattern, cleaned, flags=re.IGNORECASE | re.DOTALL)
            if match:
                matches.append(
                    RuleMatch(
                        rule_id=rule.id,
                        name=rule.name,
                        description=rule.description,
                        weight=rule.weight,
                        tags=rule.tags,
                        pattern=pattern,
                        snippet=_extract_snippet(cleaned, match),
                    )
                )
                score += rule.weight
                break

    unique_tags = {tag for match in matches for tag in match.tags}
    if unique_tags:
        score += max(0, (len(unique_tags) - 1) * 3)

    score = min(100, score)

    guardrails_score = 0.0
    guardrails_detail: Dict[str, Any] = {"enabled": False}
    if USE_GUARDRAILS:
        guardrails_score, guardrails_detail = _guardrails_jailbreak_score(cleaned)

    if USE_GUARDRAILS:
        blended_score = int(min(100, score * 0.5 + guardrails_score * 100 * 0.5))
        fused_score = max(score, blended_score)
    else:
        fused_score = score

    action = _score_to_action(fused_score)

    if matches:
        summary = f"命中 {len(matches)} 条规则，风险分数 {fused_score}/100。"
    else:
        summary = f"未命中规则，风险分数 {fused_score}/100。"

    return {
        "risk_score": fused_score,
        "action": action,
        "matched_rules": [match.__dict__ for match in matches],
        "guardrails": guardrails_detail,
        "summary": summary,
    }
