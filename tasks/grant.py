"""Task Grant — nhận quà "Startup Grant" (Company Goal + Grant Milestone) khi có chấm đỏ.

Khảo sát live 2026-07-05. Flow:
    home → icon Grant (225,150, cạnh Shop) → màn "Startup Grant" (GRANT_CHECK).
    Màn mặc định mở ở tab "Grant Milestone". Hai tab có chấm đỏ RIÊNG ở thanh tab:
      - chấm đỏ ở NỬA TRÁI thanh tab  = tab "Grant Milestone" có quà.
      - chấm đỏ ở NỬA PHẢI thanh tab  = tab "Company Goal" có quà.
    Xử lý:
      1. Nếu Company Goal có chấm đỏ → chuyển sang → Claim All (quét cả Today's + Weekly Target).
      2. Nếu Grant Milestone có chấm đỏ → chuyển sang → Claim All.
    Claim Company Goal TRƯỚC: cộng progress → có thể lên Grant Tier → mở khoá quà Milestone
    (nên re-check chấm đỏ Milestone sau khi claim Company Goal).

Overlay sau Claim All:
    - "Items Obtained!" (GRANT_OBTAINED, ~ EVENT_OBTAINED của game) — đóng bằng tap vùng trống.
    - Banner "Grant Tier Up" (khi lên tier, chỉ ở Company Goal) — cùng tap vùng trống.
    Dismiss loop tap điểm trơ (640,230) tới khi hết popup obtained VÀ panel phải đứng yên
    (loại vùng album art bên trái vì nó tự đổi đĩa). Verify live: Milestone claim → Items
    Obtained → dismiss → chấm đỏ + Claim All biến mất.

Mặc định BẬT (quà miễn phí, không rủi ro). Màn Grant ngoài page graph → điều hướng mệnh lệnh,
luôn về home qua nút nhà (369,42) ở finally.
"""
import time

import cv2

from module.base.button import Button
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import HOME_CHECK, page_home

GRANT_CHECK = Button('grant/GRANT_CHECK.png', area=(116, 20, 326, 64), threshold=0.85)
# Nút "Claim All" (chỉ hiện khi tab hiện tại có quà chưa nhận).
GRANT_CLAIM_ALL = Button('grant/GRANT_CLAIM_ALL.png', area=(845, 600, 1010, 655), threshold=0.85)
# Popup "Items Obtained!" (đặc trưng chữ, khớp cả EVENT_OBTAINED ~0.96).
GRANT_OBTAINED = Button('grant/GRANT_OBTAINED.png', area=(378, 196, 872, 262), threshold=0.85)

GRANT_ICON_XY = (225, 150)        # icon Grant ở home
MILESTONE_TAB_XY = (680, 131)     # tab "Grant Milestone"
COMPANY_TAB_XY = (1053, 131)      # tab "Company Goal"
TODAY_TAB_XY = (613, 285)         # sub-tab "Today's Target" (trong Company Goal)
WEEKLY_TAB_XY = (795, 285)        # sub-tab "Weekly Target"
CLAIM_ALL_XY = (927, 627)
GRANT_DISMISS_XY = (640, 230)     # tap vùng trống đóng overlay (đã test TRƠ trên nền)
GRANT_HOME_XY = (369, 42)         # nút nhà trên chrome màn Grant

_TABDOT_BAND = (96, 124)          # dải y chứa chấm đỏ ở thanh tab
_TABDOT_SPLIT = 1000              # cx < split → Grant Milestone, >= → Company Goal
# Vùng so khung để biết overlay đã tắt (BỎ album art bên trái vì nó tự đổi đĩa).
_RIGHT_PANEL = (90, 660, 460, 1250)


class Grant(UI):
    """Nhận quà Startup Grant khi có chấm đỏ. Mặc định BẬT."""

    def run(self) -> None:
        try:
            if self._enter():
                self.device.screenshot()
                _, company = self._tab_dots()
                if company:
                    logger.info('Grant: Company Goal có chấm đỏ → nhận')
                    self._claim_company()
                else:
                    logger.info('Grant: Company Goal không có chấm đỏ — bỏ qua')

                self.device.screenshot()
                milestone, _ = self._tab_dots()   # re-check: claim Company Goal có thể lên tier
                if milestone:
                    logger.info('Grant: Grant Milestone có chấm đỏ → nhận')
                    self._claim_milestone()
                else:
                    logger.info('Grant: Grant Milestone không có chấm đỏ — bỏ qua')
        finally:
            self._go_home()
        # Lỗi giữa chừng không tới được đây → scheduler tự phạt 30-60' rồi thử lại.
        self.config.task_delay('Grant', server_reset=True)

    # --- Điều hướng ---

    def _enter(self) -> bool:
        self._normalize_home()
        self.device.screenshot()
        if not self.appear(HOME_CHECK):
            logger.info('Grant: không đưa được về home — bỏ qua')
            return False
        self.device.click_xy(*GRANT_ICON_XY, name='GRANT_ICON')
        if not self.wait_until_appear(GRANT_CHECK, timeout=12):
            logger.info('Grant: không mở được màn Startup Grant — bỏ qua')
            return False
        logger.info('Grant: đã vào Startup Grant')
        return True

    def _normalize_home(self) -> None:
        """Về home; nếu đang kẹt trong màn Grant thì bấm nút nhà (369,42) trước
        (màn Grant KHÔNG có trong page graph)."""
        for _ in range(3):
            self.device.screenshot()
            if self.appear(HOME_CHECK):
                return
            if self.appear(GRANT_CHECK):
                self.device.click_xy(*GRANT_HOME_XY, name='GRANT_GOTO_HOME')
                time.sleep(2)
                continue
            break
        self.ui_ensure(page_home)

    # --- Chấm đỏ tab ---

    def _tab_dots(self) -> tuple:
        """(milestone_dot, company_dot): mỗi tab có chấm đỏ ở thanh tab không.
        Chấm đỏ Milestone luôn ở ~x854 (nửa trái), Company ở ~x1180 (nửa phải)."""
        hsv = cv2.cvtColor(self.device.image, cv2.COLOR_BGR2HSV)
        m = (cv2.inRange(hsv, (0, 120, 120), (10, 255, 255)) |
             cv2.inRange(hsv, (170, 120, 120), (180, 255, 255)))
        y0, y1 = _TABDOT_BAND
        band = m[y0:y1, 500:1250]
        cnts, _ = cv2.findContours(band, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        milestone = company = False
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            if w >= 6 and h >= 6:
                cx = 500 + x + w // 2
                if cx < _TABDOT_SPLIT:
                    milestone = True
                else:
                    company = True
        return milestone, company

    # --- Nhận quà ---

    def _claim_company(self) -> None:
        self.device.click_xy(*COMPANY_TAB_XY, name='COMPANY_TAB')
        time.sleep(1.2)
        for xy, nm in ((TODAY_TAB_XY, 'TODAY_TARGET'), (WEEKLY_TAB_XY, 'WEEKLY_TARGET')):
            self.device.click_xy(*xy, name=nm)
            time.sleep(1.0)
            self._claim_all_here()

    def _claim_milestone(self) -> None:
        self.device.click_xy(*MILESTONE_TAB_XY, name='MILESTONE_TAB')
        time.sleep(1.2)
        self._claim_all_here()

    def _claim_all_here(self) -> None:
        """Nếu tab/sub-tab hiện tại có nút Claim All → bấm + dismiss overlay. Lặp phòng nhiều đợt."""
        for _ in range(3):
            self.device.screenshot()
            if not self.appear(GRANT_CLAIM_ALL):
                return
            self.device.click_xy(*CLAIM_ALL_XY, name='CLAIM_ALL')
            self._dismiss_overlays()

    def _dismiss_overlays(self) -> None:
        """Tap vùng trống tới khi hết popup 'Items Obtained!' và panel phải ĐỨNG YÊN
        (xử lý cả banner 'Grant Tier Up' — cùng đóng bằng tap)."""
        y0, y1, x0, x1 = _RIGHT_PANEL
        prev = None
        for _ in range(12):
            self.device.screenshot()
            if self.appear(GRANT_OBTAINED):
                self.device.click_xy(*GRANT_DISMISS_XY, name='GRANT_DISMISS')
                time.sleep(0.9)
                prev = None
                continue
            cur = self.device.image[y0:y1, x0:x1]
            if prev is not None and float(cv2.absdiff(cur, prev).mean()) < 2.0:
                return                       # panel phải tĩnh → đã về nền sạch
            prev = cur
            self.device.click_xy(*GRANT_DISMISS_XY, name='GRANT_DISMISS')
            time.sleep(0.9)

    def _go_home(self) -> None:
        for _ in range(3):
            self.device.screenshot()
            if self.appear(HOME_CHECK):
                return
            self.device.click_xy(*GRANT_HOME_XY, name='GRANT_GOTO_HOME')
            time.sleep(2)
