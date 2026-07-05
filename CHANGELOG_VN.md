# Nhật ký thay đổi — Stella Sora Tool

## v0.1.1 (2026-07-05) — pre-release

### Sửa lỗi
- **Cleanup crash** (assertion `matchTemplate`). OpenCV ném `(-215) _img <= _templ` mỗi khi template
  lớn hơn vùng tìm — xảy ra trong `ui_current_page` và làm dừng task Cleanup. Đã sửa: nới vùng `area`
  của `GRANT_CHECK` cho vừa template, và gia cố `Button.match` — bỏ qua (kèm cảnh báo 1 lần) thay vì
  crash khi template lớn hơn vùng tìm, để một asset crop lệch không còn làm hỏng nhận diện page.

## v0.1.0 (2026-07-05) — pre-release

Bản phát hành đầu tiên. Công cụ **tự động hoá công việc hằng ngày (daily)** cho game **Stella Sora (bản EN)** chạy trên giả lập Android. Bản đóng gói portable cho Windows 64-bit — **không cần cài Python**.

> ⚠️ Đây là bản **pre-release** đầu tiên — tool vẫn đang phát triển, có thể còn thay đổi ở các phiên bản sau.

### Tổng quan

- Giao diện **desktop** (cửa sổ WebView2) — bật/tắt từng task, bấm **Start** là scheduler tự chạy hết chuỗi daily rồi hẹn giờ cho ngày hôm sau.
- **Song ngữ** giao diện: Tiếng Việt / English (đổi ngay ở màn Home).
- Điều khiển game qua **ADB** trên giả lập (nhận diện màn hình bằng ảnh mẫu, không tap mù).
- Cấu hình cá nhân lưu tại `config/` cạnh file exe; log xoay vòng tại `log/`.

### Các task tự động

Scheduler chạy lần lượt theo thứ tự dưới đây, mỗi task tự hẹn lần chạy kế tiếp (đa số theo mốc **reset daily**):

| # | Task | Tự động làm gì |
|---|------|----------------|
| 1 | **Login** | Mở game (nếu chưa chạy) và đưa về màn hình chính, vừa chờ vừa đóng popup; xử lý cả trường hợp "tap to start" khi rớt mạng. |
| 2 | **Mail** | Vào hộp thư, **Claim All** nhận toàn bộ đính kèm, đóng popup thưởng. |
| 3 | **Dispatch** *(Commission)* | Thu đội phái đi đã về (**Claim All**), rồi lấp đầy 4 slot: chọn commission → **Quick Select** đội hợp yêu cầu → chọn mốc **20h** (thưởng tối đa) → **Accept**. Lặp lại sau mỗi 4 giờ. |
| 4 | **Shop** | Nhận **hộp quà daily miễn phí** ở cửa hàng. |
| 5 | **Bounty Trial** | Tiêu **Vigor** bằng Trial Quick Battle (mặc định Basic Trial). Tự bỏ qua nếu độ khó chưa mở, tự hẹn lại nếu thiếu Vigor. |
| 6 | **Ascension** | Chạy **1 run Monolith Quick Battle** (roguelike): tự đánh, chọn thẻ theo ưu tiên, mua/upgrade ở shop theo chiến lược, lưu record. Một run ~4–12 phút. |
| 7 | **Event Daily** | **Quick Battle sweep** ở stage sự kiện đang mở theo Vigor, rồi quét **Event Missions** nhận quà. |
| 8 | **Grant** | Nhận quà **Startup Grant** (Company Goal + Grant Milestone) khi có sẵn. |
| 9 | **Daily Reward** | Nhận **nhiệm vụ daily** + **mốc điểm hoạt động**. |
| 10 | **Cleanup** | Đưa game về màn hình chính; tuỳ chọn đóng hẳn game sau khi xong. |

### Tuỳ chỉnh được gì

**Chung**
- Serial ADB & đường dẫn `adb.exe` của giả lập.
- Giờ **reset daily** (UTC) — mặc định `11:00` UTC.
- Cleanup xong **đóng game** hay **giữ ở màn hình chính** (mặc định: giữ).
- Ngôn ngữ giao diện (vi/en).

**Ascension** *(run Monolith)*
- Số run mỗi lần chạy; chọn **map** (Currents / Dust / Storm / Misstep) và **squad**.
- Ứng xử khi preset Potential chưa gắn: cảnh báo / bỏ qua / dừng.
- **Ưu tiên chọn thẻ**: theo mức tăng cấp / thẻ super rare / thẻ trái nhất.
- Chiến lược shop: chỉ mua Melody khi có Harmony Skill, mốc dừng enhance, coin dự trữ, refresh kệ/refresh thẻ, chế độ rút gọn (Brief), lưu Record, timeout run.

**Bounty Trial**
- Loại trial: Basic / Tier-up / Skill / Emblem.
- Độ khó: giữ mức game nhớ (0) hoặc chỉ định 1–6.

**Event Daily**
- Chọn **stage**: để trống = stage cao nhất, hoặc chỉ định (vd `1-12`).
- Số trận: `0` = đánh tối đa theo Vigor, hoặc đúng N trận.

### Yêu cầu

- **Windows 64-bit.**
- Giả lập Android có **ADB** (khuyến nghị **MuMu Player**; đã test với MuMu Global).
- Game **Stella Sora (EN)** — package `com.YoStarEN.StellaSora` — đã cài & đăng nhập trên giả lập.

### Cài & chạy

1. Tải **`StellaSoraTool-v0.1.0-win64.zip`** ở phần Assets của release.
2. **Giải nén cả thư mục** ra ổ đĩa — giữ nguyên `app.exe`, `_internal/` và `assets/` cạnh nhau.
3. Mở giả lập, bật ADB, đăng nhập game về màn hình Home.
4. Chạy **`app.exe`**.
5. Lần đầu: vào **Cấu hình** nhập **Serial ADB** (vd `127.0.0.1:16384`) và **đường dẫn adb**.
6. Bật các task muốn chạy → bấm **Start**.

### Lưu ý

- **Mặc định tắt sẵn** 3 task tốn tài nguyên / cần cấu hình trước: **Ascension**, **Bounty Trial**, **Event Daily**.
- Nhận diện dựa trên ảnh mẫu **bản EN**; server/ngôn ngữ khác có thể không khớp.
- Không di chuyển `_internal/` hay `assets/` ra khỏi thư mục chứa `app.exe`.
- `config/` và `log/` tự tạo cạnh `app.exe` khi chạy lần đầu.
