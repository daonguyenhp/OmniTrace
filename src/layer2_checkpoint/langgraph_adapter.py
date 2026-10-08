from typing import Dict, Any, Optional

def build_config(thread_id: str, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id
    
    return config

try:
    from langgraph.checkpoint.postgres import PostgresSaver
    HAS_POSTGRES_SAVER = True
except ImportError:
    HAS_POSTGRES_SAVER = False
    PostgresSaver = None

def get_postgres_saver(*args, **kwargs):
    if not HAS_POSTGRES_SAVER:
        raise ImportError("langgraph-checkpoint-postgres is not installed. Please install it with `pip install langgraph-checkpoint-postgres`")
    return PostgresSaver(*args, **kwargs)