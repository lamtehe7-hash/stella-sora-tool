from module.logger import logger
from module.ui.page import UI
from module.ui.pages import page_home


class Cleanup(UI):
    """Đưa game về màn hình chính cuối phiên; tùy config thì đóng hẳn game."""

    def run(self) -> None:
        self.ui_ensure(page_home)
        if self.config.close_game_on_cleanup:
            self.device.app_stop()
            logger.info('Cleanup: đã đóng game')
        else:
            logger.info('Cleanup: game để nguyên ở màn hình chính')
        self.config.task_delay('Cleanup', server_reset=True)
