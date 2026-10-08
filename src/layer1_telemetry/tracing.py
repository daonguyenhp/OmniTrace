import contextvars
from contextlib import contextmanager
from typing import Optional, Generator

from src.layer1_telemetry.spans import Span, SpanStatus
from src.layer1_telemetry.semconv import GenAIOperation

from src.config import get_settings
from src.layer1_telemetry.semconv import (
    GEN_AI_REQUEST_MODEL, 
    GEN_AI_PROMPT, 
    GEN_AI_COMPLETION,
    OMNITRACE_THREAD_ID, OMNITRACE_CHECKPOINT_ID, OMNITRACE_SUPER_STEP
)

_current_span: contextvars.ContextVar[Optional[Span]] = contextvars.ContextVar("current_span", default=None)

class Tracer:
    @contextmanager
    def start_span(self, operation: GenAIOperation, thread_id: Optional[str] = None, checkpoint_id: Optional[str] = None, super_step: Optional[int] = None) -> Generator[Span, None, None]:
        parent = _current_span.get()
        span = Span(operation=operation)

        if parent:
            span.parent_id = parent.span_id
            span.trace_id = parent.trace_id
        
        val_thread = thread_id or (parent.attributes.get(OMNITRACE_THREAD_ID) if parent else None)
        val_checkpoint = checkpoint_id or (parent.attributes.get(OMNITRACE_CHECKPOINT_ID) if parent else None)

        val_step = super_step
        if val_step is None and parent:
            val_step = parent.attributes.get(OMNITRACE_SUPER_STEP)

        if val_thread is not None:
            span.attributes[OMNITRACE_THREAD_ID] = val_thread
        if val_checkpoint is not None:
            span.attributes[OMNITRACE_CHECKPOINT_ID] = val_checkpoint
        if val_step is not None:
            span.attributes[OMNITRACE_SUPER_STEP] = val_step

        token = _current_span.set(span)
        try:
            yield span
            span.end(status=SpanStatus.OK)
        except Exception as e:
            span.add_event("exception", attributes={"error": str(e), "type": type(e).__name__})
            span.end(SpanStatus.ERROR)
            raise
        finally:
            _current_span.reset(token)
    

    def agent(self, **kwargs):
        return self.start_span(GenAIOperation.INVOKE_AGENT, **kwargs)
        
    def chat(self, **kwargs):
        return self.start_span(GenAIOperation.CHAT, **kwargs)
        
    def tool(self, **kwargs):
        return self.start_span(GenAIOperation.EXECUTE_TOOL, **kwargs)

    
    def record_llm(self, span:Span, model:str, prompt:str, completion:str, tokens:int):
        span.attributes[GEN_AI_REQUEST_MODEL] = model
        span.attributes["gen_ai.usage.total_tokens"] = tokens

        settings = get_settings()

        if settings.record_prompt:
            span.add_event(GEN_AI_PROMPT, {"content": prompt})
            if completion:
                span.add_event(GEN_AI_COMPLETION, {"content": completion})