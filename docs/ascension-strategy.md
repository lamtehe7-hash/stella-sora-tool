# Ascension / Monolith — cơ chế & chiến lược tối ưu

> Tổng hợp nghiên cứu đa nguồn (Miraheze EN, game8/gamerch/wikiru/appmedia JP, gamekee/4399 CN,
> sheet Mistique, Reddit) + verify đối kháng, đối chiếu với `tasks/ascension.py` (shop v3).
> Ngày: 2026-07-05. Mức tin cậy ghi theo từng mục. Các số liệu ở mốc Difficulty 7–8 (patch ~04/2026).

## 0. TL;DR — 3 chỗ "rò rỉ" phần thưởng lớn nhất (tool hiện tại đang bỏ lỡ)

1. **Difficulty** (impact CAO): tool GIỮ difficulty game nhớ, có thể thấp hơn mức đã clear cao nhất.
   Phần thưởng tăng đơn điệu theo difficulty — Diff1≈105 / Diff2≈210 / Diff7≈430 stub mỗi clear,
   thêm ~+300 coin/run và trần điểm Record cao hơn. Đây là đòn bẩy đơn lẻ mất mát nhiều nhất.
2. **Choice Domain / event** (impact TRUNG BÌNH): tool luôn bấm option DƯỚI CÙNG (giả định "rời đi").
   Bỏ lỡ quà miễn phí + phần thưởng quiz (trả lời đúng = 1 Potential / 6 Notes / 1 Rainbow Potential,
   rủi ro 0). 5 Choice Domain mỗi run.
3. **Số run/tuần** (impact TRUNG BÌNH): `runs_per_session=1`. Trần tuần là **3000 stub**, cần ~7 clear
   Diff7 (430×7≈3010) mới đầy. 1 run/ngày để lại ~86% trần chưa lấy nếu không gom vé.

**Chốt về chính sách SHOP/enhance hiện tại: ĐÚNG, giữ nguyên.** `enhance_reserve=360`, `milestone=180`,
"vét sạch phòng cuối", "Melody chỉ mua khi Harmony Skill cần" khớp gần như chính xác meta POWER của CN.
Chỉ cần vài tinh chỉnh nhỏ (mục 5).

---

## 1. Cơ chế run (độ tin cậy: CAO)

Run Monolith là **thang máy tuyến tính 1 đường — KHÔNG phải map nhánh kiểu Slay-the-Spire.** Loại phòng
(Domain) cố định theo chỉ số tầng; chỉ NỘI DUNG bên trong (địch/thẻ/hàng shop/NPC) là ngẫu nhiên.

- Full run ở Diff2+ = **26 tầng / 3 section**: S1 = 1-1…1-7, S2 = 2-1…2-10, S3 = 3-1…3-9
  (JP đếm ~30 tầng ở difficulty cao). Diff1 & "Misstep On One" = tháp tập sự ngắn (~7–17 tầng,
  thưởng thấp) → **không farm**.
- Bố cục cố định: tầng đầu luôn **Battle**; **Choice Domain** ở 1-3, 2-3, 2-6, 3-2, 3-5 (5/run);
  **Rival's Domain** (elite) ở 1-5, 2-4, 2-8, 3-4; **Trade Domain** (shop) 1 lần/section ở 1-6, 2-9, 3-8;
  **Boss** ở 1-7, 2-10, 3-9; **shop Portia cuối** mở sau boss chót để tiêu nốt coin.
- **Hệ quả cho tool**: KHÔNG cần logic route/chọn đường (đã đúng). Mọi quyết định là **trong phòng**,
  và có thể đánh chỉ số theo tầng cố định. Icon thang máy chỉ *preview* loại tầng kế (không phải ngã rẽ).
- 4 Monolith có lợi thế nguyên tố cố định: Currents and Shadows→Địa/Quang; Dust and Flames→Thủy/Phong;
  Storm and Thunder→Hỏa/Ám. Chọn Monolith khớp đội hình.

## 2. Quick Battle / Sweep — điểm mấu chốt cho tool (CAO/ TRUNG BÌNH)

Quick Battle tốn 1 **Monolith Stairs Pass** (JP 超高速塔頂チケット), chỉ sáng khi difficulty đó đã clear,
và **auto-clear mọi tầng Battle/Rival/Boss** — nhưng **vẫn phải TỰ chọn thẻ, shop, và option Choice Domain**.
→ Trong run swept, **sức mạnh combat vô nghĩa** (không có trận để thua, HP không quan trọng).

Giá trị "downstream" của Record đã lưu chỉ nằm ở: (a) sức mạnh ở mode KHÁC (Menace Arena, Limit Break)
— nơi potential/enhance có ích; và (b) rã Record thành Journey Ticket Stub — nơi **điểm số (số lượng
potential + note)** mới trả tiền. Cái nào chi phối quyết định enhance-nặng có tối ưu không (xem mục 4 + 8).

## 3. Kinh tế Starcoin & phân bổ tiền (CAO)

- **Starcoin (JP ステラコイン) chỉ dùng trong run, MẤT TRẮNG khi run kết thúc** (clear boss chót HOẶC
  bỏ dở). Không quy đổi sang gì bền vững. `一時撤退`/Temporary Retreat chỉ là **PAUSE** (giữ coin+tiến độ);
  chỉ khi run TERMINATE mới mất. → Phải tiêu về ~0 trước khi kết thúc; shop Portia cuối sinh ra để đúng việc đó.
- **Thu nhập ~4700 coin/run @Diff7, ~5000 @Diff8** (chưa kể event). Node Research 支度金 I = +50 coin
  đầu run; 調和の弦 I = +15% rơi note khi combat; 原初の歌謡 = +3 note đầu run.
- **Giá hàng**: Potential ~200 full / ~150–160 sale. Melody (kệ dưới, "x5") ~45–90 sale.
- **Thang Enhance RESET mỗi phòng shop.** Research-maxed: Free/60/120/180/260/340/540/740(cap).
  Base (chưa research): Free/120/180/240/320/400/600/800. **Quy tắc ROI cộng đồng: enhance khi 1 lượt
  còn ≤200 coin** (dưới 200 thì enhance lời hơn mua 1 potential 200 coin) → Free+60+120+180 = **360 coin/phòng**.
  Enhance nâng NGẪU NHIÊN 1 trong 3 potential đang sở hữu (không chọn được thẻ nào).
- **Refresh kệ shop = 100 coin, ngân sách CẢ RUN** (gated node Research 倉庫の鍵: Lab2=1 lượt, Lab3=2 lượt
  — KHÔNG phải 2/phòng). Refresh bộ thẻ ở màn chọn thẻ = 40 coin (rẻ hơn, để câu core).

**Thời điểm dùng 2 lượt refresh kệ — tính EV (JP + CN đồng thuận: "để dành 18-20 tầng cuối"):**

Refresh đáng ⟺ giá_trị_stock_mới > 100 + **opportunity cost** (số coin đó nếu để dành mua được gì sau).

| Phòng | Còn phía sau | Opportunity cost | EV |
|---|---|---|---|
| Shop 1-6 | 3 shop + 3 enhance-room + boss | CAO (100+150 coin nuôi được Free+60+120 enhance ≤200 ROI cao + core sau) | ❌ Âm |
| Shop 2-9 | 1 shop + Portia cuối | TB-cao | ❌ Âm (trừ câu core thiếu) |
| Shop 3-8 | chỉ Portia cuối | TB (coin vẫn tiêu ở Portia) | ⚠️ ~0, nên đợi |
| **Portia cuối** | KHÔNG gì — coin 100% mất | **≈ 0** (hoặc = 1 enhance bậc 540: +single-% power, **+0 Record**) | ✅ **Dương mạnh** |

Ở Portia cuối, refresh 100 → mua potential ~150 (**+60 Record + power**) + note ~45 (**+15 Record**) = biến ~295
coin sắp-mất thành +75 Record. Quan trọng: **1 SALE potential 45-72 coin RẺ/level hơn enhance bậc 180**, và refresh
(100) chia đều cho nhiều món SALE mua được (lượt refresh thật hiện 4 món SALE) → mỗi món chỉ ~35 phí refresh.
**⇒ Dồn CẢ 2 refresh charge vào phòng Portia cuối**, ưu tiên SALE hơn enhance bậc ≥180.

**⚠️ Bug đã sửa (phát hiện live-test 2026-07-05, run thật):** phòng cuối tool CHỈ dùng **1/2** refresh charge — vì
`enhance_reserve=360` bị chặn (`coin − 100 − 360 < 45`) rồi dồn 360 vào enhance 60/120/180. Đã sửa: phòng cuối chỉ
chừa **180** (2 bậc enhance rẻ nhất 60+120) qua config `enhance_reserve_last_room=180`, giải phóng budget để **cả 2
charge đều được dùng** + mua thêm SALE; bậc enhance 180 (biên, thua 1 SALE potential) nhường chỗ. *Cần verify live
run kế (tuần này đã capped 3000/3000).* **Ngoại lệ:** phòng 2-9 thiếu core Super-Rare sống-còn + dư coin → 1 refresh
sớm để câu core (ưu tiên refresh bộ thẻ 40 coin trước).

**Chính sách phân bổ tối ưu (mục tiêu POWER — mặc định, khớp meta CN 塔8):**

| Ưu tiên | Hạng mục | Ghi chú |
|---|---|---|
| 1 | Potential Drink (thẻ theo Preset) | Mua thẻ core/build còn thiếu, rồi +1 level cho thẻ đáng nâng. **Không** phí Drink cho thẻ Rcmd-Lv1 (giữ base) hay thẻ pink Super-Rare (không nâng được) |
| 2 | Enhance máy, các bậc ≤200 | Free+60+120+180 = 360/phòng |
| 3 | Melody notes — CÓ ĐIỀU KIỆN | Chỉ mua đủ ngưỡng Lv1 kích hoạt Harmony/concerto của build; **KHÔNG** nâng note/concerto lên Lv1+ (concerto Lv1→2 chỉ +9.5%, note lẻ chỉ vài % → "bẫy sức mạnh ảo") |
| 4 | Vét coin thừa ở shop Portia cuối | Coin mất trắng → mua nốt note/potential/refresh, về ~0 |

Benchmark @Diff8 (~5000 coin): ~2700 vào ~18 potential (~150) + ~1440 vào ~16 enhance (4 phòng × Free+60+120+180)
+ ~200 refresh + ~660 dư → notes. **Tool shop v3 tái tạo đúng hình dạng này → chính sách shop đã gần tối ưu.**

**Ngoại lệ note > potential per-coin**: build auto-attack (vd Wind-Shadow) — 150 coin potential = +3% auto DMG,
nhưng 45 coin/5 note auto = +6% → build này nên ưu tiên note khớp. (Tool chưa mô hình hoá; xem khuyến nghị.)

## 4. POWER vs SCORE — ngã ba chiến lược (TRUNG BÌNH)

- **Record rank (tối đa 40) tăng theo SỐ LƯỢNG potential + note thu được, KHÔNG theo level.** Điểm: mỗi
  note = 15đ; sub-potential = 60đ (1 lần khi nhận); core/SR = 120–180đ; hiệu ứng Disc Harmony "Assist" = 200–220đ.
  → **Nâng level (Drink/Enhance) cộng SỨC MẠNH nhưng 0 điểm Record.** Chỉ potential MỚI và note mới tăng rank.
- **CN gamekee** chạy A/B test: build ưu tiên potential (score 28) sát thương CAO HƠN build maxed note (score 31)
  → notes = "bẫy điểm ảo". **JP guide score-25** thì mua mọi note đúng nguyên tố — vì tối ưu ĐIỂM, không phải DMG.
  Cả hai đúng theo mục tiêu khác nhau. Tool hiện theo meta **POWER** của CN (đúng cho Record tái sử dụng mạnh).
- Nếu tài khoản farm stub bằng cách **rã Record** (score-driven): nên mua nhiều note/thẻ mới, bỏ enhance.
  → đề xuất thêm switch `objective=power|score` (mặc định `power`).

## 5. Gap-analysis vs `tasks/ascension.py`

| Vùng | Impact / Conf | Hiện tại | Tối ưu |
|---|---|---|---|
| **Difficulty** | CAO / cao | Giữ difficulty game nhớ, chỉ check Quick Battle sáng | Tự chọn difficulty đã-clear cao nhất mỗi session (Diff yield đơn điệu ↑) |
| **Event / quiz** | TB / cao | Luôn bấm option dưới cùng, không xử lý quiz | Trả lời quiz đúng (key 4 NPC/12 câu), nhận quà 0-cost; sweep nên HP-gamble được vì HP vô nghĩa |
| **Runs/session** | TB / TB | `=1`, tự dừng khi hết vé | Tiêu hết vé Stairs Pass đã gom + đọc meter N/3000 để dừng đúng trần |
| **Objective** | TB / TB | Cứng POWER (Melody chỉ khi Harmony cần) | Thêm `objective=power|score`; SCORE = mua note thả ga, tối thiểu enhance |
| **Vét phòng cuối** | THẤP / TB | Enhance tới hết tiền (đẩy bậc 260/340/540/740) | Ưu tiên mua note/potential + refresh TRƯỚC, cap enhance ở bậc ~200 (note 15đ lời hơn enhance 540 ROI kém) |
| **Tiebreak chọn thẻ** | THẤP / TB | Mức tăng level lớn nhất; SR tuyệt đối; hoà→trái | Đúng cho POWER; SCORE nên ưu tiên thẻ MỚI (+60 rank) hơn +level (+0 rank). SR cap **2/nhân vật** |
| **Hằng số enhance** | THẤP / cao | 60/360/180 giả định ladder research-maxed | OCR giá đã đọc đúng → milestone an toàn; chỉ `reserve` nên suy ra từ ladder quan sát (acc chưa maxed: bậc trả phí đầu = 120 → reserve 300) |
| **Route** | — / cao | Không có logic route | ĐÚNG — map tuyến tính, không có gì để route. Không cần đổi |

## 6. Khuyến nghị theo ưu tiên (map vào config/code)

1. **[CODE] Tự chọn difficulty đã-clear cao nhất.** Thêm `ascension.difficulty:int=0` (0=auto-max).
   Template mới cho hàng chọn Diff 2–8 + `_select_difficulty()` gọi sau `ui_ensure(page_asc_diff)`, trước
   check `ASCENSION_QUICK_BATTLE`: chọn bậc cao nhất mà Quick Battle sáng; không sáng → lùi bậc.
   *Rủi ro thấp*: chọn bậc chưa clear → Quick Battle tắt → loop hiện tại tự break, bỏ ngày (không crash).
2. **[CONFIG+CODE] Tiêu hết vé + dừng ở trần 3000.** Nâng `runs_per_session` mặc định ~5–7 (tool tự dừng
   khi hết vé). Tuỳ chọn: OCR meter "N/3000" ở trang entry (tái dùng pipeline `_read_number`) để dừng sớm.
   *Cần verify live*: vé Stairs Pass có gom qua ngày không & số cấp/ngày.
3. **[CODE] Trả lời quiz Choice Domain + nhận quà 0-cost** thay vì mù bấm option cuối. Trong
   `_handle_event_choice`: OCR câu hỏi + match answer-key (config patch-updatable), click theo TEXT (vị trí
   xáo trộn — không dùng index cố định). Non-quiz: nhận quà rõ ràng 0-cost; vẫn từ chối bán note/hi sinh HP có phí.
   Fallback OCR fail → giữ hành vi cũ (không phạt). *Answer key có sẵn trong sheet Mistique — xem mục 7.*
4. **[CODE] Switch `objective=power|score`** (mặc định `power`=hành vi hiện tại đã kiểm chứng). `score`:
   ép `buy_melody_when_needed_only=False`, enhance chỉ bậc Free, phòng cuối dồn coin vào note. *Cần verify
   live*: stub mỗi clear có phụ thuộc rank khi Record được LƯU (không rã) không (câu hỏi mở #1).
5. **[CODE] Đảo thứ tự vét phòng cuối**: chạy quét mua note/potential + refresh tới hết TRƯỚC, cap
   `_do_enhance(last_room=True)` ở bậc ~180 thay vì tới hết tiền; coin dư → quét note lần chót. Delta nhỏ (coin
   mất trắng) nhưng luôn ≥ hiện tại.
6. **[DOC] Giữ reserve/milestone/burn + suy ra reserve động.** Đã đúng theo ROI ≤200. Tuỳ chọn: tính reserve =
   tổng các bậc enhance quan sát ≤200 thay vì hardcode 360 (acc chưa maxed → 300). Ghi chú: **không** set
   `map='misstep'` để farm (tháp tập sự, stub thấp).

## 7. Đáp án quiz Monolith (nguồn: sheet Mistique — Info Dump gid=0)

> Vị trí option XÁO TRỘN mỗi lần — match theo TEXT đáp án, không theo thứ tự. Pool đang lớn dần & vài
> nguồn lệch nhau (vd Portia "số yêu thích" 3 vs 4) → lưu key ngoài, patch được.

- **BERNINA**: "kiểu Trekker admire?"→*Someone who's governed by desire*; "true to desire nghĩa là?"→*Carpe diem!*;
  "1 quãng tám có mấy nốt?"→**12**.
- **VIRIGIA**: "thích nói chuyện với ai?"→*Someone who aims high*; "aiming high là?"→*Make a plan and follow it through*;
  "khối lập phương có mấy mặt?"→**6**.
- **PORTIA**: "mấy giờ là thức khuya?"→*Twelve o'clock*; "số yêu thích của Monolith?"→*3 (luôn có 3 lựa chọn)*;
  "2 mũ 10?"→**1024**.
- **BEATRIXA**: "gì giúp giữ sức khoẻ?"→*Balanced Diet*; "món nào tốt hơn?"→*Eat more veg things*;
  "nên làm ít điều gì?"→*Don't sit too long*.

Nguồn tra cứu bổ sung khi patch: stella.ennead.cc/monolith, gachawiki, game8/gamerch/appmedia.

## 8. Câu hỏi cần TEST LIVE trước khi code (chưa chốt được từ cộng đồng)

1. **Stub mỗi clear có phụ thuộc SCORE/rank khi Record được LƯU (không rã)?** Nếu run lưu chỉ trả stub phẳng
   theo difficulty → chính sách enhance-for-power hiện tại tối ưu hoàn toàn (khuyến nghị #4 không cần flip sang score).
2. **Vé Quick Battle (Stairs Pass) có STACK qua ngày không & cấp bao nhiêu/ngày?** (đồng thuận ~1/ngày, chưa xác minh)
   → quyết định payoff của #2.
3. **Trên tài khoản NÀY, có difficulty đã-clear (Quick-Battle-sáng) cao hơn mức đang nhớ không?** → xác nhận
   độ lớn payoff #1 + layout/template hàng Diff 2–8.
4. **Trong SWEEP có bất kỳ trạng thái fail/HP nào không** (boss swept có cần HP)? → quyết định mức "hung hăng"
   khi nhận HP-gamble ở event.
5. **Ladder enhance thật trên acc này** (research-maxed Free/60/… vs base Free/120/…)? → hằng số reserve chính xác.
6. **1 slot Melody = 5 note?** + giá sale chính xác → tính score-per-coin cho SCORE mode.
7. **Answer key quiz còn đúng sau patch?** (pool lớn dần) → verify trước khi hardcode.

## Nguồn chính

- EN: stellasora.miraheze.org/wiki/Ascension, /Monolith, /Journey_Ticket_Stub (qua Wayback); Twinfinite; Reddit r/StellaSora.
- JP: game8.jp/stellasora (722615 room types, 723005/723016 currency & research, 744354 economy, 758744 events, 947004 quiz reward); gamerch 946895/947004/947348; wikiru; appmedia.
- CN: gamekee 705111 (塔8纪录发育指南 — A/B test POWER meta), 4399/233leyuan potential guide.
- Cộng đồng: sheet "Mistique's Field Reports" (Info Dump gid=0 quiz, Potential Builds gid=1930264270 quy tắc nâng).
