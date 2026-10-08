import pytest
from src.layer4_interp.logit_lens import LogitLensOracle, HAS_INTERP

# Bỏ qua bài test nếu chưa cài torch để CI/CD không bị sập
@pytest.mark.skipif(not HAS_INTERP, reason="Cần cài extra 'interp'")
def test_logit_lens_reveals_token_evolution():
    """BƯỚC 6.1: Chỉ ra được lớp mà top-1 đổi."""
    # Khởi tạo với mô hình gpt2 nhỏ (124M tham số, 12 layers)
    oracle = LogitLensOracle(model_name="gpt2")
    
    # Câu prompt test kiến thức địa lý
    prompt = "The capital of France is"
    
    # Lấy danh sách dự đoán ở từng lớp
    predictions = oracle.analyze_last_token(prompt)
    
    assert len(predictions) == 12  # GPT-2 có 12 lớp

    # Lớp cuối của lens phải trùng token mà chính model chọn.
    logits = oracle.model(prompt)
    actual_id = int(logits[0, -1].argmax())
    actual_token = oracle.model.to_string(actual_id)
    assert predictions[-1][1] == actual_token

    # Top-1 phải đổi sau lớp 0. Với câu này: lớp 0 là " not", từ lớp 1 là " now".
    first_token = predictions[0][1]
    aha_layer = next(layer for layer, token in predictions if token != first_token)
    print(
        f"\n[Logit Lens] top-1 shifted from {first_token!r} to "
        f"{predictions[aha_layer][1]!r} at layer {aha_layer}. "
        f"final layer matches model: {actual_token!r}"
    )
    assert aha_layer > 0