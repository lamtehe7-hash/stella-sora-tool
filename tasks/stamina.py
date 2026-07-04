import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import BASIC_TRIAL_CHECK, page_basic_trial

# Trang Basic Trial (khảo sát 2026-07-04): Quick Battle = sweep thật, tốn 20 Vigor/battle
# (Difficulty 6), thưởng nhận ngay không combat. Nút chỉ sáng khi difficulty đã clear.
TRIAL_QUICK_BATTLE = Button('bounty/TRIAL_QUICK_BATTLE.png', area=(780, 607, 1020, 698))
QB_START_BATTLE = Button('bounty/QB_START_BATTLE.png', area=(663, 470, 878, 552))
QB_MAX = Button('bounty/QB_MAX.png', area=(858, 283, 952, 378))
# Popup "Battle Complete": nút Confirm giữa-dưới, cùng template với dialog confirm chung
BATTLE_COMPLETE_CONFIRM = Button('common/DIALOG_CONFIRM.png', area=(500, 540, 780, 640),
                                 name='BATTLE_COMPLETE_CONFIRM')


class Stamina(UI):
    """Tiêu Vigor: Basic Trial (Bounty) -> Quick Battle -> max số battle -> Start Battle.

    Game giữ nguyên difficulty đã chọn lần trước (mặc định cao nhất đã mở) — v1 không tự chọn.
    """

    def run(self) -> None:
        self.ui_ensure(page_basic_trial)

        self.device.screenshot()
        if not self.appear(TRIAL_QUICK_BATTLE):
            logger.info('Stamina: Quick Battle không khả dụng (difficulty chưa clear?) — bỏ qua hôm nay')
            self.config.task_delay('Stamina', server_reset=True)
            return

        self.device.click(TRIAL_QUICK_BATTLE)
        if not self.wait_until_appear(QB_START_BATTLE, timeout=10):
            raise TaskError('Stamina: dialog Quick Battle không mở')

        # ">>" đẩy số battle lên tối đa theo Vigor hiện có
        self.device.click(QB_MAX)
        time.sleep(1)
        self.device.screenshot()
        self.device.click(QB_START_BATTLE)

        if not self.wait_until_appear(BATTLE_COMPLETE_CONFIRM, timeout=15):
            # Nhiều khả năng không đủ Vigor cho 1 battle — đóng dialog (X), chờ hồi
            self.device.click_xy(935, 177, name='QB_DIALOG_CLOSE')
            logger.info('Stamina: không sweep được (thiếu Vigor?) — hẹn lại sau 4h')
            self.config.task_delay('Stamina', minutes=240)
            return

        self.device.click(BATTLE_COMPLETE_CONFIRM)
        end = time.time() + 30
        while time.time() < end:
            time.sleep(1.5)
            self.device.screenshot()
            if self.handle_popup():
                continue
            if self.appear(BASIC_TRIAL_CHECK):
                logger.info('Stamina: sweep xong, trang ổn định')
                self.config.task_delay('Stamina', server_reset=True)
                return
            self.device.click_xy(640, 150, name='REWARD_DISMISS')

        raise TaskError('Stamina: không về được trang Basic Trial sau khi sweep')
