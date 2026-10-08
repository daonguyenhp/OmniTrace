from src.layer2_checkpoint.store import MemoryStore
from src.layer2_checkpoint.time_machine import TimeMachine
from src.layer2_checkpoint.store import StateSnapshot, MemoryStore

def test_time_machine_builds_causal_chain():
    store = MemoryStore()
    machine = TimeMachine(store)
    
    # --- ĐỊNH NGHĨA 4 BƯỚC SUY LUẬN GIẢ LẬP ---
    def step_1_init(state):
        state["status"] = "started"
        state["items"] = []
        return state
        
    def step_2_add_item(state):
        state["items"].append("apple")
        return state
        
    def step_3_add_item(state):
        state["items"].append("banana")
        return state
        
    def step_4_finish(state):
        state["status"] = "finished"
        return state

    # --- CHẠY LIÊN HOÀN 4 BƯỚC ---
    thread_id = "thread_time_01"
    machine.run(thread_id, [
        step_1_init, 
        step_2_add_item, 
        step_3_add_item, 
        step_4_finish
    ])
    
    # --- KIỂM CHỨNG TÍNH TOÀN VẸN CỦA CHUỖI ---
    history = store.history(thread_id)
    
    # 1. Đảm bảo sinh ra đúng 4 Checkpoints
    assert len(history) == 4
    
    # 2. Đảm bảo Super Step tăng dần
    assert history[0].super_step == 1
    assert history[3].super_step == 4
    
    # 3. Đảm bảo Sợi xích Cha-Con khép kín hoàn toàn
    assert history[0].parent_checkpoint_id is None # Gốc không có cha
    assert history[1].parent_checkpoint_id == history[0].checkpoint_id
    assert history[2].parent_checkpoint_id == history[1].checkpoint_id
    assert history[3].parent_checkpoint_id == history[2].checkpoint_id
    
    # 4. Kiểm chứng tính Kế thừa Bộ nhớ (State) ở bước cuối cùng
    final_state = history[3].state
    assert final_state["status"] == "finished"
    assert final_state["items"] == ["apple", "banana"]
    
    # 5. Kiểm chứng tính Đóng băng của Quá khứ (Immutable State)
    # Bước 2 chỉ có apple, chưa có banana
    assert history[1].state["items"] == ["apple"]


def test_time_machine_replay_executes_correctly():
    store = MemoryStore()
    machine = TimeMachine(store)
    thread_id = "thread_replay_01"
    
    # Biến đếm toàn cục để theo dõi số lần hệ thống thực thi từng hàm
    execution_counts = {"step_1": 0, "step_2": 0, "step_3": 0}
    
    def step_1(state):
        execution_counts["step_1"] += 1
        state["val"] = 10
        return state
        
    def step_2(state):
        execution_counts["step_2"] += 1
        state["val"] += 20
        return state
        
    def step_3(state):
        execution_counts["step_3"] += 1
        state["val"] += 30
        return state
        
    # 1. Chạy mạch chính (Main branch) gồm 3 bước
    machine.run(thread_id, [step_1, step_2, step_3])
    
    # Quả quyết cả 3 bước đều mới chạy đúng 1 lần
    assert execution_counts == {"step_1": 1, "step_2": 1, "step_3": 1}
    
    # Lấy Checkpoint ID của bước 2
    history = store.history(thread_id)
    chk_2_id = history[1].checkpoint_id # Chỉ mục 1 là bước 2
    
    # 2. KỊCH BẢN DELTA DEBUGGING: 
    # Causal Engine quyết định quay về bước 2, và thử chạy lại bước 3 với 1 logic khác
    def step_3_alt(state):
        execution_counts["step_3"] += 1 # Ta đếm dồn vào bước 3
        state["val"] += 100 # Trạng thái thay đổi kiểu khác
        return state
        
    new_chk_id = machine.replay(thread_id, chk_2_id, step_3_alt)
    
    # 3. KIỂM CHỨNG TÍNH THỰC THI (Execution)
    # - Hàm step_3_alt đã THỰC SỰ CHẠY (đếm tăng lên 2)
    # - Hàm step_1 và step_2 NGỦ YÊN (vẫn giữ nguyên 1, KHÔNG bị chạy lại)
    assert execution_counts == {"step_1": 1, "step_2": 1, "step_3": 2}
    
    # 4. Kiểm chứng tính Toàn vẹn của Đồ thị Nhánh rẽ (Branching Graph)
    new_snap = store.get(thread_id, new_chk_id)
    
    # Nhánh này bắt nguồn từ bước 2
    assert new_snap.parent_checkpoint_id == chk_2_id
    # Mặc dù chạy sau cùng, nhưng về mặt thời gian nó là bước 3 (kế thừa từ bước 2)
    assert new_snap.super_step == 3 
    
    # Trạng thái cộng dồn chính xác: 10 (bước 1) + 20 (bước 2) + 100 (nhánh mới) = 130
    assert new_snap.state["val"] == 130

def test_time_machine_fork_preserves_original_timeline():
    store = MemoryStore()
    machine = TimeMachine(store)
    main_thread = "thread_main_universe"
    
    # 1. Vũ trụ chính chạy 3 bước
    def step_1(state): return {"path": "A"}
    def step_2(state): state["path"] += " -> B"; return state
    def step_3(state): state["path"] += " -> C"; return state
    
    machine.run(main_thread, [step_1, step_2, step_3])
    
    # Ghi nhận lại lịch sử của vũ trụ chính trước khi rẽ nhánh
    main_history_before = store.history(main_thread)
    assert len(main_history_before) == 3
    chk_2_id = main_history_before[1].checkpoint_id # Lấy mốc Bước 2 ("A -> B")
    
    # 2. RẼ NHÁNH (FORK) từ Bước 2 sang Vũ trụ phụ
    def step_3_alt(state): 
        state["path"] += " -> D" # Rẽ sang D thay vì C
        return state
        
    alt_thread, alt_chk_id = machine.fork(
        source_thread_id=main_thread,
        source_checkpoint_id=chk_2_id,
        step_fn=step_3_alt,
        new_thread_id="thread_alt_universe"
    )
    
    # 3. KIỂM CHỨNG 1: Lịch sử Vũ trụ chính BẤT BIẾN
    main_history_after = store.history(main_thread)
    assert len(main_history_after) == 3 # Không bị phình to ra
    # Đảm bảo Hộp cuối cùng của nhánh chính vẫn giữ nguyên kết quả cũ
    assert main_history_after[2].state["path"] == "A -> B -> C"
    
    # 4. KIỂM CHỨNG 2: Vũ trụ phụ được sinh ra độc lập
    alt_history = store.history(alt_thread)
    assert len(alt_history) == 1 # Lịch sử riêng của nó chỉ mới có 1 bước (bước D)
    
    # 5. KIỂM CHỨNG 3: Móc nối Cha - Con xuyên Không-Thời gian
    alt_snap = alt_history[0]
    assert alt_snap.state["path"] == "A -> B -> D" # Kết quả của phép rẽ nhánh
    assert alt_snap.parent_checkpoint_id == chk_2_id # Nhận gốc Bước 2 của vũ trụ chính làm cha
    assert alt_snap.super_step == 3 # Vẫn kế thừa đúng bậc thời gian


def test_time_machine_resume_merges_pending_writes():
    store = MemoryStore()
    machine = TimeMachine(store)
    thread_id = "thread_resume_01"
    
    # 1. TẠO TÌNH HUỐNG GIẢ LẬP: Agent đang chờ phê duyệt
    # Trạng thái gốc chỉ có bản nháp, nhưng pending_writes chứa quyết định của con người
    incomplete_snap = StateSnapshot(
        thread_id=thread_id,
        checkpoint_id="chk_paused",
        parent_checkpoint_id=None,
        super_step=1,
        state={"draft": "Hello", "status": "drafting"},
        pending_writes={"draft": "Hello World", "human_approved": True}
    )
    store.put(incomplete_snap)
    
    # 2. ĐỊNH NGHĨA HÀM ĐI TIẾP (Resume)
    def step_2_publish(state):
        # Nếu gộp sổ (merge) ĐÚNG, draft phải biến thành "Hello World"
        # và biến human_approved phải xuất hiện trong state
        assert state["draft"] == "Hello World"
        assert state["human_approved"] is True
        
        # Agent thực hiện công việc của bước mới
        state["status"] = "published"
        return state
        
    # 3. KÍCH HOẠT THỨC TỈNH
    new_chk_id = machine.resume(thread_id, "chk_paused", step_2_publish)
    
    # 4. KIỂM CHỨNG TÍNH TOÀN VẸN SAU KHI RESUME
    final_snap = store.get(thread_id, new_chk_id)
    
    # - Chứa kết quả đã xong (do update từ pending_writes)
    assert final_snap.state["draft"] == "Hello World"
    assert final_snap.state["human_approved"] is True
    
    # - Chứa kết quả của bước vừa chạy
    assert final_snap.state["status"] == "published"
    
    # - Dọn dẹp sạch sẽ
    assert final_snap.pending_writes == {}
    assert final_snap.super_step == 2