import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field

from src.layer1_telemetry.semconv import GenAIOperation

class SpanStatus(str, Enum):
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"

@dataclass
class SpanEvent:
    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Span:
    operation: GenAIOperation
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)

    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        self.events.append(
            SpanEvent(
                name = name,
                attributes = attributes or {}
            )
        )
    
    def end(self, status: SpanStatus = SpanStatus.OK):
        self.end_time = time.time()
        self.status = status

    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000.0