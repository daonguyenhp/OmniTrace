from src.layer3_rca.oracle import OracleVerdict
from src.layer3_rca.ddmin import ddmin, mRTF

def test_ddmin_isolates_single_faulty_chunk():
    # 1. Create a scenario: 8 data segments
    chunks = [f"Segment {i}" for i in range(1, 9)]
    
    # 2. Define Oracle: Most sensitive to "Segment 5"
    # The oracle is designed to fail only when "Segment 5" is present
    def mock_oracle(test_chunks: list[str]) -> OracleVerdict:
        if any("Segment 5" in chunk for chunk in test_chunks):
            return OracleVerdict.FAIL
        return OracleVerdict.PASS
        
    # Basic check: All 8 segments definitely FAIL
    assert mock_oracle(chunks) == OracleVerdict.FAIL
    
    # 3. CHẠY DELTA DEBUGGING
    result: mRTF = ddmin(chunks, oracle=mock_oracle)
    
    # 4. VERIFICATION: Return exactly and uniquely "Segment 5"
    assert len(result.chunks) == 1
    assert result.chunks[0] == "Segment 5"

def test_ddmin_respects_max_evals():
    chunks = [f"Segment {i}" for i in range(1, 9)]
    
    def slow_oracle(test_chunks):
        if any("Segment 5" in chunk for chunk in test_chunks):
            return OracleVerdict.FAIL
        return OracleVerdict.PASS
        
    # Intentionally limit the number of Oracle calls to 2
    result: mRTF = ddmin(chunks, oracle=slow_oracle, max_evals=2)
    
    # Since it was cut short, it couldn't optimize down to 1 chunk
    # The result will return a set still containing Segment 5 but not maximally minimized
    assert len(result.chunks) > 1
    assert any("Segment 5" in c for c in result.chunks)


def test_ddmin_isolates_chunk_and_returns_mrtf_with_indices():
    # 1. Create 8 segments: ["Segment 1", "Segment 2", ..., "Segment 8"]
    # Note: Index in Python starts from 0. So "Segment 5" will have Index = 4.
    chunks = [f"Segment {i}" for i in range(1, 9)]
    
    def mock_oracle(test_chunks: list[str]) -> OracleVerdict:
        if any("Segment 5" in chunk for chunk in test_chunks):
            return OracleVerdict.FAIL
        return OracleVerdict.PASS
        
    # 2. RUN ALGORITHM
    result: mRTF = ddmin(chunks, oracle=mock_oracle)
    
    # 3. VERIFY mRTF REPORT
    # - Remaining chunks are only "Segment 5"
    assert len(result.chunks) == 1
    assert result.chunks[0] == "Segment 5"
    
    # - MOST IMPORTANT: It must show the original index of Segment 5 is 4
    assert len(result.original_indices) == 1
    assert result.original_indices[0] == 4
    
    # - Perfect metadata
    assert result.evals > 0
    assert result.is_minimized is True

def test_ddmin_respects_max_evals_in_mrtf():
    """Verify the is_minimized flag when out of budget"""
    chunks = [f"Segment {i}" for i in range(1, 9)]
    
    def slow_oracle(test_chunks):
        if any("Segment 5" in chunk for chunk in test_chunks):
            return OracleVerdict.FAIL
        return OracleVerdict.PASS
        
    # Intentionally limit the number of Oracle calls to 2
    result = ddmin(chunks, oracle=slow_oracle, max_evals=2)
    
    # The system crashed, returning a partial result
    assert len(result.chunks) > 1
    assert result.is_minimized is False
    assert result.evals == 2