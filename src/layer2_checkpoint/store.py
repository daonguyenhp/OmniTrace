from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class StateSnapshot:
    thread_id: str
    checkpoint_id: str
    parent_checkpoint_id: Optional[str]
    super_step: int

    state: Dict[str, Any] = field(default_factory=dict)
    pending_writes: Dict[str, Any] = field(default_factory=dict)

class MemoryStore:
    def __init__(self):
        self._snapshots: Dict[str, StateSnapshot] = {}
        self._timelines: Dict[str, List[str]] = {}

    def put(self, snapshot: StateSnapshot):
        tid = snapshot.thread_id
        cid = snapshot.checkpoint_id

        if tid not in self._snapshots:
            self._snapshots[tid] = {}
            self._timelines[tid] = []
        
        self._snapshots[tid][cid] = snapshot

        if cid not in self._timelines[tid]:
            self._timelines[tid].append(cid)
    
    def get(self, thread_id: str, checkpoint_id: str) -> Optional[StateSnapshot]:
        return self._snapshots.get(thread_id, {}).get(checkpoint_id)

    def latest(self, thread_id: str) -> Optional[StateSnapshot]:
        timeline = self._timelines.get(thread_id)
        if not timeline:
            return None
        
        latest_cid = timeline[-1]
        return self._snapshots[thread_id][latest_cid]
    
    def history(self, thread_id: str) -> List[StateSnapshot]:
        timeline = self._timelines.get(thread_id, [])
        return [self._snapshots[thread_id][cid] for cid in timeline]