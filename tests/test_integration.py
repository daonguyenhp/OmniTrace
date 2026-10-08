from src.layer1_telemetry.tracing import Tracer
from src.layer2_checkpoint.store import MemoryStore
from src.layer2_checkpoint.time_machine import TimeMachine
from src.layer1_telemetry.semconv import (
    OMNITRACE_THREAD_ID,
    OMNITRACE_CHECKPOINT_ID,
    OMNITRACE_SUPER_STEP,
    OMNITRACE_IS_SEMANTIC
)

def test_semantic_flag_gateway():
    """BƯỚC 3.2: Cổng kiểm chứng Khả năng Truy vết Nhân quả"""
    store = MemoryStore()
    machine = TimeMachine(store)
    tracer = Tracer()
    thread_id = "thread_gate_3_2"
    captured_spans = []

    # 1. Định nghĩa 3 bước chạy
    def step_1_clean(state):
        state["context"] = "Clean data"
        return state

    def step_2_garbage(state):
        # Intentionally add garbage to state at step 2
        state["context"] += " | [Garbage] sdf876sdfsdf"
        return state

    def step_3_crash(state):
        state["context"] += " | Step 3 affected"
        return state

    steps = [step_1_clean, step_2_garbage, step_3_crash]

    # 2. Run simulation and record
    for i, fn in enumerate(steps):
        with tracer.agent(thread_id=thread_id) as span:
            chk_id = machine.step(thread_id, fn)
            snap = store.get(thread_id, chk_id)

            span.attributes[OMNITRACE_CHECKPOINT_ID] = chk_id
            span.attributes[OMNITRACE_SUPER_STEP] = snap.super_step

            # Attach semantic flag (only attach to Step 2 - index 1)
            if i == 1:
                span.attributes[OMNITRACE_IS_SEMANTIC] = True

            captured_spans.append(span)

    # --- 3. Verify according to exact requirement 3.2 ---
    
    # a. Filter out the only Span with semantic flag
    semantic_spans = [
        s for s in captured_spans 
        if s.attributes.get(OMNITRACE_IS_SEMANTIC) is True
    ]
    assert len(semantic_spans) == 1
    target_span = semantic_spans[0]

    # b. Extract Checkpoint ID from that Span
    target_chk_id = target_span.attributes[OMNITRACE_CHECKPOINT_ID]

    # c. Go to store (Layer 2) and get the corresponding Box
    target_snap = store.get(thread_id, target_chk_id)

    # d. Decision: This is exactly Step 2, and the brain contains the right garbage
    assert target_snap.super_step == 2
    assert "[Garbage]" in target_snap.state["context"]
    
    # Confirm Step 1 is not tagged and has no garbage
    assert captured_spans[0].attributes.get(OMNITRACE_IS_SEMANTIC) is None