from typing import Dict, List, Any, Tuple
from src.layer1_telemetry.tracing import Tracer
from src.layer1_telemetry.spans import Span
from src.layer2_checkpoint.store import MemoryStore, StateSnapshot
from src.layer2_checkpoint.time_machine import TimeMachine
from src.layer1_telemetry.semconv import (
    OMNITRACE_THREAD_ID,
    OMNITRACE_CHECKPOINT_ID,
    OMNITRACE_SUPER_STEP
)

# Declare core system
store = MemoryStore()
machine = TimeMachine(store)
tracer = Tracer()

captured_spans: List[Span] = []

def dummy_agent_step(state: Dict[str, Any]) -> Dict[str, Any]:
    messages = state.get("messages", [])
    step_number = len(messages) + 1

    messages.append(f"Agent thought and completed step {step_number}")
    state["messages"] = messages

    return state

def run_integrated_step(thread_id: str) -> Tuple[Span, StateSnapshot]:
    with tracer.agent(thread_id=thread_id) as span:

        chk_id = machine.step(thread_id, dummy_agent_step)
        snap = store.get(thread_id, chk_id)

        span.attributes[OMNITRACE_CHECKPOINT_ID] = chk_id
        span.attributes[OMNITRACE_SUPER_STEP] = snap.super_step

        captured_spans.append(span)

        return span, snap
    

def run_demo(thread_id: str = "demo_omni_01"):
    for _ in range(5):
        run_integrated_step(thread_id)
        
    return captured_spans, store.history(thread_id)