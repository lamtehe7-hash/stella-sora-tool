# Ascension — Roadmap cải thiện từ data capture 26/70 (2026-07-07)

> Nghiên cứu dựa trên **data thật**: phiên capture `data/ascension_capture/20260707_140335`
> (26/70 run, Storm/Diff8/Squad1, POWER, 4.8h). Phân tích định lượng toàn bộ `session.log`
> (8989 dòng) + `frames.jsonl` (9136 frame) + soi frame PNG thật, verify đối kháng đa agent.
> Bổ trợ cho `docs/ascension-strategy.md` (cơ chế & chiến lược nền). Chỉ giữ finding đã **confirmed**
> và đề xuất **không regress**. Trạng thái: nghiên cứu XONG, chưa code (trừ khi ghi rõ).

## TL;DR — thứ tự làm

1. **[P0] ✅ ĐÃ CODE** — Retry/reconnect ADB trong `module/device/adb.py::Adb.shell()`. Verify offline
   3 case PASS (rớt-rồi-hồi-phục / cạn-retry→RequestHumanTakeover / lỗi-logic không bị nuốt). Còn nợ:
   **verify LIVE** (`adb disconnect` giữa 1 phiên `--runs 70` để xác nhận tự phục hồi thật).
2. **[P1] Fix event leak "random-trinket gamble"** — leak POWER lớn nhất đã định lượng (~24% event-click).
3. **[P2] OCR enhance giá đỏ / card level flicker** — bug thật nhưng guard hiện tại hấp thụ phần lớn;
   effort thấp, đòn bẩy nhỏ.
4. **[P3] Đảo thứ tự vét phòng cuối** — cần chốt thiết kế (đánh đổi POWER-baseline ↔ Record) trước khi code.
5. **[Polish] Quiz template-match, difficulty=0 live-test, observability** — hoãn/song song.

## Số liệu cứng (26 run)

| Chỉ số | Giá trị | Diễn giải |
|---|---|---|
| WARNING tổng | 116 | **112 là độ tin cậy OCR** (80 giá enhance, 20 card, 12 coin) |
| Enhance đọc giá | 388 lần, **80 fail (21%)** | fallback ước tính `last+60` |
| Event chọn | 171 lần: 95 default-bottom / 76 item-free | ~24% là **leak gamble** bị đánh nhầm |
| Card Select | 1208 lần, 20 dao động (1.7%) | OCR level chập chờn |
| Coin dư cuối run | **median 34** (run26=1776 = artifact crash) | enhance-until-broke tiêu coin tốt → **KHÔNG phải leak** |
| Quiz nhận diện | **0** | tool bấm mù Choice Domain |
| Difficulty | ép =8 | nhánh auto (=0) **không exercise** phiên này |

---

## (1) Reliability — SỬA để hoàn tất 70 run

### [P0] ✅ ĐÃ CODE — Retry + reconnect ADB khi transport rớt
> Implement 2026-07-07 tối: bọc `Adb.shell()` với `_ADB_RETRYABLE=(AdbError,OSError,EmulatorNotRunningError)`,
> `_RETRY_BACKOFF=(2,5,10)s`, set `_device=None` mỗi lần fail (property `.device` tự reconnect lần sau),
> cạn → `RequestHumanTakeover`. **Khác pseudo-code workflow**: gộp `EmulatorNotRunningError` vào set retryable
> để tránh lỗi property `.device` re-raise khi reconnect trúng lúc giả lập chưa sẵn sàng. Test offline PASS.
- **File/hàm**: `module/device/adb.py::Adb.shell()` — **điểm chốt DUY NHẤT** mọi lệnh ADB
  (tap/swipe/screenshot/app_*) đi qua. Bọc ở đây → mọi call site tự động được bảo vệ, không sửa `device.py`
  hay `tasks/`.
- **Thiết kế**: retry với whitelist `(adbutils.AdbError, OSError)`, backoff `(2, 5, 10)s`; **set
  `self._device = None` trước khi gọi lại `self.connect()`** (nếu không, `device` property giữ socket cũ đã
  'closed' → lặp lỗi vô hạn); cạn retry → `raise RequestHumanTakeover`. `connect()` (dòng 19-32) tái dùng
  nguyên vẹn (đã đủ start-server + connect + verify + tạo lại `_device`).
- **Effort S · Rủi ro thấp** (đã verify):
  - Các exception logic (`TaskError`/`GameStuckError`/`GameTooManyClickError`/`RequestHumanTakeover`/
    `EmulatorNotRunningError`) **không** phải subclass `AdbError`/`OSError` → whitelist không nuốt nhầm.
  - Điểm crash thật (`_buy_slot` mở dialog slot) double-tap **vô hại**; nếu double-tap trúng nút BUY thì
    guard lệch-coin sẵn có (ascension.py:1084-1091) log WARNING, không nuốt âm thầm.
  - ADB chỉ là kênh điều khiển — transport rớt **không** ảnh hưởng tiến trình game/UI trên thiết bị →
    reconnect giữa dialog shop an toàn, không desync.
- **Bằng chứng**: traceback `_launch_20260707_140334.out.log` dòng 8960-8988 — `AdbError('closed')` từ
  `check_okay()` xuyên `_buy_slot:1050 → click_xy → tap → shell`, không bị bắt → dừng session ở 26/70 sau
  17286s chạy sạch. **Nguyên nhân DUY NHẤT.**
- **Regression check**: chạy `ascension_capture.py --runs N`, cố tình `adb disconnect <serial>` giữa chừng →
  kỳ vọng WARNING "reconnect" + session tự phục hồi không crash.

### [P2, tuỳ chọn] Checkpoint tiến độ giữa run
`tasks/ascension.py::run()` sau `done += 1` (dòng 626): ghi `data/ascension_state.json`
(runs_done/map/difficulty/squad) để nếu retry cạn (giả lập crash thật) biết còn bao nhiêu run. Không bắt buộc
— retry ở tầng `shell()` là trong suốt, vòng lặp Python vẫn sống nguyên state giữa chừng. Chỉ cần khi tần
suất rớt ADB thật sự cao (hiện mới 1 lần / 26 run / 4.8h).

---

## (2) Nâng chất lượng quyết định — POWER/leak

### [P1] Event leak "random-trinket gamble" (~24% event-click)
- **Root cause**: `event_tag_has_coin` (ascension.py:513-521) chỉ đếm pixel vàng ≥20 trong cả vùng tag, không
  phân biệt **coin-là-1-kết-quả-ngẫu-nhiên** ("🪙, HP, or Potentials randomly changes!" — bare, không `×N`)
  với **coin giao dịch định lượng** ("Obtain 🪙×30"). Với event 2-option (top=gamble bare-coin,
  bottom=guaranteed 30 coin), **cả 2** bị đánh `has_coin=True` → `smart_event_choice` không thấy option
  item-free → rơi default-bottom → luôn lấy 30 coin, bỏ lỡ gamble **+EV** (Potential free ≈60đ Record; HP vô
  nghĩa trong Quick Battle sweep).
- **Fix**: thay bool đơn bằng `_event_tag_kind(img, cy) → {cost_qty, free_qty, rng_bare, free_no_tag}`.
  Tái dùng `_digit_runs` để tìm `×N` **ngay bên phải** blob coin vàng. ⚠️ **Cần viết mask mới
  "trắng-trên-navy"** (giống `read_coins`: `roi.min(axis=2)>=190`), **KHÔNG** tái dùng thẳng `_price_mask`
  (navy-trên-trắng, calib cho giá shop). Coin không kèm `×N` → `rng_bare`; ưu tiên chọn `rng_bare` khi đối
  option guaranteed cố định. Giữ nguyên hành vi các case đang ĐÚNG.
- **Effort M · Rủi ro thấp**: `event_tag_has_coin` chỉ 1 call site (dòng 1242, grep xác nhận).
- **Bằng chứng**: frame `run_01/0091` ("Gamble of Destiny") + lặp lại `run_01/0097`, `run_04/0014`
  (game machine), `run_08/0014`, `run_17/0086`, `run_19/0183` (potion/mirror). Mẫu 9 frame bucket
  default-bottom-2opt: 7/9 là leak này. Đối chứng `run_02/0104` (bán Note, cả 2 có `×N` thật) xác nhận
  taxonomy không phá case đúng.
- **Regression check**: replay `_event_tag_kind` offline trên **toàn bộ 171 frame** trong manifest trước khi build.

### Các pattern event ĐANG ĐÚNG (đừng đụng)
- **Bán Note đổi coin → từ chối** (`run_02/0104`, `run_06/0094`): đúng (Note = 15đ Record cố định > coin
  mất trắng).
- **Vendor trả phí + 1 free đáy → lấy free** (`run_04/0169`, `run_09/0090`…): đúng.
- **Gamble %HP tường minh (không icon coin) → nhận** (`run_01/0187`, `run_07/0099`): đúng (item-free heuristic
  đã xử tốt).

### [P2] Enhance OCR mù khi giá màu ĐỎ (unaffordable)
- **Root cause**: `_price_mask` (241-247) chỉ bắt navy (`r<110`); giá đỏ (coin < giá → game tô đỏ,
  BGR≈(90,52,188)) → mask trống → None → ước tính.
- **⚠️ TÁC HẠI THỰC RẤT NHỎ**: verify toàn bộ 80/80 lần fail trong 26 run → **0 lần dẫn tới quyết định kinh
  tế sai**. Guard milestone (`cost>180 → dừng`) + affordability (`coin<cost → dừng`) hấp thụ hết; coin dư
  phòng cuối luôn quá thấp (3-106, median 34) so với "vùng nguy hiểm" ≥240.
- **Fix (nếu làm)**: thêm nhánh mask đỏ `(r>150)&(r-b>40)&(g<140)`, kết hợp `navy|red` qua tham số
  `include_red=True` **chỉ bật ở `enhance_cost()`** (giữ nguyên `slot_offer`/`dialog_price` đang chạy tốt).
- **KHÔNG làm**: thay fallback `last_cost+60` bằng bảng ladder cứng — **regress** acc chưa research-maxed
  (base = Free/120/… khác maxed = Free/60/…).
- **Bug phụ thật (2/26 run)**: `last_cost` reset về None mỗi lần `_do_enhance()` gọi lại trong cùng phòng
  cuối → ước tính bậc kế tụt về 60 → 1 click enhance hụt (~6s trễ, không mất coin). Fix nhỏ: giữ `last_cost`
  qua các lần gọi trong cùng phòng.

### [P2] Card OCR dao động — không nhận diện "Lv. N+K" (delta)
- **Root cause**: `_find_lv_trio`/`card_lv` (337-403) không phân biệt `+` (delta cộng dồn) vs `▶` (thay thế
  tuyệt đối) → level đọc lật qua lại → ping-pong A,B,A (xác nhận `run_16/0019→0020→0021` khớp log
  16:54:36-44 + WARNING). Chỉ 1.7% Select nên impact thấp.
- **Thứ tự làm** (tăng dần rủi ro):
  1. Dump `log/lv_glyphs/` khi guard dao động fire (S, rủi ro 0) — thu mẫu `+`/`▶` thật.
  2. Snap toạ độ tap về `CARD_X` gần nhất thay vì `ASCENSION_SELECT.last_match[0]` thô (S) — sửa ~5/20 case.
  3. Core: phân biệt `+` vs `▶` bằng shape blob + resize trước khi tách (M) — **bắt buộc replay offline
     ~1228 Select** trước khi live.
  4. **HOÃN** tie-break bằng ribbon "Rcmd: Lv. N" — ý nghĩa Rcmd chưa kiểm chứng, dễ tạo lỗi mới.

### [P3] Phòng cuối: milestone-enhance chạy TRƯỚC vét/refresh-lượt-2 → nuốt ngân sách
- `_do_shop_room` (964-981): thứ tự hiện tại khiến **"refresh kệ lượt 2" chỉ 2/22 lần (9%)**, và
  **60% run** milestone-enhance ăn hết coin trước khi vét-phase kịp chạy ("phòng cuối còn N coin — vét" chỉ
  10/25 phòng cuối).
- **Đề xuất**: đảo — vét/burn (refresh-2 + note/potential) **trước** milestone-enhance.
- **⚠️ Cần chốt thiết kế**: giữ reserve **nhỏ** (không phải 0 tuyệt đối) trong bước vét để không hy sinh
  hoàn toàn baseline enhance khi kệ nghèo. Đây là **đánh đổi POWER-baseline ↔ Record dài hạn** — open
  question, chưa có data chọn ngưỡng. Đừng code trước khi quyết định.

---

## Câu hỏi mở §8 — data 26-run VỪA trả lời

| # | Kết luận từ data |
|---|---|
| **Q5** Ladder enhance | **XÁC NHẬN research-maxed** (Free/60/120/180/…): 26/26 run bậc trả phí đầu = 60 (không phải 120 base). |
| **Q7** Answer-key quiz còn đúng? | **ĐÚNG** cho 2/12 kiểm được qua frame: VIRIGIA "aiming high"→"Make a plan and follow it through.", BEATRIXA "health"→"Balanced Diet". |
| **Q2** Vé Quick Battle ~1/ngày? | **BÁC BỎ**: 0/8989 dòng "hết vé" dù 26 run liên tục cùng ngày → Quick Battle sáng xuyên suốt. ⇒ **khuyến nghị #2 doc §6 (dựa giả định 1 vé/ngày) cần xem lại.** |
| **Q4** HP có ý nghĩa khi sweep? | **Gợi ý gián tiếp KHÔNG** (0 WARNING HP-thấp sau các option tốn %HP) — chưa live-test dứt khoát. |

## Vẫn cần capture/live-test thêm
- **Difficulty auto (config=0)**: chưa exercise (0 dòng log); code review an toàn nhưng cần test riêng (§8 Q3).
- **Ladder enhance bậc ≥260** (+80/+200 theo doc): chưa quan sát giá thật (coin dư luôn quá thấp) — vẫn là suy luận doc.
- **Hệ quả thật của "rng_bare" gamble** khi được CHỌN: dataset 100% rơi default-bottom nên chưa có sample đo coin/HP/Potential đổi.
- **Ranh giới quiz-thật vs event-chọn-phần-thưởng**: cần làm rõ trước khi build template-match quiz.

---

## Công cụ & tính năng đã thêm (2026-07-07 tối)
- **Phân tích phiên capture (người dùng, thuần Python — không AI)**: `module/ascension_analysis.py` (engine
  `analyze_session`/`render_report_md`/`cleanup_images`) + `dev_tools/analyze_capture.py` (CLI:
  `[phiên] --json --export F --cleanup`) + GUI trong app (trang Ascension): chọn phiên → chỉ số người chơi
  → xuất báo cáo Markdown → **dọn ảnh giải phóng ổ** (26 run = 6.8GB). API app.py:
  `list_capture_sessions`/`analyze_capture`/`export_capture_report`/`cleanup_capture_images`.
- **OCR tự cải thiện** (dev): `dev_tools/rebuild_digits.py` — `--review` sinh montage + CSV để dán nhãn
  glyph OCR hụt (`log/coin_glyphs`, hiện 70 glyph), `--apply` cài thành template variant (coin dùng list →
  hiệu lực ngay). Tấn công gốc OCR-fail bền hơn vá mask.
- **Huỷ Record yếu tại màn Save** (config+GUI, mặc định OFF) — quyết định LƯU vs HUỶ **NGAY tại màn Save
  cuối run** theo **MÀU KHUNG badge rank** (không OCR số — font nâu khó). Khảo sát live 2026-07-07
  (`docs/game-map.md ▸ records`): khung silver 1–5 / green 6–10 / blue 11–20 / golden 21–30 / **chroma 31–40**
  (chroma nằm TRÊN Master → giải thích vì sao "Master and below" trong Dismantle không chọn rank ≥31).
  - Config: `dissolve_record` + `dissolve_max_band` (silver|green|blue|golden). GUI: checkbox + 1 dropdown band.
  - `tasks/ascension.py::read_record_band(img)` phân loại theo **median hue** pixel khung bão hoà (ROI
    `RECORD_BADGE_ROI`=(66,44,156,136)). **Verify**: golden hue~17-22, chroma hue~133-137 (tách rõ, đúng
    6/6 badge thật). silver/green/blue chưa có mẫu trên acc Diff8 (record luôn rank ≥29) — ngưỡng hue theo lý thuyết.
  - Logic ở `_run_loop` khi thấy `SAVE_RECORD`: đọc band → log quyết định. **Verify e2e 2026-07-07**: 1 run
    live "HOÀN TẤT" sạch (code mới không vỡ). ⚠️ **Bước HUỶ (bấm thùng rác ~448,655 + dialog confirm) chưa
    verify live → FAIL-SAFE: vẫn LƯU + log ý định, KHÔNG mất data.** Còn nợ bật huỷ thật: crop `RECORD_DISCARD`
    (thùng rác) + khảo dialog confirm (PHÁ HỦY — cần permission + record throwaway) + test giám sát.
  - (Bulk Dismantle từ Records list — theo tier dropdown — là tuỳ chọn tương lai để dọn record đã tích; đã map flow.)
- **Test dev**: `tests/test_adb_retry.py` (3 case PASS, bảo vệ hồi quy P0).

## Việc tiếp theo ngay
**Implement P0 retry+reconnect trong `Adb.shell()`** (đã verify, effort S, rủi ro thấp) → chạy lại
`ascension_capture.py --runs 70` để (a) verify retry, (b) thu data trả lời các câu mở còn thiếu.

> Nguồn: workflow `dev_tools/ascension_improve_workflow.js` (6 chiều × analyze→verify + synthesize,
> 13 agent). Manifest quyết định→frame: sinh bởi script phân tích (scratchpad, có thể tái tạo).
