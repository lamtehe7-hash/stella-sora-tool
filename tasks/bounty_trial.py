import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import (BASIC_TRIAL_CHECK, BOUNTY_GO_BASIC, page_basic_trial,
                             page_bounty)

# Trang Trial (khảo sát 2026-07-04): Quick Battle = sweep thật, tốn Vigor/battle, thưởng nhận
# ngay không combat. Nút chỉ sáng khi difficulty đã clear. Quick Battle/Start Battle/">>" cùng vị
# trí ở mọi Trial nên dùng chung template.
TRIAL_QUICK_BATTLE = Button('bounty/TRIAL_QUICK_BATTLE.png', area=(780, 607, 1020, 698))
QB_START_BATTLE = Button('bounty/QB_START_BATTLE.png', area=(663, 470, 878, 552))
QB_MAX = Button('bounty/QB_MAX.png', area=(858, 283, 952, 378))
# Popup "Battle Complete": nút Confirm giữa-dưới, cùng template với dialog confirm chung
BATTLE_COMPLETE_CONFIRM = Button('common/DIALOG_CONFIRM.png', area=(500, 540, 780, 640),
                                 name='BATTLE_COMPLETE_CONFIRM')

# --- Chọn Trial trong Bounty hub ("map") ---
# Hub: cột trái = 4 card Trial, phải = preview + nút Go (BOUNTY_GO_BASIC dùng chung cho mọi Trial).
# Toạ độ card ước lượng theo tỉ lệ mép trái từ ảnh khảo sát — CHƯA verify live cho 3 Trial ngoài Basic.
TRIAL_CARD_XY = {
    'basic':  (448, 216),
    'tierup': (448, 356),
    'skill':  (448, 495),
    'emblem': (448, 632),
}
TRIAL_LABELS = {'basic': 'Basic Trial', 'tierup': 'Tier-up Trial',
                'skill': 'Skill Trial', 'emblem': 'Emblem Trial'}
# Pills Difficulty 1..6: cột trái trang Trial, x cố định, cách đều (ước lượng theo tỉ lệ mép trái).
DIFFICULTY_X = 150
DIFFICULTY_Y0 = 130
DIFFICULTY_DY = 75


class BountyTrial(UI):
    """Tiêu Vigor bằng Trial Quick Battle (Bounty). Đổi tên từ task 'Stamina'.

    Cho phép chọn loại Trial (config.bounty.trial) và difficulty (config.bounty.difficulty).
    Mặc định (basic + difficulty 0) = đúng hành vi cũ: Basic Trial, giữ difficulty game nhớ, sweep max.
    """

    def run(self) -> None:
        cfg = self.config.bounty
        if not self._enter_trial(cfg.trial):
            return  # đã log + hẹn lại bên trong
        if cfg.difficulty:
            self._select_difficulty(cfg.difficulty)
        self._sweep()

    def _enter_trial(self, trial: str) -> bool:
        """Đưa về đúng trang Trial cần chạy. True nếu Quick Battle sẵn sàng."""
        if trial == 'basic':
            # Đường đã chứng minh: page graph tới thẳng Basic Trial.
            self.ui_ensure(page_basic_trial)
            self.device.screenshot()
            if self.appear(TRIAL_QUICK_BATTLE):
                return True
            logger.info('BountyTrial: Quick Battle không khả dụng (difficulty chưa clear?) — bỏ qua hôm nay')
            self.config.task_delay('BountyTrial', server_reset=True)
            return False

        # Trial khác: vào Bounty hub -> chọn card Trial -> Go -> chờ Quick Battle xuất hiện.
        self.ui_ensure(page_bounty)
        self.device.click_xy(*TRIAL_CARD_XY[trial], name=f'TRIAL_{trial.upper()}')
        time.sleep(1.0)
        self.device.click(BOUNTY_GO_BASIC)  # nút Go dùng chung cho mọi Trial
        if self.wait_until_appear(TRIAL_QUICK_BATTLE, timeout=10):
            logger.info(f'BountyTrial: đã vào {TRIAL_LABELS[trial]}')
            return True
        logger.info(f'BountyTrial: không mở được {TRIAL_LABELS[trial]} (difficulty chưa clear?) — bỏ qua hôm nay')
        self.config.task_delay('BountyTrial', server_reset=True)
        return False

    def _select_difficulty(self, diff: int) -> None:
        """Chọn Difficulty 1..6 (tap pill cột trái). Game giữ lựa chọn tới khi đổi."""
        diff = max(1, min(6, diff))
        y = DIFFICULTY_Y0 + (diff - 1) * DIFFICULTY_DY
        self.device.click_xy(DIFFICULTY_X, y, name=f'DIFFICULTY_{diff}')
        logger.info(f'BountyTrial: chọn Difficulty {diff}')
        time.sleep(0.8)
        self.device.screenshot()

    def _sweep(self) -> None:
        """Quick Battle -> ">>" max battle -> Start Battle -> đóng popup -> về trang Trial."""
        self.device.screenshot()
        if not self.appear(TRIAL_QUICK_BATTLE):
            logger.info('BountyTrial: Quick Battle không khả dụng — bỏ qua hôm nay')
            self.config.task_delay('BountyTrial', server_reset=True)
            return

        self.device.click(TRIAL_QUICK_BATTLE)
        if not self.wait_until_appear(QB_START_BATTLE, timeout=10):
            raise TaskError('BountyTrial: dialog Quick Battle không mở')

        # ">>" đẩy số battle lên tối đa theo Vigor hiện có (auto-clear tối đa)
        self.device.click(QB_MAX)
        time.sleep(1)
        self.device.screenshot()
        self.device.click(QB_START_BATTLE)

        if not self.wait_until_appear(BATTLE_COMPLETE_CONFIRM, timeout=15):
            # Nhiều khả năng không đủ Vigor cho 1 battle — đóng dialog (X), hẹn lại sau 4h
            self.device.click_xy(935, 177, name='QB_DIALOG_CLOSE')
            logger.info('BountyTrial: không sweep được (thiếu Vigor?) — hẹn lại sau 4h')
            self.config.task_delay('BountyTrial', minutes=240)
            return

        self.device.click(BATTLE_COMPLETE_CONFIRM)
        end = time.time() + 30
        while time.time() < end:
            time.sleep(1.5)
            self.device.screenshot()
            if self.handle_popup():
                continue
            if self.appear(BASIC_TRIAL_CHECK) or self.appear(TRIAL_QUICK_BATTLE):
                logger.info('BountyTrial: sweep xong, trang ổn định')
                self.config.task_delay('BountyTrial', server_reset=True)
                return
            self.device.click_xy(640, 150, name='REWARD_DISMISS')

        raise TaskError('BountyTrial: không về được trang Trial sau khi sweep')
