import time
from src.layer1_telemetry.semconv import GenAIOperation
from src.layer1_telemetry.spans import Span, SpanStatus

def test_span_lifecycle_and_duration():
    # 1. Bắt đầu một Span (ví dụ: kích hoạt Agent)
    span = Span(operation=GenAIOperation.INVOKE_AGENT)
    
    # Kiểm tra khởi tạo
    assert span.trace_id is not None
    assert span.span_id is not None
    assert span.start_time > 0
    assert span.end_time is None
    assert span.status == SpanStatus.UNSET

    # 2. Thêm một sự kiện vào Span
    span.add_event("agent_thought_process_started", {"strategy": "chain_of_thought"})
    assert len(span.events) == 1
    assert span.events[0].name == "agent_thought_process_started"

    # Giả lập thời gian Agent đang suy nghĩ/chạy tool mất khoảng 50ms
    time.sleep(0.05)

    # 3. Kết thúc Span
    span.end(status=SpanStatus.OK)
    
    # 4. Kiểm tra thời gian thực thi (duration_ms)
    assert span.end_time is not None
    assert span.status == SpanStatus.OK
    
    duration = span.duration_ms
    # Phải mất ít nhất 50ms (do hàm sleep) và lớn hơn 0
    assert duration >= 50.0
    
    print(f"\nTrace ID: {span.trace_id}")
    print(f"Agent thực thi mất: {duration:.2f} ms")