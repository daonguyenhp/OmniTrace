import json
from src.layer1_telemetry.semconv import (
    GenAIOperation,
    OMNITRACE_THREAD_ID,
    OMNITRACE_CHECKPOINT_ID,
    OMNITRACE_SUPER_STEP
)
from src.layer1_telemetry.spans import Span
from src.layer1_telemetry.clickhouse_sink import ClickhouseSink

from unittest.mock import MagicMock

def test_format_span_to_row():
    # 1. Tạo span giả lập và tiêm dữ liệu
    span = Span(operation=GenAIOperation.INVOKE_AGENT)
    span.attributes[OMNITRACE_THREAD_ID] = "thread_01"
    span.attributes[OMNITRACE_CHECKPOINT_ID] = "chk_abc"
    span.attributes[OMNITRACE_SUPER_STEP] = 5
    span.attributes["model"] = "gpt-4o"
    span.attributes["temperature"] = 0.7
    
    span.add_event("called_api", {"latency_ms": 120})
    span.end()
    
    # 2. Đưa qua Sink để đúc thành một Hàng (Row)
    sink = ClickhouseSink()
    row = sink.format_span_to_row(span)
    
    # 3. Kiểm chứng các cột cơ bản
    assert row["trace_id"] == span.trace_id
    assert row["operation"] == "invoke_agent"
    
    # 4. Kiểm chứng các cột Không-thời gian đã bị TÁCH RIÊNG thành công
    assert row["thread_id"] == "thread_01"
    assert row["checkpoint_id"] == "chk_abc"
    assert row["super_step"] == 5
    
    # 5. Kiểm chứng cột Attributes (phải là chuỗi JSON và KHÔNG CÒN chứa 3 key trên)
    attrs_json = json.loads(row["attributes"])
    assert attrs_json["model"] == "gpt-4o"
    assert attrs_json["temperature"] == 0.7
    assert OMNITRACE_THREAD_ID not in attrs_json  # Đã bị pop() ra
    
    # 6. Kiểm chứng cột Events (được gom lại thành 1 cột JSON mảng)
    events_json = json.loads(row["events"])
    assert len(events_json) == 1
    assert events_json[0]["name"] == "called_api"
    assert events_json[0]["attributes"]["latency_ms"] == 120

def test_clickhouse_export_with_mock():
    # 1. Tạo một "bản sao giả mạo" (Mock) của Database Client
    mock_client = MagicMock()
    
    # 2. Tiêm DB giả vào Sink
    sink = ClickhouseSink(client=mock_client)
    
    # 3. Tạo một Span nháp
    span = Span(operation=GenAIOperation.CHAT)
    span.end()
    
    # 4. Kích hoạt lệnh tạo Bảng và Xuất dữ liệu
    sink.init_schema()
    sink.export([span])
    
    # 5. KIỂM CHỨNG: Sink có thực sự ra lệnh CREATE TABLE không?
    mock_client.command.assert_called_once()
    create_query = mock_client.command.call_args[0][0] # Lấy câu query được gửi đi
    assert "CREATE TABLE IF NOT EXISTS omnitrace_spans" in create_query
    assert "ENGINE = MergeTree()" in create_query
    
    # 6. KIỂM CHỨNG: Sink có thực sự gọi hàm INSERT đúng cách không?
    mock_client.insert.assert_called_once()
    args, kwargs = mock_client.insert.call_args
    
    assert args[0] == "omnitrace_spans" # Bắn đúng vào bảng này
    
    data_matrix = args[1]
    assert len(data_matrix) == 1  # 1 Hàng dữ liệu
    assert len(data_matrix[0]) == 11 # 11 Cột dữ liệu chuẩn
    
    assert "trace_id" in kwargs["column_names"]
    assert "events" in kwargs["column_names"]