import time
from collections import deque

import cv2
import numpy as np

from module.device.adb import Adb
from module.exception import GameTooManyClickError, RequestHumanTakeover, TaskInterrupted
from module.logger import logger
from module.stop_signal import stop_requested

# screencap qua adb shell có thể bị đổi line-ending tùy Android version (bẫy kinh điển ALAS xử lý)
_PNG_FIXES = (lambda d: d,
              lambda d: d.replace(b'\r\n', b'\n'),
              lambda d: d.replace(b'\r\r\n', b'\n'))


class Device:
    def __init__(self, config):
        self.config = config
        self.adb = Adb(config.emulator.serial, config.emulator.adb_path)
        self.image: np.ndarray | None = None  # screenshot mới nhất (BGR)
        self._png_fix_index = 0               # cache kiểu line-ending đã decode thành công
        self._click_record = deque(maxlen=12)

    def connect(self) -> None:
        self.adb.connect()

    def _abort_if_stop_requested(self) -> None:
        # Chokepoint nút [Dừng]: task nào cũng screenshot/click liên tục nên ngắt ở đây
        # ăn gần như ngay (trễ tối đa ~1 nhịp sleep của task).
        if stop_requested():
            raise TaskInterrupted('Người dùng bấm Dừng')

    # --- screenshot ---

    def screenshot(self) -> np.ndarray:
        """Chụp màn hình, trả về BGR ndarray. Game landscape → ảnh 1280×720 (W×H), tức shape (720, 1280) = (h, w)."""
        self._abort_if_stop_requested()
        for attempt in range(3):
            img = self._decode(self.adb.screenshot_png())
            if img.shape[:2] == (720, 1280):
                self.image = img
                return img
            # portrait/kích thước lạ: thường là transient (launcher, màn hình xoay dở)
            logger.debug(f'Screenshot {img.shape[:2]} != (720, 1280), thử lại {attempt + 1}/3')
            time.sleep(1)
        raise RequestHumanTakeover(
            f'Screenshot ra {img.shape[:2]} thay vì (720, 1280) — kiểm tra độ phân giải giả lập '
            f'và game có đang landscape không.')

    def _decode(self, data: bytes) -> np.ndarray:
        order = [self._png_fix_index] + [i for i in range(len(_PNG_FIXES)) if i != self._png_fix_index]
        for i in order:
            img = cv2.imdecode(np.frombuffer(_PNG_FIXES[i](data), np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                self._png_fix_index = i
                return img
        raise RequestHumanTakeover('Không decode được PNG từ screencap — ADB trả dữ liệu hỏng.')

    # --- control ---

    def click(self, button) -> None:
        self._abort_if_stop_requested()
        x, y = button.click_point()
        self._click_record.append(button.name)
        self._check_click_record()
        logger.info(f'Click {button.name} @ ({int(x)}, {int(y)})')
        self.adb.tap(x, y)

    def click_xy(self, x: int, y: int, name: str = 'RAW') -> None:
        self._abort_if_stop_requested()
        self._click_record.append(name)
        self._check_click_record()
        logger.info(f'Click {name} @ ({x}, {y})')
        self.adb.tap(x, y)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300,
              name: str = 'SWIPE') -> None:
        """Vuốt (cuộn danh sách). Không tính vào click-record chống double-click."""
        self._abort_if_stop_requested()
        logger.info(f'Swipe {name} ({x1},{y1})->({x2},{y2})')
        self.adb.swipe(x1, y1, x2, y2, duration_ms)

    def _check_click_record(self) -> None:
        r = list(self._click_record)
        if len(r) == self._click_record.maxlen and len(set(r)) <= 2:
            self._click_record.clear()
            raise GameTooManyClickError(f'Click lặp quá nhiều: {set(r)}')

    # --- app ---

    @property
    def package(self) -> str:
        return self.config.emulator.package

    def app_current(self) -> str:
        return self.adb.app_current()

    def app_is_running(self) -> bool:
        return self.app_current() == self.package

    def app_start(self) -> None:
        logger.info(f'Khởi động {self.package}')
        self.adb.app_start(self.package)

    def app_stop(self) -> None:
        logger.info(f'Dừng {self.package}')
        self.adb.app_stop(self.package)
