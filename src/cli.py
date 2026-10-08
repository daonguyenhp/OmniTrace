import argparse
import sys

from src.layer1_telemetry.tracing import Tracer
from src.layer2_checkpoint.store import MemoryStore
from src.layer2_checkpoint.time_machine import TimeMachine
from src.layer1_telemetry.semconv import (
    OMNITRACE_CHECKPOINT_ID,
    OMNITRACE_SUPER_STEP,
    OMNITRACE_IS_SEMANTIC
)

def run_demo():
    
    store = MemoryStore()
    machine = TimeMachine(store)
    tracer = Tracer()
    thread_id = "thread_demo_cli"
    captured_spans = []

    # 1. Định nghĩa 3 bước
    def step_1_clean(state): return state
    def step_2_garbage(state): 
        state["context"] = "[TOXIC_GARBAGE]"
        return state
    def step_3_crash(state): return state

    steps = [step_1_clean, step_2_garbage, step_3_crash]

    print(f"Running agent on thread [{thread_id}]")
    
    # 2. Chạy giả lập và ghi hình
    for i, fn in enumerate(steps):
        with tracer.agent(thread_id=thread_id) as span:
            chk_id = machine.step(thread_id, fn)
            snap = store.get(thread_id, chk_id)

            span.attributes[OMNITRACE_CHECKPOINT_ID] = chk_id
            span.attributes[OMNITRACE_SUPER_STEP] = snap.super_step

            # Cắm cờ ngữ nghĩa ở Bước 2
            if i == 1:
                span.attributes[OMNITRACE_IS_SEMANTIC] = True

            captured_spans.append(span)
            print(f"  step {i+1}  checkpoint {chk_id}")

    # 3. Phân tích kết quả
    print("\nSpans:")
    for i, span in enumerate(captured_spans):
        is_semantic = span.attributes.get(OMNITRACE_IS_SEMANTIC, False)
        chk_id = span.attributes.get(OMNITRACE_CHECKPOINT_ID)
        
        if is_semantic:
            print(f"  step {i+1}  {chk_id}  flagged")
        else:
            print(f"  step {i+1}  {chk_id}  ok")
            
    print("\nThe oracle will target step 2 for delta debugging.")

def _utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        return


def cmd_export(case: str, path: str) -> None:
    import json
    from pathlib import Path

    from src.cases import get_case
    from src.otel_trace import export_otlp

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(export_otlp(get_case(case)), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(target)


def _open_session(case: str = "supply", file: str | None = None):
    import json
    from pathlib import Path

    from src.cases import get_case
    from src.session import OmniTraceSession

    session = OmniTraceSession()
    if file:
        session.load(json.loads(Path(file).read_text(encoding="utf-8")))
    else:
        session.run(get_case(case))
    return session


def cmd_cases() -> None:
    from src.cases import list_cases

    for case in list_cases():
        print(f"{case.id}\t{case.title}")


def cmd_isolate(case: str = "supply", file: str | None = None) -> None:
    session = _open_session(case, file)
    isolation = session.isolate()
    print(isolation["fragment"])
    print(isolation["fault_checkpoint_id"])


def cmd_fork(case: str = "supply", file: str | None = None) -> None:
    session = _open_session(case, file)
    isolation = session.isolate()
    forked = session.fork()
    print(isolation["fragment"])
    print(isolation["fault_checkpoint_id"])
    print(forked["new_thread_id"])
    print(forked["new_checkpoint_id"])
    for message in forked["messages"]:
        print(message["text"])
    banned = set(isolation["fragments"])
    if any(message["text"] in banned for message in forked["messages"]):
        raise RuntimeError("The fork still contains the failing piece")


def cmd_inspect(case: str = "supply", file: str | None = None) -> int:
    session = _open_session(case, file)
    code, text = session.inspect()
    print(text)
    return code


def cmd_serve(host: str, port: int) -> None:
    from src.web import serve

    serve(host, port)


def main():
    _utf8_stdout()
    parser = argparse.ArgumentParser(description="OmniTrace causal debugger")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("demo", help="Run the three-step demo")
    subparsers.add_parser("cases", help="List the built-in cases")

    def add_case_flags(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--case", default="supply", help="supply, tool-loop, overrefusal")
        parser.add_argument("--file", help="OpenTelemetry trace JSON, or a case JSON file")

    isolate_parser = subparsers.add_parser("isolate", help="Print the failing piece and its checkpoint")
    add_case_flags(isolate_parser)
    fork_parser = subparsers.add_parser("fork", help="Remove the failing piece and continue from that checkpoint")
    add_case_flags(fork_parser)
    inspect_parser = subparsers.add_parser("inspect", help="Inspect the failing piece. Exits 1 without the interp extra")
    add_case_flags(inspect_parser)
    export_parser = subparsers.add_parser("export", help="Write a sample case as an OpenTelemetry trace file")
    export_parser.add_argument("--case", default="supply", help="supply, tool-loop, overrefusal")
    export_parser.add_argument("-o", "--output", required=True, help="Path of the .otlp.json file")
    serve_parser = subparsers.add_parser("serve", help="Open the console at http://127.0.0.1:8765")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "cases":
        cmd_cases()
    elif args.command == "isolate":
        cmd_isolate(args.case, args.file)
    elif args.command == "fork":
        cmd_fork(args.case, args.file)
    elif args.command == "inspect":
        sys.exit(cmd_inspect(args.case, args.file))
    elif args.command == "export":
        cmd_export(args.case, args.output)
    elif args.command == "serve":
        cmd_serve(args.host, args.port)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()