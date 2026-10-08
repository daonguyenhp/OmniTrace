"""OpenTelemetry GenAI trace as the shared input file.

A file is one failed agent run: resourceSpans → spans. Each chat or
execute_tool span is one step. STATUS_CODE_ERROR is the symptom. The
failure rule sits on the resource as omnitrace.oracle.type plus
omnitrace.oracle.text or omnitrace.oracle.limit. When those attributes
are missing, the exception message is used if it appears in a span.
"""

from __future__ import annotations

from typing import Any

from src.cases import TraceCase, build_oracle, case_from_dict

_CONTENT_OPS = {"chat", "execute_tool", "text_completion"}


def load_case(payload: dict[str, Any]) -> TraceCase:
    if isinstance(payload, dict) and payload.get("resourceSpans"):
        return case_from_otlp(payload)
    return case_from_dict(payload)


def export_otlp(case: TraceCase) -> dict[str, Any]:
    spans = []
    base = 1_700_000_000_000_000_000
    for index, step in enumerate(case.steps, start=1):
        operation = "execute_tool" if step.get("tool") else "chat"
        attributes = [
            _kv("gen_ai.operation.name", operation),
            _kv("gen_ai.system", "omnitrace"),
            _kv("omnitrace.super_step", index),
            _kv("omnitrace.thread_id", case.thread_id),
        ]
        if step.get("tool"):
            attributes.append(_kv("gen_ai.tool.name", step["tool"]))
        events = [
            {
                "name": "gen_ai.user.message",
                "timeUnixNano": str(base + index * 1_000_000),
                "attributes": [_kv("content", step["text"])],
            }
        ]
        status: dict[str, str] = {"code": "STATUS_CODE_OK"}
        if step.get("flag"):
            status = {"code": "STATUS_CODE_ERROR", "message": "symptom"}
            events.append(
                {
                    "name": "exception",
                    "timeUnixNano": str(base + index * 1_000_000 + 1),
                    "attributes": [_kv("exception.message", case.needle or "FAIL")],
                }
            )
        spans.append(
            {
                "traceId": "ab" * 16,
                "spanId": f"{index:016x}",
                "name": operation,
                "kind": "SPAN_KIND_INTERNAL",
                "startTimeUnixNano": str(base + index * 1_000_000),
                "endTimeUnixNano": str(base + index * 1_000_000 + 500_000),
                "attributes": attributes,
                "events": events,
                "status": status,
            }
        )
    resource = [
        _kv("service.name", case.title),
        _kv("omnitrace.case_id", case.id),
        _kv("omnitrace.summary", case.summary),
        _kv("omnitrace.thread_id", case.thread_id),
        _kv("omnitrace.oracle.type", case.oracle_spec.get("type", "")),
    ]
    if case.oracle_spec.get("type") == "contains":
        resource.append(_kv("omnitrace.oracle.text", case.oracle_spec.get("text", "")))
    elif case.oracle_spec.get("type") == "tool_repeat":
        resource.append(_kv("omnitrace.oracle.limit", int(case.oracle_spec.get("limit", 3))))
    return {
        "resourceSpans": [
            {
                "resource": {"attributes": resource},
                "scopeSpans": [{"scope": {"name": "omnitrace"}, "spans": spans}],
            }
        ]
    }


def case_from_otlp(payload: dict[str, Any]) -> TraceCase:
    if not isinstance(payload, dict):
        raise ValueError("A trace must be a JSON object")
    raw_spans = list(_iter_spans(payload))
    if not raw_spans:
        raise ValueError("The trace has no spans")
    parsed = [_parse_span(span, index) for index, span in enumerate(raw_spans)]
    parsed.sort(key=lambda item: (item["order"], item["index"]))
    if any(item["operation"] in _CONTENT_OPS for item in parsed):
        parsed = [item for item in parsed if item["operation"] in _CONTENT_OPS]
    steps = []
    for item in parsed:
        if not item["text"]:
            continue
        step: dict[str, Any] = {"text": item["text"], "flag": False}
        if item["tool"]:
            step["tool"] = item["tool"]
        steps.append(step)
    if not steps:
        raise ValueError("The trace has no chat or tool content")
    symptom_at = [item["text"] for item in parsed if item["symptom"] and item["text"]]
    if symptom_at:
        last_symptom = symptom_at[-1]
        for step in steps:
            step["flag"] = False
        for step in reversed(steps):
            if step["text"] == last_symptom:
                step["flag"] = True
                break
    else:
        steps[-1]["flag"] = True
    resource = _resource_attributes(payload)
    oracle = _oracle(resource, steps, _exception_message(parsed))
    build_oracle(oracle)
    case_id = str(resource.get("omnitrace.case_id") or "trace")
    title = str(resource.get("service.name") or case_id)
    summary = str(resource.get("omnitrace.summary") or "Run loaded from an OpenTelemetry trace file.")
    thread_id = str(resource.get("omnitrace.thread_id") or f"thread_{case_id}")
    return TraceCase(
        id=case_id,
        title=title,
        summary=summary,
        thread_id=thread_id,
        steps=tuple(steps),
        oracle_spec=oracle,
    )


def _iter_spans(payload: dict[str, Any]):
    for resource_span in payload.get("resourceSpans") or []:
        for scope_span in resource_span.get("scopeSpans") or resource_span.get("instrumentationLibrarySpans") or []:
            for span in scope_span.get("spans") or []:
                yield span


def _resource_attributes(payload: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for resource_span in payload.get("resourceSpans") or []:
        resource = resource_span.get("resource") or {}
        merged.update(_attributes(resource.get("attributes")))
    return merged


def _parse_span(span: dict[str, Any], index: int) -> dict[str, Any]:
    attributes = _attributes(span.get("attributes"))
    operation = str(attributes.get("gen_ai.operation.name") or span.get("name") or "")
    texts = []
    exception = ""
    for event in span.get("events") or []:
        event_attributes = _attributes(event.get("attributes"))
        name = str(event.get("name") or "")
        if name == "exception":
            exception = str(event_attributes.get("exception.message") or event_attributes.get("message") or "")
            continue
        content = _event_content(event_attributes)
        if content:
            texts.append(content)
    if not texts:
        for key in ("gen_ai.prompt", "gen_ai.input.messages", "gen_ai.completion"):
            if attributes.get(key):
                texts.append(str(attributes[key]))
                break
    tool = str(attributes.get("gen_ai.tool.name") or "")
    status = span.get("status") or {}
    code = status.get("code") if isinstance(status, dict) else status
    symptom = str(code) in {"ERROR", "STATUS_CODE_ERROR", "2"} or attributes.get("omnitrace.is_semantic") is True
    order = _order(span, attributes, index)
    return {
        "index": index,
        "order": order,
        "operation": operation,
        "text": texts[0] if texts else "",
        "tool": tool,
        "symptom": symptom,
        "exception": exception,
    }


def _event_content(attributes: dict[str, Any]) -> str:
    for key in ("content", "gen_ai.prompt", "message"):
        if attributes.get(key):
            return str(attributes[key])
    return ""


def _exception_message(parsed: list[dict[str, Any]]) -> str:
    for item in reversed(parsed):
        if item["exception"]:
            return item["exception"]
    return ""


def _order(span: dict[str, Any], attributes: dict[str, Any], index: int) -> int:
    raw = span.get("startTimeUnixNano")
    if raw not in (None, ""):
        return int(raw)
    step = attributes.get("omnitrace.super_step")
    if step not in (None, ""):
        return int(step)
    return index


def _oracle(resource: dict[str, Any], steps: list[dict[str, Any]], exception: str) -> dict[str, Any]:
    kind = resource.get("omnitrace.oracle.type")
    if kind == "contains":
        text = str(resource.get("omnitrace.oracle.text") or "")
        if not text:
            raise ValueError("The trace sets omnitrace.oracle.type=contains but omnitrace.oracle.text is missing")
        return {"type": "contains", "text": text}
    if kind == "tool_repeat":
        return {"type": "tool_repeat", "limit": int(resource.get("omnitrace.oracle.limit") or 3)}
    if exception and any(exception in step["text"] for step in steps):
        return {"type": "contains", "text": exception}
    counts: dict[str, int] = {}
    for step in steps:
        name = str(step.get("tool") or "")
        if not name:
            continue
        counts[name] = counts.get(name, 0) + 1
    if counts and max(counts.values()) > 3:
        return {"type": "tool_repeat", "limit": 3}
    if exception:
        return {"type": "contains", "text": exception}
    raise ValueError(
        "The trace has no failure rule. Set omnitrace.oracle.type=contains and omnitrace.oracle.text on the resource."
    )


def _attributes(items: Any) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for item in items or []:
        if isinstance(item, dict) and item.get("key"):
            found[str(item["key"])] = _value(item.get("value"))
    return found


def _value(node: Any) -> Any:
    if not isinstance(node, dict):
        return node
    for key in ("stringValue", "boolValue", "intValue", "doubleValue"):
        if key in node:
            raw = node[key]
            if key == "intValue":
                return int(raw)
            if key == "boolValue":
                return bool(raw)
            return raw
    return None


def _kv(key: str, value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        encoded: dict[str, Any] = {"boolValue": value}
    elif isinstance(value, int):
        encoded = {"intValue": str(value)}
    else:
        encoded = {"stringValue": str(value)}
    return {"key": key, "value": encoded}
