import uuid
import copy
from typing import Callable, Dict, Any, List, Optional

from src.layer2_checkpoint.store import StateSnapshot, MemoryStore

class TimeMachine:
    def __init__(self, store: MemoryStore):
        self.store = store
    
    def step(self, thread_id: str, step_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> str:
        latest_snap = self.store.latest(thread_id)

        if latest_snap:
            super_step = latest_snap.super_step + 1
            parent_id = latest_snap.checkpoint_id
            current_state = copy.deepcopy(latest_snap.state)
        else:
            super_step = 1
            parent_id = None
            current_state = {}
        
        new_state = step_fn(current_state)
        new_checkpoint_id = f"chk_{uuid.uuid4().hex[:8]}"

        snapshot = StateSnapshot(
            thread_id=thread_id,
            checkpoint_id=new_checkpoint_id,
            parent_checkpoint_id=parent_id,
            super_step=super_step,
            state=new_state
        )

        self.store.put(snapshot)
        return new_checkpoint_id
    
    def run(self, thread_id: str, step_fns: List[Callable[[Dict[str, Any]], Dict[str, Any]]]):
        for fn in step_fns:
            self.step(thread_id, fn) 
    
    def replay(self, thread_id: str, checkpoint_id: str, step_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> str:
        target_snap = self.store.get(thread_id, checkpoint_id)
        if not target_snap:
            raise ValueError(f"Checkpoint {checkpoint_id} not found for thread {thread_id}")
        
        super_step = target_snap.super_step + 1
        parent_id = target_snap.checkpoint_id

        current_state = copy.deepcopy(target_snap.state)
        new_state = step_fn(current_state)

        new_checkpoint_id = f"chk_{uuid.uuid4().hex[:8]}"
        snapshot = StateSnapshot(
            thread_id=thread_id,
            checkpoint_id=new_checkpoint_id,
            parent_checkpoint_id=parent_id,
            super_step=super_step,
            state=new_state
        )
        
        self.store.put(snapshot)
        return new_checkpoint_id
    
    def fork(self, source_thread_id: str, source_checkpoint_id: str, step_fn: Callable[[Dict[str, Any]], Dict[str, Any]], new_thread_id: Optional[str] = None) -> tuple[str, str]:
        target_snap = self.store.get(source_thread_id, source_checkpoint_id)
        if not target_snap:
            raise ValueError(f"Checkpoint {source_checkpoint_id} not found for thread {source_thread_id}")
        
        if new_thread_id is None:
            new_thread_id = f"thd_{uuid.uuid4().hex[:8]}"
        
        super_step = target_snap.super_step + 1
        parent_id = target_snap.checkpoint_id

        current_state = copy.deepcopy(target_snap.state)
        new_state = step_fn(current_state)

        new_checkpoint_id = f"chk_{uuid.uuid4().hex[:8]}"
        snapshot = StateSnapshot(
            thread_id=new_thread_id,
            checkpoint_id=new_checkpoint_id,
            parent_checkpoint_id=parent_id,
            super_step=super_step,
            state=new_state
        )

        self.store.put(snapshot)
        
        return new_thread_id, new_checkpoint_id

    def resume(self, thread_id: str, checkpoint_id: str, step_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> str:
        target_snap = self.store.get(thread_id, checkpoint_id)
        if not target_snap:
            raise ValueError(f"Checkpoint {checkpoint_id} not found for thread {thread_id}")
            
        super_step = target_snap.super_step + 1
        parent_id = target_snap.checkpoint_id
        
        current_state = copy.deepcopy(target_snap.state)
        current_pending = copy.deepcopy(target_snap.pending_writes)
        
        current_state.update(current_pending)
        
        new_state = step_fn(current_state)
        
        new_checkpoint_id = f"chk_{uuid.uuid4().hex[:8]}"
        snapshot = StateSnapshot(
            thread_id=thread_id,
            checkpoint_id=new_checkpoint_id,
            parent_checkpoint_id=parent_id,
            super_step=super_step,
            state=new_state,
            pending_writes={}
        )
        
        self.store.put(snapshot)
        return new_checkpoint_id