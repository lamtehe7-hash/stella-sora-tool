import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import PURCHASE_CHECK, page_purchase

# Nút "Daily Gift" (góc trái-dưới màn Purchase) ở trạng thái CÒN QUÀ — label chữ "Daily Gift".
# Khi đã nhận, label đổi thành "Claimed" (nền xanh) nên template này KHÔNG match. Do đó:
#   match  = còn quà (có chấm đỏ) -> claim
#   no-match = đã nhận hôm nay    -> bỏ qua
# Bấm Daily Gift claim TRỰC TIẾP (không cần nút Claim phụ) -> popup "Items Obtained!".
DAILY_GIFT = Button('purchase/DAILY_GIFT.png', area=(10, 632, 140, 698))

# ⚠️ Màn Purchase: tap nhầm vào CARD bên phải sẽ mở hộp thoại MUA (tốn Journey Ticket). Vì vậy khi
# đóng popup "Items Obtained!" (Select anywhere to continue) CHỈ tap vùng TRÁI an toàn — (200,400)
# nằm trên tranh nhân vật, dưới các tab, không trúng card/nút nào.
SAFE_DISMISS = (200, 400)


class PurchaseGift(UI):
    """Nhận Daily Gift miễn phí ở màn Purchase: purchase -> Daily Gift (nếu còn) -> đóng popup.

    Chỉ nhận khi còn quà (label 'Daily Gift'); đã nhận thì label 'Claimed' -> DAILY_GIFT không match
    nên tự bỏ qua. Quà free, không rủi ro; xong thì hẹn tới reset daily kế.
    """

    def run(self) -> None:
        self.ui_ensure(page_purchase)

        self.device.screenshot()
        if not self.appear(DAILY_GIFT):
            logger.info('PurchaseGift: Daily Gift đã nhận (label "Claimed") — bỏ qua')
            self.config.task_delay('PurchaseGift', server_reset=True)
            return

        clicked = False
        end = time.time() + 40
        while time.time() < end:
            self.device.screenshot()
            if self.handle_popup():
                continue
            if not self.appear(PURCHASE_CHECK):
                # Popup "Items Obtained!" che màn — CHỈ tap vùng trái an toàn (tránh mở hộp mua)
                self.device.click_xy(*SAFE_DISMISS, name='REWARD_DISMISS')
                time.sleep(1)
                continue
            if not clicked:
                if self.appear_then_click(DAILY_GIFT):
                    clicked = True
                time.sleep(1.5)
                continue
            # Đã bấm & đã về màn Purchase — nút chuyển sang "Claimed" (DAILY_GIFT hết match) = xong
            if not self.appear(DAILY_GIFT):
                logger.info('PurchaseGift: đã nhận Daily Gift')
                self.config.task_delay('PurchaseGift', server_reset=True)
                return
            time.sleep(1)  # popup chưa xong / chưa kịp đổi trạng thái — chờ thêm

        raise TaskError('PurchaseGift: không hoàn tất nhận Daily Gift sau 40s')
