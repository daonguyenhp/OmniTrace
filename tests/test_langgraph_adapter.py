import pytest
from src.layer2_checkpoint.langgraph_adapter import (
    build_config,
    get_postgres_saver,
    HAS_POSTGRES_SAVER
)

def test_build_config_without_checkpoint():
    """Kiểm tra việc sinh config để chạy bình thường (từ đầu)"""
    config = build_config(thread_id="thread_abc")
    
    assert config == {
        "configurable": {
            "thread_id": "thread_abc"
        }
    }

def test_build_config_with_checkpoint():
    """Kiểm tra việc sinh config để Time Machine gọi Replay/Fork"""
    config = build_config(thread_id="thread_abc", checkpoint_id="chk_123")
    
    assert config == {
        "configurable": {
            "thread_id": "thread_abc",
            "checkpoint_id": "chk_123"
        }
    }