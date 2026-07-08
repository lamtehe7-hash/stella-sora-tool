import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import MISSIONS_CHECK, page_home, page_missions
from tasks.daily_reward import MISSIONS_CLAIM_ALL, MISSIONS_CLAIM_ALL_DONE

# Template ở trạng thái tab ĐANG chọn (chữ trắng trên pill navy; unselected = chữ tối nền sáng →
# đo 0.423, không nhầm). Nút Claim All teal/xám TÁI DÙNG của DailyReward — cùng nút cùng vị trí
# trên cả 2 tab (đo teal 1.000 trên tab Weekly 2026-07-08).
WEEKLY_AFFAIRS_TAB = Button('missions/WEEKLY_AFFAIRS_TAB.png', area=(685, 632, 830, 696))


class WeeklyReward(UI):
    """Nhận thưởng mission TUẦN: missions -> tab Weekly Affairs -> Claim All (nếu sáng) ->
    mốc điểm tuần (rương 300/600/...) -> về Home.

    Chạy kiểm mỗi ngày sau reset (no-op nhanh khi Claim All xám); tuần refresh thì tự có quà mới.
    """

    def run(self) -> None:
        self.ui_ensure(page_missions)

        # Game NHỚ tab mở lần trước — đảm bảo đang ở Weekly Affairs
        self.device.screenshot()
        if not self.appear(WEEKLY_AFFAIRS_TAB):
            self.device.click_xy(745, 664, name='WEEKLY_AFFAIRS_TAB')
            if not self.wait_until_appear(WEEKLY_AFFAIRS_TAB, timeout=10):
                raise TaskError('WeeklyReward: không mở được tab Weekly Affairs')

        clicked = False
        end = time.time() + 60
        while time.time() < end:
            self.device.screenshot()
            if self.handle_popup():
                continue
            if not self.appear(MISSIONS_CHECK):
                # Popup thưởng — tap vùng trống phía trên để đóng (cùng chỗ DailyReward đã verify)
                self.device.click_xy(640, 150, name='REWARD_DISMISS')
                time.sleep(1)
                continue
            if not clicked:
                if self.appear_then_click(MISSIONS_CLAIM_ALL):
                    clicked = True
                elif self.appear(MISSIONS_CLAIM_ALL_DONE):
                    logger.info('WeeklyReward: Claim All đang xám — không có mission tuần để nhận')
                    self._finish()
                    return
                time.sleep(1)
                continue
            # Đã bấm Claim All — chờ popup (nếu có) kịp hiện rồi xác nhận trang ổn định
            time.sleep(2)
            self.device.screenshot()
            if not self.appear(MISSIONS_CHECK):
                continue
            logger.info('WeeklyReward: đã Claim All mission tuần')
            self._finish()
            return

        raise TaskError('WeeklyReward: không hoàn tất Claim All sau 60s')

    def _finish(self) -> None:
        self._claim_week_points()
        self.ui_ensure(page_home)  # yêu cầu người dùng: xong thì về Home
        self.config.task_delay('WeeklyReward', server_reset=True)

    def _claim_week_points(self) -> None:
        """Bấm Claim mốc điểm tuần (rương 300/600/... góc trên-phải). Nút xám khi chưa đủ điểm/
        đã nhận — bấm vô hại (cùng pattern _claim_activity_points của DailyReward)."""
        self.device.click_xy(1144, 64, name='WEEK_POINTS_CLAIM')
        time.sleep(1.5)
        for _ in range(5):
            self.device.screenshot()
            if self.appear(MISSIONS_CHECK):
                return
            self.device.click_xy(640, 150, name='REWARD_DISMISS')
            time.sleep(1)
