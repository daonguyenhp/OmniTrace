from src.layer2_checkpoint.store import MemoryStore, StateSnapshot

def test_memory_store_isolation_and_retrieval():
    store = MemoryStore()
    
    # --- 1. Tạo dữ liệu cho Thread A (Nhà phân tích dữ liệu) ---
    snap_a1 = StateSnapshot(
        thread_id="thread_A", checkpoint_id="chk_a1", parent_checkpoint_id=None, 
        super_step=1, state={"role": "analyst", "data_loaded": True}
    )
    snap_a2 = StateSnapshot(
        thread_id="thread_A", checkpoint_id="chk_a2", parent_checkpoint_id="chk_a1", 
        super_step=2, state={"role": "analyst", "data_loaded": True, "clean_done": True}
    )
    store.put(snap_a1)
    store.put(snap_a2)
    
    # --- 2. Tạo dữ liệu cho Thread B (Nhà văn sáng tạo) ---
    snap_b1 = StateSnapshot(
        thread_id="thread_B", checkpoint_id="chk_b1", parent_checkpoint_id=None, 
        super_step=1, state={"role": "writer", "draft_ready": False}
    )
    store.put(snap_b1)
    
    # --- 3. KIỂM CHỨNG: Tách biệt bộ nhớ (Isolation) ---
    # Lấy lịch sử của Thread A chỉ có 2 cái, Thread B chỉ có 1 cái
    assert len(store.history("thread_A")) == 2
    assert len(store.history("thread_B")) == 1
    
    # --- 4. KIỂM CHỨNG: Hàm Get (O(1) Lookup) ---
    # Lấy checkpoint 1 của Thread A
    retrieved_a1 = store.get("thread_A", "chk_a1")
    assert retrieved_a1 is not None
    assert retrieved_a1.state["data_loaded"] is True
    
    # Thử lấy checkpoint của Thread B nhưng dùng id của Thread A -> Phải ra None
    assert store.get("thread_B", "chk_a1") is None
    
    # --- 5. KIỂM CHỨNG: Hàm Latest ---
    latest_a = store.latest("thread_A")
    assert latest_a.checkpoint_id == "chk_a2"
    assert latest_a.state["clean_done"] is True
    
    latest_b = store.latest("thread_B")
    assert latest_b.checkpoint_id == "chk_b1"