from src.layer1_telemetry.semconv import (
    GenAIOperation,
    GEN_AI_SYSTEM,
    GEN_AI_OPERATION,
    OMNITRACE_THREAD_ID,
    OMNITRACE_CHECKPOINT_ID,
    OMNITRACE_SUPER_STEP,
    OMNITRACE_IS_SEMANTIC
)

def test_gen_ai_operation_enum():
    # Đảm bảo Enum có các giá trị đúng chuẩn
    assert GenAIOperation.CHAT.value == "chat"
    assert GenAIOperation.INVOKE_AGENT.value == "invoke_agent"
    assert GenAIOperation.EXECUTE_TOOL.value == "execute_tool"
    assert GenAIOperation.CREATE_AGENT.value == "create_agent"
    assert GenAIOperation.TEXT_COMPLETION.value == "text_completion"

def test_omnitrace_specific_attributes():
    # Đảm bảo các key Spatiotemporal được định nghĩa chuẩn xác
    assert OMNITRACE_THREAD_ID == "omnitrace.thread_id"
    assert OMNITRACE_CHECKPOINT_ID == "omnitrace.checkpoint_id"
    assert OMNITRACE_SUPER_STEP == "omnitrace.super_step"
    assert OMNITRACE_IS_SEMANTIC == "omnitrace.is_semantic"

def test_opentelemetry_standard_attributes():
    # Đảm bảo các chuẩn OpenTelemetry có sẵn
    assert GEN_AI_SYSTEM == "gen_ai.system"
    assert GEN_AI_OPERATION == "gen_ai.operation.name"