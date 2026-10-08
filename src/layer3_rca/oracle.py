from enum import Enum
from typing import List, Callable, Any

class OracleVerdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"

OracleFn = Callable[[List[Any]], OracleVerdict]