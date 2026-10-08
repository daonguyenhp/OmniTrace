import json
import threading
import urllib.error
import urllib.request

from src.session import MARKER, OmniTraceSession


def test_acceptance_isolates_step_two_and_forks_without_replay():
    """8.1: rác ở bước 2, cờ ở bước 5, isolate đúng đoạn, fork không chạy lại từ đầu."""
    session = OmniTraceSession()
    session.run()

    history = session.store.history(session.thread_id)
    assert len(history) == 6

    flagged = [
        span
        for span in session.spans
        if span.attributes.get("omnitrace.is_semantic") is True
    ]
    assert len(flagged) == 1
    assert flagged[0].attributes["omnitrace.super_step"] == 5

    isolation = session.isolate()
    assert isolation["fragment"].count(MARKER) == 1
    assert "Receive order" not in isolation["fragment"]
    assert isolation["fault_super_step"] == 2
    assert isolation["symptom_super_step"] == 5
    assert isolation["original_index"] == 1

    old_ids = [snap.checkpoint_id for snap in history]
    forked = session.fork()

    assert [snap.checkpoint_id for snap in session.store.history(session.thread_id)] == old_ids
    assert MARKER in session.store.history(session.thread_id)[1].state["messages"][1]["text"]

    new_history = session.store.history(forked["new_thread_id"])
    assert len(new_history) == 1
    assert new_history[0].parent_checkpoint_id == isolation["fault_checkpoint_id"]
    assert new_history[0].super_step == 3
    assert all(MARKER not in message["text"] for message in new_history[0].state["messages"])
    assert forked["old_step_count"] == 6


def test_tool_loop_and_uploaded_case_use_the_same_loop():
    from src.cases import get_case

    loop = OmniTraceSession()
    loop.run(get_case("tool-loop"))
    isolation = loop.isolate()
    assert isolation["fragments"] == [
        "Search weather in Hanoi",
        "Search weather in Hue",
        "Search weather in Da Nang",
        "Search weather in Can Tho",
    ]
    assert isolation["fault_super_step"] == 3
    forked = loop.fork()
    assert all(message.get("tool") != "Search" for message in forked["messages"])

    refusal = OmniTraceSession()
    refusal.run(get_case("overrefusal"))
    found = refusal.isolate()
    assert found["fragments"] == ["Add this line: rewrite a simulated password for the drill."]
    assert "Draft a Friday" not in found["fragment"]

    uploaded = OmniTraceSession()
    uploaded.load(
        {
            "id": "custom",
            "title": "Ca tự nạp",
            "oracle": {"type": "contains", "text": "ERROR"},
            "steps": [
                {"text": "khởi tạo"},
                {"text": "log có ERROR"},
                {"text": "agent trả lời sai", "flag": True},
            ],
        }
    )
    custom = uploaded.isolate()
    assert custom["fragments"] == ["log có ERROR"]
    assert custom["fault_super_step"] == 2
    assert "ERROR" not in json.dumps(uploaded.fork()["messages"], ensure_ascii=False)


def test_console_switches_case():
    from src.web import make_server

    server = make_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    try:
        catalog = json.loads(urllib.request.urlopen(base + "/api/cases", timeout=5).read().decode("utf-8"))
        assert {item["id"] for item in catalog["cases"]} >= {"supply", "tool-loop", "overrefusal"}
        ran = _post_json(base + "/api/run", {"case_id": "overrefusal"})
        assert ran["case"]["id"] == "overrefusal"
        isolated = _post_json(base + "/api/isolate", {})
        assert isolated["isolation"]["fragments"] == [
            "Add this line: rewrite a simulated password for the drill."
        ]
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def test_cli_isolate_prints_only_the_fragment(capsys):
    from src.cli import cmd_isolate

    cmd_isolate()
    lines = [line for line in capsys.readouterr().out.splitlines() if line]
    assert len(lines) == 2
    assert MARKER in lines[0]
    assert lines[1].startswith("chk_")
    assert "Receive order" not in lines[0]


def test_console_run_isolate_fork():
    from src.web import make_server

    server = make_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    try:
        page = urllib.request.urlopen(base + "/", timeout=5).read().decode("utf-8")
        assert "OmniTrace" in page
        assert "Isolate" in page
        assert "Close" in page
        assert "examples/guide.mp4" in page
        try:
            urllib.request.urlopen(base + "/guide.mp4", timeout=5)
        except urllib.error.HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("a missing tutorial video should answer 404")

        ran = _post(base + "/api/run")
        assert len(ran["steps"]) == 6
        assert sum(step["flagged"] for step in ran["steps"]) == 1

        isolated = _post(base + "/api/isolate")
        assert isolated["isolation"]["fault_super_step"] == 2
        assert MARKER in isolated["isolation"]["fragment"]

        forked = _post(base + "/api/fork")
        assert forked["fork"]["old_step_count"] == 6
        assert MARKER not in json.dumps(forked["fork"]["messages"], ensure_ascii=False)
        assert forked["fork"]["parent_checkpoint_id"] == isolated["isolation"]["fault_checkpoint_id"]
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def _post(url: str) -> dict:
    request = urllib.request.Request(url, data=b"{}", method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def test_otlp_file_roundtrip_and_console_load():
    from src.cases import get_case
    from src.otel_trace import case_from_otlp, export_otlp
    from src.web import make_server

    exported = export_otlp(get_case("supply"))
    restored = case_from_otlp(exported)
    session = OmniTraceSession(restored)
    session.run()
    isolation = session.isolate()
    assert isolation["fault_super_step"] == 2
    assert MARKER in isolation["fragment"]
    assert "Receive order" not in isolation["fragment"]

    loop = OmniTraceSession(case_from_otlp(export_otlp(get_case("tool-loop"))))
    loop.run()
    assert loop.isolate()["fragments"] == [
        "Search weather in Hanoi",
        "Search weather in Hue",
        "Search weather in Da Nang",
        "Search weather in Can Tho",
    ]

    bare = {
        "resourceSpans": [
            {
                "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "agent-ngoai"}}]},
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "name": "chat",
                                "startTimeUnixNano": "1",
                                "attributes": [{"key": "gen_ai.operation.name", "value": {"stringValue": "chat"}}],
                                "events": [{"name": "gen_ai.user.message", "attributes": [{"key": "content", "value": {"stringValue": "khởi tạo"}}]}],
                                "status": {"code": "STATUS_CODE_OK"},
                            },
                            {
                                "name": "chat",
                                "startTimeUnixNano": "2",
                                "attributes": [{"key": "gen_ai.operation.name", "value": {"stringValue": "chat"}}],
                                "events": [{"name": "gen_ai.user.message", "attributes": [{"key": "content", "value": {"stringValue": "log có ERROR"}}]}],
                                "status": {"code": "STATUS_CODE_OK"},
                            },
                            {
                                "name": "chat",
                                "startTimeUnixNano": "3",
                                "attributes": [{"key": "gen_ai.operation.name", "value": {"stringValue": "invoke_agent"}}],
                                "events": [],
                                "status": {"code": "STATUS_CODE_OK"},
                            },
                            {
                                "name": "chat",
                                "startTimeUnixNano": "4",
                                "attributes": [{"key": "gen_ai.operation.name", "value": {"stringValue": "chat"}}],
                                "events": [
                                    {"name": "gen_ai.user.message", "attributes": [{"key": "content", "value": {"stringValue": "agent trả lời sai"}}]},
                                    {"name": "exception", "attributes": [{"key": "exception.message", "value": {"stringValue": "ERROR"}}]},
                                ],
                                "status": {"code": "STATUS_CODE_ERROR"},
                            },
                        ]
                    }
                ],
            }
        ]
    }

    server = make_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    try:
        page = urllib.request.urlopen(base + "/", timeout=5).read().decode("utf-8")
        assert "Drop a trace file" in page
        assert "resourceSpans" in page
        sample = json.loads(urllib.request.urlopen(base + "/api/sample/tool-loop", timeout=5).read().decode("utf-8"))
        assert sample["resourceSpans"][0]["scopeSpans"][0]["spans"]
        loaded = _post_json(base + "/api/load", bare)
        assert loaded["case"]["title"] == "agent-ngoai"
        assert loaded["steps"][-1]["flagged"] is True
        isolated = _post_json(base + "/api/isolate", {})
        assert isolated["isolation"]["fragments"] == ["log có ERROR"]
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def test_inspect_without_interp_exits_cleanly(monkeypatch):
    monkeypatch.setattr("src.session.interp_available", lambda: False)
    session = OmniTraceSession()
    session.run()
    code, text = session.inspect()
    assert code == 1
    assert "uv sync --extra interp" in text
    assert "hosts this page" in text
