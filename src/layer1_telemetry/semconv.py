from enum import Enum

# Các hằng số tiêu chuẩn của OpenTelemetry cho Generative AI
GEN_AI_SYSTEM = "gen_ai.system"
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
GEN_AI_PROMPT = "gen_ai.prompt"
GEN_AI_COMPLETION = "gen_ai.completion"
GEN_AI_OPERATION = "gen_ai.operation.name"

class GenAIOperation(str, Enum):
    """Định nghĩa các loại hành vi cốt lõi của Agent"""
    CHAT = "chat"
    TEXT_COMPLETION = "text_completion"
    INVOKE_AGENT = "invoke_agent"
    CREATE_AGENT = "create_agent"
    EXECUTE_TOOL = "execute_tool"

# Các hằng số độc quyền của OmniTrace (Phục vụ Spatiotemporal Debugging)
OMNITRACE_THREAD_ID = "omnitrace.thread_id"           # Định danh luồng suy luận của một tác vụ
OMNITRACE_CHECKPOINT_ID = "omnitrace.checkpoint_id"   # Mã định danh trạng thái tại một thời điểm
OMNITRACE_SUPER_STEP = "omnitrace.super_step"         # Số thứ tự bước lớn trong quy trình đa tác tử

# Cờ ngữ nghĩa: Đánh dấu các event/span có giá trị về mặt logic/nhân quả, 
# giúp tách biệt luồng suy luận của AI khỏi các nhiễu rác hệ thống (như network I/O)
OMNITRACE_IS_SEMANTIC = "omnitrace.is_semantic"