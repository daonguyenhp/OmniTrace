"""In-memory debug session shared by the CLI and the console.

The supply-chain scenario is the acceptance story: garbage enters at
super-step 2, the semantic flag fires at super-step 5, delta debugging
returns only that fragment, and fork resumes from the cleaned checkpoint.
"""

from __future__ import annotations

from typing import Any

from src.layer1_telemetry.semconv import (
    OMNITRACE_CHECKPOINT_ID,
    OMNITRACE_IS_SEMANTIC,
    OMNITRACE_SUPER_STEP,
)
from src.layer1_telemetry.tracing import Tracer
from src.layer2_checkpoint.store import MemoryStore
from src.layer2_checkpoint.time_machine import TimeMachine
from src.cases import TraceCase, get_case
from src.otel_trace import load_case
from src.layer3_rca.analyzer import debug_snapshot

MARKER = "[TOXIC_GARBAGE]"


def interp_available() -> bool:
    try:
        from src.layer4_interp.auto_anatomy import HAS_INTERP
        if not HAS_INTERP:
            return False
        from transformer_lens import HookedTransformer  # noqa: F401
    except Exception:
        return False
    return True


class OmniTraceSession:
    def __init__(self, case: TraceCase | None = None) -> None:
        self.case = case or get_case("supply")
        self.thread_id = self.case.thread_id
        self.store = MemoryStore()
        self.machine = TimeMachine(self.store)
        self.tracer = Tracer()
        self.spans: list[Any] = []
        self.ran = False
        self.isolation: dict[str, Any] | None = None
        self.fork_result: dict[str, Any] | None = None
        self.inspect_result: dict[str, Any] | None = None
        self._mrtf: Any = None

    def run(self, case: TraceCase | None = None) -> None:
        if case is not None:
            self.case = case
        self.thread_id = self.case.thread_id
        self.store = MemoryStore()
        self.machine = TimeMachine(self.store)
        self.tracer = Tracer()
        self.spans = []
        self.isolation = None
        self.fork_result = None
        self.inspect_result = None
        self._mrtf = None
        for step in self.case.steps:
            self._run_step(step)
        self.ran = True

    def load(self, payload: dict[str, Any]) -> None:
        self.run(load_case(payload))

    def _run_step(self, step: dict[str, Any]) -> None:
        def step_fn(state: dict[str, Any]) -> dict[str, Any]:
            messages = list(state.get("messages", []))
            message = {"text": step["text"]}
            if step.get("tool"):
                message["tool"] = step["tool"]
            messages.append(message)
            state["messages"] = messages
            return state

        flagged = bool(step.get("flag"))

        with self.tracer.agent(thread_id=self.thread_id) as span:
            checkpoint_id = self.machine.step(self.thread_id, step_fn)
            snapshot = self.store.get(self.thread_id, checkpoint_id)
            messages = snapshot.state.get("messages", [])
            if messages:
                messages[-1]["checkpoint_id"] = checkpoint_id
            span.attributes[OMNITRACE_CHECKPOINT_ID] = checkpoint_id
            span.attributes[OMNITRACE_SUPER_STEP] = snapshot.super_step
            if flagged:
                span.attributes[OMNITRACE_IS_SEMANTIC] = True
            self.spans.append(span)

    def flagged_snapshot(self):
        for span in self.spans:
            if span.attributes.get(OMNITRACE_IS_SEMANTIC) is True:
                checkpoint_id = span.attributes[OMNITRACE_CHECKPOINT_ID]
                return self.store.get(self.thread_id, checkpoint_id)
        raise RuntimeError("No step is marked as the symptom")

    def isolate(self) -> dict[str, Any]:
        if not self.ran:
            raise RuntimeError("No trace has been loaded")
        symptom = self.flagged_snapshot()
        mrtf = debug_snapshot(symptom, _messages, self.case.oracle())
        self._mrtf = mrtf
        if not mrtf.chunks:
            raise RuntimeError("Delta debugging found no failing piece")
        fragments = [chunk["text"] for chunk in mrtf.chunks]
        first = mrtf.chunks[0]
        fault = self.store.get(self.thread_id, first["checkpoint_id"])
        self.isolation = {
            "fragment": "\n".join(fragments),
            "fragments": fragments,
            "fault_checkpoint_id": first["checkpoint_id"],
            "fault_super_step": fault.super_step,
            "symptom_checkpoint_id": symptom.checkpoint_id,
            "symptom_super_step": symptom.super_step,
            "evals": mrtf.evals,
            "original_index": mrtf.original_indices[0],
            "original_indices": list(mrtf.original_indices),
        }
        return self.isolation

    def fork(self) -> dict[str, Any]:
        if self.isolation is None:
            self.isolate()
        fault_id = self.isolation["fault_checkpoint_id"]
        old_count = len(self.store.history(self.thread_id))

        banned = set(self.isolation["fragments"])

        def resume_clean(state: dict[str, Any]) -> dict[str, Any]:
            kept = [
                message
                for message in state.get("messages", [])
                if message.get("text") not in banned
            ]
            kept.append({"text": "Continue from the cleaned context"})
            state["messages"] = kept
            return state

        new_thread, new_checkpoint = self.machine.fork(
            self.thread_id, fault_id, resume_clean
        )
        new_snapshot = self.store.get(new_thread, new_checkpoint)
        self.fork_result = {
            "old_thread_id": self.thread_id,
            "old_step_count": old_count,
            "new_thread_id": new_thread,
            "new_checkpoint_id": new_checkpoint,
            "parent_checkpoint_id": new_snapshot.parent_checkpoint_id,
            "super_step": new_snapshot.super_step,
            "messages": new_snapshot.state.get("messages", []),
        }
        return self.fork_result

    def inspect(self) -> tuple[int, str]:
        if not self.ran:
            raise RuntimeError("No trace has been loaded")
        if self._mrtf is None:
            self.isolate()
        if not interp_available():
            text = (
                "Inspect runs on the machine that hosts this page. "
                "The local model could not load. On the host, run: uv sync --extra interp"
            )
            self.inspect_result = {"ok": False, "text": text}
            return 1, text
        try:
            from src.layer4_interp.auto_anatomy import run_auto_anatomy

            banned = set(self.isolation["fragments"])
            clean = " ".join(
                message["text"]
                for message in _messages(self.flagged_snapshot())
                if message.get("text") not in banned
            )
            report = run_auto_anatomy(
                mrtf=self._mrtf,
                clean_prompt=clean or "The capital of France is",
                target_token=" Paris",
                chunk_formatter=lambda chunk: chunk["text"],
            )
        except Exception as exc:
            text = (
                "Inspect runs on the machine that hosts this page. "
                f"The local model could not load ({exc}). "
                "On the host, run: uv sync --extra interp"
            )
            self.inspect_result = {"ok": False, "text": text}
            return 1, text
        self.inspect_result = {"ok": True, "text": report["report_text"]}
        return 0, report["report_text"]

    def view(self) -> dict[str, Any]:
        steps = []
        for snapshot in self.store.history(self.thread_id):
            flagged = any(
                span.attributes.get(OMNITRACE_CHECKPOINT_ID) == snapshot.checkpoint_id
                and span.attributes.get(OMNITRACE_IS_SEMANTIC) is True
                for span in self.spans
            )
            steps.append(
                {
                    "super_step": snapshot.super_step,
                    "checkpoint_id": snapshot.checkpoint_id,
                    "parent_checkpoint_id": snapshot.parent_checkpoint_id,
                    "flagged": flagged,
                    "messages": snapshot.state.get("messages", []),
                }
            )
        return {
            "ran": self.ran,
            "thread_id": self.thread_id,
            "case": {
                "id": self.case.id,
                "title": self.case.title,
                "summary": self.case.summary,
                "oracle": self.case.oracle_spec,
            },
            "needle": self.case.needle,
            "steps": steps,
            "isolation": self.isolation,
            "fork": self.fork_result,
            "inspect": self.inspect_result,
        }


def _messages(snapshot) -> list:
    return list(snapshot.state.get("messages", []))
