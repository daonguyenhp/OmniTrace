from typing import Callable, Any, Dict
from src.layer3_rca.ddmin import mRTF

try:
    from src.layer4_interp.logit_lens import HAS_INTERP as _LENS_OK
    from src.layer4_interp.logit_lens import LogitLensOracle
    from src.layer4_interp.activation_patching import HAS_INTERP as _PATCH_OK
    from src.layer4_interp.activation_patching import ActivationPatcher

    HAS_INTERP = bool(_LENS_OK and _PATCH_OK)
except ImportError:
    HAS_INTERP = False

def run_auto_anatomy(mrtf: mRTF, clean_prompt: str, target_token: str, chunk_formatter: Callable[[Any], str], model_name: str = "gpt2") -> Dict[str, Any]:
    try:
        from transformer_lens import HookedTransformer  # noqa: F401
    except (ImportError, OSError) as exc:
        raise ImportError(
            "Inspect runs on the machine that hosts this page. "
            f"The local model could not load ({exc}). "
            "On the host, run: uv sync --extra interp"
        ) from exc
    if not HAS_INTERP:
        raise ImportError(
            "Inspect runs on the machine that hosts this page. "
            "The local model could not load. On the host, run: uv sync --extra interp"
        )
    
    corrupted_prompt = "".join([chunk_formatter(c) for c in mrtf.chunks])

    lens = LogitLensOracle(model_name)
    predictions = lens.analyze_last_token(corrupted_prompt)

    final_token = predictions[-1][1]
    aha_layer = -1
    for layer, token in predictions:
        if token == final_token:
            aha_layer = layer
            break
    
    patcher = ActivationPatcher(model_name)
    n_layers = patcher.model.cfg.n_layers
    
    best_layer = -1
    max_delta = -1.0

    for layer in range(n_layers):
        _, _, delta = patcher.patch_and_measure(
            clean_prompt, corrupted_prompt, target_token, patch_layer=layer
        )
        if delta > max_delta:
            max_delta = delta
            best_layer = layer
    
    report_text = (
        f"=== OmniTrace inspect report ===\n"
        f"[1] Minimal failing context (mRTF):\n'{corrupted_prompt}'\n"
        f"[2] Logit lens: the model settles on its final token at layer {aha_layer}\n"
        f"[3] Activation patching: the strongest repair layer is {best_layer} (delta +{max_delta*100:.2f}%)\n"
        f"================================"
    )
    
    return {
        "report_text": report_text,
        "aha_layer": aha_layer,
        "causal_layer": best_layer,
        "corrupted_prompt": corrupted_prompt
    }