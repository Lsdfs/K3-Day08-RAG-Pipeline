# CP5 — Validation & Feedback Log

## Testers (5 people from outside the team)

| # | Name | Role | Date |
|---|------|------|------|
| 1 | Quang Huy | K3 Student | 04/08/2026 |
| 2 | Yen Khanh | K3 Student | 04/08/2026 |
| 3 | Quang Tung | K3 Student | 04/08/2026 |
| 4 | Diem Thanh | K3 Student | 04/08/2026 |
| 5 | Tuan Trung | K3 Student | 04/08/2026 |

## Feedback Entries

### 1. Quang Huy — "Thư viện mở cửa lúc mấy giờ?"
- **Feedback**: "Trả lời đúng giờ mở cửa nhưng không nói rõ cuối tuần khác ngày thường."
- **Action**: Added weekend hours to library_services.md data file ✅ (changelog #1)

### 2. Yen Khanh — "Học phí bao nhiêu?"
- **Feedback**: "Câu trả lời chung chung, không nói cụ thể số tiền. Em cần con số chính xác."
- **Action**: Reviewing data quality — tuition amounts in data file. Must verify chunk contains the number.

### 3. Quang Tung — "Làm sao để đăng ký môn học?"
- **Feedback**: "Bot bảo không tìm thấy thông tin. Em nghĩ bot nên gợi ý tìm ở đâu thay vì từ chối."
- **Action**: Updated system prompt to suggest alternative queries when info not found ✅ (changelog #2)

### 4. Diem Thanh — "Có học bổng nào cho sinh viên không?"
- **Feedback**: "Câu trả lời có liệt kê học bổng nhưng thiếu điều kiện GPA cụ thể. Nên bổ sung."
- **Action**: Added scholarship GPA thresholds to data ✅ (changelog #3)

### 5. Tuan Trung — Tested Vietnamese input "ký túc xá giá bao nhiêu"
- **Feedback**: "Trả lời OK. Có trích dẫn nguồn. Tốc độ nhanh."
- **Action**: No change needed — positive feedback.

---

## Changelog

| # | Change | Based on feedback from | Date |
|---|--------|----------------------|------|
| 1 | Added weekend hours to library data | Quang Huy | 04/08/2026 |
| 2 | Updated system prompt to suggest alternatives when no info found | Quang Tung | 04/08/2026 |
| 3 | Added GPA thresholds to scholarship data | Diem Thanh | 04/08/2026 |

---

## Willing Users (from CP1)

1. Quang Huy — confirmed will test ✅
2. Tuan Trung — confirmed will test ✅
3. Diem Thanh — confirmed will test ✅
