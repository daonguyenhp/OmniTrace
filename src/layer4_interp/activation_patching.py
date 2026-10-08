import logging
from typing import Tuple

try:
    import torch
    from transformer_lens import HookedTransformer
    HAS_INTERP = True
except (ImportError, OSError):
    HAS_INTERP = False
    HookedTransformer = None

class ActivationPatcher:
    def __init__(self, model_name: str = "gpt2"):
        if not HAS_INTERP:
            raise ImportError("ActivationPatcher requires transformer-lens to be installed")

        self.model = HookedTransformer.from_pretrained(model_name)

    
    def patch_and_measure(self, clean_prompt: str, corrupted_prompt: str, target_token_str: str, patch_layer: int) -> Tuple[float, float, float]:
        target_token_id = self.model.to_single_token(target_token_str)

        _, clean_cache = self.model.run_with_cache(clean_prompt)

        hook_name = f"blocks.{patch_layer}.hook_resid_post"
        clean_activation = clean_cache[hook_name]
        
        corrupted_tokens = self.model.to_tokens(corrupted_prompt)
        corrupted_logits = self.model(corrupted_tokens)

        probs_corrupted = corrupted_logits[0, -1].softmax(dim=-1)
        base_prob = probs_corrupted[target_token_id].item()

        def patch_hook(resid, hook):
            resid[:] = clean_activation[:]
            return resid
        
        patched_logits = self.model.run_with_hooks(
            corrupted_tokens,
            fwd_hooks=[(hook_name, patch_hook)]
        )
        
        probs_patched = patched_logits[0, -1].softmax(dim=-1)
        patched_prob = probs_patched[target_token_id].item()

        delta_prob = patched_prob - base_prob
        
        return base_prob, patched_prob, delta_prob