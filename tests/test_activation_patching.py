import pytest
from src.layer4_interp.activation_patching import ActivationPatcher, HAS_INTERP

@pytest.mark.skipif(not HAS_INTERP, reason="Cần cài extra 'interp'")
def test_activation_patching_restores_clean_probability():
    """Patching copies the clean residual, so P(Paris) rises by the clean-prompt amount.

    GPT-2 small only assigns about 0.0016 to " Paris" on the France prompt, so the
    delta cannot exceed 0.1. Replacing the whole residual makes layer 0 and layer 8
    move that probability by the same amount.
    """
    patcher = ActivationPatcher(model_name="gpt2")

    clean_prompt = "The capital of France is"
    corrupted_prompt = "The capital of Russia is"
    target_token = " Paris"

    base_0, patched_0, delta_0 = patcher.patch_and_measure(
        clean_prompt, corrupted_prompt, target_token, patch_layer=0
    )
    base_8, patched_8, delta_8 = patcher.patch_and_measure(
        clean_prompt, corrupted_prompt, target_token, patch_layer=8
    )

    print(
        f"\n[Layer 0] base={base_0:.4f} patched={patched_0:.4f} delta={delta_0:.4f}"
    )
    print(
        f"[Layer 8] base={base_8:.4f} patched={patched_8:.4f} delta={delta_8:.4f}"
    )

    assert patched_0 > base_0
    assert patched_8 > base_8
    assert delta_0 < 0.05
    assert delta_8 < 0.05
    assert delta_8 == pytest.approx(delta_0, abs=1e-4)