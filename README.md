# OmniTrace

**Spatiotemporal causal debugger for multi-agent LLM runs.**

OmniTrace takes one failed agent run (OpenTelemetry GenAI JSON), finds the smallest piece of context that still causes the failure, and can fork a cleaned thread from that fault checkpoint — without replaying the old run.

| Input | Output |
| --- | --- |
| One `.otlp.json` trace (`resourceSpans`) | Minimal failing fragment (ddmin / mRTF) |
| Optional: built-in sample cases | Fault vs symptom checkpoints, then an optional fork |

Author: **Nguyễn Đăng Gia Đạo**

---

## Why it exists

In multi-step agent traces, the span that *shows* the failure (symptom) is often not where the bad context entered (cause). OmniTrace:

1. **Loads** a recorded run into a checkpointed timeline  
2. **Isolates** the minimal failing fragment with delta debugging  
3. **Forks** a new thread from the fault checkpoint with that fragment removed  
4. **Inspects** (optional) the fragment inside a small local model  

---

## Quick start

Requires [Python](https://www.python.org/) ≥ 3.11 and [uv](https://github.com/astral-sh/uv).

```bash
uv sync --extra dev
uv run --extra dev omnitrace serve --port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

| Action | What it does |
| --- | --- |
| Drop / open a sample | Load one failed run |
| **Isolate** | Shrink context to the minimal failing piece |
| **Fork** | New thread from the cause, piece removed |
| **Inspect** | Optional model look (needs `--extra interp`) |

### CLI

```bash
# List built-in cases
uv run omnitrace cases

# Export a sample as OTLP JSON
uv run omnitrace export --case supply -o supply.otlp.json

# Isolate / fork from a file
uv run omnitrace isolate --file supply.otlp.json
uv run omnitrace fork --file supply.otlp.json
```

### Tests

```bash
uv run --extra dev pytest tests/ \
  --ignore=tests/test_clickhouse_sink.py \
  --ignore=tests/test_logit_lens.py \
  --ignore=tests/test_activation_patching.py \
  --ignore=tests/test_auto_anatomy.py
```

Optional extras: `telemetry`, `checkpoint`, `interp` (see `pyproject.toml`).

---

## Trace format

Any agent that exports **OpenTelemetry GenAI** JSON works.

- Top-level: `resourceSpans`
- Steps: spans named `chat` or `execute_tool`
- Symptom: `STATUS_CODE_ERROR` (or `omnitrace.is_semantic`)
- Oracle (resource attributes), if present:
  - `omnitrace.oracle.type` = `contains` + `omnitrace.oracle.text`, or
  - `omnitrace.oracle.type` = `tool_repeat` + `omnitrace.oracle.limit`

If no oracle is set, OmniTrace falls back to the exception message in the span, or a tool-repeat heuristic.

Built-in samples: `supply`, `tool-loop`, `overrefusal` (also under `examples/`).

---

## Architecture (short)

| Layer | Role |
| --- | --- |
| Telemetry | OTel GenAI spans, join keys (`thread_id`, `checkpoint_id`, `super_step`) |
| Checkpoint | In-memory store + time machine (step / fork) |
| RCA | Oracle + ddmin → mRTF (minimal failing fragment) |
| Interp | Optional logit lens / activation patching (GPT-2) |

---

## Live demo

This app is a **small Python HTTP server**, not a static site. GitHub Pages cannot host it.

| Option | Notes |
| --- | --- |
| **Local** (default) | `omnitrace serve` — best for CV / interviews |
| **Cloud VM / Railway / Render / Fly.io** | Run `serve --host 0.0.0.0 --port $PORT`; Isolate & Fork work; Inspect needs RAM + `interp` |
| **Docker** | See `Dockerfile` below |

Example public bind:

```bash
uv run omnitrace serve --host 0.0.0.0 --port 8765
```

A `Dockerfile` is included for one-click deploy on Docker-capable hosts. Free tiers may sleep when idle; do not expose an unauthenticated public instance with untrusted uploads in production.

---

## License

Personal / portfolio project. See repository for usage terms if added later.
