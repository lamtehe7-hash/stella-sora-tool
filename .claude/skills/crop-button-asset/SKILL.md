---
name: crop-button-asset
description: Cắt template button từ screenshot thành asset và sinh code Button đúng convention của dự án. Dùng khi task cần một nút/template chưa tồn tại, khi asset hiện tại miss-detect, hoặc user nói "crop asset", "cắt ảnh nút", "thêm template button".
---

# Crop Button Asset

Chu trình chuẩn: screenshot nguồn → xác định page → cắt vùng → đặt tên → sinh code Button → test match. Sai 1 ký tự tên file/biến là `appear()` fail âm thầm, nên tuân thủ convention là bắt buộc.

## Quy trình

1. **Nguồn ảnh**: dùng screenshot có sẵn trong `screenshots/raw/`, hoặc chụp mới `adb exec-out screencap -p` — bắt buộc đúng độ phân giải 1280x720 và đúng server đang hỗ trợ.
2. **Xác định page**: nút thuộc page nào trong page graph (`module/ui` + `docs/game-map.md`). Page chưa tồn tại → **dừng**, chạy skill `survey-and-map-game-flow` trước.
3. **Convention đặt tên**: `assets/<server>/<page>/<BUTTON_NAME>.png` — `BUTTON_NAME` viết UPPER_SNAKE_CASE, **khớp chính xác 100%** tên biến Button trong code.
4. **Cắt vùng**: chọn vùng tối thiểu bao trọn phần TĨNH của nút (icon/chữ cố định). TRÁNH đưa vào vùng có số/badge/đếm ngược động — chúng làm giảm match-rate theo thời gian.
5. **Sinh code**: tạo `Button(file=..., area=(x1, y1, x2, y2), threshold=0.85)` (theo đúng dạng class Button trong `module/base`), đặt trong file assets của module/task tương ứng.
6. **Test bắt buộc trước khi coi là xong**: chạy `cv2.matchTemplate` với asset mới trên:
   - ≥2 screenshot CÓ nút → score phải > threshold;
   - ≥1 screenshot KHÔNG có nút (page khác) → score phải < threshold.
7. Nếu nút này dẫn sang màn hình mới chưa map → chuyển tiếp sang `survey-and-map-game-flow` để thêm node/edge.

## Lưu ý

- Threshold mặc định 0.85; chỉ hạ khi nút có animation nhẹ, và ghi chú lý do ngay tại chỗ khai báo.
- Một nút xuất hiện ở nhiều page (VD nút Back chung) → đặt ở thư mục page phổ biến nhất, KHÔNG duplicate ảnh.
- Asset thay thế bản cũ (sau patch) → giữ nguyên tên biến, backup bản cũ theo quy trình `fix-broken-assets-after-patch` (skill sẽ tạo ở đợt sau).
