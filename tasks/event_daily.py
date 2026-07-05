"""Task EventDaily — Quick Battle sweep ở Battle Stage của sự kiện đang diễn ra.

Khảo sát live 2026-07-05 (event "A Sandstorm of GUNFIRE"). Flow:
    home → BANNER sự kiện (EVENT_BANNER, vào THẲNG event interior)
         → dartboard Battle Stage (BATTLE_STAGE_ENTER)
         → danh sách stage (cuộn NGANG, zigzag, badge đỏ "1-N")
         → chọn stage → Quick Battle (xanh) → dialog (">>" max / "+" từng trận) → Start Battle
         → popup Battle Complete → về danh sách.
Sau Quick Battle: về interior, nếu panel Event Missions có CHẤM ĐỎ thì vào nhận hết quà (quét 4
tab, bấm mọi nút Claim, đóng popup "Items Obtained!" bằng tap vùng trống). Verify live 2026-07-05
(Special Quests: Claim → Items Obtained → tab hết chấm đỏ).

Chọn stage theo config.event.stage:
    ''    = stage CAO NHẤT (cuộn hết sang phải, tap badge phải nhất).
    'W-N' = tự cuộn + OCR badge (digit-only) tìm đúng stage; không thấy → bỏ qua (KHÔNG chạy nhầm).
Số trận theo config.event.battles: 0 = max theo Vigor (">>"), N>0 = đúng N trận.

Thiếu Vigor: bấm Start Battle bật bảng "Recharge Vigor" đè lên dialog Quick Battle. Xử lý:
đóng X bảng Recharge (RECHARGE_CLOSE_XY) rồi đóng X dialog Quick Battle (QB_CLOSE_XY), hẹn lại
sau 4h — TUYỆT ĐỐI không bấm "Use" (tiêu vật phẩm). Verify live 2026-07-05 (Vigor 22 < 30).

⚠️ Sự kiện theo đợt: EVENT_BANNER + badge dartboard + danh sách stage đều là art của GUNFIRE.
Đổi sang event khác cần re-crop EVENT_BANNER (và có thể cả badge_digits) — xem docs/game-map.md.
Nhánh Battle Complete (đủ Vigor) chưa test live (khảo sát tránh tiêu Vigor); dùng chung khuôn với BountyTrial.
"""
import time

import cv2
import numpy as np

from module.base.button import Button
from module.config import ROOT
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import HOME_CHECK, page_home

# --- Entry: banner sự kiện ở home vào THẲNG event interior ---
EVENT_BANNER = Button('event/EVENT_BANNER.png', area=(40, 200, 205, 285), threshold=0.85)
# Dartboard "Battle Stage" góc dưới-phải interior: vừa để nhận diện interior vừa để click vào.
BATTLE_STAGE_ENTER = Button('event/BATTLE_STAGE_ENTER.png', area=(1030, 470, 1230, 610), threshold=0.85)
# Title "Battle Stage" trên màn danh sách stage.
BATTLE_STAGE_CHECK = Button('event/BATTLE_STAGE_CHECK.png', area=(132, 8, 320, 80), threshold=0.85)
# Nút Quick Battle (xanh lá) ở panel chi tiết stage.
EVENT_QUICK_BATTLE = Button('event/EVENT_QUICK_BATTLE.png', area=(820, 620, 1010, 700), threshold=0.85)
# Dialog Quick Battle: ">>" (max theo Vigor) + Start Battle.
EVENT_QB_MAX = Button('event/EVENT_QB_MAX.png', area=(860, 295, 950, 368), threshold=0.85)
EVENT_QB_START = Button('event/EVENT_QB_START.png', area=(670, 470, 880, 555), threshold=0.85)
# Popup "Battle Complete": nút Confirm giữa-dưới (dùng chung template dialog confirm như BountyTrial).
BATTLE_COMPLETE_CONFIRM = Button('common/DIALOG_CONFIRM.png', area=(500, 540, 780, 640),
                                 name='EVENT_BATTLE_COMPLETE')
# Bảng "Recharge Vigor" bật ĐÈ lên dialog Quick Battle khi bấm Start Battle mà thiếu Vigor
# (khảo sát live 2026-07-05, Vigor 21/240 < 30/trận). Tuyệt đối KHÔNG bấm "Use" (tiêu vật phẩm) —
# chỉ đóng bằng nút X ở header rồi đóng luôn dialog Quick Battle bên dưới.
RECHARGE_VIGOR = Button('event/RECHARGE_VIGOR.png', area=(340, 78, 590, 130), threshold=0.85)

# Toạ độ cố định trong dialog Quick Battle (khảo sát s6, 1280x720).
QB_PLUS_XY = (846, 331)       # nút "+" (tăng 1 trận)
QB_CLOSE_XY = (935, 177)      # nút X đóng dialog Quick Battle
RECHARGE_CLOSE_XY = (933, 102)  # nút X đóng bảng Recharge Vigor (đè trên QB dialog)
EVENT_HOME_XY = (377, 42)     # nút ngôi nhà trên chrome màn Event/Battle Stage

# --- Event Missions (nhận quà sau Quick Battle, khảo sát 2026-07-05) ---
# Panel "Event Missions N/48" ở event interior có CHẤM ĐỎ khi có phần thưởng chưa nhận.
# Vào panel → màn Event Missions: 4 tab trái (mỗi tab có chấm đỏ riêng), quest hoàn thành hiện
# nút "Claim" xanh (cột phải); bấm Claim → popup "Items Obtained!" → tap vùng trống đóng.
EVENT_MISSIONS_CHECK = Button('event/EVENT_MISSIONS_CHECK.png', area=(132, 8, 340, 80), threshold=0.85)
EVENT_MISSION_CLAIM = Button('event/EVENT_MISSION_CLAIM.png', threshold=0.85)  # multi-match thủ công
EVENT_OBTAINED = Button('event/EVENT_OBTAINED.png', area=(400, 180, 900, 270), threshold=0.85)
EVENT_MISSIONS_XY = (130, 645)          # tap panel "Event Missions" ở event interior
MISSION_DOT_ROI = (228, 596, 260, 624)  # ROI chấm đỏ panel (color-detect, ngưỡng thấp)
MISSION_TAB_X = 150
MISSION_TAB_Y = (176, 259, 341, 423)    # 4 tab: Common / Challenge / Adventure / Special
CLAIM_AREA = (1100, 200, 1215, 700)     # cột phải chứa nút Claim (multi-match)
OBTAINED_DISMISS_XY = (640, 160)        # tap vùng trống đóng "Items Obtained!"

# Cuộn ngang danh sách stage. LEFT = vuốt trái tay → lộ stage CAO hơn (bên phải).
SWIPE_Y = 400
SWIPE_LEFT = (1050, SWIPE_Y, 360, SWIPE_Y)   # lộ stage cao hơn
SWIPE_RIGHT = (360, SWIPE_Y, 1050, SWIPE_Y)  # lộ stage thấp hơn
_STAGE_BAND = (250, 510)     # dải y chứa badge/dartboard (so ảnh để biết đã cuộn hết)

# --- OCR badge "1-N" (digit-only): badge đỏ, chữ trắng. So khớp chuỗi digit ('1-12' -> '112'). ---
_DIGITS_DIR = ROOT / 'assets' / 'en' / 'event' / 'badge_digits'
_BADGE_ROI = (12, 66)        # dải x trong badge chứa chữ (bỏ left-cap để né glyph giả)
_GLYPH_SIZE = (14, 20)       # kích thước chuẩn hoá khi so template
_MATCH_MIN = 0.72            # ngưỡng khớp 1 glyph


def _load_digit_templates() -> dict:
    tpl = {}
    for d in '0123456789':
        img = cv2.imread(str(_DIGITS_DIR / f'd{d}.png'), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            tpl[d] = img
    return tpl


def _find_badges(img: np.ndarray) -> list:
    """List badge box (bx,by,bw,bh) đỏ trong danh sách stage, sort theo x tăng dần."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = (cv2.inRange(hsv, (0, 120, 80), (10, 255, 210)) |
         cv2.inRange(hsv, (170, 120, 80), (180, 255, 210)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 25), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w > 90 and 18 < h < 60 and y > 250:
            out.append((x, y, w, h))
    return sorted(out)


def _read_badge(img: np.ndarray, box: tuple, tpl: dict) -> str:
    """Đọc chuỗi digit-only của badge (vd '112' cho stage 1-12). '' nếu không đọc được."""
    bx, by, bw, bh = box
    roi = img[by + 2:by + bh - 2, bx + _BADGE_ROI[0]:bx + _BADGE_ROI[1]]
    if roi.size == 0:
        return ''
    g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, t = cv2.threshold(g, 150, 255, cv2.THRESH_BINARY)
    col = (t > 0).sum(0)
    runs, ins, s0 = [], False, 0
    for x, v in enumerate(col):
        if v > 0 and not ins:
            s0, ins = x, True
        elif v == 0 and ins:
            runs.append((s0, x)); ins = False
    if ins:
        runs.append((s0, len(col)))
    s = ''
    for a, b in runs:
        if b - a < 3:
            continue
        sub = t[:, a:b]
        ys = np.where(sub.sum(1) > 0)[0]
        if len(ys) == 0 or ys[-1] - ys[0] + 1 < 9:   # height>=9 -> digit (rớt dấu '-' + artifact)
            continue
        gg = cv2.resize(sub[ys[0]:ys[-1] + 1], _GLYPH_SIZE, interpolation=cv2.INTER_NEAREST)
        best, bd = 0.0, None
        for d, tp in tpl.items():
            sc = float((gg == tp).mean())
            if sc > best:
                best, bd = sc, d
        if best >= _MATCH_MIN:
            s += bd
    return s


def _stage_digits(stage: str) -> str:
    return ''.join(ch for ch in stage if ch.isdigit())


class EventDaily(UI):
    """Quick Battle sweep ở Battle Stage của sự kiện. Mặc định TẮT (DEFAULT_OFF_TASKS)."""

    def run(self) -> None:
        cfg = self.config.event
        try:
            if not self._enter_battle_stage():
                return
            if not self._select_stage(cfg.stage):
                return
            self._quick_battle(cfg.battles)
            self._claim_missions()   # nhận quà Event Missions nếu panel có chấm đỏ
        finally:
            self._go_home()          # luôn để game ở home cho task kế (Event/Missions ngoài page graph)

    # --- Điều hướng vào Battle Stage ---

    def _enter_battle_stage(self) -> bool:
        self._normalize_home()
        self.device.screenshot()
        if not self.appear(EVENT_BANNER):
            logger.info('EventDaily: không thấy banner sự kiện ở home (event kết thúc? cần '
                        're-crop EVENT_BANNER) — bỏ qua, hẹn lại sau reset')
            self.config.task_delay('EventDaily', server_reset=True)
            return False
        self.device.click(EVENT_BANNER)
        if not self.wait_until_appear(BATTLE_STAGE_ENTER, timeout=12):
            logger.info('EventDaily: không vào được event interior — bỏ qua hôm nay')
            self.config.task_delay('EventDaily', server_reset=True)
            return False
        self.device.click(BATTLE_STAGE_ENTER)
        if not self.wait_until_appear(BATTLE_STAGE_CHECK, timeout=12):
            logger.info('EventDaily: không mở được Battle Stage — bỏ qua hôm nay')
            self.config.task_delay('EventDaily', server_reset=True)
            return False
        logger.info('EventDaily: đã vào Battle Stage')
        return True

    def _normalize_home(self) -> None:
        """Đưa về home; nếu đang kẹt trong màn Event/Battle Stage thì bấm nút nhà (377,42) trước
        (các trang này KHÔNG có trong page graph nên ui_ensure không tự thoát được)."""
        for _ in range(3):
            self.device.screenshot()
            if self.appear(HOME_CHECK):
                return
            if self.appear(BATTLE_STAGE_CHECK) or self.appear(BATTLE_STAGE_ENTER):
                self.device.click_xy(*EVENT_HOME_XY, name='EVENT_GOTO_HOME')
                time.sleep(2)
                continue
            break
        self.ui_ensure(page_home)

    # --- Chọn stage ---

    def _select_stage(self, stage: str) -> bool:
        if stage.strip():
            return self._select_named(stage.strip())
        return self._select_highest()

    def _select_highest(self) -> bool:
        self._scroll_to_end(SWIPE_LEFT)     # cuộn hết sang phải = stage cao nhất
        img = self.device.screenshot()
        badges = [b for b in _find_badges(img) if b[0] + b[2] <= 1225]  # bỏ badge cắt mép phải
        if not badges:
            logger.info('EventDaily: không thấy stage nào trong danh sách — bỏ qua')
            self.config.task_delay('EventDaily', server_reset=True)
            return False
        box = max(badges, key=lambda b: b[0])   # phải nhất = cao nhất
        logger.info('EventDaily: chọn stage cao nhất (phải nhất)')
        self._tap_stage(box)
        return self._wait_stage_detail()

    def _select_named(self, stage: str) -> bool:
        target = _stage_digits(stage)
        if not target:
            logger.info(f'EventDaily: stage cấu hình "{stage}" không hợp lệ — bỏ qua')
            self.config.task_delay('EventDaily', server_reset=True)
            return False
        tpl = _load_digit_templates()
        if len(tpl) < 10:
            raise TaskError('EventDaily: thiếu template digit badge (assets/en/event/badge_digits/)')
        self._scroll_to_end(SWIPE_RIGHT)    # về đầu danh sách (stage thấp nhất)
        end_seen = False
        for _ in range(16):
            img = self.device.screenshot()
            for box in _find_badges(img):
                bx, _, bw, _ = box
                if bx < 108 or bx + bw > 1222:   # badge sát mép -> đọc thiếu, bỏ qua
                    continue
                if _read_badge(img, box, tpl) == target:
                    logger.info(f'EventDaily: tìm thấy stage {stage}')
                    self._tap_stage(box)
                    return self._wait_stage_detail()
            self.device.swipe(*SWIPE_LEFT, name='STAGE_SCROLL')  # lộ stage cao hơn
            time.sleep(0.8)
            after = self.device.screenshot()
            if self._band_same(img, after):     # cuộn không đổi -> tới cuối danh sách
                if end_seen:
                    break
                end_seen = True                  # đọc thêm 1 vòng ở cuối cho chắc
        logger.info(f'EventDaily: không tìm thấy stage {stage} trong danh sách — bỏ qua '
                    '(KHÔNG chạy nhầm stage khác)')
        self.config.task_delay('EventDaily', server_reset=True)
        return False

    def _tap_stage(self, box: tuple) -> None:
        """Tap dartboard NGAY TRÊN badge (badge nằm dưới dartboard, offset y ~ -90)."""
        bx, by, bw, bh = box
        self.device.click_xy(bx + bw // 2, by + bh // 2 - 90, name='STAGE')
        time.sleep(1.0)

    def _wait_stage_detail(self) -> bool:
        if self.wait_until_appear(EVENT_QUICK_BATTLE, timeout=8):
            return True
        logger.info('EventDaily: không mở được panel chi tiết stage — bỏ qua hôm nay')
        self.config.task_delay('EventDaily', server_reset=True)
        return False

    def _scroll_to_end(self, direction: tuple) -> None:
        """Vuốt hết cỡ 1 hướng (đến khi dải stage không đổi nữa)."""
        prev = None
        for _ in range(12):
            self.device.swipe(*direction, name='SCROLL_END')
            time.sleep(0.8)
            img = self.device.screenshot()
            if prev is not None and self._band_same(prev, img):
                return
            prev = img

    @staticmethod
    def _band_same(a: np.ndarray, b: np.ndarray) -> bool:
        y0, y1 = _STAGE_BAND
        return float(cv2.absdiff(a[y0:y1], b[y0:y1]).mean()) < 2.0

    # --- Quick Battle ---

    def _quick_battle(self, battles: int) -> None:
        self.device.click(EVENT_QUICK_BATTLE)
        if not self.wait_until_appear(EVENT_QB_START, timeout=10):
            raise TaskError('EventDaily: dialog Quick Battle không mở')

        if battles <= 0:
            self.device.click(EVENT_QB_MAX)          # max theo Vigor hiện có
        else:
            for _ in range(battles - 1):             # từ mặc định 1 trận, +(N-1)
                self.device.click_xy(*QB_PLUS_XY, name='QB_PLUS')
                time.sleep(0.2)
        time.sleep(0.8)
        self.device.screenshot()
        self.device.click(EVENT_QB_START)

        result = self._wait_battle_result(timeout=15)
        if result != 'complete':
            # 'novigor' = bảng Recharge Vigor bật lên (thiếu Vigor) -> đóng X bảng đó trước.
            # 'timeout' = không rõ, chỉ đóng dialog Quick Battle. Cả hai đều hẹn lại sau 4h.
            if result == 'novigor':
                self.device.click_xy(*RECHARGE_CLOSE_XY, name='RECHARGE_CLOSE')
                time.sleep(1.0)
                self.device.screenshot()
            self.device.click_xy(*QB_CLOSE_XY, name='QB_DIALOG_CLOSE')
            logger.info('EventDaily: không sweep được (thiếu Vigor) — hẹn lại sau 4h')
            self.config.task_delay('EventDaily', minutes=240)
            return

        self.device.click(BATTLE_COMPLETE_CONFIRM)
        end = time.time() + 30
        while time.time() < end:
            time.sleep(1.5)
            self.device.screenshot()
            if self.handle_popup():
                continue
            if self.appear(BATTLE_STAGE_CHECK) or self.appear(EVENT_QUICK_BATTLE):
                logger.info('EventDaily: sweep xong, hẹn lại sau reset')
                self.config.task_delay('EventDaily', server_reset=True)
                return
            self.device.click_xy(640, 150, name='REWARD_DISMISS')

        raise TaskError('EventDaily: không về được Battle Stage sau khi sweep')

    def _wait_battle_result(self, timeout: int) -> str:
        """Sau khi bấm Start Battle, chờ 1 trong 3 kết cục:
        'complete' = popup Battle Complete; 'novigor' = bảng Recharge Vigor (thiếu Vigor);
        'timeout' = không thấy gì trong `timeout` giây."""
        end = time.time() + timeout
        while time.time() < end:
            self.device.screenshot()
            if self.appear(RECHARGE_VIGOR):
                return 'novigor'
            if self.appear(BATTLE_COMPLETE_CONFIRM):
                return 'complete'
            time.sleep(1.0)
        return 'timeout'

    # --- Nhận quà Event Missions ---

    def _claim_missions(self) -> None:
        """Về event interior; nếu panel Event Missions có CHẤM ĐỎ thì vào nhận hết Claim ở 4 tab."""
        if not self._back_to_interior():
            return
        self.device.screenshot()
        if not self._mission_red_dot():
            logger.info('EventDaily: Event Missions không có chấm đỏ — bỏ qua nhận quà')
            return
        self.device.click_xy(*EVENT_MISSIONS_XY, name='EVENT_MISSIONS')
        if not self.wait_until_appear(EVENT_MISSIONS_CHECK, timeout=10):
            logger.info('EventDaily: không mở được Event Missions — bỏ qua nhận quà')
            return
        total = 0
        for ty in MISSION_TAB_Y:
            self.device.click_xy(MISSION_TAB_X, ty, name='MISSION_TAB')
            time.sleep(1.0)
            total += self._claim_tab()
        logger.info(f'EventDaily: đã nhận {total} phần thưởng Event Missions')

    def _back_to_interior(self) -> bool:
        """Từ màn Battle Stage (sau Quick Battle) về event interior (dartboard xuất hiện)."""
        self.device.screenshot()
        if self.appear(BATTLE_STAGE_ENTER):
            return True
        self.device.click_xy(55, 42, name='EVENT_BACK')
        if self.wait_until_appear(BATTLE_STAGE_ENTER, timeout=8):
            return True
        logger.info('EventDaily: không về được event interior để nhận quà — bỏ qua')
        return False

    def _mission_red_dot(self) -> bool:
        x1, y1, x2, y2 = MISSION_DOT_ROI
        hsv = cv2.cvtColor(self.device.image[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
        m = (cv2.inRange(hsv, (150, 110, 110), (180, 255, 255)) |
             cv2.inRange(hsv, (0, 110, 110), (10, 255, 255)))
        return int(m.sum()) // 255 >= 6

    def _claim_tab(self) -> int:
        """Bấm hết nút Claim trong tab hiện tại (có cuộn), đóng popup sau mỗi lần. Trả số claim."""
        claimed = 0
        for _ in range(20):     # chặn vòng lặp vô hạn
            self.device.screenshot()
            pt = self._find_claim()
            if pt is not None:
                self.device.click_xy(*pt, name='MISSION_CLAIM')
                self._dismiss_obtained()
                claimed += 1
                continue
            # hết Claim trên khung -> thử cuộn danh sách xuống 1 nhịp tìm tiếp
            before = self.device.image
            self.device.swipe(830, 560, 830, 300, name='MISSION_LIST_DOWN')
            time.sleep(0.8)
            after = self.device.screenshot()
            if float(cv2.absdiff(before[200:690, 440:1090],
                                 after[200:690, 440:1090]).mean()) < 2.0:
                break           # cuộn không đổi -> hết danh sách
        return claimed

    def _find_claim(self):
        """Multi-match nút Claim trong CLAIM_AREA, trả điểm click của nút TRÊN CÙNG (hoặc None)."""
        x1, y1, x2, y2 = CLAIM_AREA
        crop = self.device.image[y1:y2, x1:x2]
        tpl = EVENT_MISSION_CLAIM.template
        res = cv2.matchTemplate(crop, tpl, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(res >= EVENT_MISSION_CLAIM.threshold)
        if len(ys) == 0:
            return None
        th, tw = tpl.shape[:2]
        i = int(np.argmin(ys))     # y nhỏ nhất = nút trên cùng
        return (x1 + int(xs[i]) + tw // 2, y1 + int(ys[i]) + th // 2)

    def _dismiss_obtained(self) -> None:
        """Đóng popup 'Items Obtained!' bằng tap vùng trống tới khi popup biến mất."""
        if not self.wait_until_appear(EVENT_OBTAINED, timeout=3):
            return   # claim không mở popup (hiếm) -> thôi
        for _ in range(5):
            self.device.click_xy(*OBTAINED_DISMISS_XY, name='OBTAINED_DISMISS')
            time.sleep(0.8)
            self.device.screenshot()
            if not self.appear(EVENT_OBTAINED):
                return

    def _go_home(self) -> None:
        """Về home qua nút nhà (377,42) — mọi màn Event/Battle Stage/Missions đều có nút này."""
        for _ in range(3):
            self.device.screenshot()
            if self.appear(HOME_CHECK):
                return
            self.device.click_xy(*EVENT_HOME_XY, name='EVENT_GOTO_HOME')
            time.sleep(2)
