from src.layer2_checkpoint.store import StateSnapshot
from src.layer3_rca.analyzer import debug_snapshot
from src.layer3_rca.oracle import OracleVerdict

def test_debug_snapshot_finds_poisoned_chunk_and_checkpoint():
    step_5_snap = StateSnapshot(
        thread_id="thread_5_1",
        checkpoint_id="chk_5",
        parent_checkpoint_id="chk_4",
        super_step=5,
        state={
            "messages": [
                {"checkpoint_id": "chk_1", "text": "Initialize system"},
                {"checkpoint_id": "chk_2", "text": "Clean data | [POISONED] sdf876"},
                {"checkpoint_id": "chk_3", "text": "Analyze part 1"},
                {"checkpoint_id": "chk_4", "text": "Analyze part 2"},
                {"checkpoint_id": "chk_5", "text": "Conclusion is corrupted (Due to poison)"},
            ]
        }
    )

    def extract_messages(snap: StateSnapshot):
        return snap.state.get("messages", [])

    def garbage_oracle(chunks) -> OracleVerdict:
        for c in chunks:
            if "[POISONED]" in c["text"]:
                return OracleVerdict.FAIL
        return OracleVerdict.PASS

    mrtf = debug_snapshot(step_5_snap, extract_messages, garbage_oracle)

    assert len(mrtf.chunks) == 1
    poisoned_chunk = mrtf.chunks[0]
    
    assert "[POISONED]" in poisoned_chunk["text"]
    assert poisoned_chunk["checkpoint_id"] == "chk_2"
    assert mrtf.original_indices[0] == 1


def test_debug_snapshot_with_tool_loop_oracle():
    loop_snap = StateSnapshot(
        thread_id="thread_5_2", checkpoint_id="chk_9", parent_checkpoint_id="chk_8", super_step=9,
        state={
            "actions": [
                {"tool": "Calculator", "input": "1+1"},
                {"tool": "Search", "input": "thời tiết HN"},
                {"tool": "Search", "input": "thời tiết HCM"},
                {"tool": "Search", "input": "thời tiết Đà Nẵng"},
                {"tool": "Search", "input": "thời tiết Cần Thơ"},
                {"tool": "WriteFile", "input": "report.txt"},
            ]
        }
    )

    def extract_actions(snap: StateSnapshot):
        return snap.state.get("actions", [])

    def tool_loop_oracle(chunks) -> OracleVerdict:
        N = 3 
        counts = {}
        for c in chunks:
            tool_name = c["tool"]
            counts[tool_name] = counts.get(tool_name, 0) + 1
            if counts[tool_name] > N:
                return OracleVerdict.FAIL
        return OracleVerdict.PASS

    mrtf = debug_snapshot(loop_snap, extract_actions, tool_loop_oracle)

    assert len(mrtf.chunks) == 4
    for chunk in mrtf.chunks:
        assert chunk["tool"] == "Search"
        
    assert mrtf.original_indices == [1, 2, 3, 4]