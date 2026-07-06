# Vì sao SST không hỗ trợ bản PC của Stella Sora (chỉ dùng giả lập Android/ADB)

> Tóm tắt: **client PC Windows của Stella Sora chống tự-động-hoá** — nó lọc bỏ mọi thao tác
> click "nhân tạo" (injected). Điều khiển được màn hình nhưng **không bấm được nút**, nên tự
> động hoá qua client PC là bất khả thi bằng phần mềm an toàn. Vì vậy SST chỉ hỗ trợ **giả lập
> Android qua ADB** (như ALAS / StarRailCopilot / MaaStellaSora). Ngày kết luận: **2026-07-06**.

## Đã thử gì

Mục tiêu ban đầu: cho SST chạy được trên **cả MuMu (ADB) lẫn client PC Windows** (chọn qua config).
Đã dựng đầy đủ một backend PC và khảo sát trực tiếp trên game thật:

| Thành phần | Kết quả |
|---|---|
| **Chụp màn hình** (Windows Graphics Capture) | ✅ Hoạt động tốt — bắt được cả game DirectX, per-window (chỉ chụp cửa sổ game, không lộ desktop), ~250 ms/khung ≈ ngang ADB |
| **Nhận diện** (template matching) | ✅ UI bản PC giống hệt bản mobile → asset 1280×720 tái dùng ~80% |
| **Toạ độ / DPI** | ✅ Quy đổi chuẩn; con trỏ hệ thống tới đúng nút, **con trỏ riêng của game di theo** |
| **Cú click** | ❌ **Bị game nuốt hoàn toàn** — mọi cách đều thất bại |

## Vì sao click không được — nguyên nhân gốc

Đã chẩn đoán từng lớp, loại trừ dứt điểm:

1. **`PostMessage` (WM_LBUTTONDOWN…)** — Unity bỏ qua input dạng message.
2. **`SendInput` / `mouse_event`** (chuột) — gửi **thành công** (`n>0`, `err=0`) nhưng game **phớt lờ**.
3. **`InjectTouchInput`** (giả cảm ứng, vì game là mobile-port) — trả `ACCESS_DENIED`.
4. **Chạy quyền admin (elevated)** — **không đổi**. Vì `err=0` ngay ở tiến trình thường đã chứng
   minh **không phải** vấn đề quyền (UIPI), dù `StellaSora.exe` chạy High-integrity/admin.

Điểm mấu chốt: con trỏ hệ thống di tới đúng nút và **con trỏ riêng của game bám theo** (game đọc
vị trí con trỏ Windows), nhưng **cú click thì bị lọc**. Kết luận: game **lọc bỏ mọi input mang cờ
`LLMHF_INJECTED`** — cờ mà *mọi* lệnh bơm-input từ user-mode đều gắn. Đây là **cơ chế chống bot**.

Chỉ có thể vượt bằng:
- **Kernel driver giả phần cứng** (vd Interception) — **rủi ro khoá tài khoản** (game có anti-cheat),
  phải cài driver kernel, và đi ngược mục tiêu "tool daily an toàn".
- **Thiết bị HID vật lý** (Arduino/vi điều khiển giả chuột) — cần phần cứng riêng.

Cả hai đều **không phù hợp** cho một tool automation cá nhân, an toàn → **loại**.

## Vì sao ADB/emulator không dính vấn đề này

Trên giả lập Android, ADB **bơm input ở tầng hệ điều hành Android** (`input tap`), **nằm ngoài tầm
kiểm soát của game** — game trong sandbox không phân biệt được "chạm thật" hay "chạm từ ADB". Đây
chính xác là lý do **ALAS, StarRailCopilot, MaaStellaSora** đều điều khiển emulator chứ không phải
client PC. SST đi theo hướng đã được chứng minh này.

## Về việc "chạy ngầm" (không chiếm chuột)

Ngay cả khi bỏ qua vấn đề click, client PC **không chạy ngầm được** như ADB: điều khiển chuột PC
bắt buộc chiếm con trỏ + đưa game lên foreground. Đã nghiên cứu các hướng thay thế (RDP loopback,
VM GPU passthrough, virtual desktop, kernel input) — không hướng nào khả thi ổn định trên **1 máy
Windows Home, 1 GPU**. Chạy-ngầm-thật cần **ADB/emulator** hoặc **phần cứng riêng** (PC phụ / VPS GPU).

## Code backend PC được lưu ở đâu

Toàn bộ code + script khảo sát (WGC capture, coordinate/DPI mapping, các thử nghiệm input) được lưu
ở **git branch `archive/pc-backend`** — không nằm trên `main`. Nếu tương lai game gỡ bỏ lớp chống
bot, hoặc dùng thiết bị HID phần cứng, có thể tham khảo lại:

```bash
git checkout archive/pc-backend      # xem code PC đã khảo sát
git checkout main                    # quay lại nhánh chính (ADB-only)
```
