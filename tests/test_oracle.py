from src.layer3_rca.oracle import OracleVerdict, OracleFn

def test_oracle_behavior_on_chunks():
    # The system's input is a LIST (List of Chunks)
    # Represents data sources, messages, or context segments
    full_input = [
        "Segment 1: Clean data",
        "Segment 2: Data contaminated [Garbage]",
        "Segment 3: Valid data"
    ]
    
    def mock_oracle(chunks: list[str]) -> OracleVerdict:
        for chunk in chunks:
            if "[Garbage]" in chunk:
                return OracleVerdict.FAIL
        return OracleVerdict.PASS
        
    # --- Verify basic conditions of Delta Debugging ---
    
    # 1. Oracle on full initial data (Full Input) -> Must FAIL
    # (Because we know for sure the error occurs when we pass the whole thing to AI)
    assert mock_oracle(full_input) == OracleVerdict.FAIL
    
    # 2. Oracle on empty list (Empty Input) -> Must PASS
    # (If no data is passed and it still fails, it means the system crashes rather than due to data)
    assert mock_oracle([]) == OracleVerdict.PASS
    
    # 3. (Auxiliary check): Manually extract chunk 2 -> System PASS
    clean_subset = [full_input[0], full_input[2]]
    assert mock_oracle(clean_subset) == OracleVerdict.PASS