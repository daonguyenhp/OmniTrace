from typing import Callable, Any, List
from src.layer2_checkpoint.store import StateSnapshot
from src.layer3_rca.ddmin import ddmin, mRTF
from src.layer3_rca.oracle import OracleFn

def debug_snapshot(
    snapshot: StateSnapshot, 
    extract_fn: Callable[[StateSnapshot], List[Any]], 
    oracle: OracleFn
) -> mRTF:
    # 1. Extract the list of segments to analyze (from the state)
    chunks = extract_fn(snapshot)
    
    # 2. Run the ddmin algorithm on the set of chunks
    return ddmin(chunks, oracle)