import pytest
from src.layer3_rca.ddmin import mRTF
from src.layer4_interp.auto_anatomy import run_auto_anatomy

try:
    from src.layer4_interp.logit_lens import HAS_INTERP
except ImportError:
    HAS_INTERP = False

@pytest.mark.skipif(not HAS_INTERP, reason="Cần cài extra 'interp'")
def test_auto_anatomy_filters_out_ddmin_garbage():
    """BƯỚC 6.3: Báo cáo KHÔNG chứa phần context đã bị ddmin loại."""
    
    # 1. Giả lập kết quả mRTF trả về từ Bước 5.1
    # LƯU Ý: Giả sử list ban đầu có chứa dict {"text": "Bỏ qua đoạn rác này. "}
    # Nhưng ddmin đã chạy thành công, loại bỏ nó và chỉ giữ lại 3 chunk cốt lõi.
    mock_mrtf = mRTF(
        chunks=[
            {"checkpoint_id": "chk_2", "text": "The capital of "},
            {"checkpoint_id": "chk_3", "text": "Russia "},
            {"checkpoint_id": "chk_4", "text": "is"},
        ],
        original_indices=[1, 2, 3],
        evals=12,
        is_minimized=True
    )

    clean_prompt = "The capital of France is"
    target_token = " Paris"

    # Định nghĩa con dao mổ để trích xuất text từ dict
    def extract_text(chunk):
        return chunk["text"]

    # 2. Khởi động hệ thống Auto Anatomy
    result = run_auto_anatomy(
        mrtf=mock_mrtf,
        clean_prompt=clean_prompt,
        target_token=target_token,
        chunk_formatter=extract_text,
        model_name="gpt2"
    )

    report_text = result["report_text"]
    print(f"\n{report_text}")

    # 3. KIỂM CHỨNG BƯỚC 6.3
    
    # - Đảm bảo ĐOẠN RÁC đã bị loại bỏ hoàn toàn khỏi cuộc xét nghiệm
    assert "Bỏ qua đoạn rác này" not in report_text
    
    # - Đảm bảo báo cáo được ráp đúng từ các Chunk do mRTF cung cấp
    assert "The capital of Russia is" in report_text
    
    # - Đảm bảo bác sĩ đã tìm ra kết quả hợp lệ
    assert result["aha_layer"] >= 0
    assert result["causal_layer"] >= 0