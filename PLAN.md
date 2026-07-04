# Plan: Tool tự động daily cho Stella Sora (kiểu ALAS)

> Mục tiêu: xây dựng tool tự động làm daily cho **Stella Sora** (Yostar), mô phỏng kiến trúc của **AzurLaneAutoScript (ALAS)**.
> Ngày lập: 2026-07-03

---

## 1. Kết quả nghiên cứu sơ bộ

### 1.1. Kiến trúc ALAS (LmeSzinc/AzurLaneAutoScript)

Python bot điều khiển giả lập Android qua ADB, nhận diện màn hình bằng template matching (OpenCV) + OCR. Kiến trúc **5 tầng**:

| Tầng | Vai trò | Module chính |
|---|---|---|
| 1. Config & UI | WebUI (pywebio), sinh config từ YAML | `module/config`, `module/webui` |
| 2. Orchestration | Vòng lặp chính, dispatch task theo scheduler | `AzurLaneAutoScript`, `AzurLaneConfig`, `Function` |
| 3. Task Execution | Logic từng nhiệm vụ (Campaign, Commission, Reward...) | `module/campaign`, `module/reward`... |
| 4. UI Detection | Nhận diện màn hình: template button, OCR, điều hướng page | `module/ui`, `module/ocr`, assets |
| 5. Device Control | ADB: screenshot, click, swipe | `module/device` |

Điểm cốt lõi:
- **Task + Scheduler**: mỗi task độc lập, chạy xong tự đặt `next_run` (VD: Commission xong hẹn lại sau ~20h). Scheduler chọn task đến hạn có ưu tiên cao nhất, chạy tuần tự, treo máy 24/7 được.
- **Asset system**: hàng nghìn ảnh template nút bấm, có tool `button_extract` tự sinh code asset từ ảnh.
- **Base methods**: `wait_until_appear`, `appear_then_click`, `ui_ensure(page_x)` — mọi task viết trên các primitive này.

### 1.2. StarRailCopilot (SRC) — nên học theo bản này thay vì ALAS gốc

Cùng tác giả LmeSzinc, là **ALAS hiện đại hóa**:
- Config chuyển sang **pydantic** (ALAS cũ dùng code generator ~4000 dòng).
- OCR mới (PaddleOCR thay cnocr/mxnet đã chết).
- Asset management tốt hơn (button_extract của ALAS chậm với 4000+ template).

→ **Khi thiết kế tool mới, đọc SRC làm chuẩn kiến trúc, đọc ALAS để hiểu ý tưởng gốc.**

### 1.3. Stella Sora

- Yostar, top-down light-action RPG, có trên **iOS/Android/PC client riêng**, chạy tốt trên giả lập (MuMu, LDPlayer, BlueStacks, MEmu).
- Daily loop chính (cần khảo sát lại trong game để chốt):
  - Điểm danh/đăng nhập, nhận thư + quà bạn bè (friend gifts, tối đa 30 hồi stamina/ngày)
  - Tiêu **Vigor** (stamina) vào Ascension/Bounty Trials
  - **Commissions/Dispatch**: phái đội đi ~20h, tối đa 4 đội
  - Daily missions → nhận 100 Stellanite Dust
  - Shop: mua đồ free/rẻ hàng ngày
  - (Weekly) Boss Blitz, shop tuần...

### 1.4. ⚠️ Tool đã tồn tại: MaaStellaSora

**[MaaStellaSora](https://github.com/MaaStellaSora/MaaStellaSora)** — trợ thủ Stella Sora chạy trên **MaaFramework** (framework tự động hóa nhận diện ảnh của cộng đồng MAA), đã có auto điểm danh + dọn daily.

→ Ba lựa chọn hướng đi (chốt ở Phase 0):
- **A. Dùng/fork MaaStellaSora**: nhanh nhất, có sẵn template + pipeline; code theo chuẩn MaaFramework (pipeline JSON), tiếng Trung.
- **B. Tự viết Python theo kiến trúc ALAS/SRC** *(khuyến nghị nếu muốn học + toàn quyền tùy biến)*: chậm hơn nhưng hiểu sâu, dễ mở rộng theo ý mình; có thể "mượn" template ảnh + flow từ MaaStellaSora làm tài liệu tham khảo.
- **C. Viết project mới trên MaaFramework**: giữa A và B — framework lo tầng device/vision, mình chỉ viết pipeline + custom action.

---

## 2. Quyết định cần chốt (Phase 0)

| # | Câu hỏi | Trạng thái |
|---|---|---|
| 1 | Nền tảng chạy game? | ✅ **ĐÃ CHỐT (2026-07-04): Giả lập Android qua ADB**, ưu tiên **MuMu 12** (1280x720, screenshot nhanh qua nemu_ipc). |
| 2 | Hướng đi A/B/C? | ✅ **ĐÃ CHỐT (2026-07-04): Hướng B** — tự viết Python theo kiến trúc ALAS/SRC, mục tiêu học + sở hữu tool tùy biến riêng. MaaStellaSora chỉ dùng làm tài liệu tham khảo. |
| 3 | Server game? | ✅ **ĐÃ CHỐT (2026-07-04): Global (EN)** — thư mục asset `assets/en/`; có thể tham khảo ảnh template `base+en` của MaaStellaSora. |
| 4 | Phạm vi v1? | Chỉ daily (login → mail → dispatch → tiêu stamina → shop → daily reward). KHÔNG tự đánh combat thời gian thực — chỉ dùng sweep/quick-clear nếu game có. |

**Rủi ro cần chấp nhận**: (1) tài khoản có thể vi phạm ToS Yostar → dùng acc phụ khi dev; (2) game update UI → vỡ template, cần quy trình cập nhật asset nhanh; (3) Stella Sora là action game — nếu stage không có sweep thì auto combat rất khó, v1 né hoàn toàn.

---

## 3. Lộ trình

### Phase 1 — Nghiên cứu ALAS/SRC ✅ (hoàn thành 2026-07-04)
- [x] Clone `LmeSzinc/AzurLaneAutoScript` và `LmeSzinc/StarRailCopilot` (→ `reference/`)
- [x] Đọc theo thứ tự: `module/device` (screenshot/control) → `module/base` (Button, Timer, `wait_until_appear`) → `module/ui` (page graph, `ui_ensure`) → `module/config` + scheduler → 1 task mẫu (VD Commission/Reward của ALAS, Daily của SRC)
- [x] Ghi chú: cách họ chống flaky (retry, Timer, interval click), cách tổ chức assets
- [x] Clone `MaaStellaSora/MaaStellaSora` — đọc pipeline JSON để lấy **danh sách task daily + tên màn hình** họ đã map sẵn → được **12 task daily + page graph Home⇄10 trang con**

**Deliverable**: ✅ `docs/alas-notes.md` — 7 phần ghi chú kiến trúc + phần 8 phản biện (việc còn thiếu/mâu thuẫn cần chốt/đơn giản hóa thêm trước Phase 3).

### Phase 2 — Khảo sát game (1 buổi)
- [x] Cài Stella Sora trên giả lập, fix độ phân giải 1280x720 → **đã có sẵn (xác minh 2026-07-04)**: MuMu Player Global tại `E:\MuMuPlayerGlobal`, adb kèm theo `nx_device\12.0\shell\adb.exe`, serial `127.0.0.1:16384`, game `com.YoStarEN.StellaSora`, screenshot ra đúng 1280x720. ⚠️ Máy có 2 bản adb (MuMu + toolkit ALAS ở `E:\Games\AzurLaneAutoScript`) — tool chỉ dùng 1 bản cố định.
- [x] Khảo sát daily loop qua ADB (2026-07-04): 8 trang chụp + map (home, mail, missions, commission, shop, grant, friend, heartlink, menu) → `screenshots/raw/`
- [x] Page graph hiện thực trong `module/ui/pages.py` + 20 asset crop vào `assets/en/` — **nav test ĐẠT** (home⇄missions, home⇄heartlink)
- [x] Go hub khảo sát xong (2026-07-04 tối): go/bounty/basic_trial/ascension vào page graph, sweep Basic Trial xác minh thật
- [ ] Còn nợ: Event hub, flow tái phái commission (đội về ~trưa 05/07), xác minh nhánh Shop chưa-nhận sau reset, catalog popup login, xác minh giờ reset EN — chi tiết mục "Việc còn nợ" trong game-map.md

**Deliverable**: ✅ `docs/game-map.md` + kho screenshot. Phát hiện then chốt: phím Back Android vô dụng — điều hướng 100% bằng nút in-game (GOTO_HOME 377,42; Heartlink thoát bằng nút nguồn).

### Phase 3 — Skeleton framework (2–3 buổi)
```
stella_sora_tool/
├── module/
│   ├── device/        # ADB connect, screenshot (adbutils), click/swipe (maatouch hoặc ADB input)
│   ├── base/          # Button, Template, Timer, base task: appear(), appear_then_click(), wait_until_appear()
│   ├── ui/            # Page graph + ui_ensure(page) điều hướng tự động
│   ├── config/        # pydantic model + config.json người dùng
│   └── ocr/           # (sau) PaddleOCR đọc số stamina/số lượng
├── tasks/             # mỗi daily 1 module
├── assets/<server>/   # ảnh template theo page
├── dev_tools/         # tool crop asset từ screenshot
└── sst.py             # entry: vòng lặp scheduler (đổi tên từ alas.py, tránh nhầm với ALAS thật trên máy)
```
- [x] Device layer: kết nối ADB (adbutils), screenshot **0.28s/ảnh**, click; đã test với MuMu thật (2026-07-04)
- [x] Template matching bằng OpenCV (`cv2.matchTemplate`, threshold 0.85) — self-match test ĐẠT, sai số 0px
- [x] Primitive `appear / appear_then_click / wait_until_appear / ui_ensure` (BFS page graph + popup closers)
- [x] Dev tool crop asset: `dev_tools/crop.py` — crop từ screenshot → lưu assets/en/ + in code Button

**Milestone kiểm chứng**: script mở game → vào menu chính. ✅ ĐẠT 2026-07-04 (`python sst.py Login` → "Đã vào màn hình chính", tự hẹn next_run). Môi trường: venv Python 3.11 tại `venv/`, deps trong `requirements.txt`.

### Phase 4 — Task daily (mỗi task 0.5–1 buổi, làm tuần tự)
1. [x] `Login` — mở game, vượt popup, về màn hình chính — ĐẠT 2026-07-04 (catalog popup cold-start còn nợ); 04/07 đêm: thêm `LOGIN_TAP_START` nhận diện màn title khi Network Error (biến thể 1 nút Confirm) đá game về title giữa phiên
2. [x] `Mail` — Claim All thư — ĐẠT trên game thật 2026-07-04 (quà bạn bè tách sang `FriendGift`)
3. [~] `Dispatch` — claim-only ĐẠT 2026-07-04 (nhánh xám, tự hẹn 4h); TÁI PHÁI chưa code — khảo sát khi đội về (~trưa 05/07)
4. [x] `Stamina` — Basic Trial (Bounty) Quick Battle sweep max Vigor — ĐẠT sweep thật 2026-07-04 (20⚡/battle Difficulty 6; game nhớ difficulty đã chọn)
5. [x] `Shop` — nhận quà daily free (detect pill "Claimed") — nhánh đã-nhận ĐẠT 2026-07-04; nhánh chưa-nhận chờ xác minh sau reset
6. [x] `DailyReward` — Claim All daily missions + mốc điểm — ĐẠT 2026-07-04 cả nhánh có thưởng (popup thưởng đóng bằng blind-tap 640,150) lẫn nhánh Claim All xám
7. [x] `Cleanup` — về màn hình chính, (config `close_game_on_cleanup`) đóng game — ĐẠT 2026-07-04
8. [x] `Ascension` — Quick Battle run Monolith (1 vé/run, không tốn Vigor, mission "Participate in Ascension") — v1 ĐẠT run thật 2026-07-04 đêm; **v2 2026-07-05** (khảo sát shop live + wiki/guide): (a) nhiều thẻ 👍 → chọn theo **mức tăng level** đọc từ thanh "Lv. N"/"Lv. A ▶ B" (OCR template số 1-6, màu navy/xanh; thẻ 👍 không thanh level = Super Rare core → ưu tiên tuyệt đối; hoà → trái nhất); (b) **phòng Shop** (1-6/2-9/3-8 + phòng cuối big-sale): mua 4 Potential Drink (+1 thẻ/level, chọn 1-trong-3) rồi 4 Melody x5 (+5 note), phòng cuối refresh kệ (100 coin, ≤2 lượt) mua tiếp; (c) **Enhance** mọi phòng shop (Free lần đầu/phòng, giá tăng dần) tới hết coin — Starcoin mất trắng khi rời nên tiêu hết là tối ưu (wiki). Guide: sheet cộng đồng (thẻ build xếp theo ưu tiên; "Level 1: khỏi nâng quá base / Level 1+: nâng càng nhiều càng tốt / Level 6: luôn max"). **v3 2026-07-05** (tối ưu chiến lược, ảnh Img_test): OCR số dư Starcoin + giá slot (`coin_digits`, sinh bởi `dev_tools/build_coin_digits.py`, validate `dev_tools/validate_shop_parser.py` 18/18 PASS); mua **SALE trước** rồi rẻ trước; **Melody chỉ mua khi cần thiết** (dialog có panel "Relevant Harmony Skills" — cùng nguồn thông tin với viền xanh icon note trong Monolith Bag▸Disc Skills nhưng đọc ngay trong dialog); luôn **chừa 360 coin** để Enhance đạt mốc 180 (Free→60→120→180), giữa run dừng sau mốc 180 để dành coin, **phòng cuối vét sạch** (mua → refresh kệ → enhance hết → mua vét bỏ lọc); màn chọn thẻ không 👍 → **refresh bộ thẻ 1 lần** (40 coin, nút ↻ chỉ có ở màn nhận thẻ mới). ✅ **2 run thật 2026-07-05 hoàn tất** (4 phòng shop/run, Save Record OK): SALE-first + lọc Melody theo panel + reserve 360 + refresh thẻ 40 + refresh kệ phòng cuối + burn vét — tất cả chạy đúng, số học coin khớp 100% (chữ số '3' navy giá 320 đọc đúng cả kệ lẫn dialog). Phát hiện + vá qua 2 run: (1) **chỉ phòng đầu run có bậc Free**, phòng sau vào thẳng 60 → giá enhance đọc trực tiếp từ dòng option (`enhance_cost` + template `ENHANCE_FREE`, fallback = bậc trước +60); (2) **giá kệ đọc sai lẻ tẻ** → `dialog_price` đọc lại giá chuẩn trong dialog trước khi chốt mua; (3) **pill coin có animation đếm** → OCR None thoáng qua làm dừng enhance sớm → retry `_read_coins_stable`; (4) đối chiếu số dư sau mỗi giao dịch + dump `log/asc_audit/`. Validator offline 25/25 PASS. Bản vá (3)(1-fallback) áp sau run 2 nên chờ run lịch kế xác nhận live, nhưng logic quyết định không đổi.
9. [ ] (v1.5) `FriendGift` — khảo sát tab Friend List

### Phase 5 — Scheduler + config ✅ (có sẵn từ Phase 3-4, xác nhận 2026-07-04)
- [x] Mỗi task có `enable` + `next_run`; scheduler chạy task đến hạn, xong tự hẹn lần sau (daily → `task_delay(server_reset=True)`; Dispatch/Stamina thiếu tài nguyên → hẹn phút)
- [x] Config `config/stella.json` (pydantic validate), log + screenshot khi lỗi (`save_error_log` cho cả TaskError)
- [x] Chế độ chạy: `python sst.py` loop 24/7, `python sst.py <Task>` chạy 1 task

### Phase 6 — Hoàn thiện (tùy nhu cầu)
- [x] GUI WebUI kiểu ALAS (pywebio, 2026-07-04): `python gui.py` → http://localhost:22270 — bật/tắt task, Chạy ngay, Start/Stop scheduler (dừng sau task hiện tại), sửa config, log trực tiếp. Scheduler tách ra `module/scheduler.py` (thread + `device_lock`), sst.py CLI vẫn như cũ.
- [x] Đóng gói exe (2026-07-04): `dev_tools/build_exe.ps1 -Web` → `dist/SST/SST.exe` (~190MB onedir, assets/ config/ log/ nằm cạnh exe — ROOT tự nhận chế độ frozen). Đã test: exe serve web OK, tự tạo log/. ⚠️ exe copy sang máy khác cần sửa Cấu hình (serial + đường dẫn adb) cho giả lập máy đó; đóng exe = kill giữa chừng, nên bấm Dừng trước.
- [x] App desktop kiểu Alas (2026-07-05): `python app.py` hoặc `dev_tools/build_exe.ps1` → `dist/app/app.exe` (~191MB, windowed không console). UI tĩnh `assets/gui/` (HTML/CSS/JS) chạy trong cửa sổ WebView2 qua pywebview, bridge `js_api` (poll 1s: trạng thái + log). Layout: rail Home/sst/Cấu hình + sidebar Overview/Task + cards Scheduler-Đang chạy-Sẵn sàng-Chờ đến hạn + panel Log (Auto Scroll), theme Sáng/Tối. Đã test cả dev lẫn exe. gui.py (pywebio web) vẫn giữ nguyên.
- [ ] Auto-update asset khi game patch
- [ ] (Mở rộng) task weekly, event

---

## 4. Tech stack đề xuất

| Thành phần | Chọn | Lý do |
|---|---|---|
| Ngôn ngữ | Python 3.11+ | Theo ALAS/SRC, hệ sinh thái CV tốt |
| Device | `adbutils` (+ maatouch nếu cần click nhanh) | Chuẩn ALAS/SRC |
| Vision | OpenCV template matching | Đơn giản, đủ cho UI tĩnh |
| OCR | PaddleOCR (chỉ khi cần đọc số) | SRC đã chuyển sang, cnocr/mxnet đã chết |
| Config | pydantic v2 + JSON | Theo SRC |
| Giả lập | MuMu 12 hoặc LDPlayer, 1280x720 | ALAS/SRC hỗ trợ tốt nhất |

## 5. Skill nội bộ dự án (`.claude/skills/`)

Đã cài đợt 1 (2026-07-04): `adb-emulator-doctor`, `crop-button-asset`, `survey-and-map-game-flow`.

Tạo sau khi skeleton Phase 3 chốt cấu trúc thư mục thật: `new-daily-task-scaffold`, `run-task-debug`, `fix-flaky-task`, `add-config-field`, `fix-broken-assets-after-patch`, `asset-health-audit`, `release-package`. Bổ sung khi tới phase tương ứng: `ocr-field-calibration` (Phase 4-5), `scheduler-handoff-check` (Phase 5).

Repo tham khảo clone tại `reference/` (ALAS, StarRailCopilot, MaaStellaSora) — không sửa code trong đó, chỉ đọc.

## 6. Nguồn tham khảo
- ALAS: https://github.com/LmeSzinc/AzurLaneAutoScript (wiki DeepWiki: https://deepwiki.com/LmeSzinc/AzurLaneAutoScript)
- StarRailCopilot: https://github.com/LmeSzinc/StarRailCopilot
- MaaFramework: https://github.com/MaaXYZ/MaaFramework
- MaaStellaSora: https://github.com/MaaStellaSora/MaaStellaSora
- Stella Sora official: https://stellasora.global/
