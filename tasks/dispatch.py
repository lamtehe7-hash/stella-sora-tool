import time

from module.base.button import Button
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import COMMISSION_CHECK, page_commission

# Trạng thái xám = chưa có đội nào về (khảo sát 2026-07-04, Limit 4/4 đang chạy)
COMMISSION_CLAIM_ALL_DONE = Button('commission/COMMISSION_CLAIM_ALL_DONE.png',
                                   area=(1070, 598, 1255, 672))
# Popup "Commission Complete!" (bảng tổng kết khi Claim All đội về) — MODAL, phải đóng bằng nút
# Back / Dispatch Again; tap vùng trống KHÔNG đóng được (bug 2026-07-05: tap (640,150) 10 lần ->
# GameTooManyClick, popup kẹt che màn làm mọi task sau fail "không nhận diện page").
COMMISSION_COMPLETE = Button('commission/COMMISSION_COMPLETE.png', area=(430, 82, 852, 128))
COMMISSION_BACK = Button('commission/COMMISSION_BACK.png', area=(392, 543, 606, 600))
# Nút teal "Dispatch Again" (phái lại cả loạt vừa hoàn tất) nằm bên PHẢI nút Back trên bảng Complete,
# đối xứng gương của Back (tâm ~499) qua tâm popup (x=640) -> tâm ~(781, 571). Bấm bằng toạ độ vì
# popup Complete chỉ hiện khi có đội về (~20h/lượt) nên chưa crop/verify template được lúc code.
# An toàn: click lệch trên bảng Complete chỉ trúng vùng trống (không nút nguy hiểm) -> popup không
# đóng -> tự fallback Back + phái tay (xem _claim_all). CHƯA verify live — chạy ở lần hoàn tất kế.
COMMISSION_DISPATCH_AGAIN_XY = (781, 571)

# --- Phái lại commission (Dispatch Again), khảo sát 2026-07-05 ---
# Flow phái 1 commission: chọn commission ở list trái -> Quick Select (tự chọn đội hợp Requirement +
# Bonus) -> chọn 20h (reward tối đa, gấp ~5x so 4h) -> Accept Commission -> animation "Commission
# Start!" -> panel chuyển sang nút Recall (= đã phái). Commission đã phái ở list hiện "In Commission:
# HH:MM:SS", vẫn giữ nguyên vị trí. Limit N/4 = số slot đang chạy.
COMMISSION_QUICK_SELECT = Button('commission/COMMISSION_QUICK_SELECT.png', area=(858, 520, 1035, 575))
COMMISSION_ACCEPT = Button('commission/COMMISSION_ACCEPT.png', area=(1040, 520, 1235, 575))
COMMISSION_RECALL = Button('commission/COMMISSION_RECALL.png', area=(1040, 520, 1235, 575))
COMMISSION_LIST_X = 275                                   # tâm x cột list commission
COMMISSION_LIST_Y = (115, 186, 258, 329, 400, 471, 542, 613)  # y 8 dòng commission
COMMISSION_20H_XY = (1128, 491)                          # radio 20h (reward tối đa)


class Dispatch(UI):
    """Thu hoạch commission khi đội về + phái lại. Ưu tiên bấm "Dispatch Again" trên bảng
    Commission Complete (phái lại nhanh cả loạt vừa xong); nếu không phái lại được thì fallback
    phái tay: điền slot trống tới 4/4, mỗi slot Quick Select + chọn 20h (reward cao nhất)."""

    def run(self) -> None:
        self.ui_ensure(page_commission)

        self.device.screenshot()
        # 1. Claim nếu có đội về (Claim All sáng) + thử Dispatch Again trên bảng Complete
        if self.appear(COMMISSION_CLAIM_ALL_DONE):
            logger.info('Dispatch: chưa có đội về (Claim All xám)')
        else:
            self._claim_all()

        # 2. Phái tay điền nốt slot còn trống với 20h (fallback + phòng slot trống sẵn từ trước).
        #    Nếu Dispatch Again đã phái đủ 4/4 thì bước này thành no-op.
        n = self._redispatch()
        logger.info(f'Dispatch: phái tay thêm {n} commission (20h)')
        self.config.task_delay('Dispatch', minutes=240)

    def _claim_all(self) -> None:
        """Claim All -> trên bảng "Commission Complete!" ưu tiên bấm DISPATCH AGAIN (phái lại cả loạt
        vừa xong); nếu popup không đóng (Dispatch Again không khả dụng) thì đóng bằng Back. Slot còn
        trống sẽ do _redispatch() điền tay với 20h."""
        self.device.click_xy(1160, 633, name='COMMISSION_CLAIM_ALL')
        tried_again = False
        end = time.time() + 60
        while time.time() < end:
            time.sleep(1.5)
            self.device.screenshot()
            if self.handle_popup():
                continue
            if self.appear(COMMISSION_COMPLETE):
                if not tried_again:
                    # Ưu tiên: phái lại cả loạt bằng "Dispatch Again"
                    self.device.click_xy(*COMMISSION_DISPATCH_AGAIN_XY, name='DISPATCH_AGAIN')
                    tried_again = True
                    time.sleep(3)   # animation "Commission Start!" khi phái lại
                    continue
                # Đã bấm Dispatch Again mà popup vẫn còn -> không phái lại được -> đóng Back
                self.device.click(COMMISSION_BACK)
                logger.info('Dispatch: Dispatch Again không khả dụng — đóng Back, sẽ phái tay')
                time.sleep(1.5)
                continue
            if self.appear(COMMISSION_CHECK):
                logger.info('Dispatch: đã Claim All' + (' + Dispatch Again' if tried_again else ''))
                return
            # Popup thưởng khác (không phải modal Commission Complete) -> tap vùng trống đóng
            self.device.click_xy(640, 150, name='REWARD_DISMISS')
        logger.warning('Dispatch: Claim All/Dispatch Again không hoàn tất sau 60s — vẫn thử phái tay')

    def _redispatch(self) -> int:
        """Điền các slot commission trống tới đủ 4: mỗi commission available -> Quick Select (tự chọn
        đội hợp Requirement+Bonus) -> 20h (reward tối đa) -> Accept. Đếm cả slot đã phái sẵn để dừng ở
        4/4. Trả số commission MỚI phái. Dừng sớm nếu Quick Select không đủ Trekker."""
        in_commission = 0   # tổng slot đang chạy (đã phái sẵn + mới phái) — cap ở 4
        new = 0
        for i, y in enumerate(COMMISSION_LIST_Y):
            if in_commission >= 4:
                break
            self.device.click_xy(COMMISSION_LIST_X, y, name=f'COMM_SEL_{i % 3}')
            time.sleep(1.2)
            self.device.screenshot()
            if self.appear(COMMISSION_RECALL):
                in_commission += 1     # commission này đã đang phái -> tính vào limit, bỏ qua
                continue
            if not self.appear(COMMISSION_QUICK_SELECT):
                continue               # không phải panel phái được (list ngắn hơn / màn lạ)
            self.device.click(COMMISSION_QUICK_SELECT)   # tự chọn đội
            time.sleep(1.3)
            self.device.click_xy(*COMMISSION_20H_XY, name='COMM_20H')  # 20h = reward tối đa
            time.sleep(0.8)
            self.device.screenshot()
            if not self.appear(COMMISSION_ACCEPT):
                continue               # Quick Select không điền đủ đội (hết Trekker) -> bỏ qua
            self.device.click(COMMISSION_ACCEPT)
            time.sleep(3)              # animation "Commission Start!"
            self.device.screenshot()
            if self.appear(COMMISSION_RECALL):
                in_commission += 1
                new += 1
                logger.info(f'Dispatch: phái commission slot {in_commission}/4 (20h)')
            else:
                logger.warning('Dispatch: Accept không thành (thiếu Trekker?) — bỏ qua')
        return new
