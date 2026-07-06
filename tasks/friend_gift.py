import time

from module.base.button import Button
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import page_friend

# Rail trái — tab "Friend List" ở trạng thái CHƯA chọn (nền trắng). Khi đã ở Friend List tab đổi
# sang banner xanh nên template này KHÔNG match (đo: profile 1.000 / list 0.185) — dùng để bấm
# CHUYỂN sang list, còn "đang ở list chưa" thì nhận biết bằng GIFT_ALL.
FRIEND_LIST_TAB = Button('friend/FRIEND_LIST_TAB.png', area=(22, 185, 178, 252))
# Nút "Acquire All" (nhận stamina bạn gửi). Crop né chấm đỏ động ở góc phải-trên.
ACQUIRE_ALL = Button('friend/ACQUIRE_ALL.png', area=(885, 630, 1050, 698))
# Nút "Gift All" (gửi stamina cho mọi bạn) — pill teal, luôn có ở màn Friend List -> dùng làm mốc
# nhận biết "đang ở Friend List".
GIFT_ALL = Button('friend/GIFT_ALL.png', area=(1070, 625, 1255, 703))


class FriendGift(UI):
    """Trao đổi stamina với bạn: friend -> Friend List -> Acquire All + Gift All -> hẹn reset kế.

    Acquire All = nhận stamina bạn gửi; Gift All = gửi stamina cho tất cả bạn. Cả hai đều là thao
    tác daily MIỄN PHÍ (không tốn Vigor của mình, còn cộng điểm thân mật) nên bật sẵn như Mail.
    Giới hạn 30 lượt/ngày (badge "Today N/30") — hết lượt bấm vẫn vô hại.
    """

    def run(self) -> None:
        self.ui_ensure(page_friend)

        # Sang tab Friend List nếu chưa (ui_ensure có thể dừng ở Profile/Add Friend). Mốc: GIFT_ALL.
        self.device.screenshot()
        if not self.appear(GIFT_ALL):
            self.appear_then_click(FRIEND_LIST_TAB, interval=2)
            if not self.wait_until_appear(GIFT_ALL, timeout=10):
                raise TaskError('FriendGift: không mở được Friend List')

        acquired = gifted = False
        end = time.time() + 60
        while time.time() < end:
            self.device.screenshot()
            if self.handle_popup():
                continue
            if not self.appear(GIFT_ALL):
                # Popup thưởng (nhận/gửi stamina) che nút — tap vùng trống để đóng
                self.device.click_xy(640, 150, name='REWARD_DISMISS')
                time.sleep(1)
                continue
            if not acquired:
                # Bấm Acquire All khi còn (có chấm đỏ). Hết lượt/không có gì -> click vô hại, bỏ qua.
                if not self.appear_then_click(ACQUIRE_ALL):
                    logger.info('FriendGift: không có gì để Acquire (hết lượt hoặc bạn chưa gửi)')
                acquired = True
                time.sleep(1.5)
                continue
            if not gifted:
                self.appear_then_click(GIFT_ALL)
                gifted = True
                time.sleep(1.5)
                continue
            # Đã bấm cả hai — chờ popup cuối kịp hiện rồi xác nhận màn ổn định
            time.sleep(1.5)
            self.device.screenshot()
            if not self.appear(GIFT_ALL):
                continue
            logger.info('FriendGift: đã Acquire All + Gift All, màn ổn định')
            self.config.task_delay('FriendGift', server_reset=True)
            return

        raise TaskError('FriendGift: không hoàn tất Acquire/Gift sau 60s')
