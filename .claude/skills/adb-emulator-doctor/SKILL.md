---
name: adb-emulator-doctor
description: Kết nối và khắc phục sự cố ADB với giả lập Android trước khi chạy tool. Dùng đầu mỗi phiên làm việc có đụng tới thiết bị thật, khi gặp lỗi "device not found" / "offline" / "unauthorized", hoặc khi đổi giả lập/cổng ADB.
---

# ADB / Emulator Doctor

Mục tiêu: thiết bị sẵn sàng (đúng cổng, đúng độ phân giải **1280x720**) trước khi chạy bất kỳ code nào trong `module/device`.

## Quy trình

1. `adb devices` — nếu thiết bị hiện trạng thái `device` (không phải `offline`/`unauthorized`) → nhảy tới bước 4.
2. Nếu danh sách rỗng: xác định giả lập đang mở, connect đúng cổng mặc định:

   | Giả lập | Cổng mặc định |
   |---|---|
   | MuMu 12 | 16384 (instance kế tiếp: +32) |
   | LDPlayer | 5555 + 2×index |
   | BlueStacks 5 | 5555 / 5575 |
   | MEmu | 21503 |

   `adb connect 127.0.0.1:<port>`
3. Nếu `offline`/`unauthorized`: `adb kill-server` → `adb start-server` → connect lại. Vẫn lỗi → nhắc bật ADB/USB debugging trong settings giả lập (MuMu: Settings → Other → ADB).
4. Xác nhận độ phân giải: `adb -s <serial> shell wm size` phải trả về `1280x720`. Sai → **dừng lại**, chỉnh trong settings giả lập rồi restart giả lập (KHÔNG ép bằng `wm size` — game render theo setting giả lập, ép sẽ lệch template).
5. Smoke test: chụp 1 screenshot (`adb -s <serial> exec-out screencap -p > <scratchpad>/adb_test.png` hoặc qua adbutils) và mở xem ảnh có đúng nội dung màn hình không.
6. Nếu serial/cổng khác giá trị trong `config.json` → cập nhật lại config.

## Lưu ý

- Nhiều thiết bị cùng lúc → luôn kèm `-s <serial>` trong mọi lệnh adb.
- Hai bản adb khác version tranh nhau (giả lập thường bundle adb riêng) gây disconnect lặp: kill hết `adb.exe` trong Task Manager, chỉ dùng một bản duy nhất.
- Ghi lại serial + loại giả lập vào ghi chú phiên làm việc để lần sau khỏi dò.
