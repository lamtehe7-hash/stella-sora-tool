import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import HOME_CHECK, page_home

# Dải chữ "Select anywhere to start" — nền title xoay art nên threshold thấp hơn mặc định
LOGIN_TAP_START = Button('login/LOGIN_TAP_START.png', area=(500, 565, 790, 615),
                         threshold=0.7)


class Login(UI):
    """Mở game (nếu chưa chạy) và đưa về màn hình chính, vừa chờ vừa đóng popup."""

    def run(self) -> None:
        cold_start = not self.device.app_is_running()
        if cold_start:
            self.device.app_start()
            time.sleep(10)  # chờ load ban đầu, khỏi chụp màn hình vô ích

        end = time.time() + 120
        last_blind_tap = 0.0
        while time.time() < end:
            self.device.screenshot()
            if self.appear(HOME_CHECK):
                logger.info('Đã vào màn hình chính')
                self.config.task_delay('Login', server_reset=True)
                return
            if self.handle_popup():
                continue
            # Màn hình title "tap to start": game bị đá về đây khi mất mạng giữa chừng,
            # nên phải nhận diện bằng template chứ không chỉ dựa vào cold_start
            at_title = self.appear(LOGIN_TAP_START)
            if (cold_start or at_title) and time.time() - last_blind_tap > 5:
                self.device.click_xy(640, 620, name='LOGIN_BLIND_TAP')
                last_blind_tap = time.time()
            time.sleep(1)

        raise TaskError('Login: không về được màn hình chính sau 120s')
