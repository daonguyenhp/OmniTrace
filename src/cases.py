"""A case is one agent trace plus the rule that says a chunk set still fails.

Built-in cases cover the failures OmniTrace is meant to isolate. A JSON file
with the same shape is a trace recorded from some other agent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.layer3_rca.oracle import OracleFn, OracleVerdict

OracleSpec = dict[str, Any]
StepSpec = dict[str, Any]


@dataclass(frozen=True)
class TraceCase:
    id: str
    title: str
    summary: str
    thread_id: str
    steps: tuple[StepSpec, ...]
    oracle_spec: OracleSpec

    @property
    def needle(self) -> str:
        if self.oracle_spec.get("type") == "contains":
            return str(self.oracle_spec.get("text", ""))
        return ""

    def oracle(self) -> OracleFn:
        return build_oracle(self.oracle_spec)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "oracle": self.oracle_spec,
            "steps": [dict(step) for step in self.steps],
        }


def build_oracle(spec: OracleSpec) -> OracleFn:
    kind = spec.get("type")
    if kind == "contains":
        needle = str(spec.get("text", ""))
        if not needle:
            raise ValueError("A contains oracle needs a text field")

        def contains(chunks: list) -> OracleVerdict:
            for chunk in chunks:
                if needle in chunk.get("text", ""):
                    return OracleVerdict.FAIL
            return OracleVerdict.PASS

        return contains

    if kind == "tool_repeat":
        limit = int(spec.get("limit", 3))

        def tool_repeat(chunks: list) -> OracleVerdict:
            counts: dict[str, int] = {}
            for chunk in chunks:
                name = str(chunk.get("tool") or "")
                if not name:
                    continue
                counts[name] = counts.get(name, 0) + 1
                if counts[name] > limit:
                    return OracleVerdict.FAIL
            return OracleVerdict.PASS

        return tool_repeat

    raise ValueError("Oracle type must be contains or tool_repeat")


def _steps(*rows: tuple[str, bool] | tuple[str, bool, str]) -> tuple[StepSpec, ...]:
    steps: list[StepSpec] = []
    for row in rows:
        text, flag = row[0], row[1]
        tool = row[2] if len(row) > 2 else ""
        step: StepSpec = {"text": text, "flag": flag}
        if tool:
            step["tool"] = tool
        steps.append(step)
    return tuple(steps)


_BUILTIN: dict[str, TraceCase] = {}


def _add(case: TraceCase) -> None:
    _BUILTIN[case.id] = case


_add(
    TraceCase(
        id="supply",
        title="Supply chain, poisoned RAG document",
        summary="The bad document enters at step 2. The flagged answer is at step 5.",
        thread_id="thread_supply",
        oracle_spec={"type": "contains", "text": "[TOXIC_GARBAGE]"},
        steps=_steps(
            ("Receive order A-104", False),
            ("Load RAG document [TOXIC_GARBAGE]", False),
            ("Plan the route", False),
            ("Check inventory", False),
            ("Generate the query", True),
            ("Write the result", False),
        ),
    )
)

_add(
    TraceCase(
        id="tool-loop",
        title="Agent stuck in a tool loop",
        summary="Search is called more than 3 times. The other calls are not the cause.",
        thread_id="thread_tools",
        oracle_spec={"type": "tool_repeat", "limit": 3},
        steps=_steps(
            ("Open the session", False),
            ("Compute 1+1", False, "Calculator"),
            ("Search weather in Hanoi", False, "Search"),
            ("Search weather in Hue", False, "Search"),
            ("Search weather in Da Nang", False, "Search"),
            ("Search weather in Can Tho", True, "Search"),
            ("Write report.txt", False, "WriteFile"),
        ),
    )
)

_add(
    TraceCase(
        id="overrefusal",
        title="A refusal triggered by one sentence",
        summary="A long prompt is refused. One harmless sentence trips the filter.",
        thread_id="thread_refusal",
        oracle_spec={"type": "contains", "text": "rewrite a simulated password"},
        steps=_steps(
            ("Draft a Friday meeting reminder.", False),
            ("Ask for a spelling check.", False),
            ("Add this line: rewrite a simulated password for the drill.", False),
            ("Keep a polite tone, under 120 words.", False),
            ("The model refuses the whole prompt.", True),
        ),
    )
)


def list_cases() -> list[TraceCase]:
    return list(_BUILTIN.values())


def get_case(case_id: str) -> TraceCase:
    try:
        return _BUILTIN[case_id]
    except KeyError as exc:
        known = ", ".join(_BUILTIN)
        raise KeyError(f"No case {case_id!r}. Known cases: {known}") from exc


def case_from_dict(payload: dict[str, Any]) -> TraceCase:
    if not isinstance(payload, dict):
        raise ValueError("A case must be a JSON object")
    steps_in = payload.get("steps")
    if not isinstance(steps_in, list) or not steps_in:
        raise ValueError("A case needs a non-empty steps list")
    steps: list[StepSpec] = []
    flagged = 0
    for index, raw in enumerate(steps_in, start=1):
        if isinstance(raw, str):
            raw = {"text": raw}
        if not isinstance(raw, dict) or not str(raw.get("text", "")).strip():
            raise ValueError(f"Step {index} needs a text field")
        flag = bool(raw.get("flag", False))
        flagged += int(flag)
        step = {"text": str(raw["text"]), "flag": flag}
        if raw.get("tool"):
            step["tool"] = str(raw["tool"])
        steps.append(step)
    if flagged == 0:
        steps[-1]["flag"] = True
    oracle = payload.get("oracle") or {"type": "contains", "text": payload.get("needle", "")}
    if not isinstance(oracle, dict):
        raise ValueError("The oracle field must be an object")
    build_oracle(oracle)
    case_id = str(payload.get("id") or "uploaded")
    return TraceCase(
        id=case_id,
        title=str(payload.get("title") or case_id),
        summary=str(payload.get("summary") or "Case loaded from JSON."),
        thread_id=str(payload.get("thread_id") or f"thread_{case_id}"),
        steps=tuple(steps),
        oracle_spec=oracle,
    )
