export const meta = {
  name: 'ascension-improve-from-capture',
  description: 'Phân tích data capture Ascension 26/70 -> roadmap cải thiện tool (verified)',
  phases: [
    { title: 'Analyze', detail: '6 chiều: ADB / event-quiz / enhance-OCR / card-OCR / shop / throughput' },
    { title: 'Verify', detail: 'đối kháng từng đề xuất trên code+data thật' },
    { title: 'Synthesize', detail: 'gộp thành roadmap ưu tiên có bằng chứng' },
  ],
}

// ---- Bối cảnh chung (ground truth đã tính inline, tránh agent re-parse 967KB) ----
const CTX = `
DỰ ÁN: Stella Sora Tool — auto game Android qua ADB + template-match OpenCV. Task Ascension chạy
Monolith Quick Battle (roguelike thang máy tuyến tính), tự chọn thẻ/shop/event. Trả lời TIẾNG VIỆT.

FILE:
- Code task: tasks/ascension.py (1274 dòng). Device: module/device/adb.py (62), module/device/device.py (98).
- Chiến lược (nghiên cứu đa nguồn 2026-07-05): docs/ascension-strategy.md (§0 3 leak, §3 kinh tế coin,
  §5 gap-analysis, §6 khuyến nghị, §7 ĐÁP ÁN QUIZ, §8 câu hỏi mở).
- Data capture: data/ascension_capture/20260707_140335/ (26 run, Storm/Diff8/Squad1, POWER).
  * session.log (8989 dòng, mọi quyết định), frames.jsonl (9136 frame: run/step/ts_ms/coins/file),
    run_01..run_26/ (ảnh PNG ~350/run), summary.json, config_used.json.
- MANIFEST map quyết định->frame screenshot (đã build sẵn):
  C:/Users/lucth/AppData/Local/Temp/claude/e--Claude-Stella-Sool-Tool/2da76983-c732-46a8-84f5-5f127e8d2060/scratchpad/manifest.json
  (JSON: {event:[{run,frame,n_opt,y,why}], enh_est:[{run,frame,est}], card_osc:[{run,frame,taps}]};
   "frame" là đường dẫn tuyệt đối tới ảnh — Read được trực tiếp bằng tool Read.)

METRICS CỨNG (đã tính từ toàn bộ 26 run):
- 116 WARNING = 112 là độ tin cậy OCR: 80× "không đọc giá enhance→ước tính", 20× "dao động chọn thẻ",
  12× "số dư != kỳ vọng enhance". => OCR (giá enhance / level thẻ / coin) là nguồn nhiễu chính.
- Enhance: 388 lần đọc giá, 80 HỎNG (21%) -> fallback ước tính = last_cost+60.
- Event: 171 lần chọn — 95 rơi "option dưới cùng (mặc định an toàn)", 76 "item-free (tag không coin)".
- Card: 1208 Select, 20 dao động (1.7%).
- Coin dư cuối run: median 34, mean 102 (run 26=1776 là artifact CRASH). => enhance-until-broke tiêu
  coin tốt; HIỆU SUẤT COIN KHÔNG phải leak.
- Quiz: 0 dòng log nhắc quiz -> tool KHÔNG nhận diện Choice Domain, bấm mù như event thường.
- Difficulty: config ÉP =8 (không chạy nhánh auto difficulty=0 trong phiên này).

2 ROOT-CAUSE ĐÃ KIỂM CHỨNG (soi frame thật):
(A) Enhance OCR fail: frame run_01/0075 hiện "Enhance (260 🪙)" chữ ĐỎ (coin 168 < 260 nên game tô đỏ).
    _price_mask chỉ bắt navy (r<110) -> giá đỏ = mask trống -> None -> ước tính. NGOÀI RA ladder thực
    research-maxed = Free/60/120/180/260/340/540/740 (§3) -> fallback +60 SAI từ bậc ≥260 (thực +80 rồi +200).
(B) Event leak: frame run_01/0091 "The Gamble of Destiny" — 2 option đều có tag coin: "light it up"
    (gamble: coin/HP/Potential đổi ngẫu nhiên) vs "Obtain 🪙×30". Tool lấy 30 coin. Trong Quick Battle
    auto-clear, MẤT HP VÔ NGHĨA -> gamble là +EV để săn Potential free. Heuristic item-free mù (cả 2 có
    coin) -> rơi default-bottom. Leak POWER thật.

BLOCKER: phiên dừng ở 26/70 KHÔNG do logic mà do AdbError:closed (rớt ADB) tại
adb.py::shell -> open_shell -> check_okay, gọi từ device.click_xy lúc mua slot shop. KHÔNG có retry/reconnect.

NGUYÊN TẮC: chỉ ĐỀ XUẤT + thiết kế, KHÔNG sửa file. Mọi kết luận phải dẫn bằng chứng (dòng code cụ thể,
frame cụ thể, hoặc số liệu). Nêu rõ độ chắc chắn và rủi ro regression của mỗi đề xuất.
`

const FIND_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['dimension', 'severity', 'problems', 'proposed_changes'],
  properties: {
    dimension: { type: 'string' },
    severity: { type: 'string', enum: ['P0', 'P1', 'P2', 'P3'] },
    summary: { type: 'string' },
    problems: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['title', 'evidence'],
        properties: {
          title: { type: 'string' },
          evidence: { type: 'string', description: 'dòng code / frame / số liệu cụ thể' },
          quantified_impact: { type: 'string' },
        },
      },
    },
    proposed_changes: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['file', 'area', 'change', 'risk'],
        properties: {
          file: { type: 'string' },
          area: { type: 'string', description: 'hàm / hằng số / vùng' },
          change: { type: 'string', description: 'mô tả cụ thể, có thể kèm pseudo-code' },
          effort: { type: 'string', enum: ['S', 'M', 'L'] },
          risk: { type: 'string' },
          regression_check: { type: 'string' },
        },
      },
    },
    answers_open_questions: { type: 'array', items: { type: 'string' },
      description: 'câu §8 doc mà data này trả lời được' },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
}

const VERIFY_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['dimension', 'problem_verdicts', 'net_recommendation'],
  properties: {
    dimension: { type: 'string' },
    problem_verdicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['title', 'confirmed', 'reason'],
        properties: {
          title: { type: 'string' },
          confirmed: { type: 'boolean', description: 'vấn đề CÓ THẬT sau khi soi lại code/data?' },
          reason: { type: 'string' },
        },
      },
    },
    change_risks: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['change', 'would_regress', 'note'],
        properties: {
          change: { type: 'string' },
          would_regress: { type: 'boolean' },
          note: { type: 'string' },
        },
      },
    },
    adjusted_severity: { type: 'string', enum: ['P0', 'P1', 'P2', 'P3'] },
    net_recommendation: { type: 'string' },
  },
}

const DIMENSIONS = [
  {
    key: 'adb-reliability',
    sev: 'P0',
    prompt: `CHIỀU: Độ tin cậy ADB (blocker chặn 26/70). Đọc module/device/adb.py TOÀN BỘ + module/device/device.py
+ đuôi traceback ở data/ascension_capture/_launch_20260707_140334.out.log (grep "AdbError"/"Traceback").
Nhiệm vụ: thiết kế lớp retry/reconnect để 1 lần rớt ADB (AdbError:closed) KHÔNG giết cả session 6-8h.
Xét: (1) bọc adb.shell()/tap()/screenshot() bắt AdbError -> "adb connect <serial>" + retry N lần backoff;
(2) nơi đặt hợp lý nhất (adb.py hay device.py); (3) có cần persist tiến độ run để --resume sau reconnect;
(4) rủi ro: tap lặp gây double-buy? reconnect giữa dialog shop? Đề xuất pseudo-code cụ thể cho wrapper.`,
    frames: [],
  },
  {
    key: 'event-quiz',
    sev: 'P1',
    prompt: `CHIỀU: Chất lượng quyết định Event / Choice Domain / Quiz (leak chiến lược lớn nhất).
Đọc trong tasks/ascension.py: _handle_event_choice (~1231), event_options (~499), event_tag_has_coin (~513),
EVENT_TAG_COIN_MIN. Đọc docs/ascension-strategy.md §0.2, §5 (dòng event/quiz), §7 (ĐÁP ÁN QUIZ), §8 Q4.
Đọc MANIFEST (Bash: cat manifest.json | python -m json.tool, hoặc Read) rồi Read TỐI THIỂU 12 frame event
THẬT — trộn cả "default-bottom" lẫn "item-free", nhiều n_opt khác nhau, nhiều run khác nhau.
Phân loại từng frame theo LOẠI event: (a) gamble (+EV vì HP vô nghĩa khi sweep), (b) quà free rõ ràng,
(c) QUIZ Choice Domain (câu hỏi + đáp án text — đối chiếu §7), (d) bán note/hi sinh HP có phí, (e) khác.
Trả lời ĐỊNH LƯỢNG: trong 95 default-bottom, ước bao nhiêu là LEAK thật (gamble/free-gift/quiz bỏ lỡ) vs
đúng (từ chối bán/phí)? Có frame nào là QUIZ không (nếu Storm map có Choice Domain quiz)? Thiết kế
_handle_event_choice cải tiến: quiz->match text §7 click theo TEXT (vị trí xáo trộn); gamble->nhận;
free-gift->nhận; giữ fallback an toàn khi OCR fail. Nêu template/OCR mới cần crop.`,
    frames: [],
  },
  {
    key: 'enhance-ocr',
    sev: 'P2',
    prompt: `CHIỀU: OCR giá Enhance (80 fail/21%, root-cause đã biết: giá ĐỎ + ladder +60 sai).
Đọc trong tasks/ascension.py: enhance_cost (~264), _price_mask (~241), _read_number (~208), ENHANCE_FREE,
ENHANCE_STEP, ENHANCE_MILESTONE, _do_enhance (~1114). Đọc §3 doc (ladder research-maxed Free/60/120/180/260/340/540/740).
Read ≥5 frame enh_est từ MANIFEST. XÁC MINH: (1) có phải mọi/đa số fail là do giá ĐỎ (unaffordable) không?
(2) fallback last+60 sai bao nhiêu so với ladder thật? (3) QUAN TRỌNG — đánh giá TÁC HẠI THỰC: guard
milestone (cost>180 dừng) và affordability (coin<cost dừng) có HẤP THỤ phần lớn sai số ước tính không, khiến
80 fail phần lớn VÔ HẠI? Định lượng số lần fail thực sự dẫn tới quyết định SAI (over/under-enhance, mua hụt).
Thiết kế fix: (a) _price_mask đọc thêm chữ số ĐỎ; (b) fallback dùng ladder biết trước thay vì +60; (c) có
đáng làm không xét tác hại thực. Đề xuất kèm rủi ro regression (đừng phá OCR navy đang chạy tốt).`,
    frames: [],
  },
  {
    key: 'card-ocr',
    sev: 'P2',
    prompt: `CHIỀU: OCR level thẻ chập chờn (20 dao động/1208 = 1.7%). Đọc trong tasks/ascension.py:
card_lv (~384), _find_lv_trio (~337), _classify_digit (~315), _bar_bands (~367), pick_card (~553),
_handle_card_pick (~909, guard _focus_taps). Read ≥4 frame card_osc từ MANIFEST.
Xác định vì sao level đọc lật qua lại (anti-alias? thẻ focus vs không-focus bar ở y khác? digit template thiếu?).
Đánh giá tác hại: dao động -> ép chọn focus (có thể KHÔNG phải thẻ tối ưu). Thiết kế cải thiện độ ổn định
(đọc median-of-N, cache theo run, hay siết template digit). Nêu rõ đây là P2/P3 (impact thấp) hay đáng làm.`,
    frames: [],
  },
  {
    key: 'shop-strategy',
    sev: 'P3',
    prompt: `CHIỀU: Kiểm toán chính sách shop/coin (data cho thấy coin dư median 34 = tiêu tốt).
Đọc trong tasks/ascension.py: _do_shop_room (~964), _do_shop (~983), _buy_slot (~1044), _do_enhance (~1114),
buy_melody_when_needed_only, SHOP_RELEVANT logic (~1055), refresh (~1027). Đọc §3, §5, §6 doc.
Read 3-4 frame phòng cuối (tìm trong run_25 hoặc run_24: các frame cuối có nút Leave Monolith / màn shop).
XÁC MINH bằng số liệu (grep session.log): (1) 157 melody-skip có đúng không (đối chiếu SHOP_RELEVANT)?
(2) refresh kệ có dùng đủ 2 charge ở phòng cuối không (grep "refresh kệ lượt")? (3) coin thực sự về ~0 mọi run?
(4) ladder enhance quan sát khớp research-maxed (260/340...) -> trả lời §8 Q5. Có tinh chỉnh nào NÂNG POWER
mà rủi ro thấp không, hay chính sách đã tối ưu (giữ nguyên)? Trung thực nếu "không có gì để sửa".`,
    frames: [],
  },
  {
    key: 'throughput-robustness',
    sev: 'P3',
    prompt: `CHIỀU: Thông lượng & độ bền vận hành. Data: ~700s/run × 70 = ~13.6h/session (quá dài -> tăng xác suất
rớt ADB). Đọc _run_loop (~759) trong tasks/ascension.py chú ý các time.sleep() và xử lý màn lạ (unknown, ~897).
(1) Thời gian /run đổ vào đâu (đếm sleep trên đường đi điển hình: event 3s, shop, enhance 2.5s×~12)? Có sleep
nào rút ngắn an toàn không? (2) Xử lý "màn lạ" (unknown>=3 -> tap 740,585) có gây tap sai ở đâu không (soi log
grep "ASC_UNK")? (3) run_timeout 2400s có phù hợp (dur thực ~650-720s)? (4) Difficulty auto (config=0) KHÔNG
chạy phiên này — đọc _select_difficulty (~657), đánh giá rủi ro bật cho production (soi §6 #1, §8 Q3). (5)
save_record luôn True — cần thiết cho POWER không? Đề xuất tăng độ bền/tốc độ, rủi ro thấp.`,
    frames: [],
  },
]

phase('Analyze')
log(`Phân tích ${DIMENSIONS.length} chiều trên data 26 run (mỗi chiều tự soi frame thật + verify đối kháng)`)

const results = await pipeline(
  DIMENSIONS,
  (d) => agent(
    `${CTX}\n\n${d.prompt}\n\nDùng Read cho code & ảnh PNG, Bash/grep cho log/manifest. severity gợi ý: ${d.sev}.`,
    { label: `analyze:${d.key}`, phase: 'Analyze', schema: FIND_SCHEMA, model: 'sonnet', effort: 'high' },
  ),
  (finding, d) => {
    if (!finding) return null
    return agent(
      `${CTX}\n\nĐÂY LÀ KẾT QUẢ PHÂN TÍCH chiều "${d.key}" cần THẨM TRA ĐỐI KHÁNG:\n` +
      JSON.stringify(finding, null, 1) +
      `\n\nNhiệm vụ: KIỂM CHỨNG độc lập trên code+data THẬT. Với mỗi problem: nó CÓ THẬT không, hay đọc nhầm code/
data? Mở tasks/ascension.py + frame liên quan để xác nhận. Với mỗi proposed_change: nó có REGRESS hành vi
đang chạy tốt (26 run ổn định) không? Có bỏ sót guard hiện có đã hấp thụ vấn đề không? Điều chỉnh severity nếu
tác hại thực nhỏ hơn tưởng. net_recommendation: nên LÀM / HOÃN / BỎ, 1-2 câu.`,
      { label: `verify:${d.key}`, phase: 'Verify', schema: VERIFY_SCHEMA, model: 'sonnet', effort: 'medium' },
    ).then((v) => ({ dimension: d.key, sev_hint: d.sev, finding, verify: v }))
  },
)

phase('Synthesize')
const clean = results.filter(Boolean)
const roadmap = await agent(
  `${CTX}\n\nDưới đây là 6 chiều phân tích ĐÃ VERIFY đối kháng (mỗi mục: finding + verify):\n` +
  JSON.stringify(clean, null, 1) +
  `\n\nNhiệm vụ: gộp thành ROADMAP CẢI THIỆN ASCENSION có ưu tiên, CHỈ giữ vấn đề đã confirmed=true và đề xuất
KHÔNG regress. Sắp xếp P0->P3. Mỗi hạng mục: [mã ưu tiên] tiêu đề — file/hàm — thay đổi cụ thể — effort(S/M/L)
— rủi ro — bằng chứng (frame/dòng/số liệu). Tách rõ:
(1) SỬA để hoàn tất 70 run (reliability) vs (2) NÂNG chất lượng quyết định (POWER/leak) vs (3) polish.
Nêu các CÂU HỎI MỞ §8 mà data 26-run này VỪA TRẢ LỜI được, và câu nào vẫn cần capture/live-test thêm.
Cuối cùng: đề xuất "làm gì TIẾP THEO ngay" (1 việc P0) và ước lượng ROI mỗi nhóm. Trả lời tiếng Việt, gọn, dạng markdown.`,
  { label: 'synthesize:roadmap', phase: 'Synthesize', model: 'sonnet', effort: 'high' },
)

return { roadmap, dimensions: clean }
