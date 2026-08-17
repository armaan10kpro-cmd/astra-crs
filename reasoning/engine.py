"""Construct scoped reasoning context and request candidate patches."""

from __future__ import annotations

from typing import Any

from reasoning.model_provider import ModelProvider, MockProvider, extract_json, get_provider


SYSTEM_PROMPT = """You are ASTRA-CRS repair agent. Return ONLY valid JSON with keys:
root_cause, proposed_change, unified_diff, expected_security_property, expected_behavioural_preservation.
The unified_diff must be a minimal fix. Never claim verification passed."""


def build_context(finding: dict, *, feedback: str = "") -> str:
    parts = [
        "## Vulnerable function",
        finding.get("function", "unknown"),
        "",
        "## Source slice",
        finding.get("source_slice", ""),
        "",
        "## Sanitizer evidence",
        finding.get("sanitizer", ""),
        (finding.get("stack_trace") or "")[:1500],
        "",
        "## Reproducer",
        repr(finding.get("reproducer", "")),
        "",
        "## Regression expectations",
        "- Inputs <=31 chars: return first char of message",
        "- Inputs >=32 chars: must not trigger sanitizer (return error after fix)",
    ]
    if feedback:
        parts.extend(["", "## Prior attempt feedback", feedback])
    return "\n".join(parts)


def propose_patch(
    finding: dict,
    *,
    provider: ModelProvider | None = None,
    feedback: str = "",
    attempt: int = 1,
) -> dict[str, Any]:
    provider = provider or get_provider()
    context = build_context(finding, feedback=feedback)
    prompt = f"Attempt {attempt}. Propose a minimal security patch for this finding.\n\n{context}"

    try:
        raw = provider.complete(prompt, system=SYSTEM_PROMPT)
        proposal = extract_json(raw)
    except Exception as exc:
        if not isinstance(provider, MockProvider):
            fallback = MockProvider()
            raw = fallback.complete(prompt, system=SYSTEM_PROMPT)
            proposal = extract_json(raw)
            proposal["_fallback_from"] = provider.name
            proposal["_fallback_reason"] = str(exc)
        else:
            return {
                "status": "malformed",
                "error": str(exc),
                "provider": provider.name,
                "attempt": attempt,
            }

    return {
        "status": "candidate",
        "provider": provider.name,
        "attempt": attempt,
        "root_cause": proposal["root_cause"],
        "proposed_change": proposal["proposed_change"],
        "unified_diff": proposal["unified_diff"],
        "expected_security_property": proposal["expected_security_property"],
        "expected_behavioural_preservation": proposal["expected_behavioural_preservation"],
        "raw_response": raw[:4000] if isinstance(raw, str) else "",
    }
