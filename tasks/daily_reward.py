import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import MISSIONS_CHECK, page_missions

MISSIONS_CLAIM_ALL = Button('missions/MISSIONS_CLAIM_ALL.png', area=(1030, 556, 1215, 630))
# Trạng thái xám = không có gì để nhận (điểm match chéo cyan/xám chỉ 0.24/0.03 — không nhầm được)
MISSIONS_CLAIM_ALL_DONE = Button('missions/MISSIONS_CLAIM_ALL_DONE.png', area=(1030, 556, 1215, 630))
# Template ở trạng thái tab ĐANG chọn — không match nghĩa là đang ở tab khác
DAILY_AFFAIRS_TAB = Button('missions/DAILY_AFFAIRS_TAB.png', area=(470, 630, 650, 700))


class DailyReward(UI):
    """Nhận thưởng mission daily: missions -> tab Daily Affairs -> Claim All -> mốc điểm hoạt động."""

    def run(self) -> None:
        self.ui_ensure(page_missions)

        self.device.screenshot()
        if not self.appear(DAILY_AFFAIRS_TAB):
            self.device.click_xy(541, 664, name='DAILY_AFFAIRS_TAB')
            if not self.wait_until_appear(DAILY_AFFAIRS_TAB, timeout=10):
                raise TaskError('DailyReward: không mở được tab Daily Affairs')

        clicked = False
        end = time.time() + 60
        while time.time() < end:
            self.device.screenshot()
            if self.handle_popup():
                continue
            if not self.appear(MISSIONS_CHECK):
                # Popup thưởng chưa có asset closer — tap vùng trống để đóng
                self.device.click_xy(640, 150, name='REWARD_DISMISS')
                time.sleep(1)
                continue
            if not clicked:
                if self.appear_then_click(MISSIONS_CLAIM_ALL):
                    clicked = True
                elif self.appear(MISSIONS_CLAIM_ALL_DONE):
                    logger.info('DailyReward: Claim All đang xám — không có mission nào để nhận')
                    self._claim_activity_points()
                    self.config.task_delay('DailyReward', server_reset=True)
                    return
                time.sleep(1)
                continue
            # Đã bấm Claim All — chờ 2s cho popup (nếu có) kịp hiện rồi xác nhận trang ổn định
            time.sleep(2)
            self.device.screenshot()
            if not self.appear(MISSIONS_CHECK):
                continue
            self._claim_activity_points()
            logger.info('DailyReward: đã Claim All + mốc điểm, trang ổn định')
            self.config.task_delay('DailyReward', server_reset=True)
            return

        raise TaskError('DailyReward: không hoàn tất Claim All sau 60s')

    def _claim_activity_points(self) -> None:
        """Bấm nút Claim mốc điểm hoạt động (góc trên-phải). Nút xám khi đã nhận — bấm vô hại.
        Chưa có asset trạng thái claimable (khảo sát lúc đã nhận hết) — dùng tọa độ cố định."""
        self.device.click_xy(1144, 64, name='ACTIVITY_CLAIM')
        time.sleep(1.5)
        for _ in range(5):
            self.device.screenshot()
            if self.appear(MISSIONS_CHECK):
                return
            self.device.click_xy(640, 150, name='REWARD_DISMISS')
            time.sleep(1)
