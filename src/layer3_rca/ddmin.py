from typing import List, Any, Tuple
from dataclasses import dataclass
from src.layer3_rca.oracle import OracleVerdict, OracleFn

OMNITRACE_DDMIN_MAX_EVALS = 100

@dataclass
class mRTF:
    chunks: List[Any]   
    original_indices: List[int]
    evals: int
    is_minimized: bool

def ddmin(chunks: List[Any], oracle: OracleFn, max_evals: int = OMNITRACE_DDMIN_MAX_EVALS) -> mRTF:
    # 1. INDEXING TECHNIQUE: Convert ["A", "B"] to [(0, "A"), (1, "B")]
    c_indexed = list(enumerate(chunks))
    
    n = 2
    evals = 0
    
    def test(c_test_indexed: List[Tuple[int, Any]]) -> OracleVerdict:
        nonlocal evals
        if evals >= max_evals:
            return OracleVerdict.UNRESOLVED
        evals += 1
        
        # Remove the indexing and only pass the actual data to the Oracle
        pure_chunks = [chunk for _, chunk in c_test_indexed]
        return oracle(pure_chunks)

    # 2. Delta Debugging algorithm runs on the indexed list
    while len(c_indexed) > 1:
        subsets = []
        start = 0
        for i in range(n):
            subset_size = len(c_indexed) // n + (1 if i < len(c_indexed) % n else 0)
            subsets.append(c_indexed[start:start + subset_size])
            start += subset_size
            
        some_complement_is_failing = False
        some_subset_is_failing = False
        
        # Check the complement
        for i in range(n):
            complement = []
            for j in range(n):
                if i != j:
                    complement.extend(subsets[j])
                    
            res = test(complement)
            if res == OracleVerdict.FAIL:
                c_indexed = complement
                n = max(n - 1, 2)
                some_complement_is_failing = True
                break
                
        if some_complement_is_failing:
            continue
            
        # Check the subset
        for i in range(n):
            res = test(subsets[i])
            if res == OracleVerdict.FAIL:
                c_indexed = subsets[i]
                n = 2
                some_subset_is_failing = True
                break
                
        if some_subset_is_failing:
            continue
            
        if n == len(c_indexed):
            break
        n = min(n * 2, len(c_indexed))
        
    # 3. PACKAGE mRTF RETURN
    return mRTF(
        chunks=[chunk for _, chunk in c_indexed],
        original_indices=[idx for idx, _ in c_indexed],
        evals=evals,
        is_minimized=(evals < max_evals)
    )


