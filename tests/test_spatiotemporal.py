from src.layer1_telemetry.tracing import Tracer
from src.layer1_telemetry.semconv import (
    OMNITRACE_THREAD_ID,
    OMNITRACE_CHECKPOINT_ID,
    OMNITRACE_SUPER_STEP
)

def test_spatiotemporal_inheritance_and_filtering():
    tracer = Tracer()
    captured_spans = [] # Đóng vai trò như một Database tạm thời
    
    # 1. Truyền tọa độ vào GỐC (Agent)
    with tracer.agent(thread_id="thread_mars_01", checkpoint_id="chk_start", super_step=1) as root_span:
        captured_spans.append(root_span)
        
        # Các hàm bên trong KHÔNG CẦN truyền lại tọa độ
        with tracer.chat() as chat_span:
            captured_spans.append(chat_span)
            
            with tracer.tool() as tool_span:
                captured_spans.append(tool_span)
                
    # 2. Giả lập hành vi truy vấn của Causal Engine: 
    # "Hãy lấy cho tôi toàn bộ lịch sử của luồng 'thread_mars_01'"
    filtered_spans = [
        span for span in captured_spans 
        if span.attributes.get(OMNITRACE_THREAD_ID) == "thread_mars_01"
    ]
    
    # 3. Phải lọc ra được CẢ BA SPAN
    assert len(filtered_spans) == 3
    
    # 4. Kiểm tra chéo: Cả 3 Span đều phải giữ đúng Checkpoint và Super Step
    for span in filtered_spans:
        assert span.attributes[OMNITRACE_CHECKPOINT_ID] == "chk_start"
        assert span.attributes[OMNITRACE_SUPER_STEP] == 1