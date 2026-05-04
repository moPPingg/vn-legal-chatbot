"""Law Classifier — lightweight question→law_type predictor."""
from __future__ import annotations
import pickle, logging
from pathlib import Path
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline as SkPipeline
from app.config import FAISS_DIR

logger = logging.getLogger(__name__)
MODEL_PATH = FAISS_DIR / "classifier.pkl"
_clf: Optional[SkPipeline] = None

# Expanded Training Data (10+ examples per category for better accuracy)
TRAIN_DATA = [
    # HÌNH SỰ
    ("giết người bị phạt tù bao nhiêu năm", "hình sự"),
    ("trộm cắp tài sản trên 2 triệu", "hình sự"),
    ("tội lừa đảo chiếm đoạt tài sản qua mạng", "hình sự"),
    ("tàng trữ vận chuyển trái phép chất ma túy", "hình sự"),
    ("cố ý gây thương tích cho người khác", "hình sự"),
    ("tội nhận hối lộ tham ô tài sản", "hình sự"),
    ("hiếp dâm trẻ em bị xử lý thế nào", "hình sự"),
    ("bắt cóc tống tiền bị phạt ra sao", "hình sự"),
    ("đánh bạc tổ chức đánh bạc qua mạng", "hình sự"),
    ("tội buôn lậu trốn thuế mức độ nặng", "hình sự"),
    ("lạm dụng tín nhiệm chiếm đoạt tài sản", "hình sự"),
    
    # DÂN SỰ
    ("quyền thừa kế tài sản không có di chúc", "dân sự"),
    ("hợp đồng mua bán vay mượn tiền bạc", "dân sự"),
    ("bồi thường thiệt hại ngoài hợp đồng", "dân sự"),
    ("tranh chấp quyền sở hữu tài sản", "dân sự"),
    ("ủy quyền thực hiện giao dịch", "dân sự"),
    ("thời hiệu khởi kiện đòi nợ là bao lâu", "dân sự"),
    ("bảo lãnh vay tiền ngân hàng", "dân sự"),
    ("chấp dứt hợp đồng thuê nhà trước hạn", "dân sự"),
    ("quyền tác giả sở hữu trí tuệ", "dân sự"),
    ("cầm cố thế chấp tài sản", "dân sự"),

    # LAO ĐỘNG
    ("công ty sa thải nhân viên trái pháp luật", "lao động"),
    ("quyền lợi người lao động khi nghỉ việc", "lao động"),
    ("hợp đồng lao động xác định thời hạn", "lao động"),
    ("đóng bảo hiểm xã hội bắt buộc", "lao động"),
    ("chế độ thai sản cho lao động nữ", "lao động"),
    ("tiền lương làm thêm giờ ngày lễ tết", "lao động"),
    ("bồi thường khi đơn phương chấm dứt hợp đồng", "lao động"),
    ("trợ cấp thất nghiệp nhận ở đâu", "lao động"),
    ("quy định về thời gian thử việc", "lao động"),
    ("kỷ luật lao động khiển trách sa thải", "lao động"),

    # GIAO THÔNG
    ("vi phạm nồng độ cồn khi lái xe máy ô tô", "giao thông"),
    ("vượt đèn đỏ phạt bao nhiêu tiền", "giao thông"),
    ("gây tai nạn giao thông bỏ trốn", "giao thông"),
    ("không đội mũ bảo hiểm khi đi xe máy", "giao thông"),
    ("chạy quá tốc độ cho phép 10km/h", "giao thông"),
    ("tước giấy phép lái xe bằng lái mấy tháng", "giao thông"),
    ("đi ngược chiều trên đường một chiều", "giao thông"),
    ("chở quá số người quy định trên xe khách", "giao thông"),
    ("đậu xe đỗ xe sai quy định", "giao thông"),
    ("mức phạt lỗi không có gương chiếu hậu", "giao thông"),

    # ĐẤT ĐAI
    ("thủ tục chuyển nhượng quyền sử dụng đất", "đất đai"),
    ("làm sổ đỏ giấy chứng nhận quyền sử dụng", "đất đai"),
    ("tranh chấp ranh giới đất đai giữa hàng xóm", "đất đai"),
    ("bồi thường khi nhà nước thu hồi đất", "đất đai"),
    ("chuyển đổi mục đích sử dụng đất nông nghiệp", "đất đai"),
    ("thuế phí sang tên sổ hồng", "đất đai"),
    ("tặng cho quyền sử dụng đất cho con cái", "đất đai"),
    ("thời hạn sử dụng đất quy định thế nào", "đất đai"),
    ("điều kiện tách thửa đất", "đất đai"),
    ("cho thuê đất đai nhà xưởng", "đất đai"),

    # HÔN NHÂN GIA ĐÌNH
    ("thủ tục ly hôn thuận tình đơn phương", "hôn nhân gia đình"),
    ("chia tài sản chung sau khi ly hôn", "hôn nhân gia đình"),
    ("giành quyền nuôi con dưới 36 tháng tuổi", "hôn nhân gia đình"),
    ("mức cấp dưỡng nuôi con hàng tháng", "hôn nhân gia đình"),
    ("điều kiện đăng ký kết hôn", "hôn nhân gia đình"),
    ("xử lý ngoại tình bạo hành gia đình", "hôn nhân gia đình"),
    ("xác nhận tình trạng hôn nhân độc thân", "hôn nhân gia đình"),
    ("kết hôn với người nước ngoài", "hôn nhân gia đình"),
    ("nhận nuôi con nuôi", "hôn nhân gia đình"),
    ("tài sản riêng trước thời kỳ hôn nhân", "hôn nhân gia đình"),

    # THƯƠNG MẠI
    ("thủ tục thành lập công ty doanh nghiệp", "thương mại"),
    ("giải thể phá sản doanh nghiệp", "thương mại"),
    ("tranh chấp hợp đồng thương mại", "thương mại"),
    ("đăng ký hộ kinh doanh cá thể", "thương mại"),
    ("chuyển nhượng cổ phần vốn góp", "thương mại"),
    ("thay đổi người đại diện theo pháp luật", "thương mại"),
    ("cạnh tranh không lành mạnh", "thương mại"),
    ("nhượng quyền thương mại", "thương mại"),
    ("thủ tục cấp giấy chứng nhận đầu tư", "thương mại"),
    ("bảo hộ nhãn hiệu thương hiệu", "thương mại"),

    # THUẾ
    ("cách tính thuế thu nhập cá nhân", "thuế"),
    ("thuế thu nhập doanh nghiệp phải nộp", "thuế"),
    ("kê khai quyết toán thuế hàng năm", "thuế"),
    ("hoàn thuế gtgt giá trị gia tăng", "thuế"),
    ("trốn thuế bị phạt như thế nào", "thuế"),
    ("thuế môn bài cho hộ kinh doanh mới", "thuế"),
    ("miễn giảm thuế theo quy định", "thuế"),
    ("mã số thuế cá nhân bị khóa", "thuế"),
    ("xuất hóa đơn điện tử", "thuế"),
    ("thuế xuất nhập khẩu hàng hóa", "thuế"),

    # HÀNH CHÍNH
    ("xử phạt vi phạm hành chính nộp ở đâu", "hành chính"),
    ("thủ tục khiếu nại quyết định hành chính", "hành chính"),
    ("thời hạn giải quyết tố cáo", "hành chính"),
    ("cưỡng chế thi hành quyết định xử phạt", "hành chính"),
    ("thủ tục làm căn cước công dân gắn chip", "hành chính"),
    ("đăng ký tạm trú thường trú kt3", "hành chính"),
    ("cấp bản sao trích lục khai sinh", "hành chính"),
    ("xử phạt xây dựng nhà không phép", "hành chính"),
    ("thủ tục xin giấy phép xây dựng", "hành chính"),
    ("chứng thực sao y bản chính", "hành chính"),

    # Y TẾ
    ("quy định về khám chữa bệnh bảo hiểm y tế", "y tế"),
    ("điều kiện mở phòng khám tư nhân", "y tế"),
    ("cấp chứng chỉ hành nghề dược sĩ bác sĩ", "y tế"),
    ("xử lý sai sót y khoa gây hậu quả", "y tế"),
    ("quy định tiêm chủng vắc xin", "y tế"),
    ("bán thuốc không theo đơn phạt bao nhiêu", "y tế"),
    ("an toàn vệ sinh thực phẩm", "y tế"),
    ("kinh doanh trang thiết bị y tế", "y tế"),

    # GIÁO DỤC
    ("quy định bạo lực học đường", "giáo dục"),
    ("điều kiện thành lập trung tâm ngoại ngữ", "giáo dục"),
    ("chế độ cho giáo viên vùng sâu vùng xa", "giáo dục"),
    ("xử lý gian lận trong thi cử", "giáo dục"),
    ("thu học phí sai quy định bị phạt gì", "giáo dục"),
    ("cấp bằng tốt nghiệp chứng chỉ", "giáo dục"),
    ("quyền lợi học sinh sinh viên", "giáo dục"),

    # KHÁC
    ("quy định về nghĩa vụ quân sự đi lính", "khác"),
    ("luật bảo vệ môi trường xả thải", "khác"),
    ("sử dụng vũ khí vật liệu nổ", "khác"),
    ("quản lý chó mèo vật nuôi thả rông", "khác"),
    ("luật an ninh mạng đăng tin giả", "khác")
]

def train_classifier():
    texts, labels = zip(*TRAIN_DATA)
    # Using Word N-Grams + Char N-Grams for highly robust Vietnamese classification
    clf = SkPipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="word", 
            ngram_range=(1, 3), # Catch words and 2-3 word phrases
            min_df=1,
            sublinear_tf=True
        )),
        ("lr", LogisticRegression(max_iter=1000, C=10.0, class_weight="balanced")),
    ])
    clf.fit(list(texts), list(labels))
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    logger.info("Classifier trained and saved with %d examples", len(texts))
    return clf

def predict_law_type(question: str) -> str:
    global _clf
    if _clf is None:
        if MODEL_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                _clf = pickle.load(f)
        else:
            _clf = train_classifier()
    return _clf.predict([question])[0]
