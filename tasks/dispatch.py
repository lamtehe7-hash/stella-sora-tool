import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import COMMISSION_CHECK, page_commission

# Trạng thái xám = chưa có đội nào về (khảo sát 2026-07-04, Limit 4/4 đang chạy)
COMMISSION_CLAIM_ALL_DONE = Button('commission/COMMISSION_CLAIM_ALL_DONE.png',
                                   area=(1070, 598, 1255, 672))


class Dispatch(UI):
    """Thu hoạch commission khi đội về. Flow TÁI PHÁI chưa khảo sát được (chỉ xem được
    lúc có đội về + slot trống) — v1 chỉ Claim All rồi hẹn lại; tái phái làm tay/đợt sau."""

    def run(self) -> None:
        self.ui_ensure(page_commission)

        self.device.screenshot()
        if self.appear(COMMISSION_CLAIM_ALL_DONE):
            logger.info('Dispatch: chưa có đội về (Claim All xám) — hẹn lại sau 4h')
            self.config.task_delay('Dispatch', minutes=240)
            return

        # Claim All đang sáng — chưa có template trạng thái sáng, bấm theo tọa độ khảo sát
        self.device.click_xy(1160, 633, name='COMMISSION_CLAIM_ALL')
        end = time.time() + 60
        while time.time() < end:
            time.sleep(1.5)
            self.device.screenshot()
            if self.handle_popup():
                continue
            if not self.appear(COMMISSION_CHECK):
                # Popup thưởng — tap vùng trống để đóng
                self.device.click_xy(640, 150, name='REWARD_DISMISS')
                continue
            if self.appear(COMMISSION_CLAIM_ALL_DONE):
                logger.warning('Dispatch: đã Claim All. TODO: tái phái 4 đội — khảo sát flow '
                               'khi có slot trống rồi bổ sung.')
                self.config.task_delay('Dispatch', minutes=240)
                return
            time.sleep(1)

        raise TaskError('Dispatch: Claim All không hoàn tất sau 60s')
