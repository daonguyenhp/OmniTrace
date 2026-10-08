import logging
from typing import List, Tuple

try:
    import torch
    from transformer_lens import HookedTransformer
    HAS_INTERP = True
except (ImportError, OSError):
    HAS_INTERP = False
    HookedTransformer = None

class LogitLensOracle:
    def __init__(self, model_name: str = "gpt2"):
        if not HAS_INTERP:
            raise ImportError("LogitLensOracle requires transformer-lens to be installed")
        
        self.model_name = model_name
        self.model = HookedTransformer.from_pretrained(model_name)

    def analyze_last_token(self, prompt: str) -> List[Tuple[int, str]]:
        logits, cache = self.model.run_with_cache(prompt)

        n_layers = self.model.cfg.n_layers
        layer_predictions = []

        for layer in range(n_layers):
            resid_name = f"blocks.{layer}.hook_resid_post"
            resid_stream = cache[resid_name]

            last_token_resid = resid_stream[0, -1, :]
            layer_logits = self.model.unembed(self.model.ln_final(last_token_resid))

            top1_id = layer_logits.argmax().item()
            top1_token = self.model.to_string(top1_id)
            
            layer_predictions.append((layer, top1_token))
            
        return layer_predictions
        