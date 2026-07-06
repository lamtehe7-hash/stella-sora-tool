"""Task EventFirstClear — tự đánh (Deploy + Auto-Battle) các stage Battle Stage sự kiện còn
sao XÁM để lấy quà First Clear.

Khác EventDaily (Quick Battle sweep các stage ĐÃ master để tiêu Vigor), task này thực sự CHƠI
những stage CHƯA clear (sao xám/bạc) qua đường Go → Deploy → Auto-Battle → Victory. Khảo sát live
2026-07-07 (event "A Sandstorm of GUNFIRE", chapter 2). Flow:
    home → banner sự kiện → Battle Stage
    → với mỗi độ khó được bật (Normal/Hard/Challenge):
        chọn tab độ khó (bỏ qua nếu khoá) → cuộn từ đầu danh sách
        → tìm stage sao XÁM (unlocked, chưa master) → tap dartboard → Go (30 Vigor)
        → màn Records → Deploy → Auto-Battle (bật nếu chưa) → Victory → tap continue → về list
        → re-scan (clear 1 stage thường mở khoá stage kế) → hết stage xám thì sang độ khó khác.

Nhận biết (khảo sát live, đo màu 1280×720):
- **Tab độ khó** = 3 pill góc dưới-trái: Normal(117,668)/Hard(313,668)/#3(490,668). Pill ĐANG CHỌN
  sáng lên (mean-brightness ~177), chưa chọn ~71, KHOÁ ~48. Chuyển bằng tap; verify bằng độ sáng.
- **Sao stage** trên ribbon đỏ "N-N": VÀNG (gold px ≥120) = đã first-clear → bỏ; XÁM/bạc
  (silver px ≥400, gold≈0) = CHƯA clear → chơi; padlock 🔒 (silver ~280) = khoá clear-gate → bỏ.
  Ribbon khoá TIME-GATE ("Unlocks in Xh") bị greyed (S<120) nên bộ tìm ribbon-đỏ tự loại.

⚠️ Mặc định TẮT (event theo đợt + tốn Vigor). Đổi event cần re-crop EVENT_BANNER (xem EventDaily).
Auto-Battle: game NHỚ trạng thái (thường ON sẵn) → chỉ bấm khi trận không xong sau `auto_battle_wait`
giây (lúc đó chắc chắn auto đang OFF, bấm để bật — không sợ vô tình tắt trận đang chạy).
"""
import time

import cv2
import numpy as np

from module.base.button import Button
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import HOME_CHECK, page_home
# Tái dùng asset + hằng số điều hướng của EventDaily (cùng màn Battle Stage, không đụng logic sweep)
from tasks.event_daily import (BATTLE_STAGE_CHECK, BATTLE_STAGE_ENTER, EVENT_BANNER,
                               EVENT_HOME_XY, RECHARGE_CLOSE_XY, RECHARGE_VIGOR,
                               SWIPE_LEFT, SWIPE_RIGHT, _STAGE_BAND)

# --- Asset riêng luồng First-Clear (khảo sát + crop live 2026-07-07) ---
# Nút "Go" đỏ trong panel chi tiết stage (đánh thật, 30 Vigor/trận).
EFC_GO = Button('event/EFC_GO.png', area=(975, 624, 1120, 702))
# Title "Records" của màn chọn đội (trước Deploy) — mốc nhận biết đã vào màn Deploy.
EFC_RECORDS_CHECK = Button('event/EFC_RECORDS_CHECK.png', area=(125, 4, 320, 80))
# Nút "Deploy" teal góc dưới-phải màn Records (vào trận). Tâm thật ~(1162,682).
EFC_DEPLOY = Button('event/EFC_DEPLOY.png', area=(1072, 642, 1252, 720))
# Banner "VICTORY!" (chung mọi trận, không phụ thuộc event) — mốc trận thắng.
EFC_VICTORY = Button('event/EFC_VICTORY.png', area=(28, 176, 342, 270))

# Toạ độ cố định (khảo sát 1280×720).
DIFFICULTY_XY = {'normal': (117, 668), 'hard': (313, 668), 'challenge': (490, 668)}
AUTO_BATTLE_XY = (1218, 118)       # nút Auto-Battle góc phải-trên trong trận
VICTORY_CONTINUE_XY = (640, 640)   # "Select anywhere to continue" (vùng trơ, né stage/pill)
# Nhận biết Auto-Battle ĐANG BẬT: viền xanh phát sáng quanh nút (đo live: ON ~727 px bluish, nền ~0
# — rotation-invariant vì viền là vòng tròn). Detect thay vì hẹn giờ mù → không bao giờ vô tình TẮT
# một trận DÀI đang chạy (trận Hard/Challenge có thể ~50s).
AUTO_ROI = (1178, 82, 1258, 158)
AUTO_ON_MIN = 300

# Ngưỡng phân loại sao (đo live: gold 537-547 / gray-silver 593-770 / padlock-silver 264-288).
STAR_GOLD_MIN = 120                # ≥ = có sao vàng => đã first-clear => bỏ
STAR_SILVER_MIN = 400              # ≥ (và gold≈0) = 3 sao xám => chơi; padlock ~280 rớt dưới ngưỡng
# Độ sáng pill độ khó: chọn ~177 / chưa chọn ~71 / khoá ~48.
PILL_SELECTED = 120
PILL_LOCKED = 55


def _find_stage_ribbons(img: np.ndarray) -> list:
    """List ribbon đỏ "N-N" của các stage ĐÃ MỞ KHOÁ (ribbon đỏ bão hoà; khoá time-gate bị greyed
    S<120 nên tự rớt). Trả (x, y_ribbon, w, h_ribbon) sort theo x. Ribbon dính phần đỏ dartboard
    (contour cao) → lấy dải đáy 34px."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = (cv2.inRange(hsv, (0, 120, 80), (10, 255, 210)) |
         cv2.inRange(hsv, (170, 120, 80), (180, 255, 210)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 25), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w < 90 or w > 230 or y < 250:
            continue
        ry, rh = (y + h - 34, 34) if h > 50 else (y, h)
        if rh < 18:
            continue
        out.append((x, ry, w, rh))
    return sorted(out)


def _star_colors(img: np.ndarray, box: tuple) -> tuple:
    """(gold_px, silver_px) trong nửa PHẢI ribbon (vùng chứa sao/padlock)."""
    x, y, w, h = box
    star = img[y:y + h, x + int(w * 0.40):x + w]
    hs = cv2.cvtColor(star, cv2.COLOR_BGR2HSV)
    gold = int((cv2.inRange(hs, (18, 90, 140), (38, 255, 255)) > 0).sum())
    silver = int((cv2.inRange(hs, (0, 0, 150), (180, 70, 255)) > 0).sum())
    return gold, silver


def _pill_bright(img: np.ndarray, x: int) -> float:
    """Độ sáng trung bình pill độ khó tại cột x (dải y 650-688)."""
    return float(img[650:688, x - 55:x + 55].mean())


def _auto_battle_on(img: np.ndarray) -> bool:
    """Auto-Battle đang BẬT? Đếm pixel xanh-sáng (viền phát sáng) quanh nút góc phải-trên."""
    x1, y1, x2, y2 = AUTO_ROI
    roi = img[y1:y2, x1:x2]
    b, g, r = roi[:, :, 0].astype(int), roi[:, :, 1].astype(int), roi[:, :, 2].astype(int)
    return int(((b > 150) & (b > r + 15) & (g > 120)).sum()) >= AUTO_ON_MIN


class EventFirstClear(UI):
    """Tự first-clear stage Battle Stage sự kiện (Deploy + Auto-Battle). Mặc định TẮT."""

    def run(self) -> None:
        cfg = self.config.event_first_clear
        wanted = [d for d in ('normal', 'hard', 'challenge') if getattr(cfg, d)]
        if not wanted:
            logger.info('EventFirstClear: không bật độ khó nào — bỏ qua')
            self.config.task_delay('EventFirstClear', server_reset=True)
            return
        self._out_of_vigor = False
        try:
            if not self._enter_battle_stage():
                return
            total = 0
            for diff in wanted:
                if self._out_of_vigor:
                    break
                total += self._clear_difficulty(diff, cfg)
            logger.info(f'EventFirstClear: đã first-clear {total} stage')
            if not self._out_of_vigor:
                self.config.task_delay('EventFirstClear', server_reset=True)
        finally:
            self._go_home()

    # --- Điều hướng vào Battle Stage (khuôn giống EventDaily, delay riêng) ---

    def _enter_battle_stage(self) -> bool:
        self._normalize_home()
        self.device.screenshot()
        if not self.appear(EVENT_BANNER):
            logger.info('EventFirstClear: không thấy banner sự kiện ở home (event kết thúc? cần '
                        're-crop EVENT_BANNER) — bỏ qua, hẹn lại sau reset')
            self.config.task_delay('EventFirstClear', server_reset=True)
            return False
        self.device.click(EVENT_BANNER)
        if not self.wait_until_appear(BATTLE_STAGE_ENTER, timeout=12):
            logger.info('EventFirstClear: không vào được event interior — bỏ qua hôm nay')
            self.config.task_delay('EventFirstClear', server_reset=True)
            return False
        self.device.click(BATTLE_STAGE_ENTER)
        if not self.wait_until_appear(BATTLE_STAGE_CHECK, timeout=12):
            logger.info('EventFirstClear: không mở được Battle Stage — bỏ qua hôm nay')
            self.config.task_delay('EventFirstClear', server_reset=True)
            return False
        logger.info('EventFirstClear: đã vào Battle Stage')
        return True

    def _normalize_home(self) -> None:
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

    def _go_home(self) -> None:
        for _ in range(3):
            self.device.screenshot()
            if self.appear(HOME_CHECK):
                return
            self.device.click_xy(*EVENT_HOME_XY, name='EVENT_GOTO_HOME')
            time.sleep(2)

    # --- Chọn độ khó ---

    def _select_difficulty(self, diff: str) -> bool:
        """Chuyển sang tab độ khó `diff`. False nếu khoá (pill tối) hoặc không chọn được."""
        x, y = DIFFICULTY_XY[diff]
        self.device.screenshot()
        b = _pill_bright(self.device.image, x)
        if b >= PILL_SELECTED:
            return True                      # đã đang ở độ khó này
        if b < PILL_LOCKED:
            logger.info(f'EventFirstClear: độ khó {diff} đang KHOÁ — bỏ qua')
            return False
        self.device.click_xy(x, y, name=f'DIFF_{diff.upper()}')
        time.sleep(1.5)
        self.device.screenshot()
        if _pill_bright(self.device.image, x) >= PILL_SELECTED:
            logger.info(f'EventFirstClear: đã chọn độ khó {diff}')
            return True
        logger.info(f'EventFirstClear: không chọn được độ khó {diff} — bỏ qua')
        return False

    # --- Quét + chơi các stage xám của 1 độ khó ---

    def _clear_difficulty(self, diff: str, cfg) -> int:
        if not self._select_difficulty(diff):
            return 0
        self._scroll_to_end(SWIPE_RIGHT)     # về đầu danh sách (stage thấp nhất)
        played = 0
        last_x = None
        while played < cfg.max_stages:
            self.device.screenshot()
            box = self._leftmost_gray(self.device.image)
            if box is not None:
                if last_x is not None and abs(box[0] - last_x) < 45:
                    logger.info(f'EventFirstClear[{diff}]: stage vẫn xám sau khi đánh '
                                '(thua/chưa đạt?) — dừng độ khó này để khỏi lặp')
                    break
                status = self._play_stage(box, cfg)
                if status == 'ok':
                    played += 1
                    last_x = box[0]
                    continue
                if status == 'novigor':
                    self._out_of_vigor = True
                break                        # skip/lỗi: dừng độ khó (tránh lặp)
            # Không còn stage xám trên khung → cuộn lộ stage cao hơn; không đổi = hết list
            before = self.device.image
            self.device.swipe(*SWIPE_LEFT, name='EFC_SCROLL')
            time.sleep(0.8)
            after = self.device.screenshot()
            if self._band_same(before, after):
                break
        if played:
            logger.info(f'EventFirstClear[{diff}]: first-clear {played} stage')
        return played

    def _leftmost_gray(self, img: np.ndarray):
        """Ribbon stage xám (unlocked, chưa master) trái nhất, hoặc None."""
        for box in _find_stage_ribbons(img):
            gold, silver = _star_colors(img, box)
            if gold >= STAR_GOLD_MIN:
                continue                     # đã first-clear
            if silver >= STAR_SILVER_MIN:
                return box                   # 3 sao xám → chơi
        return None

    def _play_stage(self, box: tuple, cfg) -> str:
        """Chơi 1 stage: dartboard → Go → Deploy → Auto-Battle → Victory. Trả 'ok'|'novigor'|'skip'."""
        x, y, w, h = box
        self.device.click_xy(x + w // 2, y + h // 2 - 88, name='EFC_STAGE')  # dartboard trên ribbon
        if not self.wait_until_appear(EFC_GO, timeout=8):
            logger.info('EventFirstClear: không mở được panel chi tiết stage — bỏ qua')
            return 'skip'
        self.device.click(EFC_GO)
        res = self._wait_go_result(timeout=12)
        if res == 'novigor':
            logger.info('EventFirstClear: hết Vigor (bảng Recharge) — dừng, hẹn lại sau 4h')
            self.device.click_xy(*RECHARGE_CLOSE_XY, name='RECHARGE_CLOSE')
            time.sleep(1)
            self.config.task_delay('EventFirstClear', minutes=240)
            return 'novigor'
        if res != 'deploy':
            logger.info('EventFirstClear: không vào được màn Deploy — bỏ qua stage')
            return 'skip'
        self.device.click(EFC_DEPLOY)
        return self._run_battle(cfg)

    def _wait_go_result(self, timeout: int) -> str:
        """Sau Go: 'deploy' (màn Records), 'novigor' (bảng Recharge Vigor), 'timeout'."""
        end = time.time() + timeout
        while time.time() < end:
            self.device.screenshot()
            if self.appear(RECHARGE_VIGOR):
                return 'novigor'
            if self.appear(EFC_RECORDS_CHECK):
                return 'deploy'
            time.sleep(0.6)
        return 'timeout'

    def _run_battle(self, cfg) -> str:
        """Chờ trận xong. Nếu Auto-Battle đang OFF (không thấy viền xanh, 2 frame liên tiếp) thì bật
        lên — CHỈ bấm 1 lần/trận: auto một khi bật giữ suốt trận, nên không bấm khi đã ON (không sợ
        vô tình tắt) và không bấm lần 2 (né viền tắt thoáng qua lúc skill/kết trận). Thắng → dismiss
        Victory. Trả 'ok' hoặc 'skip'."""
        end = time.time() + cfg.run_timeout
        time.sleep(3)                    # chờ trận load xong mới xét Auto-Battle
        tapped = False
        off_streak = 0
        while time.time() < end:
            self.device.screenshot()
            if self.appear(EFC_VICTORY):
                return self._dismiss_victory()
            if _auto_battle_on(self.device.image):
                off_streak = 0
            elif not tapped:
                off_streak += 1
                if off_streak >= 2:      # 2 frame liên tiếp OFF (debounce) → bật 1 lần duy nhất
                    self.device.click_xy(*AUTO_BATTLE_XY, name='AUTO_BATTLE')
                    logger.info('EventFirstClear: Auto-Battle đang OFF — bật lên')
                    tapped = True
                    time.sleep(1.5)
            time.sleep(1.2)
        logger.warning('EventFirstClear: trận quá thời gian — bỏ qua')
        return 'skip'

    def _dismiss_victory(self) -> str:
        """Tap vùng trơ đóng màn Victory (+ popup thưởng) tới khi về Battle Stage."""
        end = time.time() + 25
        while time.time() < end:
            self.device.click_xy(*VICTORY_CONTINUE_XY, name='VICTORY_CONTINUE')
            time.sleep(1.5)
            self.device.screenshot()
            if self.appear(BATTLE_STAGE_CHECK):
                return 'ok'
            if self.handle_popup():
                continue
        logger.warning('EventFirstClear: không về được Battle Stage sau Victory')
        return 'ok'   # vẫn coi như đã clear (quà first-clear đã nhận)

    # --- Cuộn ngang danh sách (khuôn giống EventDaily) ---

    def _scroll_to_end(self, direction: tuple) -> None:
        prev = None
        for _ in range(12):
            self.device.swipe(*direction, name='EFC_SCROLL_END')
            time.sleep(0.8)
            img = self.device.screenshot()
            if prev is not None and self._band_same(prev, img):
                return
            prev = img

    @staticmethod
    def _band_same(a: np.ndarray, b: np.ndarray) -> bool:
        y0, y1 = _STAGE_BAND
        return float(cv2.absdiff(a[y0:y1], b[y0:y1]).mean()) < 2.0
