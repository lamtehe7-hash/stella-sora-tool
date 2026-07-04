import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import MAIL_CHECK, page_mail

MAIL_CLAIM_ALL = Button('mail/MAIL_CLAIM_ALL.png', area=(1075, 626, 1245, 698))


class Mail(UI):
    """Nhận toàn bộ đính kèm thư: mail -> Claim All -> đóng popup thưởng -> hẹn reset kế."""

    def run(self) -> None:
        self.ui_ensure(page_mail)

        clicked = False
        end = time.time() + 60
        while time.time() < end:
            self.device.screenshot()
            if self.handle_popup():
                continue
            if not self.appear(MAIL_CHECK):
                # Popup thưởng chưa có asset closer — tap vùng trống để đóng
                self.device.click_xy(640, 150, name='REWARD_DISMISS')
                time.sleep(1)
                continue
            if not clicked:
                if self.appear_then_click(MAIL_CLAIM_ALL):
                    clicked = True
                time.sleep(1)
                continue
            # Đã bấm Claim All — chờ 2s cho popup (nếu có) kịp hiện rồi xác nhận trang ổn định
            time.sleep(2)
            self.device.screenshot()
            if not self.appear(MAIL_CHECK):
                continue
            logger.info('Mail: đã Claim All, trang ổn định')
            self.config.task_delay('Mail', server_reset=True)
            return

        raise TaskError('Mail: không hoàn tất Claim All sau 60s')
