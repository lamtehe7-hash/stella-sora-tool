/* Logic UI: poll trạng thái từ Python (pywebview js_api) mỗi giây, render kiểu Alas.
   i18n: text tĩnh gắn data-i18n, text động dùng t(key); đổi ngôn ngữ ở Home (VI/EN). */
'use strict';

const $ = (id) => document.getElementById(id);

let lastSeq = 0;
let autoScroll = true;
let logCount = 0;
const LOG_MAX = 800;
let currentPage = 'overview';
let currentTask = null;   // tên task đang mở ở page-task
let lastState = null;     // snapshot poll gần nhất
let LANG = 'vi';

// ===== i18n =====
const I18N = {
  nav_home:       { vi: 'Home', en: 'Home' },
  nav_settings:   { vi: 'Cấu hình', en: 'Settings' },
  side_overview:  { vi: 'Overview', en: 'Overview' },
  side_task_group:{ vi: 'Task', en: 'Tasks' },
  card_scheduler: { vi: 'Scheduler', en: 'Scheduler' },
  card_running:   { vi: 'Đang chạy', en: 'Running' },
  card_pending:   { vi: 'Sẵn sàng', en: 'Ready' },
  card_waiting:   { vi: 'Chờ đến hạn', en: 'Waiting' },
  card_log:       { vi: 'Log', en: 'Log' },
  empty_task:     { vi: 'Không có task', en: 'No task' },
  setting_btn:    { vi: 'Cài đặt', en: 'Setting' },
  task_next_label:{ vi: 'Chạy kế tiếp', en: 'Next run' },
  btn_run_now:    { vi: 'Chạy ngay', en: 'Run now' },
  task_hint:      { vi: '“Chạy ngay” đặt task đến hạn tức thì. Nếu scheduler đang chạy, task sẽ được nhặt trong vòng lặp; nếu không, tool chạy đơn lẻ task này rồi dừng.',
                    en: '“Run now” makes the task due immediately. If the scheduler is running it will be picked up in the loop; otherwise the tool runs just this task once and stops.' },
  home_theme:     { vi: 'Giao diện / Theme', en: 'Theme' },
  theme_light:    { vi: 'Sáng', en: 'Light' },
  theme_dark:     { vi: 'Tối', en: 'Dark' },
  home_lang:      { vi: 'Ngôn ngữ / Language', en: 'Language' },
  home_note:      { vi: 'Tool tự động hoá Stella Sora (EN) trên giả lập — miễn phí & mã nguồn để dùng cá nhân.',
                    en: 'Automation tool for Stella Sora (EN) on emulators — free & open source for personal use.' },
  settings_title: { vi: 'Cấu hình', en: 'Settings' },
  lbl_serial:     { vi: 'Serial giả lập', en: 'Emulator serial' },
  lbl_adb:        { vi: 'Đường dẫn adb.exe', en: 'adb.exe path' },
  lbl_reset:      { vi: 'Giờ reset daily (UTC, HH:MM)', en: 'Daily reset (UTC, HH:MM)' },
  lbl_close:      { vi: 'Đóng game khi Cleanup', en: 'Close game on Cleanup' },
  btn_save:       { vi: 'Lưu cấu hình', en: 'Save' },
  saved_note:     { vi: '✓ Đã lưu', en: '✓ Saved' },
  // --- Ascension settings ---
  grp_map:        { vi: 'Map (Monolith)', en: 'Map (Monolith)' },
  lbl_map:        { vi: 'Map sẽ chạy', en: 'Map to run' },
  opt_map_keep:   { vi: 'Giữ map game nhớ', en: 'Keep current map' },
  hint_map:       { vi: 'Game nhớ map lần trước; chọn ở đây để tool tự chuyển map.',
                    en: 'The game remembers the last map; pick here to auto-switch.' },
  grp_runs:       { vi: 'Vé & số lần chạy', en: 'Tickets & runs' },
  lbl_runs:       { vi: 'Số run mỗi lần (mỗi run 1 vé)', en: 'Runs per session (1 ticket each)' },
  hint_runs:      { vi: 'Hết vé Quick Battle thì tự dừng sớm.', en: 'Stops early when out of Quick Battle tickets.' },
  grp_squad:      { vi: 'Đội hình (Squad)', en: 'Squad' },
  lbl_squad:      { vi: 'Squad dùng (0 = giữ nguyên)', en: 'Squad to use (0 = keep current)' },
  hint_squad:     { vi: 'Tự vuốt tới squad này trước khi vào run.', en: 'Auto-swipes to this squad before the run.' },
  grp_preset:     { vi: 'Kiểm tra Preset', en: 'Preset check' },
  lbl_preset:     { vi: 'Khi “Preset not set”', en: 'When “Preset not set”' },
  opt_warn:       { vi: 'Cảnh báo & chạy tiếp', en: 'Warn & continue' },
  opt_skip:       { vi: 'Bỏ qua hôm nay', en: 'Skip today' },
  opt_abort:      { vi: 'Báo lỗi & dừng', en: 'Error & stop' },
  grp_card:       { vi: 'Chọn thẻ', en: 'Card pick' },
  lbl_card:       { vi: 'Ưu tiên khi nhiều thẻ 👍', en: 'Priority when multiple 👍' },
  opt_levelgain:  { vi: 'Mức tăng level cao nhất', en: 'Highest level gain' },
  opt_sr:         { vi: 'Ưu tiên Super Rare', en: 'Prefer Super Rare' },
  opt_leftmost:   { vi: 'Thẻ trái nhất', en: 'Leftmost card' },
  lbl_smartevt:   { vi: 'Event: ưu tiên thưởng item free (Potential/Note)', en: 'Event: prefer free-item rewards (Potential/Note)' },
  grp_shop:       { vi: 'Chiến lược Shop', en: 'Shop strategy' },
  lbl_melody:     { vi: 'Chỉ mua Melody khi cần thiết', en: 'Buy Melody only when needed' },
  lbl_milestone:  { vi: 'Mốc enhance giữa run (coin)', en: 'Mid-run enhance cap (coin)' },
  lbl_reserve:    { vi: 'Coin dự trữ để enhance', en: 'Enhance reserve (coin)' },
  lbl_refshelf:   { vi: 'Refresh kệ ở phòng cuối', en: 'Refresh shelf in last room' },
  lbl_refcards:   { vi: 'Refresh bộ thẻ khi không có 👍', en: 'Refresh cards when no 👍' },
  grp_run:        { vi: 'Tinh chỉnh run', en: 'Run tuning' },
  lbl_brief:      { vi: 'Bật Brief mode (chạy nhanh)', en: 'Brief mode (faster)' },
  lbl_saverec:    { vi: 'Lưu Record cuối run', en: 'Save Record at end of run' },
  lbl_timeout:    { vi: 'Thời gian tối đa 1 run (giây)', en: 'Max run time (seconds)' },
  btn_save_asc:   { vi: 'Lưu cài đặt Ascension', en: 'Save Ascension settings' },
  lbl_diff_asc:   { vi: 'Difficulty', en: 'Difficulty' },
  opt_diff_auto:  { vi: 'Tự chọn bậc đã-clear cao nhất', en: 'Auto: highest cleared' },
  lbl_skipcap:    { vi: 'Bỏ qua khi Weekly Limit đầy (3000/3000)', en: 'Skip when Weekly Limit is full (3000/3000)' },
  hint_skipcap:   { vi: 'Đã đầy tuần thì run = 0 stub. Bỏ tick để vẫn chạy build sức mạnh Record (POWER).',
                    en: 'Capped week = 0 stubs. Uncheck to still run for Record power (POWER).' },
  lbl_objective:  { vi: 'Mục tiêu tối ưu', en: 'Optimization objective' },
  opt_power:      { vi: 'POWER — Record mạnh (mặc định)', en: 'POWER — strong Record (default)' },
  opt_score:      { vi: 'SCORE — farm stub (thử nghiệm)', en: 'SCORE — stub farm (experimental)' },
  lbl_reserve_last: { vi: 'Coin dự trữ enhance (phòng cuối)', en: 'Enhance reserve (last room)' },
  // --- Ascension: Record + phân tích phiên capture ---
  lbl_dissolve:     { vi: 'Huỷ Record yếu tại màn Save (không lưu record rác)', en: 'Discard weak Records at the Save screen' },
  lbl_dissolve_band:{ vi: 'Huỷ record có khung ≤', en: 'Discard records with frame ≤' },
  opt_band_silver:  { vi: 'Silver (rank 1–5)', en: 'Silver (rank 1–5)' },
  opt_band_green:   { vi: 'Green (rank 6–10)', en: 'Green (rank 6–10)' },
  opt_band_blue:    { vi: 'Blue (rank 11–20)', en: 'Blue (rank 11–20)' },
  opt_band_golden:  { vi: 'Golden (rank 21–30)', en: 'Golden (rank 21–30)' },
  hint_dissolve:    { vi: 'Mặc định TẮT (giữ mọi Record tái dùng POWER). Bật: tại màn Save cuối run, đọc MÀU KHUNG badge rank (silver 1–5 / green 6–10 / blue 11–20 / golden 21–30 / chroma 31–40) — record khung ≤ mức chọn sẽ bị HUỶ, chroma luôn giữ. ⚠️ Bước huỷ PHÁ HỦY chưa verify live — hiện FAIL-SAFE (vẫn LƯU + log, không mất data).',
                      en: 'Off by default (keep every Record for POWER reuse). When on: at the end-of-run Save screen, reads the rank badge FRAME COLOR (silver 1–5 / green 6–10 / blue 11–20 / golden 21–30 / chroma 31–40) — records with frame ≤ the chosen level are DISCARDED, chroma always kept. ⚠️ The discard step is DESTRUCTIVE and not verified live — currently FAIL-SAFE (still SAVES + logs, no data loss).' },
  an_grp:       { vi: 'Phân tích phiên capture', en: 'Analyze capture session' },
  an_hint:      { vi: 'Đọc data phiên nghiên cứu (ảnh + log) và tính chỉ số — thuần cục bộ, không cần mạng/AI.',
                  en: 'Reads a research session (images + log) and computes stats — fully local, no network/AI.' },
  an_session:   { vi: 'Phiên', en: 'Session' },
  an_none:      { vi: 'Chưa có phiên capture nào (chạy dev_tools/ascension_capture.py để tạo).',
                  en: 'No capture sessions yet (run dev_tools/ascension_capture.py to create one).' },
  btn_analyze:  { vi: 'Phân tích', en: 'Analyze' },
  btn_export:   { vi: 'Xuất báo cáo', en: 'Export report' },
  btn_cleanup:  { vi: 'Dọn ảnh (giải phóng ổ)', en: 'Clean images (free disk)' },
  an_confirm:   { vi: 'Xoá TOÀN BỘ ảnh chụp của phiên này để giải phóng ổ? Giữ lại log + báo cáo. KHÔNG hoàn tác được.',
                  en: 'Delete ALL screenshots of this session to free disk? Keeps log + report. Cannot be undone.' },
  m_runs:       { vi: 'Run hoàn tất', en: 'Runs done' },
  m_time:       { vi: 'Tổng thời gian', en: 'Total time' },
  m_avg:        { vi: 'TB mỗi run', en: 'Avg/run' },
  m_potion:     { vi: 'Potential đã mua', en: 'Potentials bought' },
  m_melody:     { vi: 'Melody đã mua', en: 'Melody bought' },
  m_melody_skip:{ vi: 'Melody bỏ qua', en: 'Melody skipped' },
  m_enh:        { vi: 'Lượt Enhance', en: 'Enhances' },
  m_event:      { vi: 'Event xử lý', en: 'Events' },
  m_cards:      { vi: 'Thẻ đã chọn', en: 'Cards picked' },
  m_spend_buy:  { vi: 'Coin mua hàng', en: 'Coin on shop' },
  m_spend_enh:  { vi: 'Coin enhance', en: 'Coin on enhance' },
  m_peak:       { vi: 'Coin đỉnh TB/run', en: 'Avg peak coin/run' },
  m_left:       { vi: 'Coin dư (median)', en: 'Leftover coin (median)' },
  m_images:     { vi: 'Ảnh chiếm ổ', en: 'Images on disk' },
  m_tech:       { vi: 'Kỹ thuật (độ tin cậy tool)', en: 'Technical (tool reliability)' },
  m_warn:       { vi: 'cảnh báo', en: 'warnings' },
  m_complete_yes:{ vi: '✓ Hoàn tất', en: '✓ Completed' },
  m_complete_no: { vi: '✕ Chưa xong', en: '✕ Incomplete' },
  // --- Bounty Trial settings ---
  grp_trial:      { vi: 'Loại Trial (map)', en: 'Trial type (map)' },
  lbl_trial:      { vi: 'Trial sẽ chạy', en: 'Trial to run' },
  opt_trial_basic:  { vi: 'Basic Trial — Nguyên liệu', en: 'Basic Trial — Basic Material' },
  opt_trial_tierup: { vi: 'Tier-up Trial — Thăng bậc', en: 'Tier-up Trial — Trekker Promotion' },
  opt_trial_skill:  { vi: 'Skill Trial — Nâng skill', en: 'Skill Trial — Skill Upgrade' },
  opt_trial_emblem: { vi: 'Emblem Trial — Emblem', en: 'Emblem Trial — Emblem Material' },
  lbl_difficulty: { vi: 'Độ khó', en: 'Difficulty' },
  opt_diff_keep:  { vi: 'Giữ nguyên game nhớ', en: 'Keep current' },
  hint_bounty:    { vi: 'Quick Battle tự auto-clear (sweep) tối đa số lần theo Vigor hiện có. Difficulty phải đã clear thì Quick Battle mới khả dụng.',
                    en: 'Quick Battle auto-clears (sweeps) as many times as your Vigor allows. The difficulty must be cleared before Quick Battle is available.' },
  btn_save_bounty:{ vi: 'Lưu cài đặt Bounty Trial', en: 'Save Bounty Trial settings' },
  // --- Event settings ---
  grp_event_stage:   { vi: 'Stage sự kiện', en: 'Event stage' },
  lbl_event_stage:   { vi: 'Stage sẽ Quick Battle', en: 'Stage to Quick Battle' },
  hint_event_stage:  { vi: 'Để TRỐNG = stage cao nhất (phải nhất). Nhập tên (vd 1-12) để chọn đúng stage — tool tự cuộn + OCR badge tìm.',
                       en: 'Leave EMPTY = highest stage (rightmost). Enter a name (e.g. 1-12) to pick that exact stage — the tool scrolls & OCRs badges to find it.' },
  lbl_event_battles: { vi: 'Số trận (0 = tối đa theo Vigor)', en: 'Battles (0 = max by Vigor)' },
  hint_event:        { vi: 'Sự kiện theo đợt: đổi event cần re-crop banner (assets/en/event/EVENT_BANNER.png) và chỉnh lại stage. Không tìm thấy banner/stage thì tool bỏ qua (không chạy nhầm).',
                       en: 'Events are temporary: switching events needs re-cropping the banner (assets/en/event/EVENT_BANNER.png) and re-setting the stage. If the banner/stage is not found the tool skips (never runs the wrong stage).' },
  btn_save_event:    { vi: 'Lưu cài đặt Event', en: 'Save Event settings' },
  // --- Event First Clear settings ---
  side_group_event:  { vi: 'Event', en: 'Event' },
  grp_efc_diff:      { vi: 'Độ khó tự đánh', en: 'Difficulties to clear' },
  lbl_efc_normal:    { vi: 'Normal', en: 'Normal' },
  lbl_efc_hard:      { vi: 'Hard', en: 'Hard' },
  lbl_efc_challenge: { vi: 'Challenge (tab thứ 3)', en: 'Challenge (3rd tab)' },
  hint_efc_diff:     { vi: 'Mỗi lần chạy, với từng độ khó được bật, tool tìm các stage còn sao XÁM (chưa first-clear) rồi tự đánh (Deploy + Auto-Battle). Độ khó đang KHOÁ sẽ tự bỏ qua.',
                       en: 'Each run, for every enabled difficulty, the tool finds stages that still have GRAY stars (not first-cleared) and plays them (Deploy + Auto-Battle). Locked difficulties are skipped.' },
  grp_efc_tune:      { vi: 'Tinh chỉnh', en: 'Tuning' },
  lbl_efc_max:       { vi: 'Trần số stage mỗi lần chạy', en: 'Max stages per run' },
  lbl_efc_timeout:   { vi: 'Thời gian tối đa 1 trận (giây)', en: 'Max time per battle (seconds)' },
  hint_efc_tune:     { vi: 'Auto-Battle tự bật khi phát hiện đang TẮT (nhận biết bằng viền xanh quanh nút) — không bao giờ vô tình tắt trận đang chạy. Sự kiện theo đợt: đổi event cần re-crop banner (như Event Daily).',
                       en: 'Auto-Battle is enabled only when detected OFF (via the blue ring around the button) — it never accidentally turns off a running battle. Events are temporary: switching events needs re-cropping the banner (like Event Daily).' },
  btn_save_efc:      { vi: 'Lưu cài đặt Event First Clear', en: 'Save Event First Clear settings' },
  grp_hl_invite:     { vi: 'Hẹn hò (Invite)', en: 'Dating (Invite)' },
  lbl_hl_count:      { vi: 'Số lượt hẹn mỗi ngày (tối đa 5)', en: 'Invites per day (max 5)' },
  lbl_hl_gift:       { vi: 'Tặng quà cuối buổi hẹn (x2 Affinity)', en: 'Send a gift at the end (x2 Affinity)' },
  lbl_hl_targets:    { vi: 'Ưu tiên hẹn (tên NV, cách nhau dấu phẩy)', en: 'Priority dates (character names, comma-separated)' },
  hint_hl_targets:   { vi: 'Hẹn các NV này TRƯỚC (dù nằm sâu trong lưới), rồi grid-order lấp cho đủ. ⚠️ Cần có ảnh portrait NV trong assets/en/heartlink/chars/ — báo Claude thêm tên nếu muốn. Chưa có ảnh → bỏ qua tên đó.',
                       en: 'Dates these characters FIRST (even deep in the grid), then grid-order fills the rest. ⚠️ Needs a portrait image in assets/en/heartlink/chars/ — ask Claude to add names. Missing image → that name is skipped.' },
  hint_hl:           { vi: 'Mỗi ngày tự hẹn tối đa 5 nhân vật (duyệt lưới trái→phải, trên→dưới; bỏ qua ai đã hẹn hôm nay). Mỗi lượt: Invite → chọn địa điểm ĐẦU → tua nhanh buổi hẹn (Skip) → (tuỳ chọn) tặng quà ô đầu (tốn 1 quà, +2x Affinity). Task con Mail chưa hỗ trợ.',
                       en: 'Each day auto-dates up to 5 characters (grid order left→right, top→bottom; skips those already dated today). Each: Invite → pick the FIRST location → fast-forward the date (Skip) → optionally send the first gift (costs 1 gift, +2x Affinity). The Mail sub-task is not supported yet.' },
  btn_save_hl:       { vi: 'Lưu cài đặt Heartlink', en: 'Save Heartlink settings' },
  lbl_hl_do_invite:  { vi: 'Bật hẹn hò (Invite)', en: 'Enable dating (Invite)' },
  grp_hl_mail:       { vi: 'Mail — Delivery Service (gửi quà)', en: 'Mail — Delivery Service (gifts)' },
  lbl_hl_do_mail:    { vi: 'Bật gửi quà Mail (Delivery Service)', en: 'Enable Mail gifting (Delivery Service)' },
  lbl_hl_mailcount:  { vi: 'Số quà gửi mỗi ngày (tối đa 10)', en: 'Gifts to send per day (max 10)' },
  lbl_hl_mailtop:    { vi: 'Dồn hết quà cho NV TRÊN CÙNG danh sách', en: 'Send all gifts to the TOP character in the list' },
  hint_hl_mail:      { vi: 'Hoặc nhập tên NV + số quà (tổng ≤ 10) để chỉ định người nhận — nhập tên sẽ TỰ bỏ tick "dồn cho NV trên cùng". Gửi ô quà đầu (loved 😄). ⚠️ Cần ảnh portrait NV trong assets/en/heartlink/chars/ (báo Claude thêm tên); tên không khớp → bỏ. Giới hạn game: 10 quà/ngày.',
                       en: 'Or enter character names + gift counts (total ≤ 10) to target recipients — entering names AUTO-unchecks "send to top". Sends the first gift (loved 😄). ⚠️ Needs portrait images in assets/en/heartlink/chars/ (ask Claude to add names); unmatched names are skipped. Game limit: 10 gifts/day.' },
  lbl_hl_mailname:   { vi: 'Tên NV', en: 'Name' },
  lbl_hl_mailqty:    { vi: 'Số quà', en: 'Qty' },
  // --- dynamic ---
  ready:          { vi: 'sẵn sàng', en: 'ready' },
  disabled:       { vi: 'đã tắt', en: 'disabled' },
  off_short:      { vi: 'tắt', en: 'off' },
  running_now:    { vi: '▶ đang chạy', en: '▶ running' },
  st_off:         { vi: 'Chưa chạy', en: 'Not running' },
  st_idle:        { vi: 'Đang khởi động...', en: 'Starting...' },
  st_waiting:     { vi: 'Chờ task đến hạn', en: 'Waiting for tasks' },
  st_stopped:     { vi: 'Đã dừng', en: 'Stopped' },
  st_human:       { vi: 'Cần người can thiệp', en: 'Needs attention' },
  st_run_prefix:  { vi: 'Đang chạy: ', en: 'Running: ' },
  st_err_prefix:  { vi: 'Lỗi: ', en: 'Error: ' },
  btn_start:      { vi: 'Bắt đầu', en: 'Start' },
  btn_stop:       { vi: '■ Dừng', en: '■ Stop' },
};

// Mô tả chi tiết từng task sẽ làm gì (song ngữ) — hiện ở trang chi tiết task.
const TASK_DESC = {
  Login:       { vi: 'Mở game (nếu chưa chạy) và đưa về màn hình chính, tự vượt các popup đăng nhập.',
                 en: 'Opens the game (if not running) and returns to the home screen, dismissing login popups.' },
  Mail:        { vi: 'Vào hộp thư, nhận tất cả thư & quà đính kèm (Claim All).',
                 en: 'Opens the mailbox and claims all mail & attached gifts (Claim All).' },
  Dispatch:    { vi: 'Nhận thưởng các đội commission đã về, rồi tự tái phái đủ 4 đội (Quick Select, thời lượng 20h).',
                 en: 'Claims completed commission rewards, then re-dispatches all 4 teams (Quick Select, 20h duration).' },
  Shop:        { vi: 'Vào Shop nhận quà daily miễn phí.',
                 en: 'Opens the Shop and claims the free daily gift.' },
  BountyTrial: { vi: 'Tiêu Vigor bằng Trial Quick Battle (Bounty): chọn loại Trial (map) và độ khó bên dưới, tự sweep tối đa theo Vigor.',
                 en: 'Spends Vigor via Trial (Bounty) Quick Battle: pick the Trial (map) and difficulty below, auto-sweeps to the max your Vigor allows.' },
  Ascension:   { vi: 'Chạy Monolith Quick Battle (tốn vé Monolith, KHÔNG tốn Vigor): tự chọn map/squad, chọn thẻ, mua shop và enhance theo cấu hình bên dưới.',
                 en: 'Runs Monolith Quick Battle (uses Monolith tickets, NOT Vigor): auto map/squad select, card pick, shop buying and enhancing per the settings below.' },
  EventDaily:  { vi: 'Quick Battle sweep ở Battle Stage của sự kiện (tiêu Vigor): vào qua banner sự kiện ở home, chọn stage & số trận bên dưới. Sau đó tự nhận quà Event Missions nếu có chấm đỏ.',
                 en: 'Quick Battle sweep at the current event’s Battle Stage (spends Vigor): enters via the home event banner, pick stage & battle count below. Then auto-claims Event Missions rewards if the red dot is present.' },
  EventFirstClear: { vi: 'Tự đánh (Deploy + Auto-Battle) các stage Battle Stage sự kiện còn sao XÁM để lấy quà First Clear. Chọn độ khó (Normal/Hard/Challenge) bên dưới — độ khó đang khoá sẽ tự bỏ qua. Tiêu Vigor (30/trận).',
                 en: 'Auto-plays (Deploy + Auto-Battle) the event Battle Stage stages that still have GRAY stars to grab First Clear rewards. Pick difficulties (Normal/Hard/Challenge) below — locked ones are skipped. Spends Vigor (30/battle).' },
  Grant:       { vi: 'Nhận quà Startup Grant: nếu tab "Company Goal" hoặc "Grant Milestone" có chấm đỏ thì bấm Claim All (Company Goal trước để lên Grant Tier), tự đóng popup nhận quà.',
                 en: 'Claims Startup Grant rewards: if the "Company Goal" or "Grant Milestone" tab has a red dot, presses Claim All (Company Goal first to raise Grant Tier) and auto-dismisses the reward popups.' },
  Heartlink:   { vi: 'Hẹn hò tăng Affinity qua Heartlink: tự hẹn tối đa 5 nhân vật/ngày (chọn địa điểm đầu, tua nhanh, tuỳ chọn tặng quà x2). Bỏ qua ai đã hẹn hôm nay. Task con Mail chưa làm.',
                 en: 'Raises Affinity via Heartlink dating: auto-dates up to 5 characters/day (first location, fast-forward, optional x2 gift). Skips those already dated today. The Mail sub-task is not implemented yet.' },
  DailyReward: { vi: 'Nhận tất cả nhiệm vụ hằng ngày + các mốc điểm hoạt động (chạy gần cuối để gom trọn điểm sau các task khác).',
                 en: 'Claims all daily missions plus activity-point milestones (runs near the end to collect full points after other tasks).' },
  Cleanup:     { vi: 'Về màn hình chính; (tuỳ chọn) đóng hẳn game sau khi chạy xong tất cả task.',
                 en: 'Returns to the home screen; optionally closes the game after all tasks finish.' },
};

// Tên hiển thị đẹp cho task (key nội bộ không đổi để giữ tương thích config/API).
const TASK_LABEL = { BountyTrial: 'Bounty Trial', EventDaily: 'Event Daily',
                     EventFirstClear: 'Event First Clear' };
const label = (name) => TASK_LABEL[name] || name;

// Nhóm task thu gọn/mở rộng trong sidebar (kiểu Alas). Thành viên phải LIỀN KỀ trong ORDER.
const MENU_GROUPS = { Event: ['EventDaily', 'EventFirstClear'] };
const TASK_GROUP = {};
Object.entries(MENU_GROUPS).forEach(([g, arr]) => arr.forEach((n) => { TASK_GROUP[n] = g; }));
const groupCollapsed = JSON.parse(localStorage.getItem('sst-groups') || '{}');  // {Event:true} = thu gọn

function t(key) {
  const e = I18N[key];
  return e ? (e[LANG] || e.vi) : key;
}

function applyI18n() {
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
}

async function setLang(lang) {
  LANG = (lang === 'en') ? 'en' : 'vi';
  localStorage.setItem('sst-lang', LANG);
  document.documentElement.lang = LANG;
  applyI18n();
  if (lastState) {
    renderHeader(lastState);
    if (currentPage === 'overview') renderLists(lastState);
    if (currentPage === 'task') renderTaskDetail();
  }
  syncAutoscrollBtn();
  $('page-title').textContent = titleFor(currentPage, currentTask);
  try { if (window.pywebview) await pywebview.api.set_lang(LANG); } catch (e) { /* ignore */ }
}

document.querySelectorAll('[data-lang]').forEach((b) =>
  b.addEventListener('click', () => setLang(b.dataset.lang)));

// ===== Theme =====
function setTheme(th) {
  document.documentElement.dataset.theme = th;
  localStorage.setItem('sst-theme', th);
}
setTheme(localStorage.getItem('sst-theme') || 'light');
document.querySelectorAll('[data-theme]').forEach((b) => {
  if (b.tagName === 'BUTTON') b.addEventListener('click', () => setTheme(b.dataset.theme));
});

// ===== Toast =====
let toastTimer = null;
function toast(msg) {
  const el = $('toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add('hidden'), 2500);
}

// ===== Điều hướng =====
function titleFor(page, taskName) {
  if (page === 'task') return label(taskName) || '';
  return { home: t('nav_home'), overview: t('side_overview'), settings: t('nav_settings') }[page] || '';
}

function showPage(page, taskName) {
  currentPage = page;
  currentTask = page === 'task' ? taskName : null;
  ['overview', 'task', 'home', 'settings'].forEach((p) => {
    $('page-' + p).classList.toggle('hidden', p !== page);
  });
  $('page-title').textContent = titleFor(page, taskName);

  document.querySelectorAll('.rail-item').forEach((b) => {
    b.classList.toggle('active', b.dataset.page === page ||
      (b.dataset.page === 'overview' && page === 'task'));
  });
  document.querySelectorAll('#sidebar .menu-item').forEach((m) => {
    m.classList.toggle('active',
      (m.dataset.page === page && page !== 'task') ||
      (page === 'task' && m.dataset.task === taskName));
  });

  // Cài đặt Ascension chỉ hiện khi mở đúng task Ascension
  const isAsc = page === 'task' && taskName === 'Ascension';
  $('asc-settings').classList.toggle('hidden', !isAsc);
  if (isAsc) loadAscension();

  // Cài đặt Bounty Trial chỉ hiện khi mở đúng task BountyTrial
  const isBounty = page === 'task' && taskName === 'BountyTrial';
  $('bounty-settings').classList.toggle('hidden', !isBounty);
  if (isBounty) loadBounty();

  // Cài đặt Event chỉ hiện khi mở đúng task EventDaily
  const isEvent = page === 'task' && taskName === 'EventDaily';
  $('event-settings').classList.toggle('hidden', !isEvent);
  if (isEvent) loadEvent();

  // Cài đặt Event First Clear chỉ hiện khi mở đúng task EventFirstClear
  const isEfc = page === 'task' && taskName === 'EventFirstClear';
  $('efc-settings').classList.toggle('hidden', !isEfc);
  if (isEfc) loadEventFirstClear();

  // Cài đặt Heartlink chỉ hiện khi mở đúng task Heartlink
  const isHl = page === 'task' && taskName === 'Heartlink';
  $('heartlink-settings').classList.toggle('hidden', !isHl);
  if (isHl) loadHeartlink();

  if (page === 'task' && lastState) renderTaskDetail();
  if (page === 'settings') loadConfig();
}

document.querySelectorAll('.rail-item').forEach((b) =>
  b.addEventListener('click', () => showPage(b.dataset.page)));
document.querySelector('#sidebar .menu-item[data-page="overview"]')
  .addEventListener('click', () => showPage('overview'));

// ===== Render Overview =====
function taskRow(tk, extra) {
  return `<div class="task-row">
    <div><div class="task-name">${label(tk.name)}</div>${extra || ''}</div>
    <button class="btn btn-sm" data-setting="${tk.name}">${t('setting_btn')}</button>
  </div>`;
}

function renderLists(s) {
  const running = s.tasks.filter((tk) => tk.name === s.current && s.state === 'running');
  const pending = s.tasks.filter((tk) => tk.enable && tk.ready && tk.name !== s.current);
  const waiting = s.tasks.filter((tk) => tk.enable && !tk.ready && tk.name !== s.current);
  const empty = `<div class="empty">${t('empty_task')}</div>`;

  $('list-running').innerHTML = running.length ? running.map((tk) => taskRow(tk)).join('') : empty;
  $('list-pending').innerHTML = pending.length
    ? pending.map((tk) => taskRow(tk, `<div class="task-time">${t('ready')}</div>`)).join('') : empty;
  $('list-waiting').innerHTML = waiting.length
    ? waiting.map((tk) => taskRow(tk, `<div class="task-time">${tk.next_run}</div>`)).join('') : empty;

  document.querySelectorAll('[data-setting]').forEach((b) =>
    b.addEventListener('click', () => showPage('task', b.dataset.setting)));

  const miniOf = (tk) => tk.name === s.current && s.state === 'running' ? '▶'
    : (tk.enable ? (tk.ready ? t('ready') : tk.next_run) : t('off_short'));
  const itemHtml = (tk, child) =>
    `<div class="menu-item ${child ? 'child' : ''} ${tk.enable ? '' : 'task-off'}" data-task="${tk.name}">
      ${label(tk.name)}<span class="mini">${miniOf(tk)}</span></div>`;

  let html = '';
  const doneGroups = new Set();
  s.tasks.forEach((tk) => {
    const g = TASK_GROUP[tk.name];
    if (!g) { html += itemHtml(tk, false); return; }
    if (doneGroups.has(g)) return;               // các thành viên khác gộp vào lần render đầu của nhóm
    doneGroups.add(g);
    const members = s.tasks.filter((x) => TASK_GROUP[x.name] === g);
    const col = !!groupCollapsed[g];
    const gname = t('side_group_' + g.toLowerCase());
    html += `<div class="menu-parent ${col ? 'collapsed' : ''}" data-group="${g}">
      <span class="caret">▾</span>${gname}</div>
      <div class="menu-children" data-group-body="${g}"${col ? ' style="display:none"' : ''}>
      ${members.map((m) => itemHtml(m, true)).join('')}</div>`;
  });
  $('menu-tasks').innerHTML = html;

  document.querySelectorAll('#menu-tasks .menu-parent').forEach((p) =>
    p.addEventListener('click', () => {
      const g = p.dataset.group;
      groupCollapsed[g] = !groupCollapsed[g];
      localStorage.setItem('sst-groups', JSON.stringify(groupCollapsed));
      renderLists(lastState);
    }));
  document.querySelectorAll('#menu-tasks .menu-item').forEach((m) => {
    m.addEventListener('click', () => showPage('task', m.dataset.task));
    m.classList.toggle('active', currentPage === 'task' && m.dataset.task === currentTask);
  });
}

const STATUS_DOT = {
  off: 'dot-idle', idle: 'dot-waiting', running: 'dot-running', waiting: 'dot-waiting',
  stopped: 'dot-idle', error: 'dot-error', human: 'dot-error',
};
const STATUS_KEY = {
  off: 'st_off', idle: 'st_idle', waiting: 'st_waiting', stopped: 'st_stopped', human: 'st_human',
};

function renderHeader(s) {
  $('status-dot').className = 'dot ' + (STATUS_DOT[s.state] || 'dot-idle');
  $('status-text').textContent =
    s.state === 'running' ? t('st_run_prefix') + s.current :
    s.state === 'error' ? t('st_err_prefix') + s.error :
    (STATUS_KEY[s.state] ? t(STATUS_KEY[s.state]) : s.state);

  const btn = $('btn-scheduler');
  if (s.alive) {
    btn.textContent = t('btn_stop');
    btn.className = 'btn btn-danger';
  } else {
    btn.textContent = t('btn_start');
    btn.className = 'btn btn-primary';
  }
}

function renderTaskDetail() {
  const tk = lastState.tasks.find((x) => x.name === currentTask);
  if (!tk) return;
  $('task-title').textContent = label(tk.name);
  const desc = TASK_DESC[tk.name];
  $('task-desc').textContent = desc ? (desc[LANG] || desc.vi) : '';
  $('task-enable').checked = tk.enable;
  $('task-next').textContent =
    lastState.state === 'running' && lastState.current === tk.name ? t('running_now')
      : (tk.enable ? (tk.ready ? t('ready') : tk.next_run) : t('disabled'));
}

function appendLog(lines) {
  if (!lines.length) return;
  const body = $('log-body');
  body.textContent += (body.textContent ? '\n' : '') + lines.join('\n');
  logCount += lines.length;
  if (logCount > LOG_MAX) {
    const arr = body.textContent.split('\n').slice(-LOG_MAX);
    body.textContent = arr.join('\n');
    logCount = arr.length;
  }
  if (autoScroll) body.scrollTop = body.scrollHeight;
}

// ===== Poll =====
async function poll() {
  if (!window.pywebview) return;
  try {
    const s = await pywebview.api.poll(lastSeq);
    lastState = s;
    lastSeq = s.seq;
    renderHeader(s);
    if (currentPage === 'overview') renderLists(s);
    if (currentPage === 'task') renderTaskDetail();
    appendLog(s.lines);
  } catch (e) { /* Python đang bận — bỏ qua nhịp này */ }
}

// ===== Nút bấm =====
$('btn-scheduler').addEventListener('click', async () => {
  const r = lastState && lastState.alive
    ? await pywebview.api.stop()
    : await pywebview.api.start();
  if (r) toast(r);
});

function syncAutoscrollBtn() {
  const b = $('btn-autoscroll');
  b.textContent = 'Auto Scroll ' + (autoScroll ? 'ON' : 'OFF');
  b.className = 'btn ' + (autoScroll ? 'btn-primary' : 'off');
}
$('btn-autoscroll').addEventListener('click', () => {
  autoScroll = !autoScroll;
  syncAutoscrollBtn();
  if (autoScroll) $('log-body').scrollTop = $('log-body').scrollHeight;
});

$('task-enable').addEventListener('change', async () => {
  if (currentTask) {
    const r = await pywebview.api.toggle(currentTask);
    if (r) toast(r);
    poll();
  }
});

$('btn-run-now').addEventListener('click', async () => {
  if (currentTask) {
    const r = await pywebview.api.run_now(currentTask);
    if (r) toast(r);
  }
});

// ===== Cấu hình chung =====
async function loadConfig() {
  if (!window.pywebview) return;
  const c = await pywebview.api.get_config();
  $('cfg-serial').value = c.serial;
  $('cfg-adb').value = c.adb_path;
  $('cfg-reset').value = c.daily_reset_utc;
  $('cfg-close').checked = c.close_game_on_cleanup;
}

$('btn-save-cfg').addEventListener('click', async () => {
  const r = await pywebview.api.save_config({
    serial: $('cfg-serial').value.trim(),
    adb_path: $('cfg-adb').value.trim(),
    daily_reset_utc: $('cfg-reset').value.trim(),
    close_game_on_cleanup: $('cfg-close').checked,
  });
  toast(r || t('saved_note'));
  flashSaved('cfg-saved');
});

// ===== Cài đặt Ascension =====
async function loadAscension() {
  if (!window.pywebview) return;
  const a = await pywebview.api.get_ascension();
  $('asc-map').value = a.map || '';
  $('asc-runs').value = a.runs_per_session;
  $('asc-diff').value = a.difficulty;
  $('asc-skipcap').checked = a.skip_when_capped;
  $('asc-squad').value = a.squad;
  $('asc-preset').value = a.preset_behavior;
  $('asc-card').value = a.card_priority;
  $('asc-smartevt').checked = a.smart_event_choice;
  $('asc-objective').value = a.objective;
  $('asc-melody').checked = a.buy_melody_when_needed_only;
  $('asc-milestone').value = a.enhance_milestone;
  $('asc-reserve').value = a.enhance_reserve;
  $('asc-reserve-last').value = a.enhance_reserve_last_room;
  $('asc-refshelf').checked = a.refresh_shelf_last_room;
  $('asc-refcards').checked = a.refresh_cards_no_recommend;
  $('asc-brief').checked = a.brief_mode;
  $('asc-save').checked = a.save_record;
  $('asc-dissolve').checked = a.dissolve_record;
  $('asc-dissolve-band').value = a.dissolve_max_band;
  updateDissolveUI();
  $('asc-timeout').value = a.run_timeout;
  loadCaptureSessions();
}

$('btn-save-asc').addEventListener('click', async () => {
  const r = await pywebview.api.save_ascension({
    map: $('asc-map').value,
    runs_per_session: parseInt($('asc-runs').value, 10) || 1,
    difficulty: parseInt($('asc-diff').value, 10) || 0,
    skip_when_capped: $('asc-skipcap').checked,
    squad: parseInt($('asc-squad').value, 10) || 0,
    preset_behavior: $('asc-preset').value,
    card_priority: $('asc-card').value,
    smart_event_choice: $('asc-smartevt').checked,
    objective: $('asc-objective').value,
    buy_melody_when_needed_only: $('asc-melody').checked,
    enhance_milestone: parseInt($('asc-milestone').value, 10) || 0,
    enhance_reserve: parseInt($('asc-reserve').value, 10) || 0,
    enhance_reserve_last_room: parseInt($('asc-reserve-last').value, 10) || 0,
    refresh_shelf_last_room: $('asc-refshelf').checked,
    refresh_cards_no_recommend: $('asc-refcards').checked,
    brief_mode: $('asc-brief').checked,
    save_record: $('asc-save').checked,
    dissolve_record: $('asc-dissolve').checked,
    dissolve_max_band: $('asc-dissolve-band').value,
    run_timeout: parseInt($('asc-timeout').value, 10) || 2400,
  });
  toast(r || t('saved_note'));
  flashSaved('asc-saved');
  loadAscension();
});

// Hiện/ẩn dropdown band theo checkbox "Huỷ Record yếu"
function updateDissolveUI() {
  $('asc-dissolve-band-row').style.display = $('asc-dissolve').checked ? '' : 'none';
}
$('asc-dissolve').addEventListener('change', updateDissolveUI);

// ===== Phân tích phiên capture (thuần cục bộ, không cần AI) =====
async function loadCaptureSessions() {
  if (!window.pywebview) return;
  const sel = $('asc-an-session');
  const list = await pywebview.api.list_capture_sessions();
  sel.innerHTML = '';
  if (!list.length) {
    const o = document.createElement('option');
    o.value = ''; o.textContent = t('an_none'); sel.appendChild(o);
    return;
  }
  for (const s of list) {
    const o = document.createElement('option');
    o.value = s.name;
    o.textContent = s.name + (s.has_images ? '' : ' ✓');
    sel.appendChild(o);
  }
}

function anCell(k, v) {
  return `<div class="an-cell"><div class="k">${k}</div><div class="v">${v ?? '—'}</div></div>`;
}

function renderAnalysis(d) {
  const box = $('asc-an-result');
  box.className = 'an-result';
  if (!d || d.error) { box.innerHTML = `<p class="hint">${(d && d.error) || t('an_none')}</p>`; return; }
  const p = d.player, tc = d.technical;
  const head = `<div class="an-head">Map <b>${p.map}</b> · Diff <b>${p.difficulty}</b> · `
    + `<b>${String(p.objective || '').toUpperCase()}</b> — <b>${p.runs_completed}`
    + `${p.target_runs ? '/' + p.target_runs : ''}</b> ${t('m_runs').toLowerCase()} · `
    + `${t('m_time')} <b>${p.total_time}</b> (${t('m_avg')} <b>${p.avg_run_time}</b>)</div>`;
  const grid = '<div class="an-grid">'
    + anCell(t('m_potion'), p.potion_bought) + anCell(t('m_melody'), p.melody_bought)
    + anCell(t('m_melody_skip'), p.melody_skipped) + anCell(t('m_enh'), p.enhances)
    + anCell(t('m_event'), p.events) + anCell(t('m_cards'), p.cards_picked)
    + anCell(t('m_spend_buy'), p.coin_spent_buy) + anCell(t('m_spend_enh'), p.coin_spent_enhance)
    + anCell(t('m_peak'), p.coin_peak_avg) + anCell(t('m_left'), p.coin_leftover_median)
    + anCell(t('m_images'), (d.images_mb || 0) + ' MB') + '</div>';
  const tech = `<div class="an-tech">${t('m_tech')}: ${tc.warnings_total} ${t('m_warn')} · `
    + `OCR-enh ${tc.enhance_ocr_fail} · card-osc ${tc.card_oscillation} · `
    + (tc.completed ? `<span class="ok">${t('m_complete_yes')}</span>`
                    : `<span class="bad">${t('m_complete_no')}</span>`) + '</div>';
  let runs = '<div class="an-runs"><table><thead><tr><th>Run</th><th>t</th><th>Coin↑</th>'
    + '<th>Dư</th><th>Pot</th><th>Mel</th><th>Enh</th><th>Evt</th></tr></thead><tbody>';
  for (const r of d.per_run) {
    const mm = Math.floor(r.dur_sec / 60), ss = String(r.dur_sec % 60).padStart(2, '0');
    runs += `<tr><td>${r.run}</td><td>${mm}m${ss}</td><td>${r.coin_peak}</td><td>${r.coin_last}</td>`
      + `<td>${r.potion_bought}</td><td>${r.melody_bought}</td><td>${r.enhances}</td><td>${r.events}</td></tr>`;
  }
  runs += '</tbody></table></div>';
  box.innerHTML = head + grid + tech + runs;
}

$('btn-asc-analyze').addEventListener('click', async () => {
  const s = $('asc-an-session').value;
  if (!s) { toast(t('an_none')); return; }
  renderAnalysis(await pywebview.api.analyze_capture(s));
});
$('btn-asc-export').addEventListener('click', async () => {
  const s = $('asc-an-session').value;
  if (!s) { toast(t('an_none')); return; }
  toast(await pywebview.api.export_capture_report(s));
});
$('btn-asc-cleanup').addEventListener('click', async () => {
  const s = $('asc-an-session').value;
  if (!s) { toast(t('an_none')); return; }
  if (!confirm(t('an_confirm'))) return;
  toast(await pywebview.api.cleanup_capture_images(s));
  await loadCaptureSessions();
  renderAnalysis(await pywebview.api.analyze_capture(s));
});

// ===== Cài đặt Bounty Trial =====
async function loadBounty() {
  if (!window.pywebview) return;
  const b = await pywebview.api.get_bounty();
  $('bt-trial').value = b.trial || 'basic';
  $('bt-difficulty').value = b.difficulty;
}

$('btn-save-bounty').addEventListener('click', async () => {
  const r = await pywebview.api.save_bounty({
    trial: $('bt-trial').value,
    difficulty: parseInt($('bt-difficulty').value, 10) || 0,
  });
  toast(r || t('saved_note'));
  flashSaved('bounty-saved');
  loadBounty();
});

// ===== Cài đặt Event =====
async function loadEvent() {
  if (!window.pywebview) return;
  const e = await pywebview.api.get_event();
  $('ev-stage').value = e.stage || '';
  $('ev-battles').value = e.battles;
}

$('btn-save-event').addEventListener('click', async () => {
  const r = await pywebview.api.save_event({
    stage: $('ev-stage').value,
    battles: parseInt($('ev-battles').value, 10) || 0,
  });
  toast(r || t('saved_note'));
  flashSaved('event-saved');
  loadEvent();
});

// ===== Cài đặt Event First Clear =====
async function loadEventFirstClear() {
  if (!window.pywebview) return;
  const e = await pywebview.api.get_event_first_clear();
  $('efc-normal').checked = e.normal;
  $('efc-hard').checked = e.hard;
  $('efc-challenge').checked = e.challenge;
  $('efc-max').value = e.max_stages;
  $('efc-timeout').value = e.run_timeout;
}

$('btn-save-efc').addEventListener('click', async () => {
  const r = await pywebview.api.save_event_first_clear({
    normal: $('efc-normal').checked,
    hard: $('efc-hard').checked,
    challenge: $('efc-challenge').checked,
    max_stages: parseInt($('efc-max').value, 10) || 12,
    run_timeout: parseInt($('efc-timeout').value, 10) || 180,
  });
  toast(r || t('saved_note'));
  flashSaved('efc-saved');
  loadEventFirstClear();
});

// ===== Cài đặt Heartlink =====
const HL_MAIL_ROWS = 10;

function buildMailRows() {
  const box = $('hl-mailrows');
  if (box.dataset.built) return;
  box.dataset.built = '1';
  for (let i = 0; i < HL_MAIL_ROWS; i++) {
    const row = document.createElement('div');
    row.className = 'mail-row';
    row.innerHTML = `<input id="hl-mname-${i}" type="text" placeholder="${t('lbl_hl_mailname')}">`
                  + `<input id="hl-mqty-${i}" type="number" min="0" max="10" placeholder="${t('lbl_hl_mailqty')}">`;
    box.appendChild(row);
  }
  for (let i = 0; i < HL_MAIL_ROWS; i++) $(`hl-mname-${i}`).addEventListener('input', syncMailTop);
}

function anyMailName() {
  for (let i = 0; i < HL_MAIL_ROWS; i++) if (($(`hl-mname-${i}`).value || '').trim()) return true;
  return false;
}

// Nhập tên NV custom → tự bỏ tick + disable "dồn cho NV trên cùng"
function syncMailTop() {
  const custom = anyMailName();
  const top = $('hl-mailtop');
  top.disabled = custom;
  if (custom) top.checked = false;
}

async function loadHeartlink() {
  if (!window.pywebview) return;
  buildMailRows();
  const h = await pywebview.api.get_heartlink();
  $('hl-do-invite').checked = h.do_invite;
  $('hl-count').value = h.invite_count;
  $('hl-gift').checked = h.send_gift;
  $('hl-targets').value = (h.invite_targets || []).join(', ');
  $('hl-do-mail').checked = h.do_mail;
  $('hl-mailcount').value = h.mail_count;
  const mt = h.mail_targets || [];
  for (let i = 0; i < HL_MAIL_ROWS; i++) {
    $(`hl-mname-${i}`).value = mt[i] ? mt[i].name : '';
    $(`hl-mqty-${i}`).value = (mt[i] && mt[i].qty) ? mt[i].qty : '';
  }
  $('hl-mailtop').checked = mt.length === 0;
  syncMailTop();
}

$('btn-save-hl').addEventListener('click', async () => {
  const targets = [];
  for (let i = 0; i < HL_MAIL_ROWS; i++) {
    const name = ($(`hl-mname-${i}`).value || '').trim();
    const qty = parseInt($(`hl-mqty-${i}`).value, 10) || 0;
    if (name && qty > 0) targets.push({ name, qty });
  }
  const r = await pywebview.api.save_heartlink({
    do_invite: $('hl-do-invite').checked,
    invite_count: parseInt($('hl-count').value, 10) || 5,
    send_gift: $('hl-gift').checked,
    invite_targets: $('hl-targets').value,
    do_mail: $('hl-do-mail').checked,
    mail_count: parseInt($('hl-mailcount').value, 10) || 10,
    mail_targets: targets,
  });
  toast(r || t('saved_note'));
  flashSaved('hl-saved');
  loadHeartlink();
});

function flashSaved(id) {
  const note = $(id);
  note.classList.remove('hidden');
  setTimeout(() => note.classList.add('hidden'), 2000);
}

// ===== Khởi động =====
async function boot() {
  try {
    LANG = (await pywebview.api.get_lang()) || localStorage.getItem('sst-lang') || 'vi';
  } catch (e) {
    LANG = localStorage.getItem('sst-lang') || 'vi';
  }
  localStorage.setItem('sst-lang', LANG);
  document.documentElement.lang = LANG;
  applyI18n();
  syncAutoscrollBtn();
  showPage('overview');
  poll();
  setInterval(poll, 1000);
}
if (window.pywebview) boot();
else window.addEventListener('pywebviewready', boot);
