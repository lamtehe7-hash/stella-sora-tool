import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import SHOP_CHECK, page_shop

# Hộp quà daily miễn phí góc dưới-trái; hiện pill "Claimed" khi đã nhận.
# Chưa có template trạng thái CHƯA-nhận (khảo sát 2026-07-04 đều lúc đã nhận)
# → logic: không thấy Claimed = còn quà, bấm hộp rồi xác minh Claimed xuất hiện.
SHOP_GIFT_CLAIMED = Button('shop/SHOP_GIFT_CLAIMED.png', area=(10, 625, 134, 708))


class Shop(UI):
    """Nhận quà daily miễn phí trong shop (hộp quà 72,645). KHÔNG đụng nút mua tiền thật."""

    def run(self) -> None:
        self.ui_ensure(page_shop)

        self.device.screenshot()
        if self.appear(SHOP_GIFT_CLAIMED):
            logger.info('Shop: quà daily đã nhận rồi')
            self.config.task_delay('Shop', server_reset=True)
            return

        self.device.click_xy(72, 645, name='SHOP_GIFT')
        end = time.time() + 60
        while time.time() < end:
            time.sleep(1.5)
            self.device.screenshot()
            if self.appear(SHOP_GIFT_CLAIMED):
                logger.info('Shop: đã nhận quà daily')
                self.config.task_delay('Shop', server_reset=True)
                return
            if self.handle_popup():
                continue
            if not self.appear(SHOP_CHECK):
                # Popup thưởng/danh sách quà chưa có asset — tap vùng trống để đóng
                self.device.click_xy(640, 150, name='REWARD_DISMISS')

        raise TaskError('Shop: bấm hộp quà nhưng không thấy trạng thái Claimed sau 60s')
