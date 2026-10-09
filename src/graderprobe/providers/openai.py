"""Optional OpenAI Responses API provider for semantic probe proposals.

The deterministic engine remains the source of truth. This provider is a
bounded proposal generator used only when explicitly enabled by the user.
It uses the Responses API with Structured Outputs so proposals are parsed
without regex scraping.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from graderprobe.providers.base import Proposal
from graderprobe.types import TransformSpec

_ALLOWED_KINDS = {
    "replace_literal",
    "delete_matching",
    "ast_flip_comparison",
    "ast_replace_constant",
}

_PROPOSAL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "proposals": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "description": {"type": "string"},
                    "kind": {"type": "string", "enum": sorted(_ALLOWED_KINDS)},
                    "params": {"type": "object", "additionalProperties": True},
                    "rationale": {"type": "string"},
                },
                "required": ["description", "kind", "params", "rationale"],
            },
        }
    },
    "required": ["proposals"],
}


_REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "change_type": {"type": "string", "enum": ["evaluator", "task_contract", "reference", "environment", "probe_definition", "workflow", "other"]},
        "recommended_checks": {
            "type": "array",
            "maxItems": 4,
            "items": {"type": "string", "enum": ["baseline", "invariance", "sensitivity", "determinism"]},
        },
        "rationale": {"type": "string"},
    },
    "required": ["risk", "change_type", "recommended_checks", "rationale"],
}


class OpenAIProvider:
    name = "openai-responses"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        max_output_tokens: int = 1200,
        timeout_seconds: float = 45.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("GRADERPROBE_OPENAI_MODEL", "").strip()
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.max_output_tokens = max(128, int(max_output_tokens))
        self.timeout_seconds = max(5.0, float(timeout_seconds))
        self.last_usage: dict[str, int] = {}
        self.last_request_id: str | None = None
        self.usage_events: list[dict[str, Any]] = []
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for the optional OpenAI provider")
        if not self.model:
            raise ValueError("GRADERPROBE_OPENAI_MODEL or an explicit model is required for semantic review")

    def review_release_change(self, *, task_id: str, diff_summary: str, head_report: dict[str, Any]) -> dict[str, Any]:
        prompt = {
            "task_id": task_id,
            "diff_summary": diff_summary[:16000],
            "head_report": {
                "verdict": head_report.get("verdict"),
                "metrics": head_report.get("metrics"),
                "findings": head_report.get("findings", [])[:8],
            },
            "goal": "Classify the maintainer risk of this evaluation change and recommend only the smallest additional checks. Do not decide correctness of the benchmark; deterministic local evidence remains authoritative.",
        }
        payload = {
            "model": self.model,
            "instructions": "Review a benchmark/evaluator change for release risk. Be conservative, concise, and evidence-oriented. Return only the requested schema.",
            "input": json.dumps(prompt, ensure_ascii=False),
            "max_output_tokens": self.max_output_tokens,
            "text": {"format": {"type": "json_schema", "name": "release_change_review", "strict": True, "schema": _REVIEW_SCHEMA}},
        }
        request = urllib.request.Request(
            self.base_url + "/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                body = json.loads(raw)
                self.last_request_id = getattr(getattr(response, "headers", None), "get", lambda _key: None)("x-request-id")
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAI semantic release review failed: {exc}") from exc
        self._record_usage(operation="release_review", body=body)
        text = _extract_output_text(body)
        data = json.loads(text)
        if not isinstance(data, dict):
            raise RuntimeError("OpenAI release review must return an object")
        return data

    def propose_probes(self, task, source: str) -> list[Proposal]:
        prompt = {
            "task": {
                "id": task.id,
                "description": task.description,
                "requirements": task.requirements,
                "constraints": task.constraints,
                "failure_conditions": task.failure_conditions,
                "implementation_freedom": task.implementation_freedom,
            },
            "source": source[:12000],
            "allowed_transform_kinds": sorted(_ALLOWED_KINDS),
            "goal": "Propose up to 3 small sensitivity counterfactuals that should invalidate the stated behavior. Do not claim semantic certainty.",
        }
        payload = {
            "model": self.model,
            "instructions": (
                "You propose adversarial, small, executable sensitivity probes for an evaluator. "
                "Use only the allowed transform kinds. Keep params minimal and grounded in the provided source."
            ),
            "input": json.dumps(prompt, ensure_ascii=False),
            "max_output_tokens": self.max_output_tokens,
            "text": {"format": {"type": "json_schema", "name": "probe_proposals", "strict": True, "schema": _PROPOSAL_SCHEMA}},
        }
        request = urllib.request.Request(
            self.base_url + "/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
                self.last_request_id = getattr(getattr(response, "headers", None), "get", lambda _key: None)("x-request-id")
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAI semantic probe request failed: {exc}") from exc

        self._record_usage(operation="probe_proposal", body=body)
        try:
            text = _extract_output_text(body)
            data = json.loads(text)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAI provider returned invalid structured output: {exc}") from exc
        out: list[Proposal] = []
        for item in data.get("proposals", []):
            kind = str(item.get("kind", ""))
            if kind not in _ALLOWED_KINDS:
                continue
            params = item.get("params") or {}
            if not isinstance(params, dict):
                continue
            out.append(
                Proposal(
                    description=str(item.get("description", "model-generated probe")),
                    transform=TransformSpec(kind=kind, params=params),
                    rationale=str(item.get("rationale", "")),
                )
            )
        return out


    def _record_usage(self, *, operation: str, body: dict[str, Any]) -> None:
        usage = body.get("usage") or {}
        self.last_usage = {
            k: int(v) for k, v in usage.items()
            if k in {"input_tokens", "output_tokens", "total_tokens"} and isinstance(v, (int, float))
        }
        self.usage_events.append({
            "operation": operation,
            "request_id": self.last_request_id,
            "usage": dict(self.last_usage),
        })

    @property
    def usage_summary(self) -> dict[str, int]:
        totals = {"calls": len(self.usage_events), "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        for event in self.usage_events:
            for key in ("input_tokens", "output_tokens", "total_tokens"):
                totals[key] += int((event.get("usage") or {}).get(key, 0))
        return totals


def _extract_output_text(body: dict[str, Any]) -> str:
    direct = body.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("OpenAI response did not contain structured output text")
