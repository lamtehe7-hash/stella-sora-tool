---
name: survey-and-map-game-flow
description: Khảo sát một luồng chức năng mới trong game (chụp + tài liệu hóa) và giữ docs/game-map.md + Page graph trong module/ui đồng bộ với thực tế. Dùng khi khảo sát flow mới trước khi viết task (daily lần đầu, weekly, event), khi phát hiện màn hình chưa có trong page graph, hoặc user nói "khảo sát flow", "cập nhật page graph", "thêm màn hình mới".
---

# Survey & Map Game Flow

Hai chế độ trong cùng một vòng đời tài liệu hóa màn hình: **khảo sát mới** (flow lớn chưa từng map) và **cập nhật gia tăng** (thêm 1 node/edge). Cả hai đều ghi vào `docs/game-map.md` + Page graph trong `module/ui` — luôn cập nhật CẢ HAI, không để lệch.

## Khảo sát mới (flow lớn)

1. Chuẩn bị: giả lập đúng 1280x720 (chạy `adb-emulator-doctor` nếu chưa chắc), dùng **acc phụ**.
2. Đi tay từng bước của flow. Đặt tên screenshot theo thứ tự thao tác: `screenshots/raw/<feature>/<NN>_<mô_tả_bước>.png` (NN = 01, 02...).
3. Chụp cả **trước và sau** mỗi lần bấm nút quan trọng (2 ảnh/nút).
4. Ghi chú riêng các yếu tố không ổn định: popup ngẫu nhiên, badge đỏ, khác biệt lần-đầu vs lặp-lại, animation chuyển cảnh dài.

## Cập nhật page graph

1. Node mới: đặt tên Page dạng `page_<ten>` trong code, UPPER_SNAKE trong docs — tên ở docs và code phải đối chiếu 1-1.
2. Xác định **toàn bộ** edge vào/ra của node, kể cả nút Back/Close/ESC — bỏ sót chiều quay lại là nguồn lỗi `ui_ensure` điều hướng kẹt phổ biến nhất.
3. Mỗi edge cần 1 Button asset điều hướng: đối chiếu đã crop đúng page nguồn chưa; thiếu → giao lại cho `crop-button-asset` (kèm danh sách nút cần cắt).
4. Cập nhật sơ đồ mermaid trong `docs/game-map.md` VÀ định nghĩa Page/edge trong `module/ui`.
5. **Kiểm chứng bắt buộc**: chạy thử `ui_ensure(page_mới)` từ màn hình chính — tool phải tự điều hướng đến nơi.

## Lưu ý

- Server EN/JP có thể khác layout/text — nếu phát hiện khác biệt, ghi chú ngay vào game-map.md tại node đó.
- Mỗi node ghi kèm 1 screenshot "đại diện" (ảnh sạch không popup) — sau này dùng làm ảnh test cho asset.
- Khảo sát xong flow, bàn giao: danh sách node/edge mới + danh sách asset cần crop.
