import pytest
from src.layer1_telemetry.tracing import Tracer
from src.layer1_telemetry.semconv import GenAIOperation
from src.layer1_telemetry.spans import SpanStatus

def test_tracer_builds_span_hierarchy():
    tracer = Tracer()
    
    # Dựng cây tác vụ: Agent -> Chat -> Tool
    with tracer.agent() as agent_span:
        with tracer.chat() as chat_span:
            with tracer.tool() as tool_span:
                # Ghi log thử ở tầng con sâu nhất
                tool_span.add_event("running_search_tool")
    
    # 1. Kiểm tra Trace ID phải y hệt nhau trên toàn bộ cây
    assert agent_span.trace_id == chat_span.trace_id == tool_span.trace_id
    
    # 2. Kiểm tra quan hệ Cha - Con (Gia phả)
    assert agent_span.parent_id is None
    assert chat_span.parent_id == agent_span.span_id
    assert tool_span.parent_id == chat_span.span_id
    
    # 3. Kiểm tra Operation khởi tạo từ hàm tiện ích
    assert agent_span.operation == GenAIOperation.INVOKE_AGENT
    assert chat_span.operation == GenAIOperation.CHAT
    assert tool_span.operation == GenAIOperation.EXECUTE_TOOL

def test_tracer_exception_handling():
    tracer = Tracer()
    
    # Bẫy lỗi bằng pytest (mong đợi đoạn code này sẽ ném ra ValueError)
    with pytest.raises(ValueError, match="Database is locked"):
        with tracer.tool() as span:
            span.add_event("doing_something")
            raise ValueError("Database is locked")
            
    # Dù quăng lỗi văng ra ngoài, Tracer vẫn phải đóng được Span và đánh cờ ERROR
    assert span.status == SpanStatus.ERROR
    
    # Kiểm tra xem Tracer có tự động log lại cái lỗi đó vào Event không
    assert len(span.events) == 2
    assert span.events[1].name == "exception"
    assert span.events[1].attributes["error"] == "Database is locked"