import re
import subprocess
import time

import adbutils

from module.exception import EmulatorNotRunningError, RequestHumanTakeover
from module.logger import logger

# Lỗi transport ADB đáng retry (rớt kết nối transient). EmulatorNotRunningError gộp vào vì reconnect
# giữa session có thể trúng lúc giả lập chưa sẵn sàng lại → vẫn nên thử tiếp. Các lỗi LOGIC (TaskError,
# GameStuckError, GameTooManyClickError, RequestHumanTakeover) KHÔNG phải subclass các loại này nên
# không bị nuốt nhầm. OSError bao ConnectionResetError/BrokenPipeError/TimeoutError/socket.timeout.
_ADB_RETRYABLE = (adbutils.AdbError, OSError, EmulatorNotRunningError)


class Adb:
    """Wrapper mỏng quanh adbutils: 1 serial, 1 adb server chạy từ đúng binary cấu hình.
    shell() tự reconnect + retry khi transport rớt để 1 lần mất ADB không giết cả session dài."""

    _RETRY_BACKOFF = (2, 5, 10)  # giây chờ tăng dần trước mỗi lần reconnect + thử lại shell()

    def __init__(self, serial: str, adb_path: str = 'adb'):
        self.serial = serial
        self.adb_path = adb_path
        self._client = adbutils.AdbClient(host='127.0.0.1', port=5037)
        self._device = None

    def connect(self) -> None:
        # Chạy start-server bằng đúng binary cấu hình để tránh 2 bản adb khác version kill nhau
        subprocess.run([self.adb_path, 'start-server'], capture_output=True)
        try:
            self._client.connect(self.serial, timeout=5)
        except adbutils.AdbError as e:
            raise EmulatorNotRunningError(
                f'Không connect được {self.serial} — giả lập đã mở chưa? ({e})')
        serials = [d.serial for d in self._client.device_list()]
        if self.serial not in serials:
            raise EmulatorNotRunningError(
                f'{self.serial} không có trong adb devices: {serials}')
        self._device = self._client.device(self.serial)
        logger.info(f'Đã kết nối {self.serial}')

    @property
    def device(self) -> adbutils.AdbDevice:
        if self._device is None:
            self.connect()
        return self._device

    def shell(self, cmd: str, encoding='utf-8'):
        """Gửi lệnh shell qua ADB; tự reconnect + thử lại khi transport rớt (AdbError 'closed',
        ConnectionReset...) để 1 lần rớt ADB không giết cả phiên chạy dài (đã gặp: session 26/70 run
        chết vì AdbError giữa lúc mua slot shop). Cạn retry → RequestHumanTakeover.
        ⚠️ Khi retry, lệnh (vd input tap) có thể được GỬI LẠI — an toàn ở hầu hết điểm gọi; nút mua/
        enhance đã có guard đối chiếu coin (tasks/ascension.py) hấp thụ trường hợp double-tap hiếm."""
        last_exc = None
        for attempt in range(len(self._RETRY_BACKOFF) + 1):
            try:
                return self.device.shell(cmd, encoding=encoding)
            except _ADB_RETRYABLE as e:
                last_exc = e
                self._device = None  # transport cũ hỏng → property .device sẽ connect() lại lần sau
                if attempt >= len(self._RETRY_BACKOFF):
                    break
                wait = self._RETRY_BACKOFF[attempt]
                logger.warning(
                    f'ADB shell lỗi ({e!r}) — reconnect + thử lại '
                    f'{attempt + 1}/{len(self._RETRY_BACKOFF)} sau {wait}s (cmd={cmd[:40]!r})')
                time.sleep(wait)
        raise RequestHumanTakeover(
            f'Mất kết nối ADB tới {self.serial} sau {len(self._RETRY_BACKOFF)} lần retry '
            f'({last_exc!r}) — cmd cuối {cmd[:80]!r}. Kiểm tra giả lập / adb server.'
        ) from last_exc

    def screenshot_png(self) -> bytes:
        return self.shell('screencap -p', encoding=None)

    def tap(self, x: int, y: int) -> None:
        self.shell(f'input tap {int(x)} {int(y)}')

    def swipe(self, x1, y1, x2, y2, duration_ms: int = 300) -> None:
        self.shell(f'input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration_ms)}')

    def app_current(self) -> str:
        """Package đang focus, '' nếu không xác định được."""
        out = self.shell('dumpsys window')
        m = re.search(r'mCurrentFocus=Window\{[^ ]+ [^ ]+ ([^/ ]+)/', out)
        return m.group(1) if m else ''

    def app_start(self, package: str) -> None:
        self.shell(f'monkey -p {package} -c android.intent.category.LAUNCHER 1')

    def app_stop(self, package: str) -> None:
        self.shell(f'am force-stop {package}')
