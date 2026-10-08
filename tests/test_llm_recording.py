import time
from src.layer1_telemetry.tracing import Tracer
from src.layer1_telemetry.semconv import GEN_AI_REQUEST_MODEL

def test_record_llm_with_content_enabled(monkeypatch):
    # BẬT cờ lưu nội dung
    monkeypatch.setenv("RECORD_PROMPT", "true")
    
    tracer = Tracer()
    with tracer.chat() as span:
        time.sleep(0.01) # Giả lập độ trễ
        tracer.record_llm(
            span, 
            model="gpt-4o", 
            prompt="Hello, write a poem", 
            completion="Roses are red...", 
            tokens=150
        )
        
    # 1. Attribute cấu trúc phải tồn tại
    assert span.attributes[GEN_AI_REQUEST_MODEL] == "gpt-4o"
    assert span.attributes["gen_ai.usage.total_tokens"] == 150
    assert span.duration_ms >= 10.0
    
    # 2. Event nội dung PHẢI được sinh ra (Prompt + Completion = 2 events)
    assert len(span.events) == 2
    assert span.events[0].name == "gen_ai.prompt"
    assert span.events[0].attributes["content"] == "Hello, write a poem"

def test_record_llm_with_content_disabled(monkeypatch):
    # TẮT cờ lưu nội dung
    monkeypatch.setenv("RECORD_PROMPT", "false")
    
    tracer = Tracer()
    with tracer.chat() as span:
        time.sleep(0.01)
        tracer.record_llm(
            span, 
            model="gpt-4o", 
            prompt="Top secret data", 
            completion="Secret answer", 
            tokens=200
        )
        
    # 1. Attribute cấu trúc KHÔNG ĐỔI
    assert span.attributes[GEN_AI_REQUEST_MODEL] == "gpt-4o"
    assert span.attributes["gen_ai.usage.total_tokens"] == 200
    assert span.duration_ms >= 10.0
    
    # 2. Event nội dung KHÔNG ĐƯỢC sinh ra (để bảo mật / tiết kiệm dung lượng)
    assert len(span.events) == 0