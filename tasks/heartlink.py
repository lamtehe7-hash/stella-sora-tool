"""Task Heartlink — hẹn hò tăng Affinity qua UI "điện thoại" Heartlink (server EN).

Khảo sát live 2026-07-08 (walk-through tay + demo người dùng). Task con INVITE:
    Home → icon Heartlink → phone mở tab Chat → tab INVITE → lưới NV.
    Mỗi lượt hẹn (auto grid-order trái→phải, trên→dưới):
      1. Chọn NV (tap portrait). NV đã hẹn hôm nay có ✓ xanh + panel phải nút "Invited Today" (xám)
         → HL_INVITE_BTN (teal "Invite") KHÔNG match → bỏ qua, sang NV kế.
      2. NV khả dụng → tap Invite → màn "Select Date Location" (3 ô, KHÁC nhau theo NV) → tap ô ĐẦU.
      3. Travel (xe chạy) → màn hẹn hò → tap Skip ▶| (góc phải-trên) tua nhanh hết text.
      4. Cuối buổi: Send Gift (x2 Affinity, tốn 1 quà) HOẶC Leave (theo config.send_gift).
         Gift: mở lưới quà → chọn ô ĐẦU → Send Gift → reaction → "Gifts Received!" (nhận đáp lễ).
      5. Dismiss các overlay (reaction / Gifts Received / "<NV> Affinity UP") → về màn Invite (+1/5).
    Dừng khi đạt invite_count, hết NV khả dụng (đã hẹn/greyed), hoặc chạm 5/5 (game chặn → greyed).

Task con MAIL (Delivery Service): gửi quà tăng Affinity, giới hạn 10 quà/ngày (global). Xem _mail_loop.
Verify live 2026-07-08 (Chitose 1350→3050 Affinity, 2/10 quà). Fix dialog "Start Invitation" cùng ngày.

Heartlink là UI phone fullscreen KHÔNG có nút nhà — thoát bằng nút nguồn HEARTLINK_EXIT (góc phải-trên).
Mặc định TẮT (task mới + tốn quà khi send_gift). Xem docs/game-map.md ▸ heartlink.
"""
import time

import cv2

from module.base.button import Button
from module.config import ROOT
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import (HEARTLINK_EXIT, HOME_CHECK, page_heartlink,
                             page_home)

# --- Templates nhận diện màn (crop 2026-07-08) ---
# Tiêu đề "Invite" ở đầu phone (xác nhận đang ở tab Invite).
HL_INVITE_TITLE = Button('heartlink/HL_INVITE_TITLE.png', area=(84, 136, 182, 176))
# Nút teal "Invite" trên panel phải (ACTIVE = NV còn hẹn được).
HL_INVITE_BTN = Button('heartlink/HL_INVITE_BTN.png', area=(834, 622, 956, 674))
# Nút "Invited Today" (xám) khi NV đã hẹn hôm nay — poll cùng HL_INVITE_BTN để biết CHẮC trạng thái
# (panel phải render có lag; chờ 1 trong 2 hiện rõ tránh skip nhầm NV còn hẹn được).
HL_INVITED_TODAY = Button('heartlink/HL_INVITED_TODAY.png', area=(826, 610, 964, 684))
# Tiêu đề "Select Date Location".
HL_SELECT_LOCATION = Button('heartlink/HL_SELECT_LOCATION.png', area=(756, 136, 1070, 176))
# Dialog "Start Invitation" (Cancel/Confirm) hiện SAU khi bấm Invite — RESET lại mỗi ngày ("Do not show
# again today" hết hiệu lực sau reset). KHÔNG xử lý = kẹt chờ Location → bị hiểu nhầm CAP ngày (bug 2026-07-08).
HL_START_INVITATION = Button('heartlink/HL_START_INVITATION.png', area=(340, 130, 580, 200))
# Lựa chọn "Send Gift ▸" cuối buổi hẹn (nhận biết đã tới cuối date).
HL_SEND_GIFT = Button('heartlink/HL_SEND_GIFT.png', area=(758, 496, 1210, 546))
# Nút "Never mind" ở màn chọn quà (nhận biết đang ở lưới quà).
HL_GIFT_NEVERMIND = Button('heartlink/HL_GIFT_NEVERMIND.png', area=(794, 610, 948, 662))
# Tiêu đề "Delivery Service" — nhận biết đang ở tab MAIL (task con Mail: gửi quà tăng affinity).
HL_MAIL_TITLE = Button('heartlink/HL_MAIL_TITLE.png', area=(737, 65, 1028, 138))

# --- Toạ độ tap (khảo sát live 2026-07-08) ---
HL_TAB_INVITE_XY = (288, 653)     # tab Invite (đáy phone)
HL_GRID_COLS = (147, 272, 399)    # tâm x 3 cột portrait
HL_GRID_ROWS = (232, 388, 543)    # tâm y 3 hàng hiển thị (chưa cuộn)
HL_INVITE_BTN_XY = (894, 647)     # nút Invite (bắt đầu hẹn)
HL_INVITE_CONFIRM_XY = (780, 508) # nút Confirm trên dialog "Start Invitation"
HL_LOC_FIRST_XY = (1131, 263)     # nút Select ô địa điểm ĐẦU
HL_SKIP_XY = (1189, 78)           # Skip ▶| tua nhanh buổi hẹn
HL_SEND_GIFT_XY = (983, 519)      # lựa chọn "Send Gift" cuối date
HL_LEAVE_XY = (983, 592)          # lựa chọn "Leave" cuối date
HL_GIFT_FIRST_XY = (798, 300)     # ô quà đầu (top-left) trong lưới quà
HL_GIFT_SEND_XY = (1097, 635)     # nút "Send Gift" chốt gửi quà
HL_DISMISS_XY = (640, 150)        # tap vùng trống dismiss overlay (Gifts Received/Affinity UP)

# --- Task con MAIL (Delivery Service): gửi quà tăng affinity, giới hạn 10 quà/ngày (GLOBAL) ---
HL_TAB_MAIL_XY = (397, 653)       # tab Mail (đáy phone)
HL_MAIL_TOP_XY = (275, 218)       # NV trên cùng danh sách Mail (mặc định dồn quà cho NV này)
HL_MAIL_GIFT_FIRST_XY = (694, 325)  # ô quà đầu (top-left) lưới quà Delivery
HL_MAIL_SEND_XY = (893, 646)      # nút "Send Gift" trên Delivery Service
_MAIL_LIST_REGION = (95, 178, 460, 700)  # vùng list NV bên trái (dùng khi khớp tên custom)
_MAIL_AFF_REGION = (755, 198, 1090, 224)  # vùng Lv+thanh Affinity — đổi sau mỗi lần gửi; đứng yên = cap 10/10

# --- Ưu tiên theo tên NV (③): portrait template ở assets/en/heartlink/chars/<slug>.png ---
# Lưới thứ tự CỐ ĐỊNH (NV đã hẹn KHÔNG bị đẩy xuống) → grid-order luôn chọn top; muốn hẹn favorite ở
# dưới phải cuộn tìm portrait. Template = mặt NV (crop tránh viền chọn + badge ✓). Chỉ cần crop cho
# favorite người dùng chỉ định (roster 18+ NV, không làm registry toàn bộ). Chưa có template → grid-order.
_CHARS_DIR = ROOT / 'assets' / 'en' / 'heartlink' / 'chars'
_GRID_REGION = (95, 178, 460, 700)   # vùng lưới portrait trên phone (x1,y1,x2,y2)
_PORTRAIT_THRESHOLD = 0.80


def _slug(name: str) -> str:
    """'Snowish Laru' -> 'snowish_laru' (khớp tên file portrait, không phân biệt hoa/thường)."""
    return '_'.join(str(name).lower().split())


class Heartlink(UI):
    """Hẹn hò Heartlink tăng Affinity. 2 task con: Invite + Mail (Delivery Service). Mặc định TẮT."""

    def run(self) -> None:
        hl = self.config.heartlink
        try:
            self.ui_ensure(page_heartlink)              # Home → Heartlink phone (mở tab Chat)
            if hl.do_invite:
                self._run_invite(hl)
            if hl.do_mail:
                self._run_mail(hl)
        finally:
            self._exit_home()
        self.config.task_delay('Heartlink', server_reset=True)

    # --- Điều hướng ---

    def _open_tab(self, tab_xy, check_btn, label: str) -> bool:
        """Bấm 1 tab đáy phone (Invite/Mail) + xác nhận đã ở đó. Retry 4 lần + dismiss giữa các lần:
        sau một buổi date, overlay XẾP HÀNG nhiều lớp (reaction → Gifts Received → Affinity UP) —
        _dismiss_to_invite bắt được 1 frame Invite giữa các lớp rồi thoát, các lớp còn lại nuốt cú
        tap tab (live 2026-07-08: 2 tap Mail liên tiếp đều bị nuốt → retry 2 lần không đủ)."""
        for _ in range(4):
            self.device.click_xy(*tab_xy, name=f'HL_TAB_{label.upper()}')
            if self.wait_until_appear(check_btn, timeout=8):
                logger.info(f'Heartlink: đã vào tab {label}')
                return True
            # tap tab bị overlay nuốt → xả 1 lớp overlay rồi thử lại
            self.device.click_xy(*HL_DISMISS_XY, name='HL_TAB_DISMISS')
            time.sleep(1.0)
        logger.info(f'Heartlink: không mở được tab {label} — bỏ qua')
        return False

    def _run_invite(self, hl) -> None:
        if not self._open_tab(HL_TAB_INVITE_XY, HL_INVITE_TITLE, 'Invite'):
            return
        target = max(0, min(hl.invite_count, 5))
        did = self._invite_loop(target)
        logger.info(f'Heartlink: hoàn tất {did} lượt hẹn (mục tiêu {target})')

    def _run_mail(self, hl) -> None:
        if not self._open_tab(HL_TAB_MAIL_XY, HL_MAIL_TITLE, 'Mail'):
            return
        self._mail_loop(hl)

    def _enter_invite(self) -> bool:
        """Đảm bảo đang ở tab Invite (dùng khi recover). Home/phone → Invite tab."""
        self.ui_ensure(page_heartlink)
        return self._open_tab(HL_TAB_INVITE_XY, HL_INVITE_TITLE, 'Invite')

    def _exit_home(self) -> None:
        """Thoát phone Heartlink bằng nút nguồn (HEARTLINK_EXIT) → về Home."""
        for _ in range(4):
            self.device.screenshot()
            if self.appear(HOME_CHECK):
                return
            self.device.click(HEARTLINK_EXIT)
            time.sleep(2)
        self.ui_ensure(page_home)

    # --- Vòng lặp chọn NV + hẹn ---

    def _invite_loop(self, target: int) -> int:
        """(1) Ưu tiên hẹn các NV trong invite_targets (tìm portrait, cuộn lưới); (2) grid-order lấp
        phần còn lại (9 NV hiển thị đầu). Trả số lượt thành công. Dừng khi đạt target hoặc cap ngày."""
        did = 0
        # (1) Ưu tiên theo tên — hẹn favorite ở BẤT KỲ đâu trong lưới (cuộn tìm portrait)
        for name in self.config.heartlink.invite_targets:
            if did >= target:
                break
            if not self._find_and_select_char(_slug(name)):
                continue                       # không có template / không thấy trong lưới
            if self._char_state() != 'invite':
                logger.info(f'Heartlink: "{name}" đã hẹn hôm nay / không hẹn được — bỏ qua')
                continue
            r = self._do_one_invite()
            if r == 'ok':
                did += 1
                logger.info(f'Heartlink: hẹn xong "{name}" ({did}/{target})')
                time.sleep(1.0)
            elif r == 'capped':
                logger.info('Heartlink: đã đạt giới hạn ngày → dừng')
                return did
            elif not self._recover_to_invite():
                return did
        # (2) Grid-order lấp phần còn lại (9 NV hiển thị đầu; target≤5 hiếm khi cần cuộn)
        if did < target:
            self._scroll_top()
        for (cx, cy) in self._grid_cells():
            if did >= target:
                break
            self.device.click_xy(cx, cy, name='HL_SELECT_CHAR')
            if self._char_state() != 'invite':
                continue                       # 'invited' (đã hẹn) / 'unknown' → NV kế
            result = self._do_one_invite()
            if result == 'ok':
                did += 1
                logger.info(f'Heartlink: hẹn xong lượt {did}/{target} (grid-order)')
                time.sleep(1.0)
            elif result == 'capped':
                logger.info('Heartlink: Invite không mở Date Location — có thể đã đạt giới hạn ngày → dừng')
                break
            elif not self._recover_to_invite():
                logger.warning('Heartlink: mất màn Invite sau lượt lỗi — dừng vòng')
                break
        return did

    def _grid_cells(self):
        """Sinh toạ độ portrait theo grid-order: trái→phải, trên→dưới (3 hàng hiển thị)."""
        for cy in HL_GRID_ROWS:
            for cx in HL_GRID_COLS:
                yield (cx, cy)

    # --- Ưu tiên theo tên: tìm portrait + cuộn lưới (③/④) ---

    def _find_and_select_char(self, slug: str) -> bool:
        """Cuộn lưới từ đầu, match portrait NV theo slug; thấy thì tap chọn. Trả True nếu chọn được."""
        p = _CHARS_DIR / f'{slug}.png'
        if not p.exists():
            logger.info(f'Heartlink: bỏ target "{slug}" — chưa có portrait (assets/en/heartlink/chars/{slug}.png)')
            return False
        tmpl = cv2.imread(str(p))
        self._scroll_top()
        prev = None
        for _ in range(12):
            self.device.screenshot()
            hit = self._match_portrait(tmpl)
            if hit:
                self.device.click_xy(*hit, name=f'HL_CHAR_{slug}')
                time.sleep(0.5)
                return True
            x1, y1, x2, y2 = _GRID_REGION
            cur = self.device.image[y1:y2, x1:x2]
            if prev is not None and float(cv2.absdiff(cur, prev).mean()) < 1.5:
                logger.info(f'Heartlink: không thấy "{slug}" trong lưới (đã cuộn hết)')
                return False                   # cuộn tới đáy mà không thấy
            prev = cur
            self._scroll_grid(down=True)
        return False

    def _match_portrait(self, tmpl):
        """Match portrait tmpl trong vùng lưới của screenshot hiện tại. Trả (cx,cy) tâm hoặc None."""
        x1, y1, x2, y2 = _GRID_REGION
        roi = self.device.image[y1:y2, x1:x2]
        res = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
        _, mx, _, mloc = cv2.minMaxLoc(res)
        if mx < _PORTRAIT_THRESHOLD:
            return None
        th, tw = tmpl.shape[:2]
        return (x1 + mloc[0] + tw // 2, y1 + mloc[1] + th // 2)

    def _scroll_grid(self, down: bool = True) -> None:
        """Cuộn lưới NV. down=True xem NV phía dưới (vuốt từ dưới lên)."""
        if down:
            self.device.swipe(270, 520, 270, 300, 500, name='HL_SCROLL_DOWN')
        else:
            self.device.swipe(270, 300, 270, 520, 500, name='HL_SCROLL_UP')
        time.sleep(1.0)

    def _scroll_top(self) -> None:
        """Cuộn lưới về đầu (vuốt xuống tới khi lưới đứng yên)."""
        x1, y1, x2, y2 = _GRID_REGION
        prev = None
        for _ in range(8):
            self.device.screenshot()
            cur = self.device.image[y1:y2, x1:x2]
            if prev is not None and float(cv2.absdiff(cur, prev).mean()) < 1.5:
                return
            prev = cur
            self._scroll_grid(down=False)

    def _char_state(self, timeout: float = 4.0) -> str:
        """Poll panel phải tới khi rõ trạng thái NV đang chọn (panel render có LAG):
        'invite' (còn hẹn được) | 'invited' (đã hẹn, nút xám) | 'unknown' (không rõ trong timeout)."""
        end = time.time() + timeout
        while time.time() < end:
            self.device.screenshot()
            if self.appear(HL_INVITE_BTN):
                return 'invite'
            if self.appear(HL_INVITED_TODAY):
                return 'invited'
            time.sleep(0.4)
        return 'unknown'

    def _do_one_invite(self) -> str:
        """Hẹn 1 lượt cho NV đang chọn (HL_INVITE_BTN active). Trả:
        'ok' (về lại màn Invite) | 'capped' (Invite không mở Location = cap ngày) | 'fail' (lỗi giữa flow)."""
        self.device.click_xy(*HL_INVITE_BTN_XY, name='HL_INVITE')
        # 0)+1) Poll CHUNG dialog "Start Invitation" (hiện lại sau reset ngày, có thể render trễ)
        # và màn Select Date Location trong 1 vòng. 2 vòng chờ tuần tự (3s dialog rồi 8s Location)
        # từng gây false-cap khi dialog trễ >3s: Confirm không được bấm → hiểu nhầm CAP → mất trọn
        # quota ngày (review 2026-07-08). Không mở được Location = đã cap ngày / bị chặn.
        deadline = time.time() + 12
        while time.time() < deadline:
            self.device.screenshot()
            if self.appear(HL_SELECT_LOCATION):
                break
            if self.appear(HL_START_INVITATION):
                self.device.click_xy(*HL_INVITE_CONFIRM_XY, name='HL_INVITE_CONFIRM')
                time.sleep(1.2)
                deadline = max(deadline, time.time() + 8)   # đã Confirm → chờ thêm Location mở
                continue
            time.sleep(0.5)
        if not self.appear(HL_SELECT_LOCATION):
            return 'capped'
        self.device.click_xy(*HL_LOC_FIRST_XY, name='HL_LOC_FIRST')
        # 2) Travel + buổi hẹn → Skip tới khi hiện Send Gift/Leave
        if not self._skip_date():
            return 'fail'
        # 3) Send Gift (x2) hoặc Leave
        if self.config.heartlink.send_gift and self._send_gift():
            pass
        else:
            self.device.click_xy(*HL_LEAVE_XY, name='HL_LEAVE')
        # 4) Dismiss overlay → về Invite
        return 'ok' if self._dismiss_to_invite() else 'fail'

    def _skip_date(self) -> bool:
        """Tap Skip ▶| tua nhanh buổi hẹn tới khi hiện lựa chọn cuối (HL_SEND_GIFT). Trả True nếu tới."""
        end = time.time() + 45
        while time.time() < end:
            time.sleep(1.5)
            self.device.screenshot()
            if self.appear(HL_SEND_GIFT):
                return True
            if self.appear(HL_SELECT_LOCATION):
                continue                        # màn location chưa đóng → chờ
            self.device.click_xy(*HL_SKIP_XY, name='HL_SKIP')
        logger.warning('Heartlink: không tới cuối buổi hẹn sau 45s — bỏ lượt')
        return False

    def _send_gift(self) -> bool:
        """Send Gift → lưới quà → chọn ô đầu → Send Gift chốt. Trả True nếu đã bấm gửi."""
        self.device.click_xy(*HL_SEND_GIFT_XY, name='HL_SEND_GIFT')
        if not self.wait_until_appear(HL_GIFT_NEVERMIND, timeout=8):
            logger.warning('Heartlink: không mở được lưới quà — chuyển Leave')
            return False
        self.device.click_xy(*HL_GIFT_FIRST_XY, name='HL_GIFT_FIRST')   # chọn quà đầu (loved)
        time.sleep(1.0)
        self.device.click_xy(*HL_GIFT_SEND_XY, name='HL_GIFT_SEND')     # chốt gửi
        return True

    def _dismiss_to_invite(self, timeout: int = 28) -> bool:
        """Tap vùng trống dismiss reaction / 'Gifts Received!' / 'Affinity UP' tới khi về màn Invite."""
        end = time.time() + timeout
        while time.time() < end:
            self.device.screenshot()
            if self.appear(HL_INVITE_TITLE):
                return True
            self.device.click_xy(*HL_DISMISS_XY, name='HL_DISMISS')
            time.sleep(1.3)
        return self.appear(HL_INVITE_TITLE)

    def _recover_to_invite(self) -> bool:
        """Cố về màn Invite sau lượt lỗi: tap dismiss vài lần; không được thì exit+reenter phone."""
        if self._dismiss_to_invite(timeout=10):
            return True
        self.device.click(HEARTLINK_EXIT)
        time.sleep(2)
        return self._enter_invite()

    # --- Task con Mail (Delivery Service): gửi quà tăng affinity, 10/ngày (GLOBAL) ---
    # ⚠️ SEND LOOP CHƯA VERIFY LIVE (account 10/10 lúc build 2026-07-08) — refine sau reset. An toàn:
    # game tự chặn ở 10/10 nên KHÔNG gửi quá được. Cơ chế giả định như màn quà date (tap ô quà đầu →
    # Send Gift → dismiss reaction/level-up). Cap phát hiện bằng thanh Affinity đứng yên (_MAIL_AFF_REGION).

    def _mail_loop(self, hl) -> None:
        """Gửi quà Delivery. Mặc định (mail_targets rỗng): dồn mail_count quà cho NV TRÊN CÙNG list.
        Custom: gửi qty quà cho từng (name,qty) khớp portrait, tổng ≤ mail_count & ≤10; tên không thấy → bỏ."""
        total = max(1, min(hl.mail_count, 10))
        targets = [(t.name, t.qty) for t in hl.mail_targets if str(t.name).strip() and t.qty > 0]
        sent = 0
        if targets:
            for name, qty in targets:
                if sent >= total:
                    break
                if not self._select_mail_char(_slug(name)):
                    logger.info(f'Heartlink Mail: không thấy NV "{name}" — bỏ')
                    continue
                s = self._send_gifts(min(qty, total - sent))
                sent += s
                logger.info(f'Heartlink Mail: gửi {s} quà cho "{name}" ({sent}/{total})')
                if s == 0:
                    break                            # cap global / gửi không thành → dừng
        else:
            self.device.click_xy(*HL_MAIL_TOP_XY, name='HL_MAIL_TOP')   # dồn cho NV trên cùng
            time.sleep(1.0)
            sent = self._send_gifts(total)
        logger.info(f'Heartlink Mail: hoàn tất {sent} quà Delivery')

    def _send_gifts(self, n: int) -> int:
        """Gửi tối đa n quà cho NV đang chọn: tap ô quà đầu → Send Gift → dismiss. Trả số đã gửi.
        Dừng khi rời Delivery Service hoặc thanh Affinity không đổi (cap global 10/10)."""
        sent = 0
        ax1, ay1, ax2, ay2 = _MAIL_AFF_REGION
        for _ in range(max(0, n)):
            self.device.screenshot()
            if not self.appear(HL_MAIL_TITLE):
                break                            # không còn ở Delivery Service
            before = self.device.image[ay1:ay2, ax1:ax2].copy()
            self.device.click_xy(*HL_MAIL_GIFT_FIRST_XY, name='HL_MAIL_GIFT')  # chọn ô quà đầu (loved)
            time.sleep(0.6)
            self.device.click_xy(*HL_MAIL_SEND_XY, name='HL_MAIL_SEND')        # Send Gift
            time.sleep(1.3)
            self._dismiss_to_mail()              # qua reaction / "Affinity UP" nếu có
            self.device.screenshot()
            after = self.device.image[ay1:ay2, ax1:ax2]
            if float(cv2.absdiff(after, before).mean()) < 1.5:
                logger.info('Heartlink Mail: Affinity không đổi — có thể đã 10/10 → dừng')
                break                            # gửi không thành (cap global)
            sent += 1
        return sent

    def _dismiss_to_mail(self, timeout: int = 12) -> bool:
        """Tap vùng trống dismiss reaction/level-up tới khi về lại Delivery Service."""
        end = time.time() + timeout
        while time.time() < end:
            self.device.screenshot()
            if self.appear(HL_MAIL_TITLE):
                return True
            self.device.click_xy(*HL_DISMISS_XY, name='HL_MAIL_DISMISS')
            time.sleep(1.0)
        return self.appear(HL_MAIL_TITLE)

    def _select_mail_char(self, slug: str) -> bool:
        """Cuộn list Mail tìm portrait NV theo slug + tap chọn. Trả True nếu chọn được.
        ⚠️ Portrait list Mail nhỏ hơn lưới Invite → có thể cần crop template riêng (chưa làm; verify sau)."""
        p = _CHARS_DIR / f'{slug}.png'
        if not p.exists():
            logger.info(f'Heartlink Mail: bỏ "{slug}" — chưa có portrait (assets/en/heartlink/chars/)')
            return False
        tmpl = cv2.imread(str(p))
        self._scroll_top()          # về đầu list — target sau có thể nằm TRÊN vị trí lần tìm trước
        x1, y1, x2, y2 = _MAIL_LIST_REGION
        prev = None
        for _ in range(10):
            self.device.screenshot()
            roi = self.device.image[y1:y2, x1:x2]
            res = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
            _, mx, _, mloc = cv2.minMaxLoc(res)
            if mx >= _PORTRAIT_THRESHOLD:
                th, tw = tmpl.shape[:2]
                self.device.click_xy(x1 + mloc[0] + tw // 2, y1 + mloc[1] + th // 2, name=f'HL_MAIL_{slug}')
                time.sleep(0.8)
                return True
            cur = self.device.image[y1:y2, x1:x2]
            if prev is not None and float(cv2.absdiff(cur, prev).mean()) < 1.5:
                return False                     # cuộn hết list không thấy
            prev = cur
            self._scroll_grid(down=True)
        return False
