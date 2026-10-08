import json
import os
import clickhouse_connect
from typing import Dict, Any, List

from src.layer1_telemetry.spans import Span
from src.layer1_telemetry.semconv import (
    OMNITRACE_THREAD_ID,
    OMNITRACE_CHECKPOINT_ID,
    OMNITRACE_SUPER_STEP
)

class ClickhouseSink:

    def __init__(self, client = None):
        self.client = client
    
    def connect(self):
        if self.client is None:
            self.client = clickhouse_connect.get_client(
                host=os.getenv("OMNITRACE_CH_HOST", "localhost"),
                port=int(os.getenv("OMNITRACE_CH_PORT", "8123")),
                user=os.getenv("OMNITRACE_CH_USER", "default"),
                password=os.getenv("OMNITRACE_CH_PASS", ""),
            )
    
    def init_schema(self):
        self.connect()
        self.client.command("""
            CREATE TABLE IF NOT EXISTS omnitrace_spans (
                trace_id String,
                span_id String,
                parent_id Nullable(String),
                operation String,
                start_time Float64,
                end_time Float64,
                thread_id Nullable(String),
                checkpoint_id Nullable(String),
                super_step Nullable(Int32),
                attributes String,
                events String
            ) ENGINE = MergeTree()
            ORDER BY (trace_id, start_time)
        """)
    
    def format_span_to_row(self, span: Span) -> Dict[str, Any]:
        attrs = span.attributes.copy()

        thread_id = attrs.pop(OMNITRACE_THREAD_ID, None)
        checkpoint_id = attrs.pop(OMNITRACE_CHECKPOINT_ID, None)
        super_step = attrs.pop(OMNITRACE_SUPER_STEP, None)

        events_list = [
            {
                "name": e.name,
                "timestamp": e.timestamp,
                "attributes": e.attributes
            } for e in span.events
        ]

        return {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "super_step": super_step,

            "trace_id": span.trace_id,
            "span_id": span.span_id,
            "parent_id": span.parent_id,
            "operation": span.operation.value,
            "start_time": span.start_time,
            "end_time": span.end_time,

            "attributes": json.dumps(attrs, ensure_ascii=False),
            "events": json.dumps(events_list, ensure_ascii=False)
        }

    def export(self, spans: List[Span]):
        if not spans:
            return
        
        self.connect()

        rows = [self.format_span_to_row(span) for span in spans]
        columns = list(rows[0].keys())
        data = [[row[col] for col in columns] for row in rows]
        self.client.insert("omnitrace_spans", data, column_names=columns)