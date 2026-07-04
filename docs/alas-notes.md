# Ghi chú kiến trúc ALAS / StarRailCopilot / MaaStellaSora

> Deliverable Phase 1 (2026-07-04). Nguồn: 7 reader agent đọc trực tiếp mã trong `reference/`. Phục vụ viết skeleton Phase 3.

## 1. MaaStellaSora — tri thức về game (danh sách daily + page graph sơ bộ)

### Tổng quan MaaStellaSora (domain knowledge – game *Stella Sora*)

MaaStellaSora là bộ resource cho MaaFramework (không phải Python/OpenCV thuần): `assets/interface.json` khai báo GUI + 4 server (官服/base, 台服 base+tw, 国际服 base+en, 日服 base+jp — cùng base pipeline, chỉ khác ảnh/text overlay) + import 12 file task. Mỗi task = 1 file "task list" (`assets/resource/tasks/*.json`, chỉ có tên/entry/mô tả) + 1 file "pipeline" thật (`assets/resource/base/pipeline/*.json`, state-machine node graph). Logic phức tạp (đếm số lần lặp, chọn quà, leo tháp) đẩy sang `agent/custom/*.py` chạy qua MaaFramework Custom Action/Recognition (kênh socket riêng) — kiến trúc này KHÔNG áp dụng cho tool Python+ADB của ta, chỉ tri thức game là dùng được. Độ phân giải target: **1280×720** (README: "chỉ hỗ trợ tỉ lệ 16:9"), mọi ROI trong pipeline theo hệ toạ độ này, vd `menu.png` roi `[1180,0,100,80]` = icon menu góc trên-phải màn hình chính (dùng làm "đang ở Home?" check ở hầu hết mọi task).

### Danh sách 12 daily task đã tự động hoá (tên – entry node – mô tả, trích `assets/resource/tasks/*.json`)

1. **登录游戏** entry `登录_登录` (login.json:5) – login + đóng popup event/check-in.
2. **领取每日奖励** entry `采购_入口` (shop.json:5) – vào tab 采购/商城, nhận quà ngày.
3. **心链送礼** entry `心链_入口` (talk.json:5) – tặng quà cho traveler top heart-link.
4. **邀约** entry `邀约_入口` (invite.json:5) – 5 lần mời hẹn, vòng lặp custom action `InviteAuto`.
5. **领取与赠送干劲** entry `好友_入口` (friend.json:5) – nhận & gửi động lực bạn bè.
6. **领取并重新派遣委托** entry `委托_入口` (quest.json:5) – nhận + tái phái expedition/quest.
7. **领取任务奖励** entry `任务_入口` (task.json:5) – nhiệm vụ ngày/tuần/boss, "一键领取" + "领取额外奖励".
8. **活动快速战斗** entry `活动_入口` (activity.json:5) – quét sự kiện: chọn ải, tiêu hết stamina bằng "添加战斗次数".
9. **悬赏试炼快速战斗** entry `战斗_入口` (fight.json:5) – đánh nhanh treasure-trial, chọn độ khó "1".
10. **领取基金奖励** entry `基金_入口` (grant.json:5) – nhận quà quỹ/gói tháng, dùng ColorMatch phát hiện "còn quà".
11. **领取邮箱奖励** entry `邮箱_入口` (mail.json:5) – mở mail, "一键领取".
12. **新版爬塔** entry `星塔_入口_agent` (climb_tower.json:5) – leo tháp full-auto (chọn potential, mua shop, quiz hội thoại) — **rất phức tạp, ~30 node + 5 custom action, ngoài scope v1** (v1 không auto-combat).

Suy ra **page graph** tối thiểu: `Home(menu.png icon) ⇄ {采购/商城, 心链, 邀约, 好友, 委托, 任务, 活动, 悬赏试炼, 基金, 邮箱}`, mỗi trang con là 1 nhánh đi rồi quay lại Home; không có map/world layer như Azur Lane.

### API & luồng cốt lõi (pipeline JSON – node-graph, ví dụ pseudocode từ mail.json – mẫu đơn giản nhất)

```
邮箱_入口 [DirectHit] -> next: [判断是否在主页, jump_back:通用_返回主页]
邮箱_判断是否在主页 [TemplateMatch(menu.png)] -> next: [邮箱_打开邮箱]
邮箱_打开邮箱 [Click if TemplateMatch(email.png)] -> next: [邮箱_一键领取]
邮箱_一键领取 [Click if TemplateMatch(quick_claim.png), timeout=2000] -> next: [通用_返回主页]
```
(`assets/resource/base/pipeline/mail.json:2-78`) — về cơ bản mỗi task là chuỗi "chờ state → tap → chờ state kế", đúng thứ Python tasks/ module nên biểu diễn bằng hàm tuần tự.

Recognition type quan sát được: `TemplateMatch` (roi+threshold+list nhiều template = OR), `OCR` (expected: list regex + roi + `replace` map ký tự, vd la-mã), `DirectHit` (luôn pass, dùng làm node router giả không cần nhận diện), `ColorMatch` (roi + lower/upper RGB + count pixel — `assets/resource/base/pipeline/grant.json:107-134`, phát hiện chấm đỏ thông báo khi template/OCR không ổn định), `Custom` (gọi hàm Python qua agent).

Cấu trúc `next` = list ưu tiên thử theo thứ tự, node đầu tiên match được chọn (multi-branch OR). `{"jump_back": true, "name": X}` = thử nhận diện X, nếu match thì thực thi X rồi QUAY LẠI thử tiếp các phần tử còn lại trong list gốc — pattern quan trọng nhất, dùng để xử lý popup chen ngang mà không phá luồng chính (`通用_返回主页` gom 8 loại popup khác nhau kiểu này, `assets/resource/base/pipeline/base.json:123-159`).

`活动_添加战斗次数` minh hoạ retry: `"repeat": 1, "repeat_delay": 1000, "on_error": ["通用_返回主页"]` (activity.json:147-172) — bấm lặp N lần, nếu recognition fail giữa chừng thì thoát về home an toàn thay vì kẹt.

`utool_calc_repeat` custom action (`agent/custom/action/fight.py:7-52`): đọc option input số-lần-quét → nếu =1 thì `context.override_pipeline()` biến node "添加战斗次数" thành DoNothing/skip; nếu >1 thì set `repeat = n-1` rồi override runtime. Pattern "override pipeline tại runtime theo option người dùng" — trong Python thuần chỉ cần 1 biến loop count, không cần cơ chế override.

### Khuyến nghị cho Stella Sora Tool (copy gì / đơn giản hoá gì / bỏ gì)

- **Copy**: (1) danh sách 12 task + entry-name + mô tả làm checklist scope daily v1; (2) page graph Home⇄10 trang con suy ra ở trên; (3) pattern "jump_back popup-interrupt" → viết 1 hàm Python `dismiss_popups()` chạy trước mỗi bước chờ state, thử lần lượt các template popup thường gặp (公告/签到/活动/月卡/心链…) rồi mới check state đích; (4) toạ độ ROI theo hệ 1280×720 + tên ảnh template trong `assets/resource/base/image/*` (Base, shop, task, activity, fight, grant, Invite) dùng lại được luôn làm asset mẫu nếu cùng server; (5) trick ColorMatch để phát hiện "còn quà chưa nhận" (chấm đỏ) khi template/OCR không ổn định — copy nguyên lower/upper RGB threshold.
- **Đơn giản hoá**: bỏ hẳn agent/MaaFramework socket Custom Action; thay `override_pipeline` runtime bằng biến Python thường (đếm loop count từ config); node-graph 10-20 node/task → rút gọn thành 1 hàm tuyến tính `def run_<task>(self)` với vài `if` cho nhánh popup phổ biến, dùng chung 1 `goto_home()`.
- **Bỏ hoàn toàn (ngoài scope v1)**: tự động leo tháp (`星塔_入口_agent` + ClimbTower_agent node/custom action: chọn potential, quiz hội thoại, shop mua đồ theo priority list — quá phức tạp, cần auto-combat thời gian thực); preset đội hình leo tháp (`agent/presets/*.json`); đa ngôn ngữ tw/en/jp overlay (v1 chỉ 1 server).

### Bẫy & edge case code gốc đã xử lý

- **Popup chen ngang bất kỳ lúc nào** (公告, 签到, hoạt động, 月卡 nhận, 心链 đóng...) → xử lý bằng list `next` nhiều `jump_back` thử tuần tự trong `通用_返回主页` (`base.json:123-159`). Không xử lý sẽ kẹt vòng lặp khi gặp popup lạ chưa lường trước.
- **Chờ UI hết animate trước khi nhận diện**: `post_wait_freezes`/`pre_wait_freezes` (chờ màn hình "đứng hình" N ms rồi mới OCR/match) ở `活动_等待活动界面静止` (activity.json:128-146, timeout 5000ms chờ banner tải) và `基金_判断是否已进入基金` (grant.json:56-85) — tránh click hụt do UI đang animate/tải data.
- **OCR đọc sai số La Mã**: `活动_选择活动关卡` map Ⅰ-Ⅷ → I-VIII qua field `replace` (activity.json:254-287) vì OCR hay lẫn ký tự roman với chữ Latin.
- **Hết tài nguyên (stamina) giữa chừng**: `通用_消耗所有干劲` nhận diện `max.png` threshold 0.9 (base.json:298-315) để biết đã dùng hết event stamina, tránh loop vô hạn khi bấm "add" nhưng không còn gì để thêm.
- **pre_delay chờ server pull data**: `采购_领取每日赠礼` có `pre_delay: 1000` kèm comment "đơn giản hoá vấn đề màn hình cửa hàng đang pull data gói quà chưa bấm được" (shop.json:79-101).
- **max_hit làm watchdog**: giới hạn số lần thử 1 node (`登录_通用签到` max_hit:10, `登录_启动游戏` max_hit:20, login.json:251-276) để tránh loop vô hạn khi recognition kiểu DirectHit luôn "pass" giả nhưng hành động thực tế chưa tiến triển.
- **on_error dự phòng khi icon bị che**: `委托_前往委托` (`on_error: ["通用_返回主页"]`, timeout 5000ms, quest.json:55-79) — icon ủy thác có thể bị popup khác che, bấm trượt thì thoát an toàn về home thay vì đứng hình.
- **Tách config khỏi logic**: climb-tower agent dùng field `attach` để truyền tham số (priority_list, threshold, max_count...) vào Custom action/recognition thay vì hard-code trong code Python (climb_tower_agent.json:87-98, 295-322) — pattern đáng học nếu sau này viết task cấu hình được nhiều tham số.


**Đáng tái sử dụng nhất:**
- Danh sách 12 daily task (entry node + mô tả) làm checklist scope v1: login, shop, talk/heart-link gift, invite x5, friend motivation, quest re-dispatch, task rewards, activity sweep, bounty-trial fight, fund/grant, mail — và page graph Home⇄10 trang con suy ra từ chúng
- Pattern "jump_back popup-interrupt": thử nhận diện + xử lý popup xen ngang (thông báo/checkin/event/monthly-card/heart-link-close) rồi quay lại flow chính — nên viết thành 1 hàm dismiss_popups() dùng chung mọi task
- Toạ độ ROI + tên ảnh template theo hệ 1280x720 trong assets/resource/base/image/* (menu.png, quick_claim.png, close*.png...) tái dùng trực tiếp nếu cùng server
- Trick ColorMatch (roi + lower/upper RGB + pixel count) để phát hiện chấm đỏ thông báo "còn quà chưa nhận" khi TemplateMatch/OCR không ổn định (grant.json)
- Cơ chế watchdog max_hit / on_error / repeat+repeat_delay để tránh kẹt vòng lặp khi UI không tiến triển hoặc icon bị popup che

---

## 2. Device layer (ALAS + SRC)

### Tổng quan Device layer

ALAS và SRC dùng **kiến trúc mixin chồng lớp**: `Connection(ConnectionAttr) → Adb/WSA/DroidCast/AScreenCap/Scrcpy/NemuIpc/LDOpenGL → Screenshot(...)`, `Hermit/Minitouch/Scrcpy/MaaTouch/NemuIpc → Control`, rồi `Device(Screenshot, Control, AppControl)` là class cuối cùng dùng trong task. Mỗi "method" (adb, minitouch, nemu_ipc...) là 1 file/mixin độc lập, chỉ cắm vào khi cần — dễ bỏ bớt cho bản tối giản. SRC gần như **fork y nguyên ALAS** phần device (khác nhỏ: thêm `screenshot_method_override` ưu tiên `nemu_ipc`/`ldopengl`, thêm `platform/plat.py`).

### API & luồng cốt lõi

**Khởi tạo** (`device.py:73-108`): `Device.__init__` retry tối đa 4 lần bắt `EmulatorNotRunningError` → tự gọi `emulator_start()`; sau đó `method_check()` fallback method không hợp với emulator (`nemu_ipc` chỉ MuMu, `ldopengl` chỉ LDPlayer, non-Windows bỏ cả hai); nếu `ScreenshotMethod=='auto'` → `run_simple_screenshot_benchmark()`.

**Chọn method** (`screenshot.py:32-58`, `control.py:18-27`):
```python
screenshot_methods = {'ADB':.., 'ADB_nc':.., 'uiautomator2':.., 'aScreenCap':.., 'DroidCast':.., 'scrcpy':.., 'nemu_ipc':.., 'ldopengl':..}
click_methods = {'ADB':.., 'uiautomator2':.., 'minitouch':.., 'MaaTouch':.., 'nemu_ipc':..}
method = screenshot_methods.get(config.Emulator_ScreenshotMethod, self.screenshot_adb)  # fallback ADB
```
SRC override (`screenshot.py:47-58`): nếu `nemu_ipc_available()` → luôn dùng `nemu_ipc` bất kể config; else nếu `ldopengl_available()` → dùng `ldopengl`. Đây là **method mặc định thực tế cho MuMu12/LDPlayer**, tự ghi đè config.

**Benchmark tự chọn** (`daemon/benchmark.py:157-171`): fallback nếu benchmark thất bại: `fastest_screenshot='ADB_nc'`, `fastest_click='minitouch'`; nếu minitouch và MaaTouch hòa tốc độ → ưu tiên MaaTouch.

**screenshot() loop** (`screenshot.py:60-90`): lặp tối đa 2 lần: chụp → `_handle_orientated_image` (xoay theo `self.orientation` nếu ảnh không phải 1280x720) → `check_screen_size()` (bắt buộc 1280x720, raise `RequestHumanTakeover` nếu sai) và `check_screen_black()` (màn đen → reset flag, thử lại; riêng MuMu + DroidCast thì gọi `droidcast_stop()`).

**nemu_ipc — click/screenshot nhanh nhất cho MuMu12** (`method/nemu_ipc.py`):
```python
class NemuIpcImpl:
    def __init__(self, nemu_folder, instance_id, display_id=0):  # load external_renderer_ipc.dll qua ctypes
    def connect(self, on_thread=True)   # nemu_connect(folder, instance_id) -> connect_id
    def screenshot(self, timeout=0.5)   # nemu_capture_display -> RGBA ndarray, ảnh bị lật ngược
    def down(self, x, y) / def up()      # convert_xy: (x,y) -> (height-y, x) trước khi gọi nemu_input_event_touch_*
    @staticmethod
    def serial_to_id(serial)  # "127.0.0.1:16384"->0, "127.0.0.1:16416"->1 (offset ±2 port cho phép)
```
Gọi C-function trên **thread riêng** (`WORKER_POOL.start_thread_soon` + `JobTimeout`) vì nemu_ipc có thể treo. `nemu_ipc_available()` check: Windows only + `is_mumu_family` + thử connect thật (bắt `NemuIpcIncompatible/NemuIpcError`). Tốc độ: nemu_ipc là IPC trực tiếp vào bộ nhớ emulator, nhanh hơn hẳn ADB/uiautomator2 (không qua adb shell).

**click_nemu_ipc/swipe_nemu_ipc** (`nemu_ipc.py:607-645`): down → sleep(10-20ms) → up → sleep còn lại cho đủ 50ms; swipe dùng `insert_swipe()` (từ `minitouch.py`) sinh chuỗi điểm trung gian rồi down từng điểm.

**ADB (baseline, luôn có sẵn)** (`method/adb.py`): `screenshot_adb()` = `adb shell screencap -p` (stream) → decode PNG bằng `cv2.imdecode`, thử 3 kiểu line-ending (`\r\n`, `\r\r\n`, none) do khác biệt Android version, cache kiểu đã thành công (`__screenshot_method_fixed`) để lần sau thử trước. `click_adb` = `input tap x y`, nếu quá nhanh (<50ms, tức là không thực thi) thì sleep bù. `ADB_nc` dùng adb-shell pipe qua `nc`/`busybox nc` để tránh base64-encode chậm của `adb exec-out`.

**Emulator/device detection** (`connection.py`, `connection_attr.py`): nhận diện qua **port range của serial**, không qua tên tiến trình:
- MuMu12: `16384 <= port <= 17408` (`is_mumu12_family`), MuMu6: `serial=='127.0.0.1:7555'`
- LDPlayer/BlueStacks: `5555 <= port <= 5619` hoặc bắt đầu `emulator-`
- Nox: `62001<=port<=63025`; VMOS: `5667<=port<=5699`
`serial_check()` còn tự sửa lỗi nhập serial kiểu người dùng gõ nhầm (dấu chấm/phẩy TQ, thiếu dấu `:`, port MuMu cũ dạng `12127.0.0.1:...`).

**Reconnect/retry**: decorator `retry` (mỗi method file tự định nghĩa) bọc mọi hàm ADB/nemu_ipc, tối đa `RETRY_TRIES` lần, bắt các lỗi cụ thể (`ConnectionResetError`, `AdbError` phân loại qua `handle_adb_error`/`handle_unknown_host_service`, `PackageNotInstalled`, `ImageTruncated`) rồi gọi `init()` tương ứng (vd `self.adb_reconnect()`) trước khi thử lại; hết lượt → raise `RequestHumanTakeover` (dừng hẳn, cần người can thiệp). `adb_connect()` xử lý riêng: bỏ qua serial `emulator-*`/serial thuần số (tự động connect), brute-force connect nhiều port lân cận nếu là MuMu12 và bị đổi port ngẫu nhiên.

**Orientation**: `get_orientation()` đọc `dumpsys display` bằng regex, cache vào `self.orientation` (0/1/2/3), `screenshot.py` tự xoay ảnh về 1280x720 khi cần.

### Khuyến nghị cho Stella Sora Tool

- **Copy nguyên khối**: `ConnectionAttr.revise_serial()` + các `is_*_family` (port-range detection) — rẻ, không phụ thuộc gì, tránh người dùng gõ sai serial.
- **Copy `NemuIpcImpl`** gần như nguyên bản nếu target chính là MuMu (nhanh nhất, không qua ADB). Copy `screenshot_adb`/`click_adb` làm baseline bắt buộc phải có (luôn hoạt động, mọi giả lập).
- **Đơn giản hóa**: bỏ hẳn `scrcpy`, `DroidCast`, `aScreenCap`, `hermit`, `wsa`, `ldopengl`, `uiautomator2` ở v1 — quá nhiều lựa chọn cho nhu cầu chỉ chạy MuMu/LDPlayer. Giữ tối đa 3 method: `ADB` (baseline), `nemu_ipc` (MuMu), `MaaTouch` hoặc `minitouch` (click nhanh, generic). Bỏ benchmark tự động phức tạp — hardcode ưu tiên `nemu_ipc > ADB` theo `is_mumu_family`, tương tự đơn giản hoá cho LDPlayer chỉ dùng ADB/MaaTouch (bỏ `ldopengl` vì phức tạp OpenGL hook).
- **Bỏ**: multi-platform (Linux/Mac/WSA/BlueStacks Hyper-V/Nox/VMOS/waydroid) — chỉ giữ Windows + MuMu + LDPlayer. Bỏ toàn bộ `is_over_http`, `adb_shell_nc`+reverse-server (phức tạp, chỉ cần khi ADB chậm — v1 daily không cần tối ưu tới mức đó).
- **Interface Device tối giản đề xuất**: `connect()/reconnect()`, `screenshot() -> np.ndarray (BGR, 1280x720)`, `click(x,y)`, `swipe(p1,p2)`, `app_start()/app_stop()/app_current()`, `list_device()/detect_device()`. Method thật sự nên có: `screenshot_adb`, `screenshot_nemu_ipc`, `click_adb`, `click_nemu_ipc` hoặc `click_maatouch`.

### Bẫy & edge case code gốc đã xử lý

- **ADB screencap line-ending khác nhau theo Android/emulator version** (`\r\n` vs `\r\r\n` vs none) — code thử cả 3 và cache kiểu đúng; bỏ qua bẫy này sẽ làm `cv2.imdecode` fail ngẫu nhiên trên 1 số máy.
- **MuMu12 đổi port ngẫu nhiên** khi port bị chiếm (dùng `16384+n` lân cận ±1,±2) — cần brute-force connect + tự cập nhật serial, nếu không tool sẽ mất kết nối định kỳ.
- **Ảnh chụp bị lật/lệch màu**: nemu_ipc trả RGBA và ảnh **lật ngược** (`cv2.flip(image,0)` bắt buộc); ADB screencap là RGBA cần `cvtColor(BGRA2BGR)`.
- **Màn hình đen giả** (`check_screen_black`): 1 số giả lập/emulator trả screenshot đen thui dù app đang chạy bình thường — không phải lỗi thật, cần retry riêng thay vì crash ngay.
- **MuMu "giữ ứng dụng chạy nền" (`nemud.app_keep_alive`)** phải tắt, nếu không nemu_ipc/adb sẽ không đọc đúng surface — code raise `RequestHumanTakeover` với thông báo tiếng Trung hướng dẫn tắt trong settings.
- **nemu_ipc có thể treo vô thời hạn** — bắt buộc gọi qua thread pool với timeout (`JobTimeout`), tăng dần timeout mỗi lần retry (`retry_sleep`).
- **Serial nhập tay đầy lỗi** (dấu câu Trung Quốc, thiếu `:`, định dạng MuMu cũ) — `revise_serial()` xử lý fool-proof trước khi dùng.
- **LDPlayer serial nhảy giữa `127.0.0.1:5555+n` và `emulator-5554+n`** — cần dò cặp serial (`get_serial_pair`) và chọn cái đang `status=='device'`.

**Đáng tái sử dụng nhất:**
- ConnectionAttr.revise_serial() + is_mumu_family/is_ldplayer_bluestacks_family (port-range detection) - rẻ và fool-proof cho serial nhập tay
- NemuIpcImpl (ctypes wrap external_renderer_ipc.dll) - click/screenshot nhanh nhất cho MuMu12, nên copy gần nguyên bản
- screenshot_adb + click_adb làm baseline bắt buộc (luôn chạy được trên mọi giả lập, đơn giản, ít phụ thuộc)
- Pattern retry decorator bắt lỗi cụ thể (AdbError/ConnectionResetError/PackageNotInstalled) rồi tự reconnect trước khi thử lại, raise RequestHumanTakeover khi hết lượt
- check_screen_size()/check_screen_black() - validate ảnh trước khi dùng, tránh xử lý ảnh rác/màn đen giả

---

## 3. Base primitives (Button, Timer, appear/click)

### Tổng quan Base primitives
ALAS và SRC dùng chung một tầng "base" tối giản: mọi UI trong game là **Button** (vùng ảnh + màu trung bình + vùng click), phát hiện bằng OpenCV `matchTemplate`/so màu, click bằng ADB/uiautomator2/MaaTouch. **Timer** là lớp đếm-kép (thời gian + số lần gọi) để chịu được device chậm. Vòng lặp cốt lõi luôn là: `screenshot()` → `appear()` (match) → nếu đúng thì `click()`. Một lớp an toàn riêng (không nằm trong `module/base` mà ở `module/device/device.py` + `control.py`) theo dõi **stuck** (chờ quá lâu không tiến triển) và **click lặp** (spam 1 nút hoặc bấm qua lại 2 nút) để tự raise exception thay vì treo vô hạn. SRC là bản refactor gọn hơn ALAS: tách `match_color`/`match_template`/`match_template_luma` riêng biệt, thêm `ButtonWrapper` (nhiều biến thể theo ngôn ngữ server), bỏ 3 hàm `wait_until_*` để dùng generator `loop()` thống nhất.

### API & luồng cốt lõi

**Button (ALAS `module/base/button.py:13`)**
```
Button(area, color, button, file=None, name=None)
.appear_on(image, threshold=10) -> bool          # so màu trung bình (button.py:104)
.match(image, offset=30, similarity=0.85) -> bool # matchTemplate, set self._button_offset (button.py:202)
.match_template_color(image, offset=(20,20), similarity=0.85, threshold=30) -> bool  # match trước, so màu sau (button.py:325)
```
Pseudocode `match()`: crop vùng `area+offset` từ ảnh → `cv2.matchTemplate(TM_CCOEFF_NORMED)` → `minMaxLoc` lấy `sim, point` → lưu `_button_offset = area_offset(_button, offset+point)` → `return sim > similarity`. Điểm quan trọng: **mỗi lần gọi match() đều ghi đè `_button_offset`** dù match fail hay pass — `button.button` (toạ độ click) luôn phản ánh lần match gần nhất.

**SRC Button/ButtonWrapper (`module/base/button.py:8,215`)** tách rõ:
```
Button.match_color(image, threshold=10)
Button.match_template(image, similarity=0.85, direct_match=False)      # crop theo self.search (=offset), không phải offset truyền tay
Button.match_template_color(image, similarity=0.85, threshold=30)
ButtonWrapper(name, **kwargs)          # kwargs: {lang: Button|[Button,...]}
.buttons -> cached_property thử server.lang -> 'share' -> 'cn', raise ScriptError nếu không có fallback (button.py:250-260)
```
`ClickButton(area, button=None, name=)` (button.py:419) — struct nhẹ không có template, dùng cho nút sinh runtime (vd từ color match).

**Timer (`module/base/timer.py:75`, giống hệt 2 repo)**
```
Timer(limit, count=0).start()      # nếu chưa start, reached() luôn True (fast first try)
.reached() -> bool                  # mỗi lần gọi tự +1 _access; True khi access>count AND time>limit
.reset() / .clear() / .wait()
```

**ModuleBase.appear (ALAS `base.py:212`, SRC tách thành `match_template`/`match_color`/`appear` ở `base.py:157-308`)**
```
appear(button, offset=0, interval=0, similarity=0.85, threshold=10) -> bool
  button = ensure_button(button)
  device.stuck_record_add(button)              # luôn ghi nhận, kể cả khi bị interval chặn
  if interval and not interval_reached: return False
  appear = button.match(...) hoặc button.appear_on(...) (tuỳ offset)
  if appear and interval: interval_timer[button.name].reset()   # chỉ reset khi THÀNH CÔNG
  return appear

appear_then_click(button, ...):
  if appear(button): device.click(button); return True
```
SRC gộp interval logic vào `get_interval_timer`/`interval_is_reached` (`base.py:402-440`) — sạch hơn bản ALAS lặp code interval trong từng hàm.

**wait_until_appear kiểu ALAS (`base.py:308-325`)** = while 1: screenshot(); if appear(): break. **SRC bỏ hẳn 3 hàm này**, thay bằng generator dùng chung:
```
for _ in self.loop(timeout=2):     # base.py:127 (giống hệt 2 repo)
    if self.appear(BTN): break
else:
    logger.warning('timeout')
```

**click_record & stuck detection (`module/device/device.py`, `control.py` — KHÔNG nằm trong module/base nhưng gắn chặt vào appear)**
```
detect_record = set(); stuck_timer = Timer(60, count=60).start()   # device.py:69-71
click_record = deque(maxlen=30)                                     # device.py:70
stuck_record_add(button) -> detect_record.add(str(button))          # gọi trong mọi appear()
stuck_record_check() -> nếu stuck_timer.reached(): raise GameStuckError / GameNotRunningError  # gọi ở ĐẦU screenshot()/dump_hierarchy() (device.py:162-167,181-183), TRƯỚC khi chụp ảnh mới
handle_control_check(button) -> stuck_record_clear(); click_record_add(button); click_record_check()  # gọi trong Device.click() (control.py:29-37)
click_record_check(): đếm 15 click gần nhất; 1 nút ≥12 lần -> GameTooManyClickError; 2 nút xen kẽ đều ≥6 -> GameTooManyClickError (trừ case đặc biệt Ruan Mei event, device.py:270-273)
Device.click(): handle_control_check() -> random_rectangle_point(button.button) -> dispatch theo Emulator_ControlMethod (control.py:29-47)
```
Exceptions (`module/exception.py`): `GameStuckError`, `GameTooManyClickError`, `GameNotRunningError`, `ScriptError`, `RequestHumanTakeover`, `TaskError` — tầng trên (scheduler) bắt các exception này để quyết định retry/restart emulator/dừng hẳn.

**retry.py** (`__retry_internal`, `retry`, `retry_call`) — decorator retry-với-backoff generic (dùng cho kết nối device/network), **KHÔNG** dùng trong vòng lặp appear/click (vòng đó dùng `while 1` + `Timer` trần, không dùng decorator này).

**Utils nền (`module/base/utils.py`)**: `crop(image, area, copy=True)` (line 573) tự chèn viền đen khi area vượt biên ảnh thay vì raise; `get_color`/`color_similar` (line 779, 958) so màu kiểu tolerance giống Photoshop; `random_rectangle_point` (line 35) random điểm click trong vùng.

### Khuyến nghị cho Stella Sora Tool
- **Copy nguyên**: `Timer` class, cấu trúc `Button` tối giản (area+color+button+file, match bằng `matchTemplate` RGB thường — bỏ `match_binary`/`match_luma`, chỉ cần 1 kiểu match), vòng lặp `appear→click` với interval qua `get_interval_timer` (bản SRC gọn hơn ALAS), `crop()` có viền đen, `random_rectangle_point`.
- **Copy nhưng đơn giản hoá lưới an toàn stuck/click**: giữ nguyên ý tưởng `stuck_timer` (reset khi click, raise nếu 60s không tiến triển) + đếm click lặp trong deque ngắn, nhưng không cần tách `Control`/`Hierarchy` phức tạp — gộp vào 1 class `Device` nhỏ.
- **Copy `loop(timeout=...)` generator của SRC** thay vì viết riêng `wait_until_appear/wait_until_disappear/wait_until_appear_then_click` như ALAS — ít code hơn, cùng một idiom cho mọi chỗ chờ.
- **Bỏ hẳn**: `is_gif`/animated template (match nhiều frame), `ButtonGrid` (chỉ thêm khi thực sự có UI dạng lưới), `Template` class rời (dùng cho map/point detection — v1 không có map), hierarchy/XPath detection (`HierarchyButton`, `dump_hierarchy`) trừ khi xác nhận Stella Sora expose native Android view (nhiều khả năng là game Unity/Cocos nên hierarchy vô dụng), cơ chế server-split (`split_server`, `parse_property` theo dict-per-server, `VALID_SERVER`) nếu chỉ target 1 server, `Resource`/asset lazy-load phức tạp (v1 ít asset, load thẳng lúc khởi động là đủ), `early_ocr_import`, `worker` ThreadPoolExecutor, `screenshot_tracking_add`.
- **Cân nhắc**: `ButtonWrapper` multi-lang chỉ cần nếu Stella Sora Tool hỗ trợ nhiều ngôn ngữ client ngay từ đầu; nếu không, dùng `Button` phẳng.

### Bẫy & edge case code gốc đã xử lý
- **Chỉ `reset()` interval khi match THÀNH CÔNG**, không reset khi gọi appear() thất bại — nhầm chỗ này sẽ làm interval không bao giờ trigger lại đúng nhịp (debounce-on-success, không phải debounce-on-call).
- **`stuck_record_add()` luôn chạy trước khi interval có thể return False sớm** — nếu code mới đảo thứ tự (check interval rồi mới add), thông báo stuck sẽ thiếu button đang chờ thực sự.
- **`stuck_record_check()` chạy Ở ĐẦU `screenshot()`, dùng trạng thái timer từ lần trước** — và dùng điều kiện KÉP thời gian AND số lần (`Timer(60, count=60)`): chỉ time-based sẽ báo stuck giả trên loop nhanh có delay nhỏ hợp lệ; chỉ count-based sẽ không bao giờ trigger trên device chậm nhưng vẫn hoạt động đúng — phải giữ cả hai điều kiện.
- **`click_record_check` có ngoại lệ đặc biệt** (Ruan Mei event cho phép tới 25 click liên tiếp cho 1 nút) cho thấy ngưỡng "quá nhiều click" (12 cho 1 nút / 6-6 cho 2 nút xen kẽ) là magic number cần tinh chỉnh theo từng task, không nên hardcode cứng — task sweep/dialog xác nhận lặp nhiều lần của Stella Sora có thể false-positive nếu copy nguyên số 12.
- **`Button.name` là khoá dùng chung** cho `interval_timer` dict, `detect_record` set và `click_record` deque (đều key bằng `str(button)`/name) — 2 Button khác nhau trùng tên (copy-paste asset quên đổi tên) sẽ âm thầm phá timer/stuck-state của nhau, không lỗi rõ ràng. Nên assert unique name khi load assets.
- **`crop()` tự pad viền đen khi area vượt biên ảnh** thay vì raise/slice âm kiểu Python — nếu viết lại bằng `image[y1:y2, x1:x2]` trần sẽ bị bug slicing âm (wrap-around) khi button nằm sát mép màn hình.
- **`match()` ghi đè `_button_offset` mỗi lần gọi** (kể cả fail) → phải gọi `appear()` ngay trước `click()` trên cùng 1 frame ảnh, không được cache kết quả appear từ frame cũ rồi click sau — offset có thể đã bị ghi đè bởi lần match khác.


**Đáng tái sử dụng nhất:**
- Timer (module/base/timer.py:75) - dual timer (thời gian + số lần access), copy y nguyên: chống race trên device chậm
- Vòng lặp appear() -> device.stuck_record_add() -> match() -> click() với interval throttle qua get_interval_timer/interval_is_reached (SRC base.py:402-440) - refactor sạch hơn ALAS
- Cặp click_record (deque maxlen=30, phát hiện spam click 1 nút hoặc 2 nút xen kẽ) + stuck_record (Timer(60,count=60), reset khi click) ném GameTooManyClickError/GameStuckError - lưới an toàn bắt buộc cho tool chạy không giám sát
- random_rectangle_point khi click (tránh tọa độ pixel-perfect lặp lại)
- SRC's loop(timeout=...) generator thay thế 3 hàm wait_until_appear/wait_until_disappear/wait_until_appear_then_click của ALAS - gọn hơn nhiều

---

## 4. UI page graph (ui_ensure/ui_goto)

### Tổng quan UI page graph (SRC đối chiếu ALAS)

SRC (`tasks/base/page.py`, `tasks/base/ui.py`) gần như copy y nguyên lõi thuật toán từ ALAS (`module/ui/page.py`, `module/ui/ui.py`) — cùng class `Page`, cùng `init_connection`/`ui_goto`. SRC bồi thêm: `ui_page_confirm` (chờ ổn định khi tới `page_main`), `ui_leave_special` (thoát domain/trial trước khi đi graph), `acquire_lang_checked` (OCR phát hiện ngôn ngữ). Đây là kiến trúc "page graph tự định tuyến bằng BFS ngược từ đích", không hard-code lộ trình.

### API & luồng cốt lõi

**Đăng ký page** (`page.py:6-75`, giống hệt 2 repo):
```python
class Page:
    all_pages = {}                      # name(str) -> Page
    def __init__(self, check_button):
        self.links = {}                 # dest_Page -> button để bấm tới dest
        # tự lấy tên biến qua traceback.extract_stack(), parse text trước dấu '='
        self.name = text[:text.find('=')].strip()
        Page.all_pages[self.name] = self
    def link(self, button, destination): self.links[destination] = button
    # __eq__/__hash__ theo self.name -> Page dùng được làm dict key
```
Khai báo page + cạnh kiểu đồ thị (page.py:79-92):
```python
page_character = Page(CHARACTER_CHECK)
page_character.link(CLOSE, destination=page_main)                  # character -> main
page_main.link(MAIN_GOTO_CHARACTER, destination=page_character)     # main -> character
```

**Tìm đường (BFS ngược từ đích)** — `Page.init_connection(destination)` (page.py:16-39, giống hệt cả 2 repo):
```
clear_connection()                       # reset parent=None mọi page
visited = {destination}
loop:
    for page in visited:
        for link in all_pages:
            if link not in visited and page in link.links:   # link có cạnh trỏ tới page
                link.parent = page                           # hướng đi: link -> ... -> destination
                new.add(link)
    if new == visited: break
```
→ Mỗi page ngoài `visited` được gán `.parent` = hàng xóm gần đích hơn 1 bước (BFS wavefront, comment ghi "A*" nhưng thực chất là BFS không trọng số — không cần heuristic vì đồ thị nhỏ, ~10-30 node).

**Vòng lặp điều hướng** — `ui_goto(destination)` (ui.py SRC:127-180, ALAS:229-274, gần như giống nhau):
```
init_connection(destination); interval_clear(all check_buttons)
loop screenshot:
    if ui_page_appear(destination): break                      # tới đích
    for page in all_pages:
        if page.parent and ui_page_appear(page, interval=5):    # đang đứng ở 1 page trên path
            click(page.links[page.parent])                      # bấm nút đi 1 bước tới gần đích hơn
            clicked = True; break
    if clicked: continue
    if ui_additional() or handle_popup_*(): continue             # xử lý popup chen ngang, lặp lại
clear_connection()
```
`ui_get_current_page()` (ui.py SRC:35-125): quét toàn bộ `Page.iter_pages()`, page nào `check_button` xuất hiện thì set `ui_current`; nếu không nhận diện được page nào, thử `ui_additional()`/popup handlers; timeout 10s/20 lần chụp → `raise GamePageUnknownError` kèm log liệt kê pages hỗ trợ, yêu cầu người dùng tự chuyển màn hình.
`ui_ensure(destination)`: gọi `ui_get_current_page()`, so `ui_current == destination`, nếu khác mới gọi `ui_goto`.

**Popup chen ngang** — `ui_additional()` là chuỗi `if self.handle_X(): return True` (SRC ui.py:382-417; ALAS ui.py:461-583), gọi tại CẢ hai nơi: nhánh "unknown page" trong `ui_get_current_page` và nhánh "stuck" trong `ui_goto`. ALAS có ~30 handler tích lũy qua nhiều năm cập nhật game (dấu hiệu danh sách sẽ phình dần theo thời gian).

### Khuyến nghị cho Stella Sora Tool

**Nên copy gần như nguyên vẹn:**
- Class `Page` + `init_connection` (BFS ngược từ đích) — code ngắn (~50 dòng), tự động, không cần bảo trì routing table thủ công. Rất phù hợp cho 6-8 page daily.
- Khung vòng lặp `ui_get_current_page`/`ui_goto`/`ui_ensure` — pattern "quét known pages → nếu đang ở node trên path thì bấm 1 bước → nếu không, thử popup handler → lặp" áp dụng thẳng được.
- Pattern `ui_additional()` = chuỗi handler nhỏ trả `bool`, gọi lặp lại ở nơi bị "stuck" — giữ cấu trúc này dù ban đầu danh sách ngắn (2-3 handler: OK/Xác nhận, nhận thưởng, đóng popup), để dễ mở rộng dần như ALAS đã làm.

**Nên đơn giản hóa:**
- Bỏ độ chính xác kiểu `is_in_main` của SRC (match_template_luma + image_color_count threshold để phân biệt page trùng button) — chỉ cần khi 2 page dùng chung asset dễ nhầm; v1 dùng `appear()` template match thường (similarity ~0.85), chỉ thêm color-check nếu thực sự bị nhầm page.
- Bỏ cơ chế multi-skin (`page_main` vs `page_main_white` của ALAS do game reskin UI) — không dựng song song trước, chỉ thêm khi Stella Sora thực sự đổi UI.
- Bỏ `acquire_lang_checked`/OCR đa ngôn ngữ của SRC nếu v1 chỉ nhắm 1 server/ngôn ngữ cố định.
- Bỏ `ui_ensure_index` (OCR phân trang) — không cần cho daily UI đơn giản.
- Tùy chọn: giữ hoặc bỏ auto-detect tên qua `traceback.extract_stack()` — "ảo thuật" tiện nhưng hơi fragile; có thể thay bằng `Page(check_button, name="page_x")` tường minh nếu muốn code rõ ràng hơn.

**Nên bỏ hẳn (không cần cho v1 daily-only):**
- `ui_leave_special` (thoát domain/trial) — chỉ cần nếu có combat thời gian thực.
- Toàn bộ handler liên quan map/combat trong `ui_additional` (COMBAT_EXIT, MAP_LOADING, rogue...).

### Bẫy & edge case code gốc đã xử lý

- **Debounce bằng interval**: `interval_is_reached`/`interval_reset` trên từng button, và `interval_clear(list(Page.iter_check_buttons()))` ngay đầu `ui_goto` (ui.py:135) — tránh bị "kẹt interval cũ" chặn phát hiện/bấm ngay lượt đầu sau khi gọi lại.
- **Timeout cứng + thoát an toàn**: `ui_get_current_page` giới hạn 10s/20 lần chụp, nếu vẫn không nhận diện được page nào và không popup nào xử lý được thì chủ động `raise GamePageUnknownError` (không loop vô hạn, không đoán mò bấm bừa) — log rõ danh sách page hỗ trợ để người dùng tự can thiệp.
- **Popup được xử lý ở CẢ hai điểm dừng** (unknown-page và stuck-trong-goto) chứ không chỉ một chỗ — tránh trường hợp popup xuất hiện giữa lúc đang di chuyển giữa 2 page (không phải lúc detect ban đầu).
- **Thứ tự handler có ý nghĩa**: comment ALAS ui.py:469-471 "Has a popup_confirm variant so must take precedence" — 2 popup nhìn giống nhau nhưng 1 loại cụ thể phải check trước loại chung chung, tránh xử lý sai bằng handler tổng quát.
- **Độ trễ "settle" trước khi bấm**: case `WITHDRAW` (ALAS ui.py:525-542) — comment mô tả bug game client: bấm ngay sau khi detect có thể trúng frame cũ gây treo game; code chủ động `sleep(2)` + chụp lại rồi mới bấm.
- **`clear_connection()` luôn được gọi ở cuối `ui_goto`** dù thành công hay đang lặp — tránh rò rỉ `parent` pointer cũ sang lần gọi `ui_goto` tiếp theo với đích khác.
- **`ui_button_interval_reset(button)` hook**: bấm 1 nút điều hướng có thể kéo theo popup liên quan (vd bấm vào dorm/meowfficer thì reset interval của `GET_SHIP`) — nếu không reset, popup liên quan có thể bị interval cũ che mất trong vài giây.
- **`Page.__eq__/__hash__` theo `name` (string) chứ không theo identity object** — cho phép so sánh/dùng làm dict key ổn định dù reference module khác nhau.

**Đáng tái sử dụng nhất:**
- Copy class Page + init_connection (BFS ngược từ đích, page.py:6-45) gần như nguyên vẹn — routing tự động cho 6-8 page daily, không cần bảng lộ trình thủ công
- Copy khung 3 hàm ui_get_current_page/ui_goto/ui_ensure (ui.py SRC:35-207) — vòng lặp screenshot→detect→click-1-bước→xử-lý-popup→lặp, có timeout an toàn raise GamePageUnknownError
- Copy pattern ui_additional() = chuỗi handler nhỏ trả bool, gọi cả ở nhánh unknown-page lẫn nhánh stuck-trong-goto — bắt đầu với 2-3 handler, để chỗ mở rộng dần
- Bỏ is_in_main color-count precision, multi-skin (page_main_white), acquire_lang_checked OCR đa ngôn ngữ, ui_ensure_index, ui_leave_special — không cần cho v1 daily đơn giản 1 ngôn ngữ
- Giữ nguyên interval_clear/interval_reset debounce pattern và clear_connection() cuối ui_goto để tránh state cũ rò rỉ giữa các lần gọi

---

## 5. Config + Scheduler

### Tổng quan Config + Scheduler
- SRC dùng config kiểu class-attribute + codegen (KHÔNG phải pydantic thật): `argument.yaml/task.yaml/override.yaml` → `args.json` → sinh `config_generated.py` (chỉ chạy 1 lần lúc dev, không chạy runtime). Config thực chạy là JSON `./config/<name>.json`, cấu trúc `{Task: {Group: {Arg: value}}}`.
- `AzurLaneConfig(ConfigUpdater, ManualConfig, GeneratedConfig, ConfigWatcher)`: `ConfigUpdater` đọc/ghi/migrate file, `ManualConfig` chứa hằng số tay (gồm `SCHEDULER_PRIORITY`), `GeneratedConfig` chứa default values, `ConfigWatcher` theo dõi mtime file để phát hiện sửa tay khi tool đang chạy.
- Mỗi Task có group `Scheduler`: `Enable`(bool), `NextRun`(datetime), `Command`(tên hàm task), `ServerUpdate` (giờ reset server, vd `"04:00"`).
- Vòng lặp chính ở `module/alas.py: AzurLaneAutoScript.loop()`; entry thật `src.py: StarRailCopilot(AzurLaneAutoScript)` chỉ override từng hàm task (`dungeon()`, `daily_quest()`,...) gọi vào `tasks/`.

### API & luồng cốt lõi
1. `Function.__init__(data)` (config.py:26-36): bọc raw dict thành object `.enable/.command/.next_run`; `__eq__` so `command+next_run` để phát hiện đổi task (config.py:38-45).
2. `AzurLaneConfig.get_next_task()` (config.py:204-236), pseudocode:
```
now = datetime.now() - hoarding   # hoarding=0 nếu is_hoarding_task=False
for func in data.values():
    f = Function(func)
    if not f.enable: continue
    if next_run không phải datetime: error.append(f)   # config lỗi -> ưu tiên chạy ngay
    elif next_run < now: pending.append(f)
    else: waiting.append(f)
pending = Filter(SCHEDULER_PRIORITY).apply(pending)     # sắp theo thứ tự ưu tiên khai báo
waiting = Filter(...).apply(waiting); sort theo next_run tăng dần
pending = error + pending
```
3. `get_next()` (config.py:238-263): có `pending` → lấy `pending[0]`, `is_hoarding_task=False`. Không có pending nhưng có `waiting` → `is_hoarding_task=True`, `deepcopy(waiting[0])`, cộng thêm `hoarding` (=`Optimization.TaskHoardingDuration` phút) vào `next_run` (gom nhiều task nhỏ để đỡ mở/đóng app liên tục). Không có gì cả → raise `RequestHumanTakeover` ("Please enable at least one task").
4. `AzurLaneAutoScript.get_next_task()` (alas.py:191-271): loop `while 1`: gọi `config.get_next()` → `bind(task)`; nếu `task.next_run > now` (đang ở waiting) thì xử lý theo `Optimization_WhenTaskQueueEmpty` (`stay_there`/`goto_main`/`close_game`/`close_emulator`) rồi `wait_until(next_run)`; nếu config bị sửa giữa chừng (`should_reload()`) → huỷ cached `config` (`del_cached_property`) và `continue` để tính lại pending/waiting từ đầu.
5. `task_delay(success, server_update, target, minute, task=None)` (config.py:366-428): tính nhiều candidate datetime rồi lấy `min()` — `success=True/False` → NextRun = now + 120p/30p (hardcode SuccessInterval/FailureInterval), `server_update=True` → `get_server_next_update(Scheduler_ServerUpdate)`; ghi `self.modified[f'{task}.Scheduler.NextRun']` rồi gọi `self.update()` (load+bind+save lại).
6. `task_call(task, force_call=True)` (config.py:430-460): set `NextRun=now`, `Enable=True` cho task khác (vd lỗi game → `task_call('Restart')`); raise `ScriptError` nếu task đích không tồn tại trong config user.
7. `task_stop()/task_switched()/check_task_switch()` (config.py:462-504): task tự gọi `check_task_switch()` giữa chừng, nếu config đổi (người dùng bấm dừng/đổi ưu tiên) → raise `TaskEnd` (không phải lỗi, chỉ dừng sớm để nhường task khác).
8. Vòng lặp chính `loop()` (alas.py:273-341), pseudocode:
```
while 1:
    if stop_event.is_set(): break
    checker.wait_until_available()          # chờ server maintenance
    if checker.is_recovered(): del cached config; task_call('Restart')
    task = get_next_task()
    if is_first_task and task=='Restart': skip, chỉ task_delay(server_update=True), continue
    success = run(underscore(task))
    failure_record[task] = 0 if success else failure_record[task]+1
    if failure_record[task] >= 3: notify + RequestHumanTakeover, exit(1)
    del cached config  # nạp lại config cho vòng sau
```
9. `run(command)` (alas.py:75-150): try gọi `self.__getattribute__(command)()`, bắt exception theo tầng nghiêm trọng tăng dần:
   - `TaskEnd` → return True (kết thúc bình thường)
   - `GameNotRunningError` → `task_call('Restart')`, return False (retry)
   - `GameStuckError`/`GameTooManyClickError` → log + save_error_log, `task_call('Restart')`, sleep 10s, return False
   - `GameBugError` → tương tự, log rõ "bug game client, cần restart"
   - `GamePageUnknownError` → hỏi `ServerChecker`: nếu server rớt thì `wait_until_available()` (return False), nếu server ổn → crash thật: notify + exit(1)
   - `HandledError` → log, return False (lỗi đã tự xử lý trong task, không cần thêm gì)
   - `ScriptError`/Exception khác → log traceback đầy đủ, `error_postprocess()`, save_error_log, notify, `exit(1)` (không tự retry — coi là lỗi dev, cần người sửa)
   - `RequestHumanTakeover` → notify, `exit(1)` ngay lập tức

### Khuyến nghị cho Stella Sora Tool
- **Copy nguyên khối**: mô hình `Function` (enable/command/next_run), 2 tầng pending/waiting + `Filter` ưu tiên trong `get_next_task/get_next`, `task_delay`/`task_call`/`task_stop`/`check_task_switch`, phân loại exception theo tầng nghiêm trọng trong `run()`, `failure_record` đếm 3 lần rồi dừng hẳn toàn script.
- **Đơn giản hóa mạnh**: bỏ hẳn pipeline codegen (argument.yaml/task.yaml/override.yaml → args.json → config_generated.py) — với ~7 task daily, viết tay 1 schema JSON/dataclass cố định, không cần `ConfigGenerator`/`ConfigUpdater.config_update` phức tạp (migrate version, redirection, i18n gen).
- Cân nhắc bỏ `hoarding`/`TaskHoardingDuration` (gom nhiều task chờ để mở app 1 lần) ở v1 — chỉ cần: có task pending thì chạy task ưu tiên cao nhất, không có thì sleep tới waiting sớm nhất.
- Bỏ 4 chế độ `Optimization_WhenTaskQueueEmpty` (close_game/close_emulator/goto_main/stay_there) — v1 chỉ cần 1 hành vi mặc định (vd `goto_main` hoặc đơn giản là sleep tại chỗ), thêm dần sau nếu cần.
- Bỏ hẳn phần pywebio/GUI-realtime-edit và bind/override phức tạp cho nhiều instance — SRC hỗ trợ multi-config vì phục vụ GUI đa tài khoản, v1 của Stella Sora chỉ cần 1 config file.
- Vẫn nên giữ (đơn giản hoá) `ConfigWatcher.should_reload()` — so mtime file trước mỗi vòng sleep, để người dùng sửa JSON tay mà không cần khởi động lại tool.
- Bỏ redirection/convert (migrate config cũ qua version mới) ở v1 — chỉ thêm khi tool đã public lâu và đổi schema.
- Giữ atomic write khi lưu JSON (ghi file tạm rồi rename) để tránh hỏng file khi crash giữa chừng lúc `save()`.

### Bẫy & edge case code gốc đã xử lý
- `next_run` không phải `datetime` (field lỗi/None) → xếp vào `error` list và ưu tiên chạy NGAY trước cả pending khác (config.py:218-219, 232-233), không crash — tool mới nên coi field NextRun hỏng là "cần chạy lại ngay", không phải lỗi fatal.
- `waiting_task[0]` phải `deepcopy` trước khi cộng thêm `hoarding` (config.py:256) — tránh sửa nhầm object gốc trong `self.data`/`self.waiting_task`.
- `bind()` luôn chèn `"Alas"` vào đầu `func_list` (config.py:142-148) vì giá trị global (Emulator, SCHEDULER_PRIORITY, Optimization...) nằm ở task ảo `Alas`; mỗi Function/task chỉ có value nhóm của riêng nó.
- `is_first_task`: bỏ qua task `Restart` đầu tiên khi mới khởi động script (alas.py:300-304) — tránh restart game ngay khi user vừa mở tool xong (game/emulator có thể đã mở sẵn).
- `should_reload()` dùng trong `wait_until()` khi đang idle chờ next_run — nếu người dùng sửa config lúc tool đang chờ, phải huỷ cached config và tính lại pending/waiting ngay, không đợi tới next_run cũ mới nhận ra.
- `checker.is_recovered()` trong `loop()`: khi server bảo trì xong, chủ động gọi lại task Restart vì comment gốc ghi "có bug hiếm khó tái hiện, config đôi khi không tự cập nhật dù đã đổi" (alas.py:286-293) — nên giữ safety-net này dù nghe lạ.
- `GamePageUnknownError` không tự kết luận lỗi ngay — check server qua `ServerChecker` trước rồi mới quyết định crash hay chờ, tránh restart loop vô ích khi lỗi do server sập chứ không phải bug game (alas.py:103-117).
- `task_call` raise `ScriptError` nếu task đích không tồn tại trong config user (config.py:446-447) — copy check này để tránh gọi nhầm task đã bị đổi tên/xoá giữa các version.
- `failure_record` đếm theo **từng task riêng** (dict theo tên task) chứ không đếm global — 1 task lỗi liên tục không chặn task khác chạy, nhưng đủ 3 lần thì dừng TOÀN BỘ script (coi là lỗi nghiêm trọng cần người can thiệp), không chỉ tắt riêng task đó.
- Serialize JSON qua `json.dumps(..., default=str)` để tự chuyển datetime → ISO string, đọc lại qua `parse_value`/`datetime.fromisoformat` (utils.py:204-207) — JSON không có kiểu datetime native, tool mới phải tự xử lý parse/serialize 2 chiều này nếu tự viết config store.

**Đáng tái sử dụng nhất:**
- Model Function(enable/command/next_run) + get_next_task/get_next 2 tầng pending/waiting kèm Filter ưu tiên (SCHEDULER_PRIORITY) — lõi scheduler đáng copy nhất
- task_delay(success/server_update/target/minute) lấy min() các candidate datetime, và task_call(task) để chain task (vd lỗi -> gọi Restart)
- run() phân loại exception theo tầng nghiêm trọng (TaskEnd/GameNotRunningError/GameStuckError/GamePageUnknownError/ScriptError/RequestHumanTakeover) — bản đồ lỗi rất đáng tái dùng cho v1
- failure_record đếm lỗi theo từng task riêng, đủ 3 lần thì RequestHumanTakeover dừng hẳn script
- ConfigWatcher.should_reload() (so mtime file) để phát hiện user sửa JSON tay khi tool đang chạy, không cần restart

---

## 6. Giải phẫu task mẫu

### Tổng quan giải phẫu task
Xem xét `tasks/assignment` (SRC — nhận thưởng + phái cử, tương đương commission) và `module/commission/commission.py` (ALAS). Cả hai theo mẫu chung: 1 class kế thừa chuỗi mixin UI, có `run()` public làm entry point, được gọi bởi entry class cấp trên (`src.py: StarRailCopilot`), rồi kết thúc bằng tự ghi lịch chạy tiếp (`task_delay`) và có thể gọi task khác (`task_call`). Scheduler nằm ở `module/alas.py` — SRC gần như copy nguyên bản base này từ ALAS.

### API & luồng cốt lõi
**Kế thừa & entry point** (`tasks/assignment/assignment.py:16`, `claim.py:14`, `dispatch.py:46`, `ui.py:177`):
```
class Assignment(AssignmentClaim, SynthesizeUI)  # -> AssignmentDispatch -> AssignmentUI -> UI
```
`src.py:51-53`: `def assignment(self): Assignment(config=self.config, device=self.device).run()` — tên method = `inflection.underscore(TaskName)`, tra cứu động bằng `getattr(self, command)()` (`module/alas.py:79`).

**run() pseudocode** (`assignment.py:17-100`):
```
def run(self, assignments=None, duration=None, join_event=None):
    self.config.update_battle_pass_quests(); self.config.update_daily_quests()  # refresh state
    assignments = assignments or [config.Assignment_Name_1..4]   # đọc config, dedupe
    self.menu_enter_top(page_assignment)                          # điều hướng UI
    self.dispatched = {}; self.has_new_dispatch = False           # state instance (KHÔNG lưu config)
    if config.Assignment_ClaimAll: self.claim_all()
    ...quét & claim/dispatch theo priority nhóm...
    with self.config.multi_set():
        if <đạt điều kiện>: self.config.task_call('DailyQuest')        # gọi task khác
        if self.dispatched: self.config.task_delay(target=min(self.dispatched.values()))
        else: self.config.task_delay(minute=120)                       # fallback an toàn khi rỗng
```
`DailyQuestUI.run()` (`tasks/daily/daily_quest.py:410-447`): `for _ in range(5): get_daily_rewards() -> break nếu got; else OCR quest list -> check_future_achieve() -> do_daily_quests() -> break nếu done==0`; kết `task_call('DataUpdate')` nếu có claim + `task_delay(server_update=True)`.

**Config primitives cốt lõi** (`module/config/config.py`):
- `task_delay(success=None, server_update=None, target=None, minute=None, task=None)` (:366) — set `{task}.Scheduler.NextRun`, lấy `min()` nếu nhiều điều kiện.
- `task_call(task, force_call=True)` (:430) — set NextRun=now + Enable=True cho task khác, raise `ScriptError` nếu task không tồn tại trong config.
- `multi_set()` (:327) — context manager gộp nhiều lần set config thành 1 lần save.

**Scheduler loop** (`module/alas.py`):
```
def get_next_task(self):  # :191 — chọn config.get_next() theo Scheduler.NextRun sớm nhất, bind args
def run(self, command):   # :75 — screenshot -> getattr(self,command)() -> bắt exception theo loại
def loop(self):           # :273 — vòng lặp vô hạn: get_next_task -> run -> đếm failure_record
```
`run()` bắt exception theo tầng: `TaskEnd`→coi như success; `GameNotRunningError/GameStuckError/GameBugError`→`task_call('Restart')` rồi tiếp tục; `GamePageUnknownError`→check server status; `ScriptError`/`RequestHumanTakeover`/`Exception` khác→log, notify, `exit(1)`. `loop()` đếm `failure_record[task]`, ≥3 lần liên tiếp thất bại → coi là cần người can thiệp, `exit(1)`.

ALAS `RewardCommission.run()` (`module/commission/commission.py:603-639`): `ui_ensure(page_reward) -> commission_receive() -> handle_info_bar() -> commission_start()`; scheduler: `task_delay(target=future_finish)` nếu có commission đang chạy, else `task_delay(success=False)`.

### Khuyến nghị cho Stella Sora Tool
- **Copy nguyên**: bộ 3 primitive config `task_delay/task_call/multi_set` — đây là xương sống kiến trúc "task tự hẹn next_run", đơn giản và đã proven.
- **Copy nguyên**: `run(command)` wrapper của scheduler với try/except theo từng loại exception + `failure_record` đếm dồn (3 lần fail → dừng, cần người can thiệp). Cho v1 chỉ cần vài exception: `GameNotRunningError`, `GameStuckError`, generic `Exception` → `exit`.
- **Copy pattern**: mỗi task = 1 class có `run()` public, method dispatcher ở entry class (`self.<task_name>()` khởi tạo `TaskClass(config, device).run()`), đọc config trực tiếp qua `self.config.<Group>_<Field>` (typed generated config).
- **Copy pattern ALAS commission**: "nhận thưởng trước (nếu có) → thực hiện hành động → tính lịch tiếp theo từ finish_time thực tế" — khớp với mô hình "claim rồi làm" của 7 daily Stella Sora.
- **Đơn giản hóa**: bỏ các layer quét đa nhóm phức tạp của Assignment (`_check_inlist/_check_all/_dispatch_remain/_check_event`) — Stella Sora daily đơn giản hơn nhiều, chỉ cần 1-2 tầng: kiểm tra trạng thái → claim nếu claimable → làm nếu chưa.
- **Đơn giản hóa**: bỏ OCR quest-matching + `stored.DailyQuest`/keyword class hierarchy (`AssignmentEntry.find`, `KEYWORDS_DAILY_QUEST`) — v1 không cần OCR nhận diện quest động, chỉ cần chuỗi template-match + click cố định cho từng daily UI đã biết trước.
- **Bỏ hẳn**: `cross_get/cross_set` (điều phối chéo giữa nhiều task, ví dụ GemsFarming delay) — chỉ cần khi có task phụ thuộc lẫn nhau, chưa cần cho 7 daily độc lập.
- **Bỏ hẳn**: cơ chế OilMaxed/GemsFarming-specific của ALAS (đặc thù Azur Lane) — không liên quan Stella Sora.

### Bẫy & edge case code gốc đã xử lý
1. `assignment.py:82-94` — `min(self.dispatched.values())` sẽ `ValueError` nếu dict rỗng; code check `if len(self.dispatched)` trước, else log error + `task_delay(minute=120)` làm fallback.
2. `assignment.py:87-90` — nếu thời điểm dispatch xong gần server reset (<4h) thì ưu tiên delay tới server update thay vì delay theo dispatch, tránh miss cửa sổ daily reset.
3. `claim.py:_exit_report` (:107-135) — assignment dạng EVENT không đóng report bằng nút thường (`REDISPATCH`/`CLOSE_REPORT`) mà có `EVENT_COMPLETED` riêng; phải check riêng để tránh vòng lặp treo.
4. `commission.py:_commission_start_click` (:329-409) — có `comm_timer`/`count>=3` raise `GameStuckError` chủ động khi gặp "commission list flashing bug" đã biết trước (game bug), tránh loop vô hạn.
5. `commission.py:commission_receive` (:582-601) — bắt riêng `OilMaxed`, xử lý phụ (mua food tiêu dầu) rồi retry tối đa 3 lần trước khi `RequestHumanTakeover`.
6. `commission.py:_commission_scan_all` (:290-313) — phát hiện dữ liệu "night commission" cache cũ khi không phải giờ đêm → chủ động re-scan thay vì tin ngay kết quả OCR đầu tiên.
7. `module/alas.py:get_next_task` (:300-304) — `is_first_task` guard: bỏ qua task `Restart` đầu tiên khi vừa khởi động scheduler, tránh restart app ngay khi mới mở tool.
8. `daily_quest.py:run` (:410-426) — vòng `for _ in range(5)` có early-break khi `done == 0` (không còn quest nào làm được), tránh vòng lặp vô hạn khi OCR/click không match nữa.

**Đáng tái sử dụng nhất:**
- Bộ 3 config primitive task_delay/task_call/multi_set (module/config/config.py:327,366,430) — xương sống cơ chế task tự hẹn lịch, nên copy gần như nguyên bản
- Scheduler run(command)+loop() với try/except phân theo loại exception và failure_record đếm dồn 3 lần fail → human takeover (module/alas.py:75-150,273-340)
- Mẫu class task: 1 class kế thừa mixin UI, run() public, đọc config trực tiếp, kết thúc bằng task_delay/task_call trong multi_set() — dùng làm khuôn cho cả 7 daily task
- Pattern ALAS commission: claim reward trước → thực hiện hành động → tính next_run từ finish_time thực tế, đơn giản hơn Assignment nên ưu tiên tham khảo bản này
- Bẫy đáng nhớ nhất: guard min() trên dict rỗng, và is_first_task để không auto-restart app ngay khi mới mở tool

---

## 7. Asset pipeline (dev_tools)

### Tổng quan Asset pipeline (SRC dev_tools)

SRC sinh code Python (`Button`/`ButtonWrapper`) tự động từ ảnh PNG full-screen đặt đúng convention thư mục — không cần tool GUI, không nhập tay toạ độ. Quy trình: chụp full-screen 1280x720 → paint đen (0,0,0) mọi vùng ngoài nút cần bắt → lưu đúng tên file theo quy ước → chạy `python -m dev_tools.button_extract` → codegen ra `tasks/<module>/assets/assets_<module>_<sub>.py`. File gốc: `dev_tools/button_extract.py` (356 dòng), `module/base/button.py` (Button/ButtonWrapper), `module/base/utils/utils.py` (get_bbox/get_color/load_image).

### API & luồng cốt lõi

**Convention tên file** — regex `REGEX_ASSETS` (button_extract.py:62-70):
`assets/<server>/<module>/<ASSET_NAME>[.<frame>][.<ATTR>].png`
- `server`: `share|cn|en` (`VALID_LANG=['cn','en']`, module/config/server.py:8). Đếm thực tế: 781 ảnh ở `share` vs chỉ 93/98 ở `cn`/`en` → đa số nút dùng chung, cn/en chỉ override nút có TEXT khác ngôn ngữ.
- `module`: đường dẫn lồng nhau `[a-zA-Z0-9_/]+` (VD `daily/reward`) → 1 task có nhiều file assets con thay vì 1 file khổng lồ.
- `attr` optional: `AREA|SEARCH|COLOR|BUTTON|GRID` để override 1 thuộc tính riêng của ảnh gốc cùng tên.
- `frame` optional `.N`: nhiều ảnh cùng tên khác frame → gộp thành `list[Button]` (item lặp lại kiểu carousel/list).

**Ràng buộc ảnh nguồn** (quy ước cốt lõi của cả pipeline): PNG phải đúng `ASSETS_RESOLUTION=(1280,720)` (config_manual.py:22-24, kiểm tra tại button_extract.py:117-119), alpha luôn 255 (không dùng transparency thật), vùng "không phải nút" phải là RGB đen tuyệt đối `(0,0,0)`. Đã verify bằng `assets/share/daily/reward/ACTIVE_POINTS_1_CHECKED.png`: size=(1280,720), corner pixel=[0,0,0,255]. `get_bbox(image, threshold=0)` (utils.py:815) tìm bbox vùng non-black qua `cv2.threshold` trên ảnh grayscale — không cần alpha thật, chỉ cần nền đen tuyệt đối.

**`AssetsImage.parse()`** (button_extract.py:113-129), pseudocode:
```
image = load_image(file)                       # PIL->np, RGBA2RGB (drop alpha)
assert image_size(image) == (1280, 720)        # else: warning + invalid, bị loại êm
bbox  = get_bbox(image, threshold=0)           # -> area
mean  = get_color(image, area=bbox)            # -> color trung bình (r,g,b)
if attr == 'GRID': grids = parse_grid(image)   # cv2.findContours trên marker trắng vẽ sẵn
```
`parse_grid()` (button_extract.py:23-58): threshold ảnh về nhị phân (127-255=trắng), `cv2.findContours` lấy từng ô đánh dấu, xếp theo hàng (y) rồi cột (x) → 1 ảnh gốc tự cắt thành N frame (VD bảng lịch thưởng theo ngày) mà không cần crop N ảnh tay.

**`DataAssets`** (button_extract.py:173-293) — gộp `AssetsImage` theo `(module, assets, server, frame)` bằng `deep_set/deep_get` (dict lồng nhau):
- `area/color/button` mặc định = bbox/mean của ảnh base (attr rỗng); `search` mặc định = `area_pad(area, pad=-20)` rồi clip vào màn hình (`DataAssets.area_to_search`, dòng 192-195) — tức window tìm kiếm lớn hơn `area` 20px mỗi cạnh (docstring Button.__init__, button.py:13).
- Override AREA/SEARCH/COLOR/BUTTON chỉ set field tương ứng, đè lên base; nếu frame 1 có override mà frame khác không có, override đó tự lan sang mọi frame khác (dòng 280-291).
- `iter_assets()` (dòng 233-259) validate: ảnh attr mồ côi (không có ảnh base/frame-1 tương ứng) → cảnh báo + loại; `SEARCH` chỉ hợp lệ ở frame 1.

**Codegen** (`generate_code`, dòng 296-351): dọn sạch `assets.py`/mọi `.py` cũ trong `tasks/<module>/assets/` (trừ `__init__.py`) trước khi ghi lại (dòng 301-308), rồi dùng `CodeGenerator` (module/base/code_generator.py) — 1 lớp helper phát code Python đọc được, commit vào git — để in mỗi asset thành:
```python
NAME = ButtonWrapper(name='NAME',
    share=Button(file=..., area=..., search=..., color=..., button=...),
    cn=Button(...),  # chỉ có nếu tồn tại override riêng cn
)
```

**Runtime dùng lại chính ảnh gốc làm template**: `Button.image` là `cached_property` = `load_image(self.file, self.area)` (button.py:74-76) — tức lúc match template, code load lại đúng file PNG 1280x720 rồi crop theo `area`, KHÔNG lưu template đã crop riêng. `ButtonWrapper.buttons` (button.py:248-260) chọn Button theo thứ tự fallback `[server.lang, 'share', 'cn']` — fallback resolve LÚC CHẠY (runtime), không bake cứng lúc build; nếu không có bản nào phù hợp → `raise ScriptError` rõ ràng (dòng 260).

**So với ALAS** (`reference/AzurLaneAutoScript/dev_tools/button_extract.py`): thuật toán trích bbox/color giống hệt (get_bbox+get_color), nhưng ALAS: (1) không có `share`, phải có đủ ảnh cho từng server cn/en/jp/tw hoặc bake cứng fallback-copy-từ-cn ngay lúc build (dòng 97-102); (2) mỗi module = 1 file `assets.py` phẳng dưới `module/<name>/`, không có nested submodule; (3) `Button` không có `search`/`GRID`/`frame`, và `Template` (ảnh `TEMPLATE_*`) là class riêng biệt tách khỏi Button. → SRC "làm lại" chủ yếu để: gộp Button+Template làm một, tách rõ `search` (vùng tìm) khỏi `area` (vùng template) khỏi `button` (điểm click), thêm GRID/frame để không phải crop tay N ảnh giống nhau, và thêm tầng `share` để không phải duplicate asset cho mỗi ngôn ngữ.

### Khuyến nghị cho Stella Sora Tool

**Copy gần như nguyên bản** (giá trị cao, đơn giản, đã proven):
- Convention "ảnh nguồn full 1280x720, nền ngoài-nút sơn đen tuyệt đối, `get_bbox(threshold=0)` + `get_color(mean)`" — cực rẻ để dev thêm asset mới (chỉ cần crop 1 ảnh, không nhập toạ độ tay).
- Regex filename → tự động index → codegen: walk thư mục `assets/<module>/<NAME>[.ATTR].png`, sinh `Button(area=..., search=..., color=..., button=...)` thành file `.py` review được trên git diff (không phải blob nhị phân).
- `Button` giữ 3 vùng tách biệt: `area` (crop template để so khớp), `search` (vùng crop để tìm, mặc định = area nới rộng ~20px), `button` (điểm click, có thể lệch khỏi area) — rất đáng giữ vì click point thường khác vùng nhận diện.
- Bước dọn file `.py` cũ trước khi regenerate, để asset bị xoá không để lại code rác.

**Đơn giản hoá mạnh** (Stella Sora là game 1 server/1 ngôn ngữ, theo brief v1 không cần map/grid):
- Bỏ hẳn tầng `server` (`share/cn/en`) và toàn bộ logic fallback `ButtonWrapper.buttons` — chỉ 1 bộ ảnh `assets/<module>/<NAME>.png`, `Button` phẳng không cần đa-server.
- Gộp 1 file `assets.py` mỗi module (kiểu ALAS) thay vì tách nhiều file `assets_<module>_<sub>.py` — ít phức tạp hơn khi project nhỏ.
- Bỏ `GRID`/`frame` (multi-frame list) ở v1; thêm lại sau nếu gặp UI dạng bảng lặp (VD lịch điểm danh) cần tự cắt N ô.
- Override `AREA`/`COLOR`/`BUTTON`/`SEARCH` riêng file: SRC dùng rất ít trong thực tế (chỉ vài chục file override so với 781 ảnh base) — có thể chỉ giữ `SEARCH`+`BUTTON` override, bỏ `AREA`/`COLOR` override, thêm lại khi cần.
- `CodeGenerator` class tổng quát (code_generator.py) có thể thay bằng vài dòng f-string đơn giản — không cần abstraction Object/List/ListItem đầy đủ.

**Bỏ hẳn**: đa server/đa ngôn ngữ, GRID contour-parsing, `posi` (vị trí ô grid), `Template` class riêng của ALAS (không cần vì Button đã đủ).

### Bẫy & edge case code gốc đã xử lý

1. **Resolution mismatch bị nuốt lặng lẽ**: ảnh không đúng 1280x720 chỉ log warning rồi đánh `valid=False`, âm thầm loại khỏi codegen — không raise lỗi cứng (button_extract.py:117-119). Dev quên crop đúng full-screen sẽ mất asset mà không có exception rõ ràng.
2. **File attribute mồ côi**: `XXX.AREA.png` tồn tại nhưng thiếu `XXX.png` (base) hoặc thiếu frame 1 tương ứng → warning + loại, tránh crash khi codegen (dòng 250-255).
3. **`SEARCH` chỉ hợp lệ ở frame 1**: `SEARCH` với frame>1 bị từ chối (dòng 256-258) — tránh nhầm lẫn ngữ nghĩa multi-frame với vùng tìm kiếm riêng.
4. **Kế thừa override từ frame 1 sang các frame khác** nếu frame đó không tự override (dòng 280-291) — tránh phải lặp lại AREA/COLOR/BUTTON cho từng frame trong 1 GRID.
5. **Giả định nền đen tuyệt đối**: nếu nội dung thật của nút có màu đen thuần (0,0,0), `get_bbox` sẽ cắt nhầm/mất phần đó — giả định ngầm xuyên suốt pipeline, cần biết khi crop ảnh mới (không dùng transparency thật, alpha luôn 255).
6. **Dọn sạch trước khi regenerate**: xoá mọi `.py` cũ trong `assets/` (trừ `__init__.py`) trước khi ghi lại (dòng 301-308) — nếu bỏ bước này, asset đã xoá khỏi ảnh gốc vẫn còn code rác tồn tại.
7. **Bỏ qua dotfile** khi walk thư mục ảnh (`.DS_Store`...) (dòng 162) — tránh crash khi parse tên file không khớp regex.
8. **`_button_offset` được set kể cả khi match thất bại** (điểm match tốt nhất vẫn ghi vào offset, `match_template`, button.py:133-139) và phải `clear_offset()` khi release resource (button.py:82-85) — nếu quên clear, offset cũ có thể rò rỉ sang lần match tiếp theo cho nút có vị trí xê dịch nhẹ.
9. **Fallback thiếu asset raise lỗi rõ ràng** thay vì lỗi ngầm: `ButtonWrapper.buttons` thử `[server.lang, 'share', 'cn']`, hết cả 3 mà vẫn không có → `raise ScriptError` (button.py:260) thay vì trả None gây crash mơ hồ ở chỗ khác.

**Đáng tái sử dụng nhất:**
- Convention ảnh nguồn: full 1280x720, nền ngoài-nút sơn đen tuyệt đối (RGB 0,0,0), get_bbox(threshold=0)+get_color(mean) tự tính area/color — dev chỉ crop 1 ảnh, không nhập toạ độ tay
- Regex filename -> walk thư mục -> codegen Button(area, search, color, button) thành .py review được trên git diff, xoá code cũ trước khi ghi lại tránh rác
- Button tách 3 vùng riêng: area (template match), search (vùng crop để tìm, mặc định area nới ~20px), button (điểm click có thể lệch khỏi area) — nên giữ nguyên vì click point hay khác vùng nhận diện
- Bỏ hẳn tầng server/share/cn-en (game 1 ngôn ngữ), bỏ GRID/frame và override AREA/COLOR riêng file ở v1 — chỉ 1 bộ ảnh assets/<module>/<NAME>.png, 1 file assets.py mỗi module kiểu ALAS
- Runtime dùng lại chính PNG gốc làm template (Button.image = load_image(file, area) lazy-load) thay vì lưu template crop riêng — đơn giản, ít file trùng lặp

---

## 8. Phản biện độ đầy đủ — việc còn thiếu trước Phase 3

### Còn thiếu (cần tra thêm khi viết skeleton)
- Logging: chưa section nào quyết định hệ thống log. Tra `module/logger/logger.py` (rich Console/RichHandler, ép utf-8 stdout) và `module/logger/error.py: save_error_log(config, device)` — khi crash tự dump traceback+screenshot+config snapshot vào `log/<timestamp>/`. Cần chốt: dùng rich hay logging chuẩn, có giữ cơ chế error-dump-kèm-screenshot không.
- Notify: `run()`/`task_call` trong ghi chú nhắc 'notify' nhiều lần nhưng không section nào giải thích. Tra `module/notify.py` (thư viện `onepush`, YAML config nhiều provider Discord/Telegram/ServerChan...). Cần chốt v1 có cần báo lỗi ra ngoài hay chỉ log nội bộ.
- app_start/app_stop có 2 TẦNG tách biệt mà không note nào nêu: `module/device/app_control.py: class AppControl` (raw `adb shell am start/force-stop`, generic) khác hẳn `tasks/login/login.py: Login.app_start/app_stop/app_restart` (xử lý popup agreement, chờ màn login ổn định, cloud game riêng). Tra `tasks/login/login.py:170-200` và `src.py:6-16` (StarRailCopilot.restart/start/stop/goto_main override) để biết ranh giới Device vs Task layer.
- Config mặc định cho user mới: chưa ai đọc `config/template.json` (schema JSON baked sẵn) và `config/deploy.template.yaml`/`ConfigUpdater.config_update` — cần biết cấu trúc này để quyết định cách sinh config lần đầu cho Stella Sora Tool.
- Timezone reset server: tra `module/config/utils.py:278-289` (`server_timezone()`, `server_time_offset()`, dict `SERVER_TO_TIMEZONE`) + `get_server_next_update/get_server_last_update`. Thiếu domain fact quan trọng: server Stella Sora target (CN/quốc tế/khác) reset lúc mấy giờ theo timezone nào — cần tra doc game hoặc hỏi người dùng, không chỉ tra code.
- Dependency/requirements: không section nào liệt kê `requirements.txt`/`requirements-in.txt` gốc (opencv-python, numpy, adbutils, retry, rich, pyyaml, inflection, pydantic, pponnxcr, onnxruntime, pywebio, starlette, uvicorn...). Cần tra file này để chốt danh sách lib tối thiểu cho skeleton Phase 3.
- Entry point/CLI: tra `src.py` (`if __name__=='__main__': src=StarRailCopilot('src'); src.loop()`) — không argparse, `config_name` là string hardcode ánh xạ `config/<name>.json`; entry class (`src.py`) còn là nơi map `Task -> TaskClass(config,device).run()` qua method cùng tên. Chưa section nào mô tả entry point thật của skeleton (alas.py) sẽ trông như thế nào.
- Restart định kỳ theo thời gian (không phải do lỗi): không thấy cơ chế 'restart game mỗi N giờ để chống leak' trong cả ALAS/SRC — cần xác nhận rõ ràng đây KHÔNG phải yêu cầu v1, tránh người viết skeleton tự thêm nhầm task không có căn cứ.
- ServerChecker thật ra là gì: tra `module/server_checker.py` — hiện là STUB rỗng (`is_available()->True` cố định, comment 'server check is not supported yet'), không phải cơ chế theo dõi bảo trì server hoạt động thật như ghi chú [config-scheduler] ngụ ý.
- Threading model tổng thể: `nemu_ipc` dùng `WORKER_POOL` riêng (device layer), nhưng chưa section nào chốt toàn app có chạy đa luồng gì khác không (GUI thread, watcher thread...) — cần xác nhận v1 là 1 process, 1 thread chính, blocking loop hoàn toàn vì không có GUI.

### Mâu thuẫn/mơ hồ cần chốt
- [device] đề xuất Device sở hữu trọn `app_start()/app_stop()/app_current()` như API tối giản, nhưng code thật đặt orchestration (chờ ổn định, xử lý popup) ở TASK layer (`tasks/login/login.py`), Device chỉ raw am start/stop. Cần chốt ranh giới rõ: Device = primitive không điều kiện, Login task = logic chờ+xử lý popup.
- [config-scheduler] khuyên 'giữ nguyên safety-net `checker.is_recovered()`' như cơ chế phát hiện bảo trì server có thật, nhưng `module/server_checker.py` là STUB rỗng trong SRC hiện tại (chưa hoạt động thật bao giờ). Cần quyết định: stub y hệt SRC (đơn giản) hay tự xây network-check thật cho Stella Sora — 2 lựa chọn khác hẳn nhau về effort, ghi chú hiện chưa phân biệt.
- [device] tự mâu thuẫn nội bộ về control method: một câu nói giữ 'MaaTouch hoặc minitouch' (chưa chọn), câu khác (Interface tối giản) chỉ liệt kê `click_maatouch` bỏ hẳn minitouch — chưa chốt dùng cái nào, và chưa đặt câu hỏi liệu v1 (không real-time) có cần method click nhanh nào ngoài ADB/nemu_ipc hay không.
- [tasks] nêu `error_postprocess()` như hook chung nên copy, nhưng ví dụ thật (`src.py:29-33`) chỉ áp dụng cho 'cloud game' (thoát để đỡ phí cloud) — không liên quan Stella Sora (game cài local). Dễ bị hiểu nhầm là hook bắt buộc phải có.
- [base] và [assets] dùng chữ 'frame' cho 2 khái niệm khác nhau: GRID/frame trong asset pipeline (nhiều ảnh cùng tên → list Button cho UI dạng bảng lặp, [assets] khuyên giữ) vs animated multi-frame template/'is_gif' ([base] khuyên bỏ hẳn) — cần tách rõ thuật ngữ khi viết skeleton để không xoá nhầm tính năng cần giữ.

### Nên đơn giản hóa thêm cho v1
- `ServerChecker`: implement y hệt bản STUB của SRC (trả cố định true/false, không network call thật) — đủ dùng v1, tránh xây health-check phức tạp cho tính năng SRC còn chưa làm thật.
- Bỏ hẳn `MaaTouch`/`minitouch`: v1 chỉ điều hướng UI + click nút cố định (không real-time combat) nên `adb input tap` (ADB) + `nemu_ipc` (MuMu) đã đủ nhanh/chính xác — không cần cài thêm binary/service ngoài (MaaTouch APK, minitouch push binary).
- Bỏ hẳn subsystem `notify` (onepush đa provider + YAML) — v1 chỉ cần log lỗi console/file; nếu thật sự cần báo ngoài, dùng thẳng 1 webhook đơn giản (`requests.post`) thay vì abstraction đa provider.
- Đơn giản hoá logging: bỏ tuỳ biến sâu `rich.Console`/`Theme`/`RichHandler` — dùng `logging` chuẩn + `RotatingFileHandler`, chỉ giữ Ý TƯỞNG `save_error_log` (chụp screenshot + dump config lúc crash) vì giá trị debug cao, không cần rendering đẹp.
- Bỏ hẳn `deploy/` (installer tự tìm adb/emulator, tự update qua git, tự cài pip, `console.bat`, ~14 file Windows-specific) — v1 chạy trong venv Python có sẵn, user tự cài theo hướng dẫn tay.
- Bỏ hẳn GUI/webapp (`gui.py`, `webapp/`, `pywebio`+`starlette`+`uvicorn`+`watchgod`) khỏi cả kiến trúc lẫn `requirements.txt` — cắt luôn dependency (~8 package) thay vì chỉ 'không dùng tới'.
- Bỏ OCR-related deps khỏi requirements ban đầu (`pponnxcr`, `onnxruntime`, `shapely`, `pyclipper`) vì OCR đã đồng thuận để 'sau' ở cả 3 section — thêm lại đúng lúc triển khai module/ocr, không kéo sẵn từ đầu.
- Bỏ cơ chế multi-config/multi-instance (`config/<name>.json` chọn qua argv/GUI cho nhiều tài khoản) — v1 hardcode 1 tên config cố định (vd `config/stella.json`), không cần layer chọn instance.
